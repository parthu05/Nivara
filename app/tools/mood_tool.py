from __future__ import annotations

from sqlalchemy import select

from app.database.models import MoodEntry, SessionLocal
from app.memory.short_term import ensure_session


def save_mood(session_id: str, score: float, label: str = "", note: str = "") -> str:
    ensure_session(session_id)
    clamped = max(0.0, min(10.0, float(score)))
    with SessionLocal() as db:
        entry = MoodEntry(
            session_id=session_id,
            score=clamped,
            label=label.strip()[:80],
            note=note.strip(),
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
    return f"Logged mood {clamped:g}/10" + (f" ({entry.label})" if entry.label else "") + "."


def list_moods(session_id: str, limit: int = 14) -> list[dict]:
    with SessionLocal() as db:
        rows = db.scalars(
            select(MoodEntry)
            .where(MoodEntry.session_id == session_id)
            .order_by(MoodEntry.id.desc())
            .limit(limit)
        ).all()
    return [
        {
            "id": row.id,
            "score": row.score,
            "label": row.label,
            "note": row.note,
            "created_at": row.created_at.isoformat() if row.created_at else "",
        }
        for row in rows
    ]
