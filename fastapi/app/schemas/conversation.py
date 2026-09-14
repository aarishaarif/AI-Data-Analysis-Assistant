from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.chat import MessageResponse


class ConversationCreate(BaseModel):
    dataset_id: str
    title: str = Field(default="New analysis", max_length=255)


class ConversationResponse(BaseModel):
    id: str
    dataset_id: str
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationDetail(ConversationResponse):
    messages: list[MessageResponse]
