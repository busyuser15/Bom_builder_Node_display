import requests

# ------------------------------
# 1️⃣ AUTHENTICATION
# ------------------------------
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

token_resp = requests.post(TOKEN_URL, data=token_data)
token_resp.raise_for_status()
access_token = token_resp.json()["access_token"]

headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

url = f"https://api.businesscentral.dynamics.com/v2.0/{TENANT_ID}/CKIN01_UAT_131224/api/v2.0/companies"
resp = requests.get(url, headers=headers)
print(resp.json())
