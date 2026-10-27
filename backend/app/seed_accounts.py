import json
import os
import sys
from getpass import getpass

from sqlalchemy import select

from app.core.auth import hash_password
from app.db.migrations import ensure_schema
from app.db.models import Account
from app.db.session import SessionLocal

EXPECTED_USERS = {
    "candidate1": "candidate",
    "candidate2": "candidate",
    "candidate3": "candidate",
    "test": "candidate",
    "hr": "hr",
}


async def seed_accounts() -> None:
    raw_accounts = os.environ.get("INITIAL_ACCOUNTS_JSON")
    if not raw_accounts:
        if not sys.stdin.isatty():
            raise RuntimeError(
                "INITIAL_ACCOUNTS_JSON is required for non-interactive account setup"
            )
        accounts = {
            username: getpass(f"Initial password for {username}: ")
            for username in EXPECTED_USERS
        }
    else:
        accounts = json.loads(raw_accounts)
    if not isinstance(accounts, dict) or set(accounts) != set(EXPECTED_USERS):
        raise ValueError(
            "Initial accounts must include exactly candidate1, candidate2, candidate3, test, and hr"
        )
    if any(not isinstance(password, str) or not password for password in accounts.values()):
        raise ValueError("Initial account passwords must be non-empty strings")

    await ensure_schema()
    async with SessionLocal() as session:
        for username, role in EXPECTED_USERS.items():
            account = await session.scalar(
                select(Account).where(Account.username == username)
            )
            if account is None:
                session.add(
                    Account(
                        username=username,
                        password_hash=hash_password(accounts[username]),
                        role=role,
                    )
                )
        await session.commit()


if __name__ == "__main__":
    import asyncio

    asyncio.run(seed_accounts())
