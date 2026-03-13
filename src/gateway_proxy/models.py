from pydantic import BaseModel, ConfigDict
from typing import List, Any


class Message(BaseModel):
    model_config = ConfigDict(extra="allow")

    role: str
    content: Any


class MessageRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    model: str
    messages: List[Message]
    max_tokens: int | None = 8096
    temperature: float | None = 0.7
    tools: list | None = None
    system: str | list | None = None


class EmbeddingRequest(BaseModel):

    model: str
    input: str | list
