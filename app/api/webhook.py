import uuid
import asyncio
import logging
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import mimetypes

from ..core.config import settings
from ..models.responses import WebhookResponse
from ..services.storage import upload_file, make_read_sas_url
from ..services.document_processor import process_document_async

router = APIRouter(prefix="/api/v1", tags=["webhook"])

@router.post("/webhook", response_model=WebhookResponse)
async def receive_document(
    client_name: str = Form(..., description="Client's name"),
    client_id: str = Form(..., description="Customer's folder ID"),
    file: UploadFile = File(..., description="File for processing")
):
    #Validation taille
    content = await file.read()
    if len(content) > settings.max_file_size:
        raise HTTPException(413, "Fichier trop volumineux (max 300MB)")
    
    #Validation extension
    suffix = Path(file.filename).suffix.lower()
    if suffix not in settings.allowed_extensions:
        raise HTTPException(400, f"Extension {suffix} non autorisée")
    
    #Upload vers Azure
    mime = file.content_type or mimetypes.guess_type(file.filename)[0]
    new_name = f"{client_id}_{uuid.uuid4().hex}{suffix}"
    blub_url = await upload_file(content, new_name, mime)

    # Traitement asynchrone
    sas_url = make_read_sas_url("file-automation-ratios", new_name)
    asyncio.create_task(process_document_async(sas_url, client_id, client_name, file.filename))

    logging.info(f"Document reçu: {file.filename}")

    return WebhookResponse(
        status="accepted",
        blob_url=blub_url,
        original_name=file.filename,
        size_bytes=len(content)

    )