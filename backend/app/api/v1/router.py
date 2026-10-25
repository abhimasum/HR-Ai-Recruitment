from fastapi import APIRouter

from app.api.v1.endpoints import candidates, chat, jobs, review

api_router = APIRouter()
api_router.include_router(candidates.router, prefix="/screening", tags=["candidates"])
api_router.include_router(
    review.router, prefix="/screening/candidates", tags=["human review"]
)
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
