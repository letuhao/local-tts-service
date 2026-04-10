# local-tts-service

A local Text-to-Speech service with an OpenAI-compatible API, powered by [Kokoro TTS](https://github.com/thewh1teagle/kokoro-onnx). Runs on your own hardware — no cloud API keys needed. Integrates with [LoreWeave](https://github.com/letuhao1994) as an external TTS provider.

## Features

- OpenAI-compatible `POST /v1/audio/speech` endpoint
- Streaming audio output (chunked transfer encoding) for low-latency playback
- 54 voices across 9 languages (English, Spanish, French, Hindi, Italian, Japanese, Portuguese, Chinese)
- Multiple output formats: mp3, wav, opus, flac, aac, pcm
- Model and voice discovery via `/v1/models` and `/v1/voices`
- Portable — no system ffmpeg install required (`static-ffmpeg` bundles it)

## Quick Start

```bash
# Clone
git clone https://github.com/letuhao1994/local-tts-service.git
cd local-tts-service

# Install dependencies
pip install -r requirements.txt

# Download model files
# Place these in the project:
#   models/kokoro-v1.0.onnx  (311MB) — from https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0
#   voices/voices-v1.0.bin   (27MB)  — same release page

# Run
uvicorn app.main:app --host 0.0.0.0 --port 9880
```

## API Usage

### Generate Speech

```bash
curl -X POST http://localhost:9880/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"model":"kokoro-v1.0","voice":"af_heart","input":"Hello world","response_format":"mp3"}' \
  --output speech.mp3
```

### List Models

```bash
curl http://localhost:9880/v1/models
```

### List Voices

```bash
curl http://localhost:9880/v1/voices
```

## Configuration

Configuration via environment variables (prefix `TTS_`) or `.env` file:

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

## LoreWeave Integration

This service integrates with LoreWeave's provider-registry system. To connect:

1. Deploy this service (locally or in Docker)
2. In LoreWeave UI, go to **Settings > Model Providers > Add Provider**
3. Set **Provider Kind** to `openai` (or a custom kind), **Endpoint URL** to `http://localhost:9880`, and enter your API key
4. Add a model with the **TTS** capability flag enabled
5. The model will appear in LoreWeave's TTS model selectors

See [docs/EXTERNAL_AI_SERVICE_INTEGRATION_GUIDE.md](docs/EXTERNAL_AI_SERVICE_INTEGRATION_GUIDE.md) for the full integration spec.

## Docker

```bash
docker build -t local-tts-service .
docker run -p 9880:9880 \
  -v ./models:/app/models \
  -v ./voices:/app/voices \
  local-tts-service
```

## License

[MIT](LICENSE)
