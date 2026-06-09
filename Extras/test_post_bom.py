import requests
import json

BACKEND_URL = "http://localhost:5000"

def make_bom_entries():
    entries = []
    # create two parents with 5 children each
    for p in range(1, 3):
        parent = f"PARENT{p:03d}"
        for i in range(1, 6):
            comp = f"P{p}C{i:03d}"
            entry = {
                "LEVEL": 1,
                "PARENT PART NUMBER": parent,
                "COMPONENT PART NUMBER": comp,
                "STATUS": "Active",
                "TYPE": "PART",
                "QTY": 1.0,
                "Attrib:SPAREPART": "",
                "Attrib:SPAREPART SEVERITY": "",
                "Attrib:SPARESLISTQTY": 0
            }
            entries.append(entry)
    return entries

def main():
    bom_data = make_bom_entries()
    payload = {"bom_data": bom_data}

    url = f"{BACKEND_URL}/api/upload-to-bc"
    print(f"Posting {len(bom_data)} BOM entries to {url}")
    resp = requests.post(url, json=payload)
    try:
        print("Status:", resp.status_code)
        print(json.dumps(resp.json(), indent=2))
    except Exception:
        print("Response text:", resp.text)

if __name__ == '__main__':
    main()
