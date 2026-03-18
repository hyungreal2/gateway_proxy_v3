import os

import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from gateway_proxy.user_logger import (
    identify_user,
    _user_id_hash,
    get_user_logger,
    _user_loggers,
)


@pytest.fixture(autouse=True)
def clear_logger_cache():
    _user_loggers.clear()
    yield
    _user_loggers.clear()


def _mock_request(headers=None, client_host="127.0.0.1"):
    req = MagicMock()
    req.headers = headers or {}
    req.client.host = client_host
    return req


# --- identify_user tests ---

def test_identify_user_x_api_key():
    req = _mock_request(headers={"x-api-key": "sk-ant-key123"})
    assert identify_user(req) == "sk-ant-key123"


def test_identify_user_x_goog_api_key():
    req = _mock_request(headers={"x-goog-api-key": "goog-key456"})
    assert identify_user(req) == "goog-key456"


def test_identify_user_authorization_bearer():
    req = _mock_request(headers={"authorization": "Bearer tok789"})
    assert identify_user(req) == "tok789"


def test_identify_user_priority_x_api_key_over_goog():
    req = _mock_request(headers={
        "x-api-key": "ant-key",
        "x-goog-api-key": "goog-key",
    })
    assert identify_user(req) == "ant-key"


def test_identify_user_fallback_client_host():
    req = _mock_request(headers={}, client_host="10.0.0.5")
    assert identify_user(req) == "10.0.0.5"


# --- _user_id_hash tests ---

def test_user_id_hash_length():
    h = _user_id_hash("some-api-key")
    assert len(h) == 8
    assert all(c in "0123456789abcdef" for c in h)


def test_user_id_hash_deterministic():
    assert _user_id_hash("key1") == _user_id_hash("key1")
    assert _user_id_hash("key1") != _user_id_hash("key2")


# --- get_user_logger tests ---

def test_get_user_logger_creates_file(tmp_path, monkeypatch):
    monkeypatch.setattr("gateway_proxy.user_logger.settings.LOG_DIR", str(tmp_path))

    ulogger = get_user_logger("abcd1234")

    assert ulogger.name == "gateway_proxy.user.abcd1234"
    assert ulogger.propagate is False
    assert os.path.isfile(tmp_path / "users" / "abcd1234.log")


def test_get_user_logger_caches(tmp_path, monkeypatch):
    monkeypatch.setattr("gateway_proxy.user_logger.settings.LOG_DIR", str(tmp_path))

    l1 = get_user_logger("aabb1122")
    l2 = get_user_logger("aabb1122")
    assert l1 is l2


# --- Integration test ---

def test_messages_creates_user_log(mock_vllm, tmp_path, monkeypatch):
    monkeypatch.setattr("gateway_proxy.user_logger.settings.LOG_DIR", str(tmp_path))

    from gateway_proxy.main import app
    client = TestClient(app)

    r = client.post(
        "/v1/messages",
        json={
            "model": "test",
            "messages": [{"role": "user", "content": "hello"}],
        },
        headers={"x-api-key": "test-key-abc"},
    )

    assert r.status_code == 200

    user_hash = _user_id_hash("test-key-abc")
    log_file = tmp_path / "users" / f"{user_hash}.log"
    assert log_file.exists()

    log_content = log_file.read_text()
    assert "IN POST /v1/messages" in log_content
    assert "OUT POST /v1/messages" in log_content
