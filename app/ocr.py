import os, json
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence.aio import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from azure.ai.documentintelligence.models import AnalyzeResult


ENDPOINT = os.getenv("AZURE_DI_ENDPOINT")
CRED = os.getenv("AZURE_DI_KEY")
MODEL_ID = "prebuilt-read"



async def file_ocr (blob_url: str) -> dict:
    client = DocumentIntelligenceClient(
        endpoint=ENDPOINT,
        credential=AzureKeyCredential(CRED)
    )

    async with client :
        poller = await client.begin_analyze_document(
            MODEL_ID, AnalyzeDocumentRequest(url_source=blob_url)
        )
        result: AnalyzeResult = await poller.result()
        return result.content