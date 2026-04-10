from fastapi import APIRouter, Request

from app.models.schemas import VoicesResponse, VoiceInfo

router = APIRouter()


@router.get("/v1/voices")
async def list_voices(request: Request) -> VoicesResponse:
    manager = getattr(request.app.state, "engine_manager", None)
    if manager is None:
        return VoicesResponse(voices=[])

    return VoicesResponse(
        voices=[VoiceInfo(**v) for v in manager.get_voice_info()]
    )
