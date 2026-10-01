from __future__ import annotations

from app.llm.provider import llm
from app.memory.long_term import get_profile, recent_wellness_snapshot
from app.memory.short_term import get_recent_messages
from app.tools.resource_tool import lookup_resources

SYSTEM_PROMPT = """You are Nivara, a warm, grounded mental-wellness companion.

Rules:
- You are not a therapist, doctor, or crisis service. Do not diagnose or prescribe.
- Be concise, human, and specific. Prefer one small next step over a lecture.
- Keep replies to 2-4 sentences and about 60 words unless the user asks for detail.
- Use retrieved knowledge when it helps; do not invent clinical facts.
- If the user may be in crisis, encourage emergency help and 988 / IASP. Never provide harm instructions.
- Reflect feelings first, then ask at most one gentle question.
- If a tool already saved a mood or journal, acknowledge that briefly.
"""


def conversation_node(state: dict) -> dict:
    if state.get("safety_label") == "crisis" and state.get("reply"):
        return {}

    session_id = state["session_id"]
    user_message = state["user_message"]
    history = get_recent_messages(session_id)
    profile = get_profile(session_id)
    snapshot = recent_wellness_snapshot(session_id)
    knowledge = lookup_resources(user_message)
    tool_notes = state.get("tool_notes") or ""
    concern_note = ""
    if state.get("safety_label") == "concern":
        concern_note = (
            "The user sounds in significant distress. Be extra careful, avoid pep-talk cliches, "
            "and mention real-world support if it fits."
        )

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if profile:
        messages.append({"role": "system", "content": f"Known user memory:\n{profile}"})
    messages.append({"role": "system", "content": f"Wellness snapshot:\n{snapshot}"})
    if knowledge:
        messages.append({"role": "system", "content": f"Retrieved knowledge:\n{knowledge}"})
    if tool_notes:
        messages.append({"role": "system", "content": f"Tool results:\n{tool_notes}"})
    if concern_note:
        messages.append({"role": "system", "content": concern_note})
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    reply = llm.chat(messages, max_tokens=180)
    if tool_notes and tool_notes not in reply:
        reply = f"{reply}\n\n_{tool_notes}_"
    return {"reply": reply}
