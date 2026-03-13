import pytest

class MockVLLM:

    async def chat(self, payload):
        return {
            "choices":[
                {
                    "message":{
                        "content":"mock response"
                    }
                }
            ]
        }

    async def embeddings(self, payload):
        return {
            "data":[
                {"embedding":[0.1,0.2,0.3]}
            ]
        }


class MockBypass:

    async def messages(self, payload, api_key=None):
        return {
            "role": "assistant",
            "content": [{"type": "text", "text": "bypass mock response"}]
        }


@pytest.fixture
def mock_vllm(monkeypatch):

    from gateway_proxy import main

    monkeypatch.setattr(main, "vllm", MockVLLM())


@pytest.fixture
def mock_bypass(monkeypatch):

    from gateway_proxy import main

    monkeypatch.setattr(main, "bypass", MockBypass())
