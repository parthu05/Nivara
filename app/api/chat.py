from __future__ import annotations

from pydantic import BaseModel, Field

from app.api.auth import get_current_user
from app.agents.orchestrator import run_turn
from app.database.models import UserAccount
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/api", tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    reply: str
    safety_label: str
    tool_notes: str = ""


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, user: UserAccount = Depends(get_current_user)) -> ChatResponse:
    try:
        result = run_turn(user.session_id, payload.message)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "The language model is unavailable. Start Ollama locally "
                f"(or switch LLM_PROVIDER) and retry. ({exc.__class__.__name__})"
            ),
        ) from exc
    return ChatResponse(**result)
