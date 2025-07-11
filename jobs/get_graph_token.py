import os, asyncio, pathlib
import msal
from msal import SerializableTokenCache
import httpx
from dotenv import load_dotenv

load_dotenv()

#------------CONFIG-------------------------------------
CACHE_PATH = pathlib.Path(__file__).resolve().parents[1] / ".msal_ratios.cache"
CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
TENANT_ID = os.getenv("AZURE_TENANT_ID")
SCOPES = ["Files.ReadWrite.All"]
#-------------------------------------------------------

#Verification si token en cache

token_cache = SerializableTokenCache()
if CACHE_PATH.exists():
    token_cache.deserialize(CACHE_PATH.read_text())

#Obtention du token 
app = msal.PublicClientApplication (
    client_id=CLIENT_ID,
    authority=f"https://login.microsoftonline.com/{TENANT_ID}",
    token_cache=token_cache
)

def get_graph_token():

    # 1) Tente le cache d'abord
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])
        if result and "access_token" in result:
            return result["access_token"]

    # 2) sinon on lance le device-code flow une fois
    flow = app.initiate_device_flow(scopes=SCOPES)
    print(f"Variable flow >>> {flow}")
    if "user_code" not in flow:
        raise RuntimeError("Device-code flow impossible: " + str(flow))
    
    print(">>> Ouvre", flow["verification_uri"])
    print(">>> Entre le code :", flow["user_code"])

    result = app.acquire_token_by_device_flow(flow)
    if "access_token" not in result:
        raise RuntimeError("Auth failed:" + str(result))
    CACHE_PATH.write_text(token_cache.serialize())
    return result["access_token"]

token = get_graph_token()

async def main():
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(
        base_url="https://graph.microsoft.com/v1.0",
        headers=headers,
        timeout=30
    ) as client:
        me_drive = await client.get("/me/drive")
        me_drive.raise_for_status()
        print("Mon drive ID : " + me_drive.json()["id"])

if __name__ == "__main__":
    asyncio.run(main())
