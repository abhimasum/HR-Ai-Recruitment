"""Resume screening graph: score -> decide (AUTO_ACCEPTED / PENDING_HUMAN_REVIEW / AUTO_REJECTED)."""
import json
import re
from typing import TypedDict

from langgraph.graph import END, StateGraph

from app.core.config import settings
from app.services.llm import get_llm


class ScreeningState(TypedDict, total=False):
    jd_text: str
    resume_text: str
    score: int
    reasoning: str
    status: str


def _parse_score_json(text: str) -> dict:
    """Robustly extract and parse JSON object containing score and reasoning."""
    # Try finding first JSON object {...}
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    # Fallback to cleaning backticks
    cleaned = re.sub(r"```json|```", "", text).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Fallback if LLM failed to produce valid JSON
        score_match = re.search(r'"score"\s*:\s*(\d+)', text)
        score = int(score_match.group(1)) if score_match else 50
        return {"score": score, "reasoning": text.strip()[:500]}


async def score_node(state: ScreeningState) -> dict:
    llm = get_llm(temperature=0.0)
    prompt = (
        "You are an expert HR recruitment evaluator. Score how well the candidate resume matches the job description from 0 to 100.\n"
        'Return ONLY valid JSON matching this structure: {"score": <int between 0 and 100>, "reasoning": "<short explanation>"}.\n\n'
        f"Job description:\n{state['jd_text']}\n\nResume:\n{state['resume_text']}"
    )
    result = await llm.ainvoke(prompt)
    content = str(result.content)
    data = _parse_score_json(content)
    
    score_val = int(data.get("score", 0))
    return {
        "score": max(0, min(100, score_val)),
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
