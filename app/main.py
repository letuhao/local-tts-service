import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.routers import tts, models, voices, health
from app.services.engine_manager import EngineManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: load all engines
    kokoro_model = settings.models_dir / "kokoro-v1.0.onnx"
    kokoro_voices = settings.voices_dir / "voices-v1.0.bin"
    piper_dir = settings.voices_dir / "piper"

    manager = EngineManager(
        kokoro_model_path=kokoro_model,
        kokoro_voices_path=kokoro_voices,
        piper_voices_dir=piper_dir,
    )

    if manager.is_ready:
        app.state.engine_manager = manager
        logger.info("TTS engines ready — %d voices available", len(manager.get_voices()))
    else:
        app.state.engine_manager = None
        logger.warning("No TTS engines loaded")

    yield

    # Shutdown
    app.state.engine_manager = None
    logger.info("TTS engines unloaded")


app = FastAPI(
    title="local-tts-service",
    description="Local Text-to-Speech service with OpenAI-compatible API",
    version="0.2.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(models.router)
app.include_router(voices.router)
app.include_router(tts.router)
