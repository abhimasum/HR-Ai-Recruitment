from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.dependencies import get_current_account
from app.db.models import Account
from app.workflows.rag_graph import answer_policy_question

router = APIRouter()


class PolicyQuestion(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)


class PolicyAnswer(BaseModel):
    answer: str
    sources: list[str]
    grounded: bool


@router.post("/policy", response_model=PolicyAnswer)
async def ask_policy(
    payload: PolicyQuestion,
    _: Account = Depends(get_current_account),
) -> PolicyAnswer:
    return PolicyAnswer(**(await answer_policy_question(payload.question)))
