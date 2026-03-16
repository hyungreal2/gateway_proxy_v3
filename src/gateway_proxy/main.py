from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from .models import MessageRequest, EmbeddingRequest
from .converters import (
    anthropic_to_openai_messages,
    openai_to_anthropic
)
from .vllm_client import VLLMClient
from .bypass_client import BypassClient
from .gemini_client import GeminiClient
from .logger import get_logger
from .config import settings

logger = get_logger(__name__)

app = FastAPI(title="LLM Gateway")

vllm = VLLMClient(
    base_url=settings.VLLM_BASE_URL,
    api_key=settings.VLLM_API_KEY,
    extra_headers=settings.vllm_extra_headers(),
)

bypass = BypassClient(
    base_url=settings.ANTHROPIC_BASE_URL,
    api_key=settings.ANTHROPIC_API_KEY,
)

gemini = GeminiClient(api_key=settings.GEMINI_API_KEY)

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/v1/messages")
async def messages(req: MessageRequest, request: Request):

    try:
        if req.model.startswith("gemini-"):
            dst = gemini.endpoint(req.model)
            logger.info("IN POST /v1/messages model=%s → OUT %s", req.model, dst)

            payload = req.model_dump(exclude_none=True)
            api_key = request.headers.get("x-goog-api-key") or settings.GEMINI_API_KEY
            resp = await gemini.messages(payload, api_key=api_key)

            logger.info("OK  POST /v1/messages model=%s ← %s", req.model, dst)
            return JSONResponse(resp)

        if req.model.startswith("claude-"):
            dst = f"{settings.ANTHROPIC_BASE_URL}/v1/messages"
            logger.info("IN POST /v1/messages model=%s → OUT %s", req.model, dst)

            payload = req.model_dump(exclude_none=True)
            api_key = request.headers.get("x-api-key") or settings.ANTHROPIC_API_KEY
            resp = await bypass.messages(payload, api_key=api_key)

            logger.info("OK  POST /v1/messages model=%s ← %s", req.model, dst)
            return JSONResponse(resp)

        dst = f"{settings.VLLM_BASE_URL}/chat/completions"
        logger.info("IN POST /v1/messages model=%s → OUT %s", req.model, dst)

        openai_msgs = anthropic_to_openai_messages([m.model_dump() for m in req.messages])
        payload = {
            "model": req.model,
            "messages": openai_msgs,
            "max_tokens": req.max_tokens,
            "temperature": req.temperature,
            "tools": req.tools
        }

        resp = await vllm.chat(payload)
        result = openai_to_anthropic(resp, model=req.model)

        logger.info("OK  POST /v1/messages model=%s ← %s", req.model, dst)
        return JSONResponse(result)

    except Exception as e:
        logger.exception("ERR POST /v1/messages model=%s", req.model)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/messages/bypass")
async def messages_bypass(req: MessageRequest, request: Request):

    try:
        dst = f"{settings.ANTHROPIC_BASE_URL}/v1/messages"
        logger.info("IN POST /v1/messages/bypass model=%s → OUT %s", req.model, dst)

        payload = req.model_dump(exclude_none=True)
        api_key = request.headers.get("x-api-key") or settings.ANTHROPIC_API_KEY
        resp = await bypass.messages(payload, api_key=api_key)

        logger.info("OK  POST /v1/messages/bypass model=%s ← %s", req.model, dst)
        return JSONResponse(resp)

    except Exception as e:
        logger.exception("ERR POST /v1/messages/bypass model=%s", req.model)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/embeddings")
async def embeddings(req: EmbeddingRequest):

    if not req.input:
        raise HTTPException(status_code=400, detail="missing input")

    dst = f"{settings.VLLM_BASE_URL}/embeddings"
    logger.info("IN POST /v1/embeddings model=%s → OUT %s", req.model, dst)

    resp = await vllm.embeddings({
        "model": req.model,
        "input": req.input
    })

    logger.info("OK  POST /v1/embeddings model=%s ← %s", req.model, dst)
    return resp


if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080
    )
