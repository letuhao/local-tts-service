"""Routes TTS requests to the appropriate engine based on voice ID."""

import logging
from pathlib import Path

from app.services.tts_engine import TTSEngine
from app.services.piper_engine import PiperEngine

logger = logging.getLogger(__name__)


class EngineManager:
    """Holds all TTS engines and routes requests by voice ID."""

    def __init__(
        self,
        kokoro_model_path: Path | None,
        kokoro_voices_path: Path | None,
        piper_voices_dir: Path | None,
    ):
        self._kokoro: TTSEngine | None = None
        self._piper: PiperEngine | None = None

        # Load Kokoro engine
        if kokoro_model_path and kokoro_voices_path and kokoro_model_path.exists() and kokoro_voices_path.exists():
            self._kokoro = TTSEngine(kokoro_model_path, kokoro_voices_path)
        else:
            logger.warning("Kokoro model files not found, Kokoro engine disabled")

        # Load Piper engine
        if piper_voices_dir and piper_voices_dir.exists():
            self._piper = PiperEngine(piper_voices_dir)
            if not self._piper.get_voices():
                logger.warning("No Piper voices found in %s", piper_voices_dir)
                self._piper = None
        else:
            logger.warning("Piper voices dir not found, Piper engine disabled")

    def _resolve_engine(self, voice: str):
        """Return the engine that owns this voice."""
        if self._piper and self._piper.has_voice(voice):
            return self._piper
        if self._kokoro and voice in self._kokoro.get_voices():
            return self._kokoro
        return None

    def get_voices(self) -> list[str]:
        voices = []
        if self._kokoro:
            voices.extend(self._kokoro.get_voices())
        if self._piper:
            voices.extend(self._piper.get_voices())
        return voices

    def get_voice_info(self) -> list[dict]:
        info = []
        if self._kokoro:
            info.extend(self._kokoro.get_voice_info())
        if self._piper:
            info.extend(self._piper.get_voice_info())
        return info

    def has_voice(self, voice: str) -> bool:
        return self._resolve_engine(voice) is not None

    async def synthesize(
        self,
        text: str,
        voice: str,
        speed: float = 1.0,
        response_format: str = "mp3",
    ) -> bytes:
        engine = self._resolve_engine(voice)
        if engine is None:
            raise ValueError(f"Unknown voice: {voice}")
        return await engine.synthesize(text, voice, speed, response_format)

    async def synthesize_stream(
        self,
        text: str,
        voice: str,
        speed: float = 1.0,
        response_format: str = "mp3",
    ):
        engine = self._resolve_engine(voice)
        if engine is None:
            raise ValueError(f"Unknown voice: {voice}")
        async for chunk in engine.synthesize_stream(text, voice, speed, response_format):
            yield chunk

    @property
    def is_ready(self) -> bool:
        return self._kokoro is not None or self._piper is not None
