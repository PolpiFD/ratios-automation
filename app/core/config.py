# app/core/config.py
import os
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv()


class Settings(BaseModel):
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
    table_name: str = os.getenv("AZURE_STORAGE_TABLE_NAME", "")
    
    # Document Intelligence
    azure_di_endpoint: str = os.getenv("AZURE_DI_ENDPOINT", "")
    azure_di_key: str = os.getenv("AZURE_DI_KEY", "")
    
    # OneDrive
    drive_id: str = os.getenv("DRIVE_ID", "")
    
    # OpenAI
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    
    # App config
    max_file_size: int = 300 * 1024 * 1024
    allowed_extensions: set = {".pdf", ".jpeg", ".png", ".jpg"}

settings = Settings()