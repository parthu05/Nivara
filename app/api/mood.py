from __future__ import annotations

from app.api.auth import get_current_user
from app.database.models import UserAccount
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends

from app.tools.mood_tool import list_moods, save_mood

router = APIRouter(prefix="/api/mood", tags=["mood"])


class MoodIn(BaseModel):
    score: float = Field(ge=0, le=10)
    label: str = ""
    note: str = ""


@router.post("")
def create_mood(payload: MoodIn, user: UserAccount = Depends(get_current_user)) -> dict:
    message = save_mood(user.session_id, payload.score, payload.label, payload.note)
    return {"ok": True, "message": message}


@router.get("")
def get_moods(user: UserAccount = Depends(get_current_user)) -> dict:
    return {"items": list_moods(user.session_id)}
