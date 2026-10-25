from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.workflows.rag_graph import answer_policy_question

router = APIRouter()


class PolicyQuestion(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)


class PolicyAnswer(BaseModel):
    answer: str
    sources: list[str]
    grounded: bool


@router.post("/policy", response_model=PolicyAnswer)
async def ask_policy(payload: PolicyQuestion) -> PolicyAnswer:
    return PolicyAnswer(**(await answer_policy_question(payload.question)))
