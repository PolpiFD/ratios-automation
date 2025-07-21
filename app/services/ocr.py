import os, json
from pathlib import Path
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence.aio import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from azure.ai.documentintelligence.models import AnalyzeResult
from ..core.config import settings

MODEL_ID = "prebuilt-read"

async def file_ocr (blob_url: str, pages: str = "1") -> dict:
    client = DocumentIntelligenceClient(
        endpoint=settings.azure_di_endpoint,
        credential=AzureKeyCredential(settings.azure_di_key)
    )

    async with client :
        poller = await client.begin_analyze_document(
            MODEL_ID, AnalyzeDocumentRequest(url_source=blob_url),
            pages=pages
        )
        result: AnalyzeResult = await poller.result()

        return result.content