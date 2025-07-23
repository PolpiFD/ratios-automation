import uuid
import asyncio
import logging
import re
import html
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

def sanitize_and_validate_input(value: str, field_name: str, max_length: int, allow_special_chars: bool = False) -> str:
    """
    Sanitise et valide les entrées utilisateur
    
    Args:
        value: La valeur à valider
        field_name: Le nom du champ pour les messages d'erreur
        max_length: Longueur maximale autorisée
        allow_special_chars: Autorise quelques caractères spéciaux pour les noms
    
    Returns:
        str: La valeur sanitisée
        
    Raises:
        HTTPException: Si la validation échoue
    """
    # Vérification basique
    if not value or not value.strip():
        raise HTTPException(400, f"{field_name} ne peut pas être vide")
    
    # Nettoyage et sanitisation
    cleaned_value = value.strip()
    
    # Échappement HTML pour prévenir XSS
    cleaned_value = html.escape(cleaned_value)
    
    # Validation de la longueur
    if len(cleaned_value) > max_length:
        raise HTTPException(400, f"{field_name} trop long (max {max_length} caractères)")
    
    # Validation des caractères selon le type de champ
    if field_name == "ID client":
        # Pour client_id: uniquement alphanumériques, tirets et underscores
        if not re.match(r'^[a-zA-Z0-9_-]+$', cleaned_value):
            raise HTTPException(400, f"{field_name} ne peut contenir que des lettres, chiffres, tirets et underscores")
    elif field_name == "Nom client":
        # Pour client_name: lettres, chiffres, espaces et quelques caractères spéciaux courants
        if allow_special_chars:
            if not re.match(r'^[a-zA-Z0-9\s\.\-_&\(\)]+$', cleaned_value):
                raise HTTPException(400, f"{field_name} contient des caractères non autorisés")
        else:
            if not re.match(r'^[a-zA-Z0-9\s\.\-_]+$', cleaned_value):
                raise HTTPException(400, f"{field_name} contient des caractères non autorisés")
    
    # Vérification contre les patterns dangereux
    dangerous_patterns = [
        r'<script.*?>.*?</script>',  # Scripts
        r'javascript:',              # URLs JavaScript
        r'on\w+\s*=',               # Event handlers
        r'<iframe.*?>',             # iframes
        r'<object.*?>',             # objects
        r'<embed.*?>'               # embeds
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, cleaned_value, re.IGNORECASE):
            raise HTTPException(400, f"{field_name} contient du contenu potentiellement dangereux")
    
    return cleaned_value

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
    # Validation et sanitisation des paramètres
    client_name = sanitize_and_validate_input(client_name, "Nom client", 100, allow_special_chars=True)
    client_id = sanitize_and_validate_input(client_id, "ID client", 50)

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