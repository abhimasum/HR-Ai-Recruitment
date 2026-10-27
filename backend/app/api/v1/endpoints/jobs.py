from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_account, get_session, require_hr
from app.db.models import Account, Candidate, Job
from app.api.v1.schemas import JobSummaryOut

router = APIRouter()


class JobIn(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    description: str = Field(..., min_length=20, max_length=20000)
    is_active: bool = True


class JobOut(JobIn):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("", response_model=list[JobOut])
async def list_jobs(
    active_only: bool = True,
    account: Account = Depends(get_current_account),
    session: AsyncSession = Depends(get_session),
) -> list[Job]:
    if not active_only and account.role != "hr":
        raise HTTPException(status_code=403, detail="HR access required")
    query = select(Job).order_by(Job.created_at.desc())
    if active_only:
        query = query.where(Job.is_active.is_(True))
    return list((await session.scalars(query)).all())


@router.get("/summary", response_model=list[JobSummaryOut])
async def job_application_summary(
    session: AsyncSession = Depends(get_session),
    _: Account = Depends(require_hr),
) -> list[JobSummaryOut]:
    rows = (await session.execute(
        select(
            Job.id,
            Job.title,
            Job.is_active,
            func.count(Candidate.id),
            func.avg(Candidate.score),
        )
        .outerjoin(Candidate, Candidate.job_id == Job.id)
        .group_by(Job.id)
        .order_by(Job.created_at.desc())
    )).all()
    return [
        JobSummaryOut(
            id=job_id,
            title=title,
            is_active=is_active,
            application_count=application_count,
            average_match_percent=(
                round(float(average_score), 1) if average_score is not None else None
            ),
        )
        for job_id, title, is_active, application_count, average_score in rows
    ]


@router.get("/{job_id}", response_model=JobOut)
async def get_job(
    job_id: int,
    account: Account = Depends(get_current_account),
    session: AsyncSession = Depends(get_session),
) -> Job:
    job = await session.get(Job, job_id)
    if job is None or (not job.is_active and account.role != "hr"):
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("", response_model=JobOut, status_code=status.HTTP_201_CREATED)
async def create_job(
    payload: JobIn,
    session: AsyncSession = Depends(get_session),
    _: Account = Depends(require_hr),
) -> Job:
    job = Job(**payload.model_dump())
    session.add(job)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=409, detail="A job with this title already exists"
        ) from exc
    await session.refresh(job)
    return job


@router.put("/{job_id}", response_model=JobOut)
async def update_job(
    job_id: int,
    payload: JobIn,
    session: AsyncSession = Depends(get_session),
    _: Account = Depends(require_hr),
) -> Job:
    job = await session.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    for field, value in payload.model_dump().items():
        setattr(job, field, value)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=409, detail="A job with this title already exists"
        ) from exc
    await session.refresh(job)
    return job


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_job(
    job_id: int,
    session: AsyncSession = Depends(get_session),
    _: Account = Depends(require_hr),
) -> Response:
    job = await session.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    job.is_active = False
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
