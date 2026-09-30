from __future__ import annotations

from sqlalchemy import select

from app.database.models import ChatSession, JournalEntry, MoodEntry, SessionLocal
from app.llm.provider import llm
from app.memory.short_term import ensure_session


def get_profile(session_id: str) -> str:
    ensure_session(session_id)
    with SessionLocal() as db:
        row = db.get(ChatSession, session_id)
        return (row.profile_summary if row else "") or ""


def recent_wellness_snapshot(session_id: str) -> str:
    with SessionLocal() as db:
        moods = db.scalars(
            select(MoodEntry)
            .where(MoodEntry.session_id == session_id)
            .order_by(MoodEntry.id.desc())
            .limit(5)
        ).all()
        journals = db.scalars(
            select(JournalEntry)
            .where(JournalEntry.session_id == session_id)
            .order_by(JournalEntry.id.desc())
            .limit(3)
        ).all()
    mood_bits = [f"{m.score}/10 {m.label}".strip() for m in moods] or ["none yet"]
    journal_bits = [j.title for j in journals] or ["none yet"]
    return f"Recent moods: {', '.join(mood_bits)}. Recent journals: {', '.join(journal_bits)}."


def maybe_update_profile(session_id: str, user_message: str, assistant_reply: str) -> None:
    """Keep a short non-clinical summary so later chats feel continuous."""
    current = get_profile(session_id)
    snapshot = recent_wellness_snapshot(session_id)
    try:
        summary = llm.chat(
            [
                {
                    "role": "system",
                    "content": (
                        "Update a brief user-memory note for a wellness chatbot. "
                        "No diagnoses. No sensitive crisis details. Max 80 words. "
                        "Keep only preferences, coping styles, and themes the user volunteered."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Current memory:\n{current or '(empty)'}\n\n"
                        f"{snapshot}\n\n"
                        f"User: {user_message}\nAssistant: {assistant_reply}\n\n"
                        "Return only the updated memory note."
                    ),
                },
            ],
            temperature=0.2,
            max_tokens=180,
        )
    except Exception:
        return
    with SessionLocal() as db:
        row = db.get(ChatSession, session_id)
        if row is None:
            return
        row.profile_summary = summary.strip()
        db.commit()
