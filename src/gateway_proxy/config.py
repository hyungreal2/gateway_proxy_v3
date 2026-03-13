from pydantic_settings import BaseSettings

class Settings(BaseSettings):

    VLLM_BASE_URL: str = "http://localhost:8080"
    VLLM_API_KEY: str | None = None
    LOG_DIR: str = "logs"
    ANTHROPIC_BASE_URL: str = "https://api.anthropic.com"
    ANTHROPIC_API_KEY: str | None = None

settings = Settings()
