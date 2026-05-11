import os
import tempfile
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
        # 4. Send to Business Central API
        # For now, we'll just acknowledge the changes
        
        return jsonify({
            "status": "success",
            "message": f"Changes saved: {len(phantom_changes)} phantom, {len(treat_as_part_changes)} treat as part, {len(description_changes)} descriptions"
        }), 200
        
    except Exception as exc:
        print(f"Error saving changes: {str(exc)}")
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
