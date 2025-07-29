# app/main.py
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from dotenv import load_dotenv
load_dotenv()

from .api import webhook, health
from .core.config import settings
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# Configuration logging selon environnement
if settings.debug:
    log_level = logging.DEBUG
else:
    log_level = logging.INFO

logging.basicConfig(
    level=log_level,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)

# Désactiver logs sensibles en production
if not settings.debug:
    logging.getLogger("azure").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

# Création app FastAPI
app = FastAPI(
    title="Ratios Automation API",
    description="API d'automatisation de traitement documentaire",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,  # Pas de docs en prod
    redoc_url="/redoc" if settings.debug else None
)

# Sécurité - Host de confiance
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["ratios.lovable.app", "localhost", "127.0.0.1", "*.infomaniak.com", "*.ngrok.io", "*.ngrok-free.app"]
)

# CORS - Restreint aux domaines autorisés
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ratios.lovable.app"],  # Production uniquement
    allow_credentials=False,  # Pas de cookies pour une API
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type", "X-API-Key"],  # Headers spécifiques
)

# Configuration SlowAPI rate limiting
app.state.limiter = webhook.limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Routes
app.include_router(webhook.router)
app.include_router(health.router)

# Point d'entrée
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        access_log=settings.debug  # Pas de logs d'accès en prod
    )