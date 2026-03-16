import httpx
import logging

logger = logging.getLogger(__name__)

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com"


class GeminiClient:

    def __init__(self, api_key=None):
        self.api_key = api_key

    def _anthropic_to_gemini(self, req: dict) -> dict:
        contents = []
        for msg in req.get("messages", []):
            role = "model" if msg["role"] == "assistant" else "user"
            content = msg["content"]
            if isinstance(content, str):
                parts = [{"text": content}]
            else:
                parts = [{"text": b["text"]} for b in content if b.get("type") == "text"]
            contents.append({"role": role, "parts": parts})

        payload: dict = {"contents": contents}

        system = req.get("system")
        if system:
            if isinstance(system, str):
                payload["systemInstruction"] = {"parts": [{"text": system}]}
            elif isinstance(system, list):
                parts = [{"text": b["text"]} for b in system if b.get("type") == "text"]
                payload["systemInstruction"] = {"parts": parts}

        gen_config: dict = {}
        if req.get("max_tokens"):
            gen_config["maxOutputTokens"] = req["max_tokens"]
        if req.get("temperature") is not None:
            gen_config["temperature"] = req["temperature"]
        if gen_config:
            payload["generationConfig"] = gen_config

        return payload

    def _gemini_to_anthropic(self, resp: dict, model: str) -> dict:
        candidate = resp["candidates"][0]
        text = "".join(p.get("text", "") for p in candidate["content"]["parts"])
        usage = resp.get("usageMetadata", {})
        return {
            "id": "msg_gemini",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": text}],
            "model": model,
            "stop_reason": "end_turn",
            "usage": {
                "input_tokens": usage.get("promptTokenCount", 0),
                "output_tokens": usage.get("candidatesTokenCount", 0),
            },
        }

    def endpoint(self, model: str) -> str:
        return f"{GEMINI_BASE_URL}/v1beta/models/{model}:generateContent"

    async def messages(self, req_dict: dict, api_key: str | None = None) -> dict:
        model = req_dict["model"]
        key = api_key or self.api_key
        headers = {"Content-Type": "application/json"}
        if key:
            headers["x-goog-api-key"] = key

        payload = self._anthropic_to_gemini(req_dict)
        url = self.endpoint(model)

        async with httpx.AsyncClient() as client:
            r = await client.post(url, json=payload, headers=headers, timeout=60)
            if not r.is_success:
                logger.error("gemini error status=%s body=%s", r.status_code, r.text)
            r.raise_for_status()
            return self._gemini_to_anthropic(r.json(), model)
