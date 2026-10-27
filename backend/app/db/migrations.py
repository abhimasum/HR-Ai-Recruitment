from sqlalchemy import text

from app.db.models import Base
from app.db.session import engine


async def ensure_schema() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(
            text(
                "ALTER TABLE candidates "
                "ADD COLUMN IF NOT EXISTS account_id INTEGER "
                "REFERENCES accounts(id) ON DELETE SET NULL"
            )
        )
        await conn.execute(
            text(
                "ALTER TABLE candidates "
                "ADD COLUMN IF NOT EXISTS job_id INTEGER "
                "REFERENCES jobs(id) ON DELETE SET NULL"
            )
        )
        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_candidates_account_id "
                "ON candidates(account_id)"
            )
        )
        await conn.execute(
            text("CREATE INDEX IF NOT EXISTS ix_candidates_job_id ON candidates(job_id)")
        )
        await conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_candidates_account_job "
                "ON candidates(account_id, job_id)"
            )
        )
