"""TTS engine wrapping piper-tts for Vietnamese (and other Piper-supported languages)."""

import asyncio
import logging
import re
from pathlib import Path

import numpy as np
from piper.config import SynthesisConfig
from piper.voice import PiperVoice

from app.services.audio_encoder import encode_audio

logger = logging.getLogger(__name__)


class PiperEngine:
    """Manages Piper TTS voices and provides synthesis."""

    def __init__(self, piper_voices_dir: Path):
        self._voices: dict[str, PiperVoice] = {}
        self._voice_meta: list[dict] = []

        if not piper_voices_dir.exists():
            logger.warning("Piper voices dir not found: %s", piper_voices_dir)
            return

        # Load all .onnx files in the piper voices directory
        for onnx_file in sorted(piper_voices_dir.glob("*.onnx")):
            json_file = Path(str(onnx_file) + ".json")
            if not json_file.exists():
                logger.warning("Missing config for %s, skipping", onnx_file.name)
                continue

            voice_id = onnx_file.stem  # e.g. "vi_VN-vais1000-medium"
            try:
                voice = PiperVoice.load(str(onnx_file))
                self._voices[voice_id] = voice
                self._voice_meta.append(self._build_meta(voice_id, voice))
                logger.info("Loaded Piper voice: %s (sample_rate=%d)", voice_id, voice.config.sample_rate)
            except Exception:
                logger.exception("Failed to load Piper voice: %s", onnx_file.name)

        logger.info("Loaded %d Piper voices", len(self._voices))

    @staticmethod
    def _build_meta(voice_id: str, voice: PiperVoice) -> dict:
        parts = voice_id.split("-")
        lang_code = parts[0] if parts else "unknown"
        dataset = parts[1] if len(parts) > 1 else ""
        quality = parts[2] if len(parts) > 2 else ""
        name = f"{dataset} ({quality})" if quality else dataset

        lang_map = {"vi_VN": "vi", "en_US": "en", "en_GB": "en"}

        return {
            "voice_id": voice_id,
            "name": name.capitalize() if name else voice_id,
            "language": lang_map.get(lang_code, lang_code),
            "gender": "female",
        }

    def get_voices(self) -> list[str]:
        return list(self._voices.keys())

    def get_voice_info(self) -> list[dict]:
        return self._voice_meta

    def has_voice(self, voice_id: str) -> bool:
        return voice_id in self._voices

    def _synthesize_raw(self, text: str, voice_id: str, speed: float) -> tuple[np.ndarray, int]:
        """Synthesize text to raw float32 samples (runs in thread)."""
        voice = self._voices[voice_id]
        sample_rate = voice.config.sample_rate

        syn_config = SynthesisConfig(
            length_scale=1.0 / speed if speed else 1.0,
        )

        # synthesize() returns an iterable of AudioChunk
        all_samples = []
        for chunk in voice.synthesize(text, syn_config=syn_config):
            all_samples.append(chunk.audio_float_array)

        if not all_samples:
            return np.array([], dtype=np.float32), sample_rate

        samples = np.concatenate(all_samples)
        return samples, sample_rate

    async def synthesize(
        self,
        text: str,
        voice: str,
        speed: float = 1.0,
        response_format: str = "mp3",
    ) -> bytes:
        samples, sample_rate = await asyncio.to_thread(
            self._synthesize_raw, text, voice, speed
        )
        audio_bytes = await asyncio.to_thread(
            encode_audio, samples, sample_rate, response_format
        )
        return audio_bytes

    async def synthesize_stream(
        self,
        text: str,
        voice: str,
        speed: float = 1.0,
        response_format: str = "mp3",
    ):
        """Yield encoded audio chunks. Split text into sentences for streaming."""
        sentences = _split_sentences(text)
        for sentence in sentences:
            if not sentence.strip():
                continue
            chunk = await self.synthesize(sentence, voice, speed, response_format)
            yield chunk


def _split_sentences(text: str) -> list[str]:
    """Simple sentence splitter for streaming."""
    parts = re.split(r'(?<=[.!?。！？])\s+', text)
    return [p for p in parts if p.strip()]
