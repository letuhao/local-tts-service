from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    app_name: str = "local-tts-service"
    host: str = "0.0.0.0"
    port: int = 9880
    api_key: str = "dev_key"

    # Paths
    models_dir: Path = Path("models")
    voices_dir: Path = Path("voices")

    # TTS engine
    default_model: str = "kokoro-v1"
    default_voice: str = "af_heart"

    model_config = {"env_prefix": "TTS_", "env_file": ".env"}


settings = Settings()
