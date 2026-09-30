from __future__ import annotations

from sqlalchemy import select

from app.database.models import JournalEntry, SessionLocal
from app.memory.short_term import ensure_session


def save_journal(session_id: str, content: str, title: str = "Journal") -> str:
    ensure_session(session_id)
    text = content.strip()
    if not text:
        return "I need a little more writing to save a journal entry."
    with SessionLocal() as db:
        entry = JournalEntry(session_id=session_id, title=title[:200], content=text)
        db.add(entry)
        db.commit()
        db.refresh(entry)
    return f"Saved journal entry #{entry.id} ({entry.title})."


def list_journals(session_id: str, limit: int = 10) -> list[dict]:
    with SessionLocal() as db:
        rows = db.scalars(
            select(JournalEntry)
            .where(JournalEntry.session_id == session_id)
            .order_by(JournalEntry.id.desc())
            .limit(limit)
        ).all()
    return [
        {
            "id": row.id,
            "title": row.title,
            "content": row.content,
            "created_at": row.created_at.isoformat() if row.created_at else "",
        }
        for row in rows
    ]
