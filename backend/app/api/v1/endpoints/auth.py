from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_account, get_session
from app.core.auth import (
    SESSION_COOKIE,
    SESSION_TTL_SECONDS,
    create_session_token,
    verify_password,
)
from app.core.config import settings
from app.db.models import Account

router = APIRouter()


class LoginIn(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1, max_length=200)


class AccountOut(BaseModel):
    id: int
    username: str
    role: str

    model_config = {"from_attributes": True}


@router.post("/login", response_model=AccountOut)
async def login(
    payload: LoginIn,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> Account:
    if not settings.auth_signing_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured",
        )
    account = await session.scalar(
        select(Account).where(Account.username == payload.username)
    )
    if account is None or not verify_password(payload.password, account.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    response.set_cookie(
        SESSION_COOKIE,
        create_session_token(account.id, settings.auth_signing_key),
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="lax",
        path="/",
    )
    return account


@router.get("/me", response_model=AccountOut)
async def current_account(
    account: Account = Depends(get_current_account),
) -> Account:
    return account


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> Response:
    response.delete_cookie(
        SESSION_COOKIE,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="lax",
        path="/",
    )
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
