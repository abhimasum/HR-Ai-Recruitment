from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Candidate, Evaluation
from app.db.session import SessionLocal
from app.evaluation.deepeval_runner import run_screening_evaluation
from app.services.resume_parser import extract_text
from app.workflows.screening_graph import screening_graph

router = APIRouter()


async def get_session():
    async with SessionLocal() as session:
        yield session


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
    action: str  # "approve" | "reject"


@router.post("/resume", response_model=CandidateOut)
async def screen_resume(
    name: str = Form(...),
    jd_text: str = Form(...),
    resume: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
):
    try:
        resume_text = extract_text(resume.filename or "", await resume.read())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not resume_text:
        raise HTTPException(status_code=400, detail="Could not read any text from the resume.")

    result = await screening_graph.ainvoke({"jd_text": jd_text, "resume_text": resume_text})

    candidate = Candidate(
        name=name, jd_text=jd_text, resume_text=resume_text,
        score=result["score"], status=result["status"], reasoning=result["reasoning"],
    )
    session.add(candidate)
    await session.flush()

    metrics = await run_screening_evaluation(jd_text, resume_text, result["reasoning"])
    session.add(Evaluation(
        candidate_id=candidate.id,
        geval_score=metrics.get("geval_score"),
        hallucination_score=metrics.get("hallucination_score"),
        bias_score=metrics.get("bias_score"),
        details=metrics.get("details", {}),
    ))
    await session.commit()

    return CandidateOut(
        id=candidate.id, name=name, score=candidate.score, status=candidate.status,
        reasoning=candidate.reasoning,
        geval_score=metrics.get("geval_score"),
        hallucination_score=metrics.get("hallucination_score"),
        bias_score=metrics.get("bias_score"),
    )


@router.get("/candidates", response_model=list[CandidateOut])
async def list_candidates(session: AsyncSession = Depends(get_session)):
    rows = (await session.execute(
        select(Candidate, Evaluation)
        .outerjoin(Evaluation, Evaluation.candidate_id == Candidate.id)
        .order_by(Candidate.created_at.desc())
    )).all()
    return [
        CandidateOut(
            id=c.id, name=c.name, score=c.score, status=c.status, reasoning=c.reasoning,
            geval_score=e.geval_score if e else None,
            hallucination_score=e.hallucination_score if e else None,
            bias_score=e.bias_score if e else None,
        )
        for c, e in rows
    ]


@router.post("/candidates/{candidate_id}/decision", response_model=CandidateOut)
async def hitl_decision(
    candidate_id: int, body: DecisionIn, session: AsyncSession = Depends(get_session)
):
    if body.action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="action must be approve or reject")
    candidate = await session.get(Candidate, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    if candidate.status != "PENDING_HUMAN_REVIEW":
        raise HTTPException(status_code=409, detail="Candidate is not awaiting human review")
    candidate.status = "HR_APPROVED" if body.action == "approve" else "HR_REJECTED"
    await session.commit()
    return CandidateOut(
        id=candidate.id, name=candidate.name, score=candidate.score,
        status=candidate.status, reasoning=candidate.reasoning,
    )
