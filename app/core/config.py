# app/core/config.py
import os
import secrets
from pydantic import BaseModel
from typing import Set

class Settings(BaseModel):
    # Sécurité
    webhook_api_key: str = os.getenv("WEBHOOK_API_KEY", "")
    
    # Azure Auth
    azure_client_id: str = os.getenv("AZURE_CLIENT_ID", "")
    azure_client_secret: str = os.getenv("AZURE_CLIENT_SECRET", "")
    azure_tenant_id: str = os.getenv("AZURE_TENANT_ID", "")
    
    # Azure Storage
    azure_storage_account_url: str = os.getenv("AZURE_STORAGE_ACCOUNT_URL", "")
    azure_storage_account_name: str = os.getenv("AZURE_STORAGE_ACCOUNT_NAME", "")
    azure_storage_account_key: str = os.getenv("AZURE_STORAGE_ACCOUNT_KEY", "")
    azure_blob_container: str = os.getenv("AZURE_BLOB_CONTAINER", "")
    
    # Azure Table
    azure_table_url: str = os.getenv("AZURE_STORAGE_TABLE_URL", "")
    azure_table_name: str = os.getenv("AZURE_STORAGE_TABLE_NAME", "")
    
    # Document Intelligence
    azure_di_endpoint: str = os.getenv("AZURE_DI_ENDPOINT", "")
    azure_di_key: str = os.getenv("AZURE_DI_KEY", "")
    
    # SharePoint (Client Ratios)
    sharepoint_client_id: str = os.getenv("SHAREPOINT_CLIENT_ID", "")
    sharepoint_client_secret: str = os.getenv("SHAREPOINT_CLIENT_SECRET", "")
    sharepoint_tenant_id: str = os.getenv("SHAREPOINT_TENANT_ID", "")
    sharepoint_site_url: str = os.getenv("SHAREPOINT_SITE_URL", "")
    
    # OneDrive (legacy - à supprimer plus tard)
    drive_id: str = os.getenv("DRIVE_ID", "")
    
    # OpenAI
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

    # Supabase
    supabase_url_sync: str = os.getenv("SUPABASE_URL_SYNC", "")
    auth_key_supabase: str = os.getenv("AUTH_KEY_SUPABASE", "")
    
    # App config
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    max_file_size: int = 300 * 1024 * 1024
    allowed_extensions: set = {".pdf", ".jpeg", ".png", ".jpg"}
    
    # Extensions d'images à convertir en PDF
    image_extensions: set = {".jpeg", ".png", ".jpg"}
    
    # Extensions HEIC (ajoutées si pillow-heif disponible)
    heic_extensions: set = {".heic", ".heif"}

settings = Settings()