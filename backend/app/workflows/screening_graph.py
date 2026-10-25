"""Resume screening graph: score -> decide (AUTO_ACCEPTED / PENDING_HUMAN_REVIEW / AUTO_REJECTED)."""
import json
import re
from typing import TypedDict

from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from app.core.config import settings

llm = ChatOpenAI(model=settings.llm_model, api_key=settings.openai_api_key or None, temperature=0)


class ScreeningState(TypedDict, total=False):
    jd_text: str
    resume_text: str
    score: int
    reasoning: str
    status: str


async def score_node(state: ScreeningState) -> dict:
    prompt = (
        "Score how well the resume matches the job description from 0 to 100. "
        'Return JSON only, in the form {"score": <int>, "reasoning": "<short explanation>"}.\n\n'
        f"Job description:\n{state['jd_text']}\n\nResume:\n{state['resume_text']}"
    )
    result = await llm.ainvoke(prompt)
    raw = re.sub(r"```json|```", "", result.content).strip()
    data = json.loads(raw)
    return {
        "score": max(0, min(100, int(data["score"]))),
        "reasoning": str(data.get("reasoning", "")),
    }


async def decide_node(state: ScreeningState) -> dict:
    score = state["score"]
    if score >= settings.accept_threshold:
        status = "AUTO_ACCEPTED"
    elif score >= settings.reject_threshold:
        status = "PENDING_HUMAN_REVIEW"
    else:
        status = "AUTO_REJECTED"
    return {"status": status}


builder = StateGraph(ScreeningState)
builder.add_node("score", score_node)
builder.add_node("decide", decide_node)
builder.set_entry_point("score")
builder.add_edge("score", "decide")
builder.add_edge("decide", END)
screening_graph = builder.compile()
