import os, aiofiles, httpx, asyncio
from azure.data.tables.aio import TableClient
from azure.identity.aio import DefaultAzureCredential
from ..core.config import settings
from .sharepoint import sharepoint_service



async def query_folder_id(client_folder_id: str, categorie: str) -> str | None:
    """
    Cherche l'entity dont:
        client_folder_id == <client_folder_id>
        ET category        == <categorie>
    Retourne folder_id ou None.
    """
    credential = DefaultAzureCredential(managed_identity_client_id=settings.azure_client_id)
    async with TableClient(settings.azure_table_url, settings.azure_table_name, credential=credential) as table:
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


async def upload_to_sharepoint(file_bytes: bytes, filename: str, folder_path: str):
    """
    Charge le fichier dans le dossier SharePoint cible
    """
    await sharepoint_service.upload_file_to_folder(file_bytes, filename, folder_path)


async def classer(blob_url: str, filename: str, client_folder_id: str,
                  categorie: str, graph_token: str = None):
    """
    Étapes :
    1. Trouver le sous-dossier correspondant (table Azure)
    2. Télécharger le fichier depuis Blob
    3. Le pousser dans SharePoint
    """
    target_folder_path = await query_folder_path(client_folder_id, categorie)
    if not target_folder_path:
        raise RuntimeError("Sous-dossier SharePoint introuvable pour la catégorie")

    data = await download_blob(blob_url)
    await upload_to_sharepoint(data, filename, target_folder_path)
    return "OK CLASSEMENT SHAREPOINT"


async def query_folder_path(client_folder_id: str, categorie: str) -> str | None:
    """
    Cherche le chemin du dossier SharePoint pour un client et une catégorie donnés
    Retourne le chemin complet ou None
    """
    credential = DefaultAzureCredential(managed_identity_client_id=settings.azure_client_id)
    async with TableClient(settings.azure_table_url, settings.azure_table_name, credential=credential) as table:
        filt = (
            f"client_folder_id eq '{client_folder_id}' "
            f"and RowKey eq '{categorie}'"
        )
        entities = table.query_entities(query_filter=filt, results_per_page=1)
        async for page in entities.by_page():
            async for e in page:
                return e.get("folder_path")  # Nouveau champ pour le chemin SharePoint
    return None