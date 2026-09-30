from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.agents.conversation_agent import conversation_node
from app.agents.safety_agent import safety_node
from app.agents.wellness_agent import wellness_node
from app.memory.long_term import maybe_update_profile
from app.memory.short_term import add_message, ensure_session


class GraphState(TypedDict, total=False):
    session_id: str
    user_message: str
    safety_label: str
    safety_reason: str
    tool_notes: str
    reply: str


def _route_after_safety(state: GraphState) -> str:
    if state.get("safety_label") == "crisis":
        return "end"
    return "wellness"


def build_graph():
    graph = StateGraph(GraphState)
    graph.add_node("safety", safety_node)
    graph.add_node("wellness", wellness_node)
    graph.add_node("conversation", conversation_node)
    graph.add_edge(START, "safety")
    graph.add_conditional_edges(
        "safety",
        _route_after_safety,
        {"end": END, "wellness": "wellness"},
    )
    graph.add_edge("wellness", "conversation")
    graph.add_edge("conversation", END)
    return graph.compile()


_GRAPH = None


def get_graph():
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = build_graph()
    return _GRAPH


def run_turn(session_id: str, user_message: str) -> dict:
    ensure_session(session_id)
    add_message(session_id, "user", user_message)
    result = get_graph().invoke(
        {
            "session_id": session_id,
            "user_message": user_message,
            "safety_label": "ok",
            "safety_reason": "",
            "tool_notes": "",
            "reply": "",
        }
    )
    reply = result.get("reply") or "I'm here, but I could not form a response just then. Please try again."
    add_message(session_id, "assistant", reply)
    if result.get("safety_label") != "crisis":
        maybe_update_profile(session_id, user_message, reply)
    return {
        "reply": reply,
        "safety_label": result.get("safety_label", "ok"),
        "tool_notes": result.get("tool_notes", ""),
    }
