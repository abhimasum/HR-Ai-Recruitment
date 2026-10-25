from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas import CandidateOut, DecisionIn
from app.db.models import Candidate
from app.db.session import SessionLocal

router = APIRouter()


async def get_session():
    async with SessionLocal() as session:
        yield session


@router.post("/{candidate_id}/decision", response_model=CandidateOut)
async def hitl_decision(
    candidate_id: int,
    body: DecisionIn,
    session: AsyncSession = Depends(get_session),
) -> CandidateOut:
    if body.action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="action must be approve or reject")
    candidate = await session.get(Candidate, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    if candidate.status != "PENDING_HUMAN_REVIEW":
        raise HTTPException(status_code=409, detail="Candidate is not awaiting human review")
    candidate.status = "HR_APPROVED" if body.action == "approve" else "HR_REJECTED"
    await session.commit()
    return CandidateOut(
        id=candidate.id,
        name=candidate.name,
        score=candidate.score,
        status=candidate.status,
        reasoning=candidate.reasoning,
    )
