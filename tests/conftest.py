import pytest

class MockVLLM:

    async def chat(self, payload):
        return {
            "choices": [
                {
                    "message": {
                        "content": "mock response"
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
            },
        }

    async def chat_tool_calls(self, payload):
        return {
            "choices": [
                {
                    "message": {
                        "tool_calls": [
                            {
                                "id": "call_abc",
                                "function": {
                                    "name": "get_weather",
                                    "arguments": "{\"city\": \"Seoul\"}",
                                },
                            },
                            {
                                "id": "call_def",
                                "function": {
                                    "name": "get_time",
                                    "arguments": "{\"tz\": \"KST\"}",
                                },
                            },
                        ]
                    },
                    "finish_reason": "tool_calls",
                }
            ],
            "usage": {
                "prompt_tokens": 15,
                "completion_tokens": 25,
            },
        }

    async def embeddings(self, payload):
        return {
            "data": [
                {"embedding": [0.1, 0.2, 0.3]}
            ]
        }


class MockBypass:

    async def messages(self, payload, api_key=None):
        return {
            "role": "assistant",
            "content": [{"type": "text", "text": "bypass mock response"}]
        }


class MockGemini:

    def endpoint(self, model):
        return f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    async def messages(self, payload, api_key=None):
        return {
            "id": "msg_gemini",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": "gemini mock response"}],
            "model": payload.get("model", "gemini-mock"),
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 5, "output_tokens": 10},
        }


@pytest.fixture
def mock_vllm(monkeypatch):

    from gateway_proxy import main

    monkeypatch.setattr(main, "vllm", MockVLLM())


@pytest.fixture
def mock_vllm_tools(monkeypatch):

    from gateway_proxy import main

    mock = MockVLLM()
    mock.chat = mock.chat_tool_calls
    monkeypatch.setattr(main, "vllm", mock)


@pytest.fixture
def mock_bypass(monkeypatch):

    from gateway_proxy import main

    monkeypatch.setattr(main, "bypass", MockBypass())


@pytest.fixture
def mock_gemini(monkeypatch):

    from gateway_proxy import main

    monkeypatch.setattr(main, "gemini", MockGemini())
