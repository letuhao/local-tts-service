# local-tts-service

A local Text-to-Speech service with an OpenAI-compatible API, powered by [Kokoro TTS](https://github.com/thewh1teagle/kokoro-onnx). Runs entirely on your own hardware — no cloud API keys, no CUDA, no GPU required.

## Features

- **OpenAI-compatible API** — drop-in replacement for OpenAI's TTS endpoint
- **Streaming audio** — chunked transfer encoding for low-latency playback (~200ms to first audio)
- **54 voices, 9 languages** — English, Spanish, French, Hindi, Italian, Japanese, Portuguese, Chinese
- **Multiple output formats** — mp3, wav, opus, flac, aac, pcm
- **Zero system dependencies** — ffmpeg is bundled via `static-ffmpeg`, no manual install needed
- **CPU-only** — the model is 82M parameters, runs fast on any modern CPU
- **Docker ready** — single command to build and run

## Prerequisites

- Python 3.10+ (tested on 3.12)
- ~500MB disk space (model files + dependencies)
- Docker (optional, for containerized deployment)

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/letuhao/local-tts-service.git
cd local-tts-service
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Download model files

Download both files from [kokoro-onnx releases](https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0):

| File | Size | Place in |
|------|------|----------|
| `kokoro-v1.0.onnx` | 311 MB | `models/` |
| `voices-v1.0.bin` | 27 MB | `voices/` |

Using curl:

```bash
# Download model
curl -L -o models/kokoro-v1.0.onnx \
  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx

# Download voices
curl -L -o voices/voices-v1.0.bin \
  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
```

### 4. Run the service

```bash
uvicorn app.main:app --host 0.0.0.0 --port 9880
```

You should see:

```
INFO:     Loading kokoro model from models/kokoro-v1.0.onnx
INFO:     Loaded 54 voices
INFO:     TTS engine ready
INFO:     Uvicorn running on http://0.0.0.0:9880
```

## API Reference

### Generate Speech

```
POST /v1/audio/speech
```

Request body:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model` | string | yes | Model name (e.g. `kokoro-v1.0`) |
| `voice` | string | yes | Voice ID (e.g. `af_heart`) — see [Available Voices](#available-voices) |
| `input` | string | yes | Text to synthesize (max 4096 characters) |
| `response_format` | string | no | `mp3` (default), `wav`, `opus`, `flac`, `aac`, `pcm` |
| `speed` | number | no | Playback speed: 0.25 to 4.0 (default 1.0) |

Example:

```bash
curl -X POST http://localhost:9880/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "kokoro-v1.0",
    "voice": "af_heart",
    "input": "Hello, this is a test of the local TTS service.",
    "response_format": "mp3",
    "speed": 1.0
  }' \
  --output speech.mp3
