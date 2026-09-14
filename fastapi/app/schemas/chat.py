from datetime import datetime

from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class ChatRequest(MessageCreate):
    dataset_id: str
    conversation_id: str | None = None


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    metadata: dict | None = None
    created_at: datetime


class ChatResponse(BaseModel):
    conversation_id: str
    message: MessageResponse
    analysis: dict | None = None
    visualization: dict | None = None
