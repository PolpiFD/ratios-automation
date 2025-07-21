import os
from azure.storage.blob.aio import BlobServiceClient
from azure.storage.blob import ContentSettings
from azure.identity.aio import DefaultAzureCredential
from azure.storage.blob import generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta
from ..core.config import settings

print(f"Account URL -> {settings.azure_storage_account_url}")

credential = DefaultAzureCredential()
blob_service = BlobServiceClient(account_url=settings.azure_storage_account_url, credential=credential)
container_client = blob_service.get_container_client(settings.azure_blob_container)



async def upload_file (data: bytes, filename: str, mime: str) -> str:
    blob_name = filename
    blob_client = container_client.get_blob_client(blob_name)
    await blob_client.upload_blob(
        data,
        overwrite=False,
        content_settings=ContentSettings(content_type=mime)
    )
    return blob_client.url

def make_read_sas_url (container: str, blob_name: str, seconds: int = 60) -> str:
    sas = generate_blob_sas(
        account_name=settings.azure_storage_account_name,
        container_name=container,
        blob_name=blob_name,
        account_key=settings.azure_storage_account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(seconds=seconds)
    )
    return f"{settings.azure_storage_account_url}/{container}/{blob_name}?{sas}"