from pydantic import BaseModel, Field


class TTSRequest(BaseModel):
    model: str
    voice: str
    input: str = Field(..., max_length=4096)
    instructions: str | None = None
    response_format: str = "mp3"
    speed: float = Field(default=1.0, ge=0.25, le=4.0)


class VoiceInfo(BaseModel):
    voice_id: str
    name: str
    language: str
    gender: str
    preview_url: str | None = None


class VoicesResponse(BaseModel):
    voices: list[VoiceInfo]


class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    created: int = 0
    owned_by: str = "local"


class ModelsResponse(BaseModel):
    object: str = "list"
    data: list[ModelInfo]


class HealthResponse(BaseModel):
    status: str
    version: str
