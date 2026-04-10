# CLAUDE.md — local-tts-service

## What is this project?

A local Text-to-Speech (TTS) service that exposes an **OpenAI-compatible REST API**. It is designed to integrate with LoreWeave's provider-registry system as an external AI service, but can also be used standalone.

## Architecture

- **Language:** Python
- **Framework:** FastAPI
- **API Standard:** OpenAI-compatible (`POST /v1/audio/speech`, `GET /v1/models`)
- **Integration:** LoreWeave provider-registry (see `docs/EXTERNAL_AI_SERVICE_INTEGRATION_GUIDE.md`)

## Key Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /v1/audio/speech` | Generate speech from text (streaming + non-streaming) |
| `GET /v1/models` | List available TTS models |
| `GET /v1/voices` | List available voices |
| `GET /health` | Health check |

## API Contract

Requests follow the OpenAI TTS format:
```json
{
  "model": "model-name",
  "voice": "voice-id",
  "input": "Text to synthesize",
  "response_format": "mp3",
  "speed": 1.0
}
```

Response: raw audio bytes with `Content-Type: audio/mpeg` (or format-appropriate MIME type). Supports chunked transfer encoding for streaming.

## Auth

Accepts `Authorization: Bearer {api_key}` header. For local development, accepts any token.

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run dev server
uvicorn app.main:app --reload --port 9880

# Run tests
pytest

# Lint
ruff check .

# Format
ruff format .
```

## TTS Engines

### Multi-engine architecture
`EngineManager` routes requests to the correct engine based on voice ID:
- `af_*`, `am_*`, `bf_*`, etc. → **Kokoro** (9 languages, 54 voices)
- `vi_VN-*` → **Piper** (Vietnamese)

### Kokoro (primary)
- **Model:** Kokoro TTS (82M params) via `kokoro-onnx`
- **Files:** `models/kokoro-v1.0.onnx` (311MB) + `voices/voices-v1.0.bin` (27MB)
- **Streaming:** `kokoro.create_stream()` yields audio chunks per sentence
- 54 voices across 9 languages (en-us, en-gb, es, fr, hi, it, ja, pt, zh)

### Piper (Vietnamese)
- **Model:** Piper TTS via `piper-tts`
- **Files:** `voices/piper/vi_VN-vais1000-medium.onnx` (61MB) + `.onnx.json`
- **Streaming:** sentence-splitting based (Piper doesn't natively stream)
- Vietnamese voices from rhasspy/piper-voices

### Shared
- **Audio encoding:** `static-ffmpeg` (portable) for mp3/wav/opus/flac/aac
- **Concurrency:** All inference runs in thread pool (`asyncio.to_thread`)

## Project Structure

```
app/
  main.py              — FastAPI app + lifespan (engine loading)
  config.py            — Settings via pydantic-settings (env prefix: TTS_)
  routers/
    tts.py             — POST /v1/audio/speech (streaming)
    models.py          — GET /v1/models (scans models/ dir)
    voices.py          — GET /v1/voices (from all engines)
    health.py          — GET /health
  services/
    engine_manager.py  — Multi-engine router (voice → engine)
    tts_engine.py      — Kokoro-onnx wrapper
    piper_engine.py    — Piper TTS wrapper (Vietnamese)
    audio_encoder.py   — PCM-to-format encoding via ffmpeg
  models/
    schemas.py         — Pydantic request/response schemas
models/                — ONNX model weights (git-ignored)
voices/                — Kokoro voice embeddings (git-ignored)
  piper/               — Piper voice models (git-ignored)
tests/
docs/
  EXTERNAL_AI_SERVICE_INTEGRATION_GUIDE.md
```

## Integration with LoreWeave

This service is called by LoreWeave's provider-registry-service. The flow:
1. User registers this service as a provider in LoreWeave (endpoint URL + API key)
2. LoreWeave resolves credentials and forwards TTS requests here
3. This service processes the request and returns audio
4. LoreWeave handles usage tracking and billing

See `docs/EXTERNAL_AI_SERVICE_INTEGRATION_GUIDE.md` for the full integration spec.
