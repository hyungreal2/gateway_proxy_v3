import httpx


class VLLMClient:

    def __init__(self, base_url, api_key=None):

        self.base_url = base_url
        self.api_key = api_key

    def _headers(self):
        if self.api_key:
            return {"Authorization": f"Bearer {self.api_key}"}
        return {}

    async def chat(self, payload):

        async with httpx.AsyncClient() as client:

            r = await client.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                headers=self._headers(),
                timeout=60
            )

            r.raise_for_status()

            return r.json()

    async def embeddings(self, payload):

        async with httpx.AsyncClient() as client:

            r = await client.post(
                f"{self.base_url}/v1/embeddings",
                json=payload,
                headers=self._headers(),
                timeout=60
            )

            r.raise_for_status()

            return r.json()
