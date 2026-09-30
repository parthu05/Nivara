from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import ChatSession, Message, SessionLocal


def ensure_session(session_id: str) -> None:
    with SessionLocal() as db:
        existing = db.get(ChatSession, session_id)
        if existing is None:
            db.add(ChatSession(id=session_id, profile_summary=""))
            db.commit()


def get_recent_messages(session_id: str, limit: int = 12) -> list[dict[str, str]]:
    with SessionLocal() as db:
        rows = db.scalars(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.id.desc())
            .limit(limit)
        ).all()
    rows = list(reversed(rows))
    return [{"role": row.role, "content": row.content} for row in rows]


def add_message(session_id: str, role: str, content: str) -> None:
    ensure_session(session_id)
    with SessionLocal() as db:
        db.add(Message(session_id=session_id, role=role, content=content))
        db.commit()
