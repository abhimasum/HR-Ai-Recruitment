from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.db.models import Base
from app.db.session import engine
from app.db.vector_store import init_schema
from app.seed.hr_policies import seed_policies_if_empty


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_schema()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed_policies_if_empty()
    yield


app = FastAPI(title="AI HR Recruitment System", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
