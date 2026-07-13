"""AI Assistant API routes."""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.services.ai_service import AIService
from app.api.deps import get_current_user
from app.models.user import User

from app.core.rate_limit import rate_limiter

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    provider: Optional[str] = "gemini"


class ChatResponse(BaseModel):
    response: str
    source: str
    suggestions: list[str]


@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(rate_limiter)])
async def chat(
    data: ChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Send a message to the AI FinOps assistant."""
    assistant = AIService(db)
    return await assistant.chat(data.message, provider=data.provider or "gemini", user_id=user.id)


@router.post("/chat/stream", dependencies=[Depends(rate_limiter)])
async def chat_stream(
    data: ChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Stream response from the AI assistant."""
    assistant = AIService(db)
    return StreamingResponse(
        assistant.chat_stream(data.message, provider=data.provider or "gemini", user_id=user.id),
        media_type="text/event-stream"
    )
