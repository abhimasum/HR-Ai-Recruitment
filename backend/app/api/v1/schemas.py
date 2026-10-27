from pydantic import BaseModel


class CandidateOut(BaseModel):
    id: int
    name: str
    job_id: int | None = None
    job_title: str | None = None
    score: int
    status: str
    reasoning: str
    geval_score: float | None = None
    hallucination_score: float | None = None
    bias_score: float | None = None


class JobSummaryOut(BaseModel):
    id: int
    title: str
    is_active: bool
    application_count: int
    average_match_percent: float | None


class DecisionIn(BaseModel):
    action: str
