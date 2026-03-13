from pydantic import BaseModel
from typing import List, Any


class Message(BaseModel):
    role: str
    content: Any


class MessageRequest(BaseModel):

    model: str
    messages: List[Message]
    temperature: float | None = 0.7
    tools: list | None = None


class EmbeddingRequest(BaseModel):

    model: str
    input: str | list
