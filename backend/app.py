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
        rows = parse_bom_excel(temp_path)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass

    return jsonify({"rowCount": len(rows), "rows": rows})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
