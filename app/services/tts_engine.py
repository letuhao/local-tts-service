"""TTS engine wrapping kokoro-onnx."""

import asyncio
import logging
from pathlib import Path

import numpy as np
from kokoro_onnx import Kokoro

from app.services.audio_encoder import encode_audio

logger = logging.getLogger(__name__)

# Voice ID prefix -> language code mapping
_LANG_FROM_PREFIX = {
    "a": "en-us",
    "b": "en-gb",
    "e": "es",
    "f": "fr-fr",
    "h": "hi",
    "i": "it",
    "j": "ja",
    "p": "pt-br",
    "z": "zh",
}


def _guess_lang(voice: str) -> str:
    """Infer language from voice ID prefix (e.g. 'af_heart' -> 'en-us')."""
    if voice and len(voice) >= 1:
        return _LANG_FROM_PREFIX.get(voice[0], "en-us")
    return "en-us"


class TTSEngine:
    """Manages kokoro-onnx model and provides TTS inference."""

    def __init__(self, model_path: Path, voices_path: Path):
        logger.info("Loading kokoro model from %s", model_path)
        self._kokoro = Kokoro(str(model_path), str(voices_path))
        self._voices = self._kokoro.get_voices()
        logger.info("Loaded %d voices", len(self._voices))

    def get_voices(self) -> list[str]:
        return self._voices

    def get_voice_info(self) -> list[dict]:
        """Return structured voice metadata."""
        result = []
        gender_map = {"f": "female", "m": "male"}
        lang_name = {
            "a": ("en", "American English"),
            "b": ("en", "British English"),
            "e": ("es", "Spanish"),
            "f": ("fr", "French"),
            "h": ("hi", "Hindi"),
            "i": ("it", "Italian"),
            "j": ("ja", "Japanese"),
            "p": ("pt", "Portuguese"),
            "z": ("zh", "Chinese"),
        }
        for v in self._voices:
            lang_prefix = v[0] if len(v) >= 1 else "a"
            gender_char = v[1] if len(v) >= 2 else "f"
            name = v.split("_", 1)[1].capitalize() if "_" in v else v
            lang_code, _ = lang_name.get(lang_prefix, ("en", "English"))
            result.append({
                "voice_id": v,
                "name": name,
                "language": lang_code,
                "gender": gender_map.get(gender_char, "neutral"),
            })
        return result

    async def synthesize(
        self,
        text: str,
        voice: str = "af_heart",
        speed: float = 1.0,
        response_format: str = "mp3",
        lang: str | None = None,
    ) -> bytes:
        """Generate full audio for the given text.

        Runs inference in a thread to avoid blocking the event loop.
        """
        lang = lang or _guess_lang(voice)

        samples, sample_rate = await asyncio.to_thread(
            self._kokoro.create,
            text,
            voice=voice,
            speed=speed,
            lang=lang,
        )

        audio_bytes = await asyncio.to_thread(
            encode_audio, samples, sample_rate, response_format
        )
        return audio_bytes

    async def synthesize_stream(
        self,
        text: str,
        voice: str = "af_heart",
        speed: float = 1.0,
        response_format: str = "mp3",
        lang: str | None = None,
    ):
        """Yield encoded audio chunks as they are generated."""
        lang = lang or _guess_lang(voice)

        async for samples, sample_rate in self._kokoro.create_stream(
            text, voice=voice, speed=speed, lang=lang
        ):
            chunk = await asyncio.to_thread(
                encode_audio, samples, sample_rate, response_format
            )
            yield chunk
