import logging

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
from .user_logger import identify_user, get_user_logger, _user_id_hash
from .config import settings

logger = get_logger(__name__)

_MAX_LOG_LEN = 2000


def _trunc(obj) -> str:
    s = str(obj)
    return s[:_MAX_LOG_LEN] + "..." if len(s) > _MAX_LOG_LEN else s


def _get_ulogger(request: Request) -> logging.Logger:
    raw = identify_user(request)
    return get_user_logger(_user_id_hash(raw))


app = FastAPI(title="LLM Gateway")

vllm = VLLMClient(
    base_url=settings.VLLM_BASE_URL,
    api_key=settings.VLLM_API_KEY,
    extra_headers=settings.vllm_extra_headers(),
    timeout=settings.HTTP_TIMEOUT,
)

bypass = BypassClient(
    base_url=settings.ANTHROPIC_BASE_URL,
    api_key=settings.ANTHROPIC_API_KEY,
    timeout=settings.HTTP_TIMEOUT,
)

gemini = GeminiClient(api_key=settings.gemini_api_key, timeout=settings.HTTP_TIMEOUT)

@app.get("/health")
def health():
    return {"status": "ok"}


def _resolve_destination(model: str) -> str:
    if model.startswith("gemini-"):
        return gemini.endpoint(model)
    if model.startswith("claude-"):
        return f"{settings.ANTHROPIC_BASE_URL}/v1/messages"
    return f"{settings.VLLM_BASE_URL}/chat/completions"


async def _dispatch(req: MessageRequest, request: Request):
    if req.model.startswith("gemini-"):
        payload = req.model_dump(exclude_none=True)
        api_key = request.headers.get("x-goog-api-key") or settings.gemini_api_key
        return await gemini.messages(payload, api_key=api_key)

    if req.model.startswith("claude-"):
        payload = req.model_dump(exclude_none=True)
        api_key = request.headers.get("x-api-key") or settings.ANTHROPIC_API_KEY
        return await bypass.messages(payload, api_key=api_key)

    openai_msgs = anthropic_to_openai_messages([m.model_dump() for m in req.messages])
    payload = {
        "model": req.model,
        "messages": openai_msgs,
        "max_tokens": req.max_tokens,
        "temperature": req.temperature,
        "tools": req.tools,
    }
    resp = await vllm.chat(payload)
    return openai_to_anthropic(resp, model=req.model)


@app.post("/v1/messages")
async def messages(req: MessageRequest, request: Request):
    ulog = _get_ulogger(request)

    try:
        dst = _resolve_destination(req.model)
        logger.info("IN POST /v1/messages model=%s → OUT %s", req.model, dst)
        ulog.info("IN POST /v1/messages model=%s messages=%s", req.model, _trunc(req.messages))
        result = await _dispatch(req, request)
        logger.info("OK  POST /v1/messages model=%s ← %s", req.model, dst)
        ulog.info("OUT POST /v1/messages model=%s result=%s", req.model, _trunc(result))
        return JSONResponse(result)

    except Exception as e:
        logger.exception("ERR POST /v1/messages model=%s", req.model)
        ulog.error("ERR POST /v1/messages model=%s error=%s", req.model, _trunc(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/messages/bypass")
async def messages_bypass(req: MessageRequest, request: Request):
    ulog = _get_ulogger(request)

    try:
        dst = f"{settings.ANTHROPIC_BASE_URL}/v1/messages"
        logger.info("IN POST /v1/messages/bypass model=%s → OUT %s", req.model, dst)
        ulog.info("IN POST /v1/messages/bypass model=%s messages=%s", req.model, _trunc(req.messages))

        payload = req.model_dump(exclude_none=True)
        api_key = request.headers.get("x-api-key") or settings.ANTHROPIC_API_KEY
        resp = await bypass.messages(payload, api_key=api_key)

        logger.info("OK  POST /v1/messages/bypass model=%s ← %s", req.model, dst)
        ulog.info("OUT POST /v1/messages/bypass model=%s result=%s", req.model, _trunc(resp))
        return JSONResponse(resp)

    except Exception as e:
        logger.exception("ERR POST /v1/messages/bypass model=%s", req.model)
        ulog.error("ERR POST /v1/messages/bypass model=%s error=%s", req.model, _trunc(e))
        raise HTTPException(status_code=500, detail=str(e))


def _is_gemini_embedding_model(model: str) -> bool:
    return model.startswith("text-embedding-") or model.startswith("text-multilingual-embedding-")


@app.post("/v1/embeddings")
async def embeddings(req: EmbeddingRequest, request: Request):
    ulog = _get_ulogger(request)

    if not req.input:
        raise HTTPException(status_code=400, detail="missing input")

    try:
        if _is_gemini_embedding_model(req.model):
            is_batch = isinstance(req.input, list)
            dst = gemini.embed_endpoint(req.model, batch=is_batch)
            logger.info("IN POST /v1/embeddings model=%s → OUT %s", req.model, dst)
            ulog.info("IN POST /v1/embeddings model=%s input=%s", req.model, _trunc(req.input))

            resp = await gemini.embed(req.model, req.input, api_key=settings.gemini_api_key)

            logger.info("OK  POST /v1/embeddings model=%s ← %s", req.model, dst)
            ulog.info("OUT POST /v1/embeddings model=%s result=%s", req.model, _trunc(resp))
            return resp

        dst = f"{settings.VLLM_BASE_URL}/embeddings"
        logger.info("IN POST /v1/embeddings model=%s → OUT %s", req.model, dst)
        ulog.info("IN POST /v1/embeddings model=%s input=%s", req.model, _trunc(req.input))

        resp = await vllm.embeddings({
            "model": req.model,
            "input": req.input
        })

        logger.info("OK  POST /v1/embeddings model=%s ← %s", req.model, dst)
        ulog.info("OUT POST /v1/embeddings model=%s result=%s", req.model, _trunc(resp))
        return resp

    except Exception as e:
        logger.exception("ERR POST /v1/embeddings model=%s", req.model)
        ulog.error("ERR POST /v1/embeddings model=%s error=%s", req.model, _trunc(e))
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080
    )
