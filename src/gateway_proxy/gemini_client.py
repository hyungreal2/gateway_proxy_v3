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

    def embed_endpoint(self, model: str, batch: bool = False) -> str:
        action = "batchEmbedContents" if batch else "embedContent"
        return f"{GEMINI_BASE_URL}/v1beta/models/{model}:{action}"

    async def embed(self, model: str, input_data, api_key: str | None = None) -> dict:
        key = api_key or self.api_key
        headers = {"Content-Type": "application/json"}

        is_batch = isinstance(input_data, list)

        if is_batch:
            url = self.embed_endpoint(model, batch=True)
            payload = {
                "requests": [
                    {
                        "model": f"models/{model}",
                        "content": {"parts": [{"text": t}]},
                    }
                    for t in input_data
                ]
            }
        else:
            url = self.embed_endpoint(model, batch=False)
            payload = {"content": {"parts": [{"text": input_data}]}}

        if key:
            url = f"{url}?key={key}"

        async with httpx.AsyncClient() as client:
            r = await client.post(url, json=payload, headers=headers, timeout=self.timeout)
            if not r.is_success:
                logger.error("gemini embed error status=%s body=%s", r.status_code, r.text)
            r.raise_for_status()
            resp = r.json()

        if is_batch:
            data = [
                {"object": "embedding", "embedding": e["values"], "index": i}
                for i, e in enumerate(resp["embeddings"])
            ]
        else:
            data = [{"object": "embedding", "embedding": resp["embedding"]["values"], "index": 0}]

        return {"object": "list", "data": data, "model": model}

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
