from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.db.database import get_db
from app.db.models import ChatMessage, Conversation
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.analysis_service import answer_question
from app.services.dataset_service import get_dataset

router = APIRouter(tags=["chat"])


def output(message: ChatMessage) -> dict:
    return {"id": message.id, "role": message.role, "content": message.content, "metadata": message.metadata_json, "created_at": message.created_at}


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    dataset = get_dataset(db, payload.dataset_id)
    if payload.conversation_id:
        conversation = db.get(Conversation, payload.conversation_id)
        if not conversation or conversation.dataset_id != dataset.id:
            raise HTTPException(status_code=404, detail="Conversation not found for this dataset.")
    else:
        conversation = Conversation(dataset_id=dataset.id, title=payload.message[:80], expires_at=datetime.utcnow() + timedelta(hours=settings.default_data_ttl_hours))
        db.add(conversation)
        db.flush()
    user_message = ChatMessage(conversation_id=conversation.id, role="user", content=payload.message)
    db.add(user_message)
    content, analysis, visualization = answer_question(dataset.file_path, payload.message)
    metadata = analysis | ({"chart_id": visualization["chart_id"], "chart_type": visualization["type"]} if visualization else {})
    assistant_message = ChatMessage(conversation_id=conversation.id, role="assistant", content=content, metadata_json=metadata)
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)
    return {"conversation_id": conversation.id, "message": output(assistant_message), "analysis": analysis, "visualization": visualization}
