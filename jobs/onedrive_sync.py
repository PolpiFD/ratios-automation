import os, asyncio, logging, re
from datetime import datetime, timezone
import msal
import httpx
from azure.data.tables import TableClient

from dotenv import load_dotenv
load_dotenv()

#------------CONFIG-------------------------------------
CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
TENANT_ID = os.getenv("AZURE_TENANT_ID")
CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
UPN = os.getenv("AZURE_UPN")
#-------------------------------------------------------

#Obtention du token 
app = msal.ConfidentialClientApplication(
    client_id=CLIENT_ID,
    client_credential=CLIENT_SECRET,
    authority=f"https://login.microsoftonline.com/{TENANT_ID}"
)
token = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
access_token = token["access_token"]
print(access_token)

headers = {"Authorization": f"Bearer {access_token}"}

with httpx.Client(base_url="https://graph.microsoft.com/v1.0",
                  headers=headers, timeout=30) as session:
    resp = session.get(f"/users/{UPN}/drive")
    resp.raise_for_status()
    drive_info = resp.json()

print("Drive ID :", drive_info["id"])