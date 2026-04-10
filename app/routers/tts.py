from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.models.schemas import TTSRequest
from app.services.audio_encoder import FORMAT_CONTENT_TYPES, SUPPORTED_FORMATS

router = APIRouter()


def _get_engine(request: Request):
    engine = request.app.state.tts_engine
    if engine is None:
        raise HTTPException(503, "TTS engine not loaded")
    return engine


@router.post("/v1/audio/speech")
async def generate_speech(req: TTSRequest, request: Request):
    engine = _get_engine(request)

    if req.voice not in engine.get_voices():
        raise HTTPException(400, f"Unknown voice: {req.voice}. Use GET /v1/voices to list available voices.")

    if req.response_format not in SUPPORTED_FORMATS:
        raise HTTPException(400, f"Unsupported format: {req.response_format}. Supported: {', '.join(sorted(SUPPORTED_FORMATS))}")

    content_type = FORMAT_CONTENT_TYPES.get(req.response_format, "audio/mpeg")

    async def audio_stream():
        async for chunk in engine.synthesize_stream(
            text=req.input,
            voice=req.voice,
            speed=req.speed,
            response_format=req.response_format,
        ):
            yield chunk

    return StreamingResponse(audio_stream(), media_type=content_type)
