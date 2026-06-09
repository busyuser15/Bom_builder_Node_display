import requests
import json
import os


try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# Hard-coded credentials
CLIENT_ID = "21e698d9-1eab-42be-beb7-76096e1af3db"
CLIENT_SECRET = "5MN8Q~nVFMWB9ImKBDslluO66eDj8u.WzHSMEdc~"
TENANT_ID = "697d6604-5c29-4ca0-9dea-9db421a85492"

TOKEN_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"

token_data = {
    "grant_type": "client_credentials",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "scope": "https://api.businesscentral.dynamics.com/.default"
}

token_resp = requests.post(TOKEN_URL, data=token_data)
print(f"Token response status: {token_resp.status_code}")
if not token_resp.ok:
    print(f"Token error response: {token_resp.json()}")
    token_resp.raise_for_status()
access_token = token_resp.json()["access_token"]
print(f"Access token obtained: {access_token[:20]}...")  # Print first 20 chars for verification

# Companies endpoint requires BC_ENVIRONMENT in the URL
BC_ENVIRONMENT = "CKIN01_UAT_08052026"

url = f"https://api.businesscentral.dynamics.com/v2.0/{TENANT_ID}/{BC_ENVIRONMENT}/api/v2.0/companies"

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

response = requests.get(url, headers=headers)

print(f"Companies response status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    
    # Extract and print GUIDs
    for company in data.get("value", []):
        print(f"Company Name: {company['name']}")
        print(f"Company GUID: {company['id']}")
        print("-" * 40)

else:
    print(response.text)

