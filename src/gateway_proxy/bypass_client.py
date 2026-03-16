import httpx
import logging

logger = logging.getLogger(__name__)


class BypassClient:

    def __init__(self, base_url, api_key=None, timeout=60):
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout

    async def messages(self, payload, api_key=None):

        headers = {"Content-Type": "application/json"}

        key = api_key or self.api_key
        if key:
            headers["x-api-key"] = key
            headers["anthropic-version"] = "2023-06-01"

        logger.info("bypass payload keys=%s", list(payload.keys()))

        async with httpx.AsyncClient() as client:

            r = await client.post(
                f"{self.base_url}/v1/messages",
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )

            if not r.is_success:
                logger.error("bypass error status=%s body=%s", r.status_code, r.text)

            r.raise_for_status()

            return r.json()
