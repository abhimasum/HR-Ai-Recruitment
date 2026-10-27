from collections.abc import AsyncIterator

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import read_session_token
from app.core.config import settings
from app.db.models import Account
from app.db.session import SessionLocal


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


async def get_current_account(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> Account:
    account_id = read_session_token(
        request.cookies.get("hr_session"), settings.auth_signing_key
    )
    if account_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please sign in",
        )
    account = await session.get(Account, account_id)
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please sign in",
        )
    return account


async def require_candidate(
    account: Account = Depends(get_current_account),
) -> Account:
    if account.role != "candidate":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Candidate access required",
        )
    return account


async def require_hr(
    account: Account = Depends(get_current_account),
) -> Account:
    if account.role != "hr":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="HR access required",
        )
    return account
