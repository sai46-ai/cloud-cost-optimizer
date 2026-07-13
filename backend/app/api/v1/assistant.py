"""AI Assistant API routes."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.ai_service import AIService
from app.api.deps import get_current_user
from app.models.user import User

from app.core.rate_limit import rate_limiter

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


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
    return await assistant.chat(data.message, user.id)
