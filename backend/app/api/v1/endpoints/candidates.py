from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session, require_candidate, require_hr
from app.db.models import Account, Candidate, Evaluation, Job
from app.api.v1.schemas import CandidateOut
from app.evaluation.deepeval_runner import run_screening_evaluation
from app.services.resume_parser import extract_text
from app.workflows.screening_graph import screening_graph

router = APIRouter()


@router.post("/resume", response_model=CandidateOut)
async def screen_resume(
    job_id: int = Form(...),
    resume: UploadFile = File(...),
    account: Account = Depends(require_candidate),
    session: AsyncSession = Depends(get_session),
):
    job = await session.get(Job, job_id)
    if job is None or not job.is_active:
        raise HTTPException(status_code=404, detail="Open position not found")
    existing = await session.scalar(
        select(Candidate.id).where(
            Candidate.account_id == account.id,
            Candidate.job_id == job.id,
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=409, detail="You have already applied for this position"
        )
    try:
        resume_text = extract_text(resume.filename or "", await resume.read())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not resume_text:
        raise HTTPException(status_code=400, detail="Could not read any text from the resume.")

    result = await screening_graph.ainvoke(
        {"jd_text": job.description, "resume_text": resume_text}
    )

    candidate = Candidate(
        account_id=account.id,
        job_id=job.id,
        name=account.username,
        jd_text=job.description,
        resume_text=resume_text,
        score=result["score"],
        status=result["status"],
        reasoning=result["reasoning"],
    )
    session.add(candidate)
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=409, detail="You have already applied for this position"
        ) from exc

    metrics = await run_screening_evaluation(
        job.description, resume_text, result["reasoning"]
    )
    session.add(
        Evaluation(
            candidate_id=candidate.id,
            geval_score=metrics.get("geval_score"),
            hallucination_score=metrics.get("hallucination_score"),
            bias_score=metrics.get("bias_score"),
            details=metrics.get("details", {}),
        )
    )
    await session.commit()

    return CandidateOut(
        id=candidate.id,
        name=candidate.name,
        job_id=job.id,
        job_title=job.title,
        score=candidate.score,
        status=candidate.status,
        reasoning=candidate.reasoning,
        geval_score=metrics.get("geval_score"),
        hallucination_score=metrics.get("hallucination_score"),
        bias_score=metrics.get("bias_score"),
    )


@router.get("/candidates", response_model=list[CandidateOut])
async def list_candidates(
    session: AsyncSession = Depends(get_session),
    _: Account = Depends(require_hr),
):
    rows = (await session.execute(
        select(Candidate, Evaluation, Job.title)
        .outerjoin(Evaluation, Evaluation.candidate_id == Candidate.id)
        .outerjoin(Job, Job.id == Candidate.job_id)
        .order_by(Candidate.created_at.desc())
    )).all()
    return [
        CandidateOut(
            id=c.id,
            name=c.name,
            score=c.score,
            status=c.status,
            reasoning=c.reasoning,
            job_id=c.job_id,
            job_title=job_title,
            geval_score=e.geval_score if e else None,
            hallucination_score=e.hallucination_score if e else None,
            bias_score=e.bias_score if e else None,
        )
        for c, e, job_title in rows
    ]


@router.get("/me", response_model=list[CandidateOut])
async def list_my_applications(
    account: Account = Depends(require_candidate),
    session: AsyncSession = Depends(get_session),
):
    rows = (await session.execute(
        select(Candidate, Evaluation, Job.title)
        .outerjoin(Evaluation, Evaluation.candidate_id == Candidate.id)
        .outerjoin(Job, Job.id == Candidate.job_id)
        .where(Candidate.account_id == account.id)
        .order_by(Candidate.created_at.desc())
    )).all()
    return [
        CandidateOut(
            id=candidate.id,
            name=candidate.name,
            job_id=candidate.job_id,
            job_title=job_title,
            score=candidate.score,
            status=candidate.status,
            reasoning=candidate.reasoning,
            geval_score=evaluation.geval_score if evaluation else None,
            hallucination_score=evaluation.hallucination_score if evaluation else None,
            bias_score=evaluation.bias_score if evaluation else None,
        )
        for candidate, evaluation, job_title in rows
    ]
