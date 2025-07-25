"""AI-related API endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from fastapi.responses import HTMLResponse

from app.services.ai_service import AIService

router = APIRouter()


class SuggestionRequest(BaseModel):
    context: str
    field_name: str


class CommentRequest(BaseModel):
    user_input: str


@router.post("/ai/suggest", response_class=HTMLResponse)
def get_suggestion(
    request: SuggestionRequest,
    ai_service: AIService = Depends(AIService),
):
    """Generate a creative suggestion for a form field."""
    suggestion = ai_service.generate_suggestion(
        context=request.context, field_name=request.field_name
    )
    return suggestion


@router.post("/ai/comment", response_class=HTMLResponse)
def get_comment(
    request: CommentRequest,
    ai_service: AIService = Depends(AIService),
):
    """Generate a funny comment."""
    comment = ai_service.generate_comment(user_input=request.user_input)
    return comment