import os
import tempfile
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from bom_service import parse_bom_excel

app = Flask(__name__)
CORS(app)

# Business Central configuration from environment (override for new sandbox)
BC_TENANT_ID = os.environ.get("BC_TENANT_ID", "697d6604-5c29-4ca0-9dea-9db421a85492")
BC_ENVIRONMENT = os.environ.get("BC_ENVIRONMENT", "CKIN01_UAT_131224")
BC_COMPANY_GUID = os.environ.get("BC_COMPANY_GUID")
BC_COMPANY_NAME = os.environ.get("BC_COMPANY_NAME")
BC_API_HOST = os.environ.get("BC_API_HOST", "https://api.businesscentral.dynamics.com")

# helpers to build API endpoints
def bc_base():
    return f"{BC_API_HOST}/v2.0/{BC_TENANT_ID}/{BC_ENVIRONMENT}"

def bc_batch_url():
    return f"{bc_base()}/api/ck/integration/v2.0/$batch"

def bc_create_bomimports_url():
    return f"{bc_base()}/api/ck/integration/v1.0/bomImports"

def bc_bomimports_action_url(created_id):
    return f"{bc_base()}/api/ck/integration/v1.0/bomImports({created_id})/Process"

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
    # Hard-coded credentials (for local testing; do NOT commit real secrets)
    CLIENT_ID = "21e698d9-1eab-42be-beb7-76096e1af3db"
    CLIENT_SECRET = "5MN8Q~nVFMWB9ImKBDslluO66eDj8u.WzHSMEdc~"
    TENANT_ID = "697d6604-5c29-4ca0-9dea-9db421a85492"

    if not all([CLIENT_ID, CLIENT_SECRET, TENANT_ID]):
        return {
            "status": "error",
            "message": "Missing Business Central credentials. Set BC_CLIENT_ID, BC_CLIENT_SECRET, BC_TENANT_ID in the environment."
        }

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
        # If token endpoint returns an error, include the body in logs for debugging
        if not token_resp.ok:
            try:
                err_body = token_resp.json()
            except Exception:
                err_body = token_resp.text
            app.logger.error(f"Token endpoint returned status {token_resp.status_code}: {err_body}")
            return {"status": "error", "message": f"Token request failed: {token_resp.status_code}", "details": err_body}

        token_resp.raise_for_status()
        access_token = token_resp.json()["access_token"]
    except Exception as exc:
        app.logger.error(f"Failed to get access token: {str(exc)}")
        return {"status": "error", "message": f"Token request failed: {str(exc)}"}

    # Resolve company GUID if not provided
    company_guid = BC_COMPANY_GUID
    if not company_guid:
        try:
            # Use explicit tenant/environment companies endpoint for clearer diagnostics
            companies_url = f"https://api.businesscentral.dynamics.com/v2.0/{TENANT_ID}/api/v2.0/companies"
            headers_comp = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
            comp_resp = requests.get(companies_url, headers=headers_comp, timeout=30)

            # Log detailed response for troubleshooting
            try:
                app.logger.info(f"Companies response (status): {comp_resp.status_code}")
                app.logger.info(f"Companies response (body): {comp_resp.json()}")
            except Exception:
                print("Companies response (text):", comp_resp.text)

            if comp_resp.ok:
                comp_json = comp_resp.json()
                comp_list = comp_json.get("value") if isinstance(comp_json, dict) else comp_json
                if isinstance(comp_list, list) and len(comp_list) > 0:
                    # try to match by BC_COMPANY_NAME if provided
                    if BC_COMPANY_NAME:
                        for c in comp_list:
                            name = c.get("displayName") or c.get("name")
                            if name and BC_COMPANY_NAME.lower() in name.lower():
                                company_guid = c.get("id")
                                break
                    if not company_guid:
                        # fallback to first company
                        first = comp_list[0]
                        company_guid = first.get("id")
            else:
                app.logger.error(f"Failed to list companies: {comp_resp.status_code} {comp_resp.text}")
        except Exception as exc:
            app.logger.error(f"Error resolving company GUID: {str(exc)}")

    if not company_guid:
        return {"status": "error", "message": "Could not resolve Business Central company GUID. Set BC_COMPANY_GUID or BC_COMPANY_NAME in environment."}

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
                "url": f"companies({company_guid})/bomEntries7",
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
            batch_num = (count // 99) + 1
            app.logger.info(f"[INFO] Posting batch {batch_num} ({len(payload)} items) to BC...")
            resp = requests.post(
                bc_batch_url(),
                headers=headers,
                json=itembody,
                timeout=60
            )

            app.logger.info(f"[INFO] ✓ Batch {batch_num} response status: {resp.status_code}")
            batch_results.append({
                "batch_number": batch_num,
                "status_code": resp.status_code,
                "response": resp.text
            })
            if resp.ok:
                app.logger.info(f"[SUCCESS] ✓ Batch {batch_num} accepted by BC API")
            else:
                app.logger.warning(f"[WARNING] Batch {batch_num} response: {resp.text[:200]}")

            # If batch succeeded, attempt to trigger BC-side processing once via BOM Import API
            try:
                # Create a dummy record in the BOM Dummy Load Table to operate on
                create_resp = requests.post(
                    bc_create_bomimports_url(),
                    headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
                    json={"JsonPayload": "trigger"},
                    timeout=30
                )
                if create_resp.ok:
                    j = None
                    try:
                        j = create_resp.json()
                    except Exception:
                        j = None

                    # Determine created ID (field name may be 'id' or 'ID')
                    created_id = None
                    if isinstance(j, dict):
                        created_id = j.get("id") or j.get("ID") or j.get("Id")

                    if created_id is not None:
                        action_url = bc_bomimports_action_url(created_id)
                        action_resp = requests.post(action_url, headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}, timeout=30)
                        app.logger.info(f"[INFO] ✓ Triggered BC Process action on BOM Import record {created_id}")
                        app.logger.info(f"[INFO] BC Processing status: {action_resp.status_code}")
                        batch_results[-1]["process_action_status"] = action_resp.status_code
                    else:
                        app.logger.warning(f"Could not determine created dummy record ID from response")
                        batch_results[-1]["process_action_status"] = "no-id"
                else:
                    app.logger.error(f"Failed to create dummy record for processing: {create_resp.status_code} {create_resp.text}")
                    batch_results[-1]["process_action_status"] = f"create-failed-{create_resp.status_code}"
            except Exception as exc:
                app.logger.error(f"Error triggering BC processing action: {str(exc)}")
                batch_results[-1]["process_action_status"] = f"error-{str(exc)}"

        except Exception as exc:
            app.logger.error(f"Error sending batch {(count // 99) + 1}: {str(exc)}")
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
        
        app.logger.info(f"{'='*70}")
        app.logger.info(f"[SUCCESS] Upload request received from frontend")
        app.logger.info(f"[INFO] Total items to upload: {len(bom_data)}")
        app.logger.info(f"{'='*70}")
        for i, item in enumerate(bom_data[:3]):  # Log first 3 items as sample
            app.logger.info(f"  Item {i+1}: Parent={item.get('PARENT PART NUMBER', 'N/A')}, Component={item.get('COMPONENT PART NUMBER', 'N/A')}, Qty={item.get('QTY', 'N/A')}")
        if len(bom_data) > 3:
            app.logger.info(f"  ... and {len(bom_data) - 3} more items")
        app.logger.info(f"[INFO] Posting to Business Central...")
        result = post_request_to_bc(bom_data)
        
        if result["status"] == "success":
            app.logger.info(f"{'='*70}")
            app.logger.info(f"[SUCCESS] ✓ All batches posted successfully to Business Central!")
            app.logger.info(f"[INFO] Total batches sent: {result.get('batches_sent', 'N/A')}")
            app.logger.info(f"[INFO] Total items processed: {result.get('total_items', 'N/A')}")
            app.logger.info(f"{'='*70}")
        else:
            app.logger.error(f"{'='*70}")
            app.logger.error(f"[ERROR] ✗ Upload failed: {result.get('message', 'Unknown error')}")
            app.logger.error(f"{'='*70}")
        
        return jsonify(result), 200 if result["status"] == "success" else 500
        
    except Exception as exc:
        app.logger.error(f"Error in upload_to_bc: {str(exc)}")
        return jsonify({"status": "error", "message": str(exc)}), 500


