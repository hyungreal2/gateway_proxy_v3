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


def test_log_vllm_routing(mock_vllm, caplog):
    import logging
    with caplog.at_level(logging.INFO, logger="gateway_proxy.main"):
        client.post(
            "/v1/messages",
            json={"model": "Qwen/Qwen2.5-7B-Instruct", "messages": [{"role": "user", "content": "hi"}]}
        )

    in_logs  = [r.message for r in caplog.records if r.message.startswith("IN")]
    ok_logs  = [r.message for r in caplog.records if r.message.startswith("OK")]

    assert any("Qwen/Qwen2.5-7B-Instruct" in m and "/chat/completions" in m for m in in_logs)
    assert any("Qwen/Qwen2.5-7B-Instruct" in m and "/chat/completions" in m for m in ok_logs)


def test_log_bypass_routing(mock_bypass, caplog):
    import logging
    with caplog.at_level(logging.INFO, logger="gateway_proxy.main"):
        client.post(
            "/v1/messages",
            json={"model": "claude-3-5-sonnet-20241022", "messages": [{"role": "user", "content": "hi"}]}
        )

    in_logs = [r.message for r in caplog.records if r.message.startswith("IN")]
    ok_logs = [r.message for r in caplog.records if r.message.startswith("OK")]

    assert any("claude-3-5-sonnet-20241022" in m and "/v1/messages" in m for m in in_logs)
    assert any("claude-3-5-sonnet-20241022" in m and "/v1/messages" in m for m in ok_logs)


def test_log_embeddings_routing(mock_vllm, caplog):
    import logging
    with caplog.at_level(logging.INFO, logger="gateway_proxy.main"):
        client.post(
            "/v1/embeddings",
            json={"model": "embed-model", "input": "hello"}
        )

    in_logs = [r.message for r in caplog.records if r.message.startswith("IN")]
    ok_logs = [r.message for r in caplog.records if r.message.startswith("OK")]

    assert any("embed-model" in m and "/embeddings" in m for m in in_logs)
    assert any("embed-model" in m and "/embeddings" in m for m in ok_logs)


def test_messages_routes_gemini(mock_gemini):

    r = client.post(
        "/v1/messages",
        json={
            "model": "gemini-2.5-flash",
            "messages": [{"role": "user", "content": "Hello!"}]
        }
    )

    assert r.status_code == 200
    assert r.json()["role"] == "assistant"
    assert r.json()["model"] == "gemini-2.5-flash"


def test_log_gemini_routing(mock_gemini, caplog):
    import logging
    with caplog.at_level(logging.INFO, logger="gateway_proxy.main"):
        client.post(
            "/v1/messages",
            json={"model": "gemini-2.5-flash", "messages": [{"role": "user", "content": "hi"}]}
        )

    in_logs = [r.message for r in caplog.records if r.message.startswith("IN")]
    ok_logs = [r.message for r in caplog.records if r.message.startswith("OK")]

    assert any("gemini-2.5-flash" in m and "generateContent" in m for m in in_logs)
    assert any("gemini-2.5-flash" in m and "generateContent" in m for m in ok_logs)


def test_embeddings(mock_vllm):

    r = client.post(
        "/v1/embeddings",
        json={
            "model":"embed",
            "input":"hello"
        }
    )

    assert r.status_code == 200
