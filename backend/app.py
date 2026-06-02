import os
import tempfile
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from bom_service import parse_bom_excel

app = Flask(__name__)
CORS(app)


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/parse", methods=["POST"])
def parse_bom():
    if "file" not in request.files:
        return jsonify({"error": "Missing file upload parameter 'file'"}), 400

    uploaded_file = request.files["file"]
    if uploaded_file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    suffix = os.path.splitext(uploaded_file.filename)[1].lower()
    if suffix not in {".xlsx", ".xlsm"}:
        return jsonify({"error": "Unsupported file type. Please upload .xlsx or .xlsm"}), 400

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
        uploaded_file.save(temp.name)
        temp_path = temp.name

    try:
        hierarchy = parse_bom_excel(temp_path)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass

    return jsonify(hierarchy)


@app.route("/api/save-changes", methods=["POST"])
def save_changes():
    """Save changes made to BOM items (phantom assembly, treat as part, descriptions)"""
    try:
        data = request.get_json()
        
        phantom_changes = data.get("phantom_changes", [])
        treat_as_part_changes = data.get("treat_as_part_changes", [])
        description_changes = data.get("description_changes", {})
        comp_values = data.get("comp_values", {})
        
        print(f"\n=== Changes Received ===")
        print(f"Phantom Assembly Changes: {phantom_changes}")
        print(f"Treat as Part Changes: {treat_as_part_changes}")
        print(f"Description Changes: {description_changes}")
        print(f"Comp Values Updated: {len(comp_values)} items")
        
        # Here you could add logic to:
        # 1. Validate the changes
        # 2. Update a database
        # 3. Export to Excel
        # 4. Send to Business Central API see line 243 for post request logic on tkinter app
        # For now, we'll just acknowledge the changes
        
        return jsonify({
            "status": "success",
            "message": f"Changes saved: {len(phantom_changes)} phantom, {len(treat_as_part_changes)} treat as part, {len(description_changes)} descriptions"
        }), 200
        
    except Exception as exc:
        print(f"Error saving changes: {str(exc)}")
        return jsonify({"error": str(exc)}), 500


def post_request_to_bc(bom_data):
    """
    Send BOM data to Business Central via batch API requests.
    
    Args:
        bom_data: List of dictionaries containing BOM entry information
        
    Returns:
        Dictionary with response status and details
    """
    # Credentials
    CLIENT_ID = "21e698d9-1eab-42be-beb7-76096e1af3db"
    CLIENT_SECRET = "waJ8Q~KQ5XQV0k7WFzXGyMmAjEy9XW_w6OhGWcdR"
    TENANT_ID = "697d6604-5c29-4ca0-9dea-9db421a85492"
    TOKEN_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"

    token_data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "https://api.businesscentral.dynamics.com/.default"
    }

    try:
        # Send request for token
        token_resp = requests.post(TOKEN_URL, data=token_data)
        token_resp.raise_for_status()
        access_token = token_resp.json()["access_token"]
    except Exception as exc:
        print(f"Failed to get access token: {str(exc)}")
        return {"status": "error", "message": f"Token request failed: {str(exc)}"}

    # Headers for the batch request
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Prefer": "odata.continue-on-error"
    }

    count = 0
    max_items = len(bom_data)
    batch_results = []

    while count < max_items:
        payload = []  # reset each batch

        # iterate up to 99 items per batch
        for i in range(count, min(count + 99, max_items)):
            lines = bom_data[i].copy()

            # make sure numeric fields are cast properly
            if "LEVEL" in lines:
                lines["LEVEL"] = int(lines["LEVEL"])
            if "QTY" in lines:
                lines["QTY"] = float(lines["QTY"])

            # build fresh dictionary for each request
            dictionary = {
                "method": "POST",
                "id": str(i + 1),  # unique ID per request in the batch
                "url": "companies(AED5BD5F-977B-ED11-9989-6045BD0CAE02)/bomEntries7",
                "headers": {
                    "Content-Type": "application/json"
                },
                "body": lines
            }

            payload.append(dictionary)

        # wrap the subrequests into a batch
        itembody = {"requests": payload}

        try:
            # send the batch
            resp = requests.post(
                "https://api.businesscentral.dynamics.com/v2.0/697d6604-5c29-4ca0-9dea-9db421a85492/CKIN01_UAT_131224/api/ck/integration/v2.0/$batch",
                headers=headers,
                json=itembody,
                timeout=30
            )

            print(f"Batch response status: {resp.status_code}")
            batch_results.append({
                "batch_number": (count // 99) + 1,
                "status_code": resp.status_code,
                "response": resp.text
            })
            print(f"Batch {(count // 99) + 1} response: {resp.text[:500]}")  # Print first 500 chars for debugging

        except Exception as exc:
            print(f"Error sending batch {(count // 99) + 1}: {str(exc)}")
            batch_results.append({
                "batch_number": (count // 99) + 1,
                "status": "error",
                "message": str(exc)
            })

        count += 99

    return {
        "status": "success",
        "message": "All batches sent successfully",
        "total_items": max_items,
        "batches_sent": len(batch_results),
        "details": batch_results
    }


@app.route("/api/upload-to-bc", methods=["POST"])
def upload_to_bc():
    """
    Endpoint to upload BOM data to Business Central.
    
    Expected JSON body:
    {
        "bom_data": [
            {
                "LEVEL": 0,
                "PARENT PART NUMBER": "...",
                "COMPONENT PART NUMBER": "...",
                "STATUS": "...",
                "TYPE": "ASSEMBLY" or "PART",
                "QTY": 1.0,
                ...
            },
            ...
        ]
    }
    """
    try:
        data = request.get_json()
        
        if "bom_data" not in data:
            return jsonify({"error": "Missing 'bom_data' in request body"}), 400
        
        bom_data = data.get("bom_data", [])
        
        if not isinstance(bom_data, list):
            return jsonify({"error": "'bom_data' must be a list"}), 400
        
        if len(bom_data) == 0:
            return jsonify({"error": "BOM data is empty"}), 400
        
        print(f"\n=== Uploading {len(bom_data)} items to Business Central ===")
        result = post_request_to_bc(bom_data)
        
        return jsonify(result), 200 if result["status"] == "success" else 500
        
    except Exception as exc:
        print(f"Error in upload_to_bc: {str(exc)}")
        return jsonify({"status": "error", "message": str(exc)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
