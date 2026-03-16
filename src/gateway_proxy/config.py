import json
from pydantic_settings import BaseSettings

class Settings(BaseSettings):

    VLLM_BASE_URL: str = "http://localhost:8080/v1"
    VLLM_API_KEY: str | None = None
    VLLM_EXTRA_HEADERS: str | None = None
    LOG_DIR: str = "logs"
    ANTHROPIC_BASE_URL: str = "https://api.anthropic.com"
    ANTHROPIC_API_KEY: str | None = None

    def vllm_extra_headers(self) -> dict:
        if not self.VLLM_EXTRA_HEADERS:
            return {}
        return json.loads(self.VLLM_EXTRA_HEADERS)

settings = Settings()
