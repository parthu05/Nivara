from __future__ import annotations

import re

CRISIS_REPLY = (
    "I'm really glad you told me, and I want you to get support from people who can help in real life. "
    "I am not a crisis service or a substitute for emergency care.\n\n"
    "If you might act on thoughts of suicide or you are in danger right now, contact local emergency services. "
    "Use the support resource shown at the top of the app to find help in your country. "
    "You can also find local resources at https://findahelpline.com/\n\n"
    "If you can, stay with someone you trust or keep a helpline on the line until you feel safer."
)

_CRISIS = re.compile(
    r"\b("
    r"kill myself|killing myself|suicide|suicidal|end my life|ending my life|"
    r"want to die|wanna die|don't want to live|dont want to live|"
    r"self[- ]harm|cut myself|hurt myself|better off dead|"
    r"no reason to live"
    r")\b",
    re.IGNORECASE,
)

_CONCERN = re.compile(
    r"\b("
    r"panic attack|can't go on|cant go on|hopeless|worthless|"
    r"self[- ]harm|overdose|don't want to be here|dont want to be here"
    r")\b",
    re.IGNORECASE,
)


def classify_safety(text: str) -> tuple[str, str]:
    raw = text.strip()
    if not raw:
        return "ok", "empty"
    if _CRISIS.search(raw):
        return "crisis", "matched crisis language"
    if _CONCERN.search(raw):
        return "concern", "matched high-distress language"
    return "ok", "no crisis markers"


def safety_node(state: dict) -> dict:
    label, reason = classify_safety(state["user_message"])
    update: dict = {"safety_label": label, "safety_reason": reason}
    if label == "crisis":
        update["reply"] = CRISIS_REPLY
    return update
