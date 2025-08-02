from pydantic import BaseModel

class WebhookResponse(BaseModel):
    status: str
    original_name: str
    size_bytes: int
    message: str = "Document accepté pour le traitement"

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str = "1.0.0"

