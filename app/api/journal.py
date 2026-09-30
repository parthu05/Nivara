from __future__ import annotations

from app.api.auth import get_current_user
from app.database.models import UserAccount
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends

from app.tools.journal_tool import list_journals, save_journal

router = APIRouter(prefix="/api/journal", tags=["journal"])


class JournalIn(BaseModel):
    title: str = "Journal"
    content: str = Field(min_length=1, max_length=8000)


@router.post("")
def create_journal(
    payload: JournalIn, user: UserAccount = Depends(get_current_user)
) -> dict:
    message = save_journal(user.session_id, payload.content, payload.title)
    return {"ok": True, "message": message}


@router.get("")
def get_journals(user: UserAccount = Depends(get_current_user)) -> dict:
    return {"items": list_journals(user.session_id)}
