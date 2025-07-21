import os, aiofiles, httpx, asyncio
from azure.data.tables.aio import TableClient
from azure.identity.aio import DefaultAzureCredential

# ---- CONFIG -----------------------------------------------------------------
TABLE_URL  = "https://ratiostorage.table.core.windows.net"
TABLE_NAME = "ClientFolderIndex"
CLIENT_ID  = os.getenv("AZURE_CLIENT_ID")          # service principal
DRIVE_ID   = os.getenv("DRIVE_ID")                 # id global du drive
# -----------------------------------------------------------------------------


async def query_folder_id(client_folder_id: str, categorie: str) -> str | None:
    """
    Cherche l'entity dont:
        client_folder_id == <client_folder_id>
        ET category        == <categorie>
    Retourne folder_id ou None.
    """
    credential = DefaultAzureCredential(managed_identity_client_id=CLIENT_ID)
    async with TableClient(TABLE_URL, TABLE_NAME, credential=credential) as table:
        filt = (
            f"client_folder_id eq '{client_folder_id}' "
            f"and RowKey eq '{categorie}'"
        )
        entities = table.query_entities(query_filter=filt, results_per_page=1)
        async for page in entities.by_page():
            async for e in page:
                return e["folder_id"]
    return None


async def download_blob(blob_url: str) -> bytes:
    async with httpx.AsyncClient(timeout=60) as cli:
        resp = await cli.get(blob_url)
        resp.raise_for_status()
        return resp.content


async def upload_to_onedrive(file_bytes: bytes, filename: str, folder_id: str, token: str):
    """
    Charge le fichier dans le dossier OneDrive cible :
    PUT /drives/{driveId}/items/{folder_id}:/{filename}:/content
    """
    url = f"https://graph.microsoft.com/v1.0/drives/{DRIVE_ID}/items/{folder_id}:/{filename}:/content"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/octet-stream"
    }
    async with httpx.AsyncClient(timeout=60) as cli:
        r = await cli.put(url, headers=headers, content=file_bytes)
        r.raise_for_status()


async def classer(blob_url: str, filename: str, client_folder_id: str,
                  categorie: str, graph_token: str):
    """
    Étapes :
    1. Trouver le sous-dossier correspondant (table Azure)
    2. Télécharger le fichier depuis Blob
    3. Le pousser dans OneDrive
    """
    target_folder = await query_folder_id(client_folder_id, categorie)
    if not target_folder:
        raise RuntimeError("Sous-dossier OneDrive introuvable pour la catégorie")

    data = await download_blob(blob_url)
    await upload_to_onedrive(data, filename, target_folder, graph_token)
    return "OK CLASSEMENT"