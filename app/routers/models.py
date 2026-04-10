import time
from pathlib import Path

from fastapi import APIRouter

from app.config import settings
from app.models.schemas import ModelsResponse, ModelInfo

router = APIRouter()


@router.get("/v1/models")
async def list_models() -> ModelsResponse:
    models = []
    models_dir = settings.models_dir
    if models_dir.exists():
        for f in sorted(models_dir.glob("*.onnx")):
            models.append(ModelInfo(
                id=f.stem,
                created=int(f.stat().st_mtime),
                owned_by="local",
            ))

    # Fallback if no models found on disk
    if not models:
        models.append(ModelInfo(id=settings.default_model, owned_by="local"))

    return ModelsResponse(data=models)
