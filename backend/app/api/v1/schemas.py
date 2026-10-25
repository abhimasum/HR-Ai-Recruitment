from pydantic import BaseModel


class CandidateOut(BaseModel):
    id: int
    name: str
    score: int
    status: str
    reasoning: str
    geval_score: float | None = None
    hallucination_score: float | None = None
    bias_score: float | None = None


class DecisionIn(BaseModel):
    action: str
