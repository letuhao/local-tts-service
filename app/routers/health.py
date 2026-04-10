from fastapi import APIRouter
from app.models.schemas import HealthResponse

router = APIRouter()


@router.get("/health")
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok", version="0.1.0")
