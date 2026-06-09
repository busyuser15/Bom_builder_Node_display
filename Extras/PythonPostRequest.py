import requests
import json
import os

# ------------------------------
# 1️⃣ AUTHENTICATION (use environment variables)
# ------------------------------
# Optionally load a local .env if python-dotenv is installed (development only)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

CLIENT_ID = os.environ.get("BC_CLIENT_ID")
CLIENT_SECRET = os.environ.get("BC_CLIENT_SECRET")
TENANT_ID = os.environ.get("BC_TENANT_ID")
if not all([CLIENT_ID, CLIENT_SECRET, TENANT_ID]):
    raise RuntimeError(
        "Missing Business Central credentials. Set BC_CLIENT_ID, BC_CLIENT_SECRET, BC_TENANT_ID in environment or a .env file"
    )

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
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json",
    "Prefer": "odata.continue-on-error"
}

# ------------------------------
# 2️⃣ API ENDPOINTS (GET instead of POST)
# ------------------------------
# Note: Use "API" endpoints (preferred over OData) if available in your environment.
# Replace <companyId> or company name as needed.
BASE_URL = "https://api.businesscentral.dynamics.com/v2.0/697d6604-5c29-4ca0-9dea-9db421a85492/CKIN01_UAT_131224/api/v2.0/companies(17813768-9200-ef11-9f88-6045bdd223c3)"
BATCH_URL = "https://{{BASE_URL}}/api/v2.0/$batch"
# Items
# ✅ Items
ITEMS_URL = "https://api.businesscentral.dynamics.com/v2.0/697d6604-5c29-4ca0-9dea-9db421a85492/CKIN01_UAT_131224/ODataV4/Company('CK%20International%20Ltd')/Items"

# ✅ BOM Header
BOM_HEADER_URL = "https://api.businesscentral.dynamics.com/v2.0/697d6604-5c29-4ca0-9dea-9db421a85492/CKIN01_UAT_131224/ODataV4/Company('CK%20International')/ProductionBOMHeader"

# ✅ BOM Line
BOM_LINES_URL = "https://api.businesscentral.dynamics.com/v2.0/697d6604-5c29-4ca0-9dea-9db421a85492/CKIN01_UAT_131224/ODataV4/Company('CK%20International')/ProductionBOMLine"

Itembody = {
	"requests": [
        {
			"method": "POST",
			"id": "1",
			"url":"companies(AED5BD5F-977B-ED11-9989-6045BD0CAE02)/bomEntries7",
			"headers": headers,
            "body": {
                "LEVEL": 1,
                "PARENT_PART_NUMBER": "PARENT001",
                "COMPONENT_PART_NUMBER": "COMP001",
                "STATUS": "Active",
                "TYPE": "Normal",
                "QTY": 10,
                "Attrib_SPAREPART": "True",
                "Attrib_SPAREPART_SEVERITY": "Low",
                "Attrib_SPARESLISTQTY": 2,
                "Phantom_Assembly": False,
                "Treat_as_part": True,
                "Description": "Sample BOM Component"
	            }
        },
		{
			"method": "POST",
			"id": "2",
			"url":"companies(AED5BD5F-977B-ED11-9989-6045BD0CAE02)/bomEntries7",
			"headers": headers,
            "body": {
                "LEVEL": 1,
                "PARENT_PART_NUMBER": "PARENT002",
                "COMPONENT_PART_NUMBER": "COMP002",
                "STATUS": "Active",
                "TYPE": "Normal",
                "QTY": 10,
                "Attrib_SPAREPART": "True",
                "Attrib_SPAREPART_SEVERITY": "Low",
                "Attrib_SPARESLISTQTY": 2,
                "Phantom_Assembly": False,
                "Treat_as_part": True,
                "Description": "Sample BOM Component 2"
	            }
		}

    ]
}

Headbody = {
	"requests": [
        {
			"method": "GET",
			"id": "2",
			#"url": "https://api.businesscentral.dynamics.com/v2.0/697d6604-5c29-4ca0-9dea-9db421a85492/CKIN01_UAT_131224/ODataV4/Company('CK%20International%20Ltd')/Items",
			"url":"companies(AED5BD5F-977B-ED11-9989-6045BD0CAE02)/productionBOMHeaders?$top=3",
            "headers": headers
		},
        #{
		#	"method": "GET",
		#	"id": "1",
		#	"url":"companies(AED5BD5F-977B-ED11-9989-6045BD0CAE02)/Production BOM Header?$filter=number eq '001014'",
		#	"headers": headers
        #}
    ]
}


#https://api.businesscentral.dynamics.com/v2.0/CKIN01_UAT_131224/api/v2.0/companies('CK%20International%20Ltd')/Items('001008')

#https://{{baseurl}}/api/[publisher]/[group]/[version]/$batch
Itemresponse = requests.post("https://api.businesscentral.dynamics.com/v2.0/697d6604-5c29-4ca0-9dea-9db421a85492/CKIN01_UAT_131224/api/ck/integration/v2.0/$batch",headers=headers,json=Itembody,)
print(Itemresponse.status_code)
print(Itemresponse.text)

#Headresponse = requests.post("https://api.businesscentral.dynamics.com/v2.0/697d6604-5c29-4ca0-9dea-9db421a85492/CKIN01_UAT_131224/api/v2.0/$batch",headers=headers,json=Headbody, )
#print(Headresponse.status_code)
#print(Headresponse.text)


#Production BOM Header (99000771)
#Where-Used Line (99000790)