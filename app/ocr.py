import os, json
from pathlib import Path
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence.aio import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from azure.ai.documentintelligence.models import AnalyzeResult


ENDPOINT = os.getenv("AZURE_DI_ENDPOINT")
CRED = os.getenv("AZURE_DI_KEY")
MODEL_ID = "prebuilt-read"



async def file_ocr (blob_url: str, pages: str = "1") -> dict:
    client = DocumentIntelligenceClient(
        endpoint=ENDPOINT,
        credential=AzureKeyCredential(CRED)
    )

    async with client :
        poller = await client.begin_analyze_document(
            MODEL_ID, AnalyzeDocumentRequest(url_source=blob_url),
            pages=pages
        )
        result: AnalyzeResult = await poller.result()
                # Sauvegarde pour tests
        cache_name = f"ocr_{hash(blob_url) % 1000000}.json"
        cache_path = Path("samples") / cache_name
        cache_path.parent.mkdir(exist_ok=True)
        
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(result.content, f, ensure_ascii=False, indent=2)
        return result.content