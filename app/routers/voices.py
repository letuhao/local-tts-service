from fastapi import APIRouter, Request

from app.models.schemas import VoicesResponse, VoiceInfo

router = APIRouter()


@router.get("/v1/voices")
async def list_voices(request: Request) -> VoicesResponse:
    engine = getattr(request.app.state, "tts_engine", None)
    if engine is None:
        return VoicesResponse(voices=[])

    return VoicesResponse(
        voices=[VoiceInfo(**v) for v in engine.get_voice_info()]
    )
