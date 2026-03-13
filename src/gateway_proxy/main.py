from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from .models import MessageRequest, EmbeddingRequest
from .converters import (
    anthropic_to_openai_messages,
    openai_to_anthropic
)
from .vllm_client import VLLMClient
from .bypass_client import BypassClient
from .logger import get_logger
from .config import settings

logger = get_logger(__name__)

app = FastAPI(title="LLM Gateway")

vllm = VLLMClient(
    base_url=settings.VLLM_BASE_URL,
    api_key=settings.VLLM_API_KEY,
)

bypass = BypassClient(
    base_url=settings.ANTHROPIC_BASE_URL,
    api_key=settings.ANTHROPIC_API_KEY,
)

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/v1/messages")
async def messages(req: MessageRequest, request: Request):

    try:
        if req.model.startswith("claude-"):
            payload = req.model_dump(exclude_none=True)

            logger.info("bypass request model=%s messages=%s", req.model, req.messages)

            api_key = request.headers.get("x-api-key") or settings.ANTHROPIC_API_KEY
            resp = await bypass.messages(payload, api_key=api_key)

            logger.info("bypass response %s", resp)

            return JSONResponse(resp)

        openai_msgs = anthropic_to_openai_messages([m.model_dump() for m in req.messages])

        payload = {
            "model": req.model,
            "messages": openai_msgs,
            "max_tokens": req.max_tokens,
            "temperature": req.temperature,
            "tools": req.tools
        }

        logger.info("request model=%s messages=%s", req.model, openai_msgs)

        resp = await vllm.chat(payload)

        result = openai_to_anthropic(resp)

        logger.info("response %s", result)

        return JSONResponse(result)

    except Exception as e:
        logger.exception("gateway_error")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/messages/bypass")
async def messages_bypass(req: MessageRequest, request: Request):

    try:
        payload = req.model_dump(exclude_none=True)

        logger.info("bypass request model=%s messages=%s", req.model, req.messages)

        api_key = request.headers.get("x-api-key") or settings.ANTHROPIC_API_KEY
        resp = await bypass.messages(payload, api_key=api_key)

        logger.info("bypass response %s", resp)

        return JSONResponse(resp)

    except Exception as e:
        logger.exception("bypass_error")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/embeddings")
async def embeddings(req: EmbeddingRequest):

    if not req.input:
        raise HTTPException(status_code=400, detail="missing input")

    resp = await vllm.embeddings({
        "model": req.model,
        "input": req.input
    })

    return resp


if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080
    )
