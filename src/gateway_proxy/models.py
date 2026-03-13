from pydantic import BaseModel
from typing import List, Any


class Message(BaseModel):
    role: str
    content: Any


class MessageRequest(BaseModel):

    model: str
    messages: List[Message]
    max_tokens: int | None = 8096
    temperature: float | None = 0.7
    tools: list | None = None
    system: str | list | None = None


class EmbeddingRequest(BaseModel):

    model: str
    input: str | list
