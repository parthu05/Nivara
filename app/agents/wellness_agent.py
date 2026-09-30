from __future__ import annotations

import re

from app.tools.journal_tool import save_journal
from app.tools.mood_tool import save_mood

_MOOD = re.compile(
    r"\b(log|track|record|save|rate)\b.{0,24}\bmood\b|\bmood\b.{0,12}\b([0-9]|10)\b",
    re.IGNORECASE,
)
_JOURNAL = re.compile(
    r"\b(journal|diary|write this down|save this)\b",
    re.IGNORECASE,
)
_SCORE = re.compile(r"\b([0-9]|10)\b")


def _maybe_mood(session_id: str, text: str) -> str | None:
    if not _MOOD.search(text):
        return None
    match = _SCORE.search(text)
    if not match:
        return None
    note = text.strip()
    return save_mood(session_id, float(match.group(1)), note=note)


def _maybe_journal(session_id: str, text: str) -> str | None:
    if not _JOURNAL.search(text):
        return None
    if len(text.strip()) < 12:
        return None
    title = "Journal"
    lowered = text.lower()
    if "grateful" in lowered:
        title = "Gratitude"
    return save_journal(session_id, text, title=title)


def wellness_node(state: dict) -> dict:
    if state.get("safety_label") == "crisis":
        return {"tool_notes": ""}
    session_id = state["session_id"]
    text = state["user_message"]
    notes = [item for item in (_maybe_mood(session_id, text), _maybe_journal(session_id, text)) if item]
    return {"tool_notes": " ".join(notes)}