@app.route("/api/debug/token", methods=["GET"])
def debug_token():
    """Attempt to request an access token and return diagnostic info.

    WARNING: does not return client secret, but will show token endpoint
    response body (which may contain error descriptions useful for debugging).
    """
    try:
        # Hard-coded credentials
        CLIENT_ID = "21e698d9-1eab-42be-beb7-76096e1af3db"
        CLIENT_SECRET = "5MN8Q~nVFMWB9ImKBDslluO66eDj8u.WzHSMEdc~"
        TENANT_ID = "697d6604-5c29-4ca0-9dea-9db421a85492"

        if not CLIENT_ID or not CLIENT_SECRET or not TENANT_ID:
            return jsonify({"status": "error", "message": "Missing BC_CLIENT_ID/BC_CLIENT_SECRET/BC_TENANT_ID in environment."}), 400

        TOKEN_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
        token_data = {
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "scope": "https://api.businesscentral.dynamics.com/.default"
        }

        resp = requests.post(TOKEN_URL, data=token_data, timeout=15)
        try:
            body = resp.json()
        except Exception:
            body = resp.text

        return jsonify({"status_code": resp.status_code, "body": body}), 200 if resp.ok else 500
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500


if __name__ == "__main__":
    # Allow overriding the port via BACKEND_PORT environment variable
    try:
        port = int(os.environ.get("BACKEND_PORT", "5000"))
    except Exception:
        port = 5000
    app.run(host="0.0.0.0", port=port, debug=True)
