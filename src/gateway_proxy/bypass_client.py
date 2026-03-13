import httpx


class BypassClient:

    def __init__(self, base_url, api_key=None):
        self.base_url = base_url
        self.api_key = api_key

    async def messages(self, payload):

        headers = {"Content-Type": "application/json"}

        if self.api_key:
            headers["x-api-key"] = self.api_key
            headers["anthropic-version"] = "2023-06-01"

        async with httpx.AsyncClient() as client:

            r = await client.post(
                f"{self.base_url}/v1/messages",
                json=payload,
                headers=headers,
                timeout=60,
            )

            r.raise_for_status()

            return r.json()
