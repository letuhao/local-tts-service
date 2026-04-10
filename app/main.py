import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.routers import tts, models, voices, health
from app.services.tts_engine import TTSEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: load model once
    model_path = settings.models_dir / "kokoro-v1.0.onnx"
    voices_path = settings.voices_dir / "voices-v1.0.bin"

    if model_path.exists() and voices_path.exists():
        app.state.tts_engine = TTSEngine(model_path, voices_path)
        logger.info("TTS engine ready")
    else:
        app.state.tts_engine = None
        logger.warning(
            "Model files not found. Place kokoro-v1.0.onnx in %s and voices-v1.0.bin in %s",
            settings.models_dir,
            settings.voices_dir,
        )

    yield

    # Shutdown
    app.state.tts_engine = None
    logger.info("TTS engine unloaded")


app = FastAPI(
    title="local-tts-service",
    description="Local Text-to-Speech service with OpenAI-compatible API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(models.router)
app.include_router(voices.router)
app.include_router(tts.router)
