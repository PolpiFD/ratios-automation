import os
from pathlib import Path
from uuid import uuid4
from azure.storage.blob.aio import BlobServiceClient
from azure.storage.blob import ContentSettings
from azure.identity.aio import DefaultAzureCredential
from azure.storage.blob import generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta


ACCOUNT_URL = os.getenv("AZURE_STORAGE_ACCOUNT_URL")
CONTAINER = "file-automation-ratios"
print (f"Account url -> {ACCOUNT_URL}")

credential = DefaultAzureCredential()
print (f"crendential -> {credential}")
blob_service = BlobServiceClient(account_url=ACCOUNT_URL, credential=credential)
container_client = blob_service.get_container_client(CONTAINER)


####################################################################################

async def upload_file (data: bytes, filename: str, mime: str) -> str:
    blob_name = filename
    blob_client = container_client.get_blob_client(blob_name)

    await blob_client.upload_blob(
        data,
        overwrite=False,
        content_settings=ContentSettings(content_type=mime)
    )
    return blob_client.url

def make_read_sas_url (container: str, blob_name: str, minutes: int = 15) -> str:
    print("make_read_sas_url -> OKKK")
    sas = generate_blob_sas(
        account_name=os.getenv("AZURE_STORAGE_ACCOUNT_NAME"),
        container_name=container,
        blob_name=blob_name,
        account_key=os.getenv("AZURE_STORAGE_ACCOUNT_KEY"),
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(minutes=minutes)
    )
    return f"{os.getenv('AZURE_STORAGE_ACCOUNT_URL')}/{container}/{blob_name}?{sas}"