import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.migrations import ensure_schema
from app.db.vector_store import init_schema
from app.seed.jobs import seed_jobs_if_empty
from app.seed.hr_policies import seed_policies_if_empty

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_schema()
    await ensure_schema()
    await seed_jobs_if_empty()
    try:
        await seed_policies_if_empty()
    except Exception as exc:
        logger.warning(f"Could not seed sample policies at startup: {exc}")
    yield


app = FastAPI(title="AI HR Recruitment System", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
