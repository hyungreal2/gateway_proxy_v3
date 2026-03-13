from fastapi.testclient import TestClient
from gateway_proxy.main import app

client = TestClient(app)


def test_health():

    r = client.get("/health")

    assert r.status_code == 200


def test_messages(mock_vllm):

    r = client.post(
        "/v1/messages",
        json={
            "model":"test",
            "messages":[
                {"role":"user","content":"hello"}
            ]
        }
    )

    assert r.status_code == 200


def test_messages_routes_claude_to_bypass(mock_bypass):

    r = client.post(
        "/v1/messages",
        json={
            "model": "claude-3-5-sonnet-20241022",
            "messages": [
                {"role": "user", "content": "Hello!"}
            ]
        }
    )

    assert r.status_code == 200
    assert r.json()["role"] == "assistant"


def test_messages_bypass(mock_bypass):

    r = client.post(
        "/v1/messages/bypass",
        json={
            "model": "claude-3-5-sonnet-20241022",
            "messages": [
                {"role": "user", "content": "Hello!"}
            ]
        }
    )

    assert r.status_code == 200
    assert r.json()["role"] == "assistant"


def test_embeddings(mock_vllm):

    r = client.post(
        "/v1/embeddings",
        json={
            "model":"embed",
            "input":"hello"
        }
    )

    assert r.status_code == 200
