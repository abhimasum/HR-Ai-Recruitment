from fastapi import APIRouter

from app.api.v1.endpoints import chat, screening

api_router = APIRouter()
api_router.include_router(screening.router, prefix="/screening", tags=["screening"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
