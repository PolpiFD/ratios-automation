import uuid
import asyncio
import logging
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Header
import mimetypes
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from typing import Optional

from ..core.config import settings
from ..models.responses import WebhookResponse
from ..services.storage import upload_file, make_read_sas_url
from ..services.document_processor import process_document_async


limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/api/v1", tags=["webhook"])

def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """Vérification de la clé API"""
    if not x_api_key or x_api_key != settings.webhook_api_key:
        raise HTTPException(
            status_code=401, 
            detail="Clé API invalide ou manquante"
        )
    return x_api_key

@router.post("/webhook", response_model=WebhookResponse)
@limiter.limit("15/minute")
async def receive_document(
    client_name: str = Form(..., description="Client's name"),
    client_id: str = Form(..., description="Customer's folder ID"),
    file: UploadFile = File(..., description="File for processing"),
    api_key: str = Depends(verify_api_key)  # 🔒 Authentification ajoutée
):
    # Validation supplémentaire des paramètres
    if not client_name.strip() or len(client_name) > 100:
        raise HTTPException(400, "Nom client invalide")
    
    if not client_id.strip() or len(client_id) > 50:
        raise HTTPException(400, "ID client invalide")

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

    # Traitement asynchrone
    sas_url = make_read_sas_url("file-automation-ratios", new_name)
    asyncio.create_task(process_document_async(sas_url, client_id, client_name, file.filename))

    logging.info(f"Document reçu: {file.filename}")

    return WebhookResponse(
        status="accepted",
        blob_url=blub_url,
        original_name=file.filename,
        size_bytes=len(content)

    )