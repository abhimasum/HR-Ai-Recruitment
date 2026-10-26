"""Resume screening graph: score -> decide (AUTO_ACCEPTED / PENDING_HUMAN_REVIEW / AUTO_REJECTED)."""
from typing import TypedDict

from langgraph.graph import END, StateGraph

from app.core.config import settings
from app.services.llm import get_llm
from app.workflows.rules import parse_screening_response, screening_status


class ScreeningState(TypedDict, total=False):
    jd_text: str
    resume_text: str
    score: int
    reasoning: str
    status: str


async def score_node(state: ScreeningState) -> dict:
    llm = get_llm(temperature=0.0)
    prompt = (
        "You are an expert HR recruitment evaluator. Score how well the candidate resume matches the job description from 0 to 100.\n"
        'Return ONLY valid JSON matching this structure: {"score": <int between 0 and 100>, "reasoning": "<short explanation>"}.\n\n'
        f"Job description:\n{state['jd_text']}\n\nResume:\n{state['resume_text']}"
    )
    result = await llm.ainvoke(prompt)
    content = str(result.content)
    data = parse_screening_response(content)
    
    return {
        "score": data["score"],
        "reasoning": data["reasoning"],
    }


async def decide_node(state: ScreeningState) -> dict:
    score = state["score"]
    return {
        "status": screening_status(
            score, settings.accept_threshold, settings.reject_threshold
        )
    }


builder = StateGraph(ScreeningState)
builder.add_node("score_resume", score_node)
builder.add_node("decide", decide_node)
builder.set_entry_point("score_resume")
builder.add_edge("score_resume", "decide")
builder.add_edge("decide", END)
screening_graph = builder.compile()