```

### List Models

```
GET /v1/models
```

```bash
curl http://localhost:9880/v1/models
```

Response:

```json
{
  "object": "list",
  "data": [
    { "id": "kokoro-v1.0", "object": "model", "owned_by": "local" }
  ]
}
```

### List Voices

```
GET /v1/voices
```

```bash
curl http://localhost:9880/v1/voices
```

Response:

```json
{
  "voices": [
    { "voice_id": "af_heart", "name": "Heart", "language": "en", "gender": "female" },
    { "voice_id": "am_adam", "name": "Adam", "language": "en", "gender": "male" }
  ]
}
```

### Health Check

```
GET /health
```

```bash
curl http://localhost:9880/health
```

## Available Voices

| Prefix | Language | Voices |
|--------|----------|--------|
| `af_*` | American English (female) | `af_alloy`, `af_aoede`, `af_bella`, `af_heart`, `af_jessica`, `af_kore`, `af_nicole`, `af_nova`, `af_river`, `af_sarah`, `af_sky` |
| `am_*` | American English (male) | `am_adam`, `am_echo`, `am_eric`, `am_fenrir`, `am_liam`, `am_michael`, `am_onyx`, `am_puck`, `am_santa` |
| `bf_*` | British English (female) | `bf_alice`, `bf_emma`, `bf_isabella`, `bf_lily` |
| `bm_*` | British English (male) | `bm_daniel`, `bm_fable`, `bm_george`, `bm_lewis` |
| `ef_*` / `em_*` | Spanish | `ef_dora`, `em_alex`, `em_santa` |
| `ff_*` | French | `ff_siwis` |
| `hf_*` / `hm_*` | Hindi | `hf_alpha`, `hf_beta`, `hm_omega`, `hm_psi` |
| `if_*` / `im_*` | Italian | `if_sara`, `im_nicola` |
| `jf_*` / `jm_*` | Japanese | `jf_alpha`, `jf_gongitsune`, `jf_nezumi`, `jf_tebukuro`, `jm_kumo` |
| `pf_*` / `pm_*` | Portuguese | `pf_dora`, `pm_alex`, `pm_santa` |
| `zf_*` / `zm_*` | Chinese | `zf_xiaobei`, `zf_xiaoni`, `zf_xiaoxiao`, `zf_xiaoyi`, `zm_yunjian`, `zm_yunxi`, `zm_yunxia`, `zm_yunyang` |

## Configuration

Configuration via environment variables (prefix `TTS_`) or a `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `TTS_HOST` | `0.0.0.0` | Bind address |
| `TTS_PORT` | `9880` | Bind port |
| `TTS_API_KEY` | `dev_key` | API key for auth |
| `TTS_MODELS_DIR` | `models` | Path to model files |
| `TTS_VOICES_DIR` | `voices` | Path to voice files |
| `TTS_DEFAULT_MODEL` | `kokoro-v1` | Default model name |
| `TTS_DEFAULT_VOICE` | `af_heart` | Default voice |

See [.env.example](.env.example) for a template.

## Docker

### Using Docker Compose (recommended)

```bash
docker compose up
```

### Using Docker directly

```bash
# Build
docker build -t local-tts-service .

# Run (mount your model files)
docker run -p 9880:9880 \
  -v ./models:/app/models \
  -v ./voices:/app/voices \
  local-tts-service
```

Model files must be downloaded before running — they are mounted as volumes, not baked into the image.

## Using with Python (OpenAI SDK)

Since this service is OpenAI-compatible, you can use the official OpenAI Python SDK:

```python
from openai import OpenAI
from pathlib import Path

client = OpenAI(
    base_url="http://localhost:9880/v1",
    api_key="dev_key",  # any key works for local
)

response = client.audio.speech.create(
    model="kokoro-v1.0",
    voice="af_heart",
    input="Hello from the OpenAI SDK!",
    response_format="mp3",
)

Path("output.mp3").write_bytes(response.content)
```

## Using with JavaScript/TypeScript

```javascript
const response = await fetch('http://localhost:9880/v1/audio/speech', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    model: 'kokoro-v1.0',
    voice: 'af_heart',
    input: 'Hello from JavaScript!',
    response_format: 'mp3',
  }),
});

const audioBlob = await response.blob();
```

## LoreWeave Integration

This service integrates with LoreWeave's provider-registry system. To connect:

1. Deploy this service (locally or in Docker)
2. In LoreWeave UI, go to **Settings > Model Providers > Add Provider**
3. Set **Provider Kind** to `openai` (or a custom kind), **Endpoint URL** to `http://localhost:9880`, and enter your API key
4. Add a model with the **TTS** capability flag enabled
5. The model will appear in LoreWeave's TTS model selectors

See [docs/EXTERNAL_AI_SERVICE_INTEGRATION_GUIDE.md](docs/EXTERNAL_AI_SERVICE_INTEGRATION_GUIDE.md) for the full integration spec.

## Project Structure

```
app/
  main.py              — FastAPI app + startup lifecycle
  config.py            — Settings (env prefix: TTS_)
  routers/
    tts.py             — POST /v1/audio/speech
    models.py          — GET /v1/models
    voices.py          — GET /v1/voices
    health.py          — GET /health
  services/
    tts_engine.py      — Kokoro-ONNX wrapper
    audio_encoder.py   — PCM-to-format encoding via ffmpeg
  models/
    schemas.py         — Pydantic request/response schemas
models/                — ONNX model weights (git-ignored)
voices/                — Voice embedding files (git-ignored)
tests/
docs/
```

## License

[MIT](LICENSE)
