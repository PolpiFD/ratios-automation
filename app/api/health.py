from datetime import datetime

from fastapi import APIRouter

from ..models.responses import HealthResponse

router = APIRouter(tags=["monitoring"])

@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat()
    )

@router.get("/ready")
async def readiness_check():
    #teser les connexions (à implémenter)
    return {"status": "ready"}