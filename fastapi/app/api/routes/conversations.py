from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db.database import get_db
from app.db.models import Conversation
from app.schemas.chat import MessageResponse
from app.schemas.conversation import ConversationCreate, ConversationDetail, ConversationResponse
from app.services.dataset_service import get_dataset

router = APIRouter(prefix="/conversations", tags=["conversations"])


def message_out(message) -> dict:
    return {"id": message.id, "role": message.role, "content": message.content, "metadata": message.metadata_json, "created_at": message.created_at}


def conversation_out(conversation) -> dict:
    return {"id": conversation.id, "dataset_id": conversation.dataset_id, "title": conversation.title, "created_at": conversation.created_at, "updated_at": conversation.updated_at}


def get_conversation(db: Session, conversation_id: str) -> Conversation:
    conversation = db.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return conversation


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(payload: ConversationCreate, db: Session = Depends(get_db)):
    dataset = get_dataset(db, payload.dataset_id)
    conversation = Conversation(dataset_id=dataset.id, title=payload.title, expires_at=datetime.utcnow() + timedelta(hours=settings.default_data_ttl_hours))
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation_out(conversation)


@router.get("/{conversation_id}", response_model=ConversationDetail)
def read_conversation(conversation_id: str, db: Session = Depends(get_db)):
    conversation = get_conversation(db, conversation_id)
    return conversation_out(conversation) | {"messages": [message_out(item) for item in conversation.messages]}


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
def messages(conversation_id: str, db: Session = Depends(get_db)):
    return [message_out(item) for item in get_conversation(db, conversation_id).messages]


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(conversation_id: str, db: Session = Depends(get_db)):
    db.delete(get_conversation(db, conversation_id))
    db.commit()
