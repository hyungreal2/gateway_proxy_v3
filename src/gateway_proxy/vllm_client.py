import httpx
import logging

logger = logging.getLogger(__name__)


class VLLMClient:

    def __init__(self, base_url, api_key=None, extra_headers=None, timeout=60):

        self.base_url = base_url
        self.api_key = api_key
        self.extra_headers = extra_headers or {}
        self.timeout = timeout

    def _headers(self):
        headers = dict(self.extra_headers)
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def chat(self, payload):

        async with httpx.AsyncClient() as client:

            r = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=self._headers(),
                timeout=self.timeout
            )

            if not r.is_success:
                logger.error("vllm error status=%s body=%s", r.status_code, r.text)

            r.raise_for_status()

            return r.json()

    async def embeddings(self, payload):

        async with httpx.AsyncClient() as client:

            r = await client.post(
                f"{self.base_url}/embeddings",
                json=payload,
                headers=self._headers(),
                timeout=self.timeout
            )

            r.raise_for_status()

            return r.json()
