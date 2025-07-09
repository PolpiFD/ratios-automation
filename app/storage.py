import os
from pathlib import Path
from uuid import uuid4
from azure.storage.blob.aio import BlobServiceClient
from azure.storage.blob import ContentSettings
from azure.identity.aio import DefaultAzureCredential


ACCOUNT_URL = os.getenv("AZURE_STORAGE_ACCOUNT_URL")
CONTAINER = "file-automation-ratios"

credential = DefaultAzureCredential()
blob_service = BlobServiceClient(account_url=ACCOUNT_URL, crendential=credential)
container_client = blob_service.get_container_client(CONTAINER)

#print(blob_service)

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
