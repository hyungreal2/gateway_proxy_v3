import httpx
import logging

from .converters import anthropic_to_gemini, gemini_to_anthropic

logger = logging.getLogger(__name__)

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com"


class GeminiClient:

    def __init__(self, api_key=None, timeout=60):
        self.api_key = api_key
        self.timeout = timeout

    def endpoint(self, model: str) -> str:
        return f"{GEMINI_BASE_URL}/v1beta/models/{model}:generateContent"

    async def messages(self, req_dict: dict, api_key: str | None = None) -> dict:
        model = req_dict["model"]
        key = api_key or self.api_key
        headers = {"Content-Type": "application/json"}
        if key:
            headers["x-goog-api-key"] = key

        payload = anthropic_to_gemini(req_dict)
        url = self.endpoint(model)

        async with httpx.AsyncClient() as client:
            r = await client.post(url, json=payload, headers=headers, timeout=self.timeout)
            if not r.is_success:
                logger.error("gemini error status=%s body=%s", r.status_code, r.text)
            r.raise_for_status()
            return gemini_to_anthropic(r.json(), model)
