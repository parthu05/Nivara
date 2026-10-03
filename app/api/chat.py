from __future__ import annotations

from pydantic import BaseModel, Field

from app.api.auth import get_current_user
from app.agents.orchestrator import run_turn
from app.database.models import UserAccount
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.memory.long_term import maybe_update_profile

router = APIRouter(prefix="/api", tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    reply: str
    safety_label: str
    tool_notes: str = ""


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    background_tasks: BackgroundTasks,
    user: UserAccount = Depends(get_current_user),
) -> ChatResponse:
    try:
        result = run_turn(user.session_id, payload.message)
    except Exception as exc:
        detail = str(exc)
        if not detail:
            detail = (
                "Google Gemini is unavailable. If you want to use Ollama instead, install it from "
                "https://ollama.com/download, start `ollama serve`, then run `ollama pull llama3.2` "
                "and `ollama pull nomic-embed-text`."
            )
        raise HTTPException(
            status_code=503,
            detail=f"{detail}",
        ) from exc
    if result.get("safety_label") != "crisis":
        background_tasks.add_task(
            maybe_update_profile, user.session_id, payload.message, result["reply"]
        )
    return ChatResponse(**result)
