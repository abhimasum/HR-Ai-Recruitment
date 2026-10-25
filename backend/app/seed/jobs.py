from sqlalchemy import func, select

from app.db.models import Job
from app.db.session import SessionLocal

SAMPLE_JOBS = [
    {
        "title": "Senior Backend Engineer",
        "description": (
            "Build and maintain Python services using FastAPI and PostgreSQL. "
            "Requirements: Python, FastAPI, SQL, API design, testing, and five or more "
            "years of backend engineering experience."
        ),
    },
    {
        "title": "Frontend Engineer",
        "description": (
            "Build accessible web applications with React and TypeScript. "
            "Requirements: React, TypeScript, CSS, frontend testing, and three or more "
            "years of frontend engineering experience."
        ),
    },
    {
        "title": "Data Analyst",
        "description": (
            "Analyze business data and deliver clear reports and dashboards. "
            "Requirements: SQL, Python, data visualization, stakeholder communication, "
            "and two or more years of analytics experience."
        ),
    },
]


async def seed_jobs_if_empty() -> None:
    async with SessionLocal() as session:
        count = await session.scalar(select(func.count()).select_from(Job))
        if count:
            return
        session.add_all(Job(**job) for job in SAMPLE_JOBS)
        await session.commit()
