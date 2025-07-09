import os, json
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence.aio import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest


ENDPOINT = os.getenv("AZURE_DI_ENDPOINT")
CRED = os.getenv("AZURE_DI_KEY")
MODEL_ID = "prebuilt-read"

async def file_ocr (blob_url: str) -> str:
    client = DocumentIntelligenceClient(
        endpoint=ENDPOINT,
        credential=AzureKeyCredential(CRED)
    )

    async with client :
        poller = await client.begin_analyze_document(
            MODEL_ID, AnalyzeDocumentRequest(url_source=blob_url)
        )
        result = poller.result
        #print(result)