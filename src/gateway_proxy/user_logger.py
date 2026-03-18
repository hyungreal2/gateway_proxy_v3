import hashlib
import logging
import os
from logging.handlers import RotatingFileHandler

from fastapi import Request

from .config import settings

_user_loggers: dict[str, logging.Logger] = {}


def identify_user(request: Request) -> str:
    if api_key := request.headers.get("x-api-key"):
        return api_key
    if goog_key := request.headers.get("x-goog-api-key"):
        return goog_key
    if auth := request.headers.get("authorization"):
        if auth.lower().startswith("bearer "):
            return auth[7:]
        return auth
    return request.client.host


def _user_id_hash(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()[:8]


def get_user_logger(user_id_hash: str) -> logging.Logger:
    if user_id_hash in _user_loggers:
        return _user_loggers[user_id_hash]

    logger = logging.getLogger(f"gateway_proxy.user.{user_id_hash}")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    log_dir = os.path.join(settings.LOG_DIR, "users")
    os.makedirs(log_dir, exist_ok=True)

    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handler = RotatingFileHandler(
        os.path.join(log_dir, f"{user_id_hash}.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
    )
    handler.setFormatter(fmt)
    logger.addHandler(handler)

    _user_loggers[user_id_hash] = logger
    return logger
