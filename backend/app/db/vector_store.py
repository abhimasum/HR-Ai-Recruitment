"""Custom pgvector store built directly on SQLAlchemy (no managed vector DB)."""
from sqlalchemy import text

from app.core.config import settings
from app.db.session import SessionLocal, engine
from app.services.embeddings import get_embeddings


async def init_schema() -> None:
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS policy_chunks (
                id SERIAL PRIMARY KEY,
                source TEXT NOT NULL,
                content TEXT NOT NULL,
                embedding vector({settings.embedding_dim}) NOT NULL
            )
        """))


async def count_chunks() -> int:
    async with SessionLocal() as session:
        result = await session.execute(text("SELECT COUNT(*) FROM policy_chunks"))
        return int(result.scalar_one())


async def add_chunks(source: str, chunks: list[str]) -> None:
    vectors = await get_embeddings().aembed_documents(chunks)
    async with SessionLocal() as session:
        for content, vector in zip(chunks, vectors):
            await session.execute(
                text(
                    "INSERT INTO policy_chunks (source, content, embedding) "
                    "VALUES (:source, :content, CAST(:embedding AS vector))"
                ),
                {"source": source, "content": content, "embedding": str(vector)},
            )
        await session.commit()


async def similarity_search(query: str, k: int = 4) -> list[dict]:
    """Cosine similarity search using pgvector's <=> operator."""
    query_vector = str(await get_embeddings().aembed_query(query))
    sql = text("""
        SELECT source, content,
               1 - (embedding <=> CAST(:q AS vector)) AS score
        FROM policy_chunks
        ORDER BY embedding <=> CAST(:q AS vector)
        LIMIT :k
    """)
    async with SessionLocal() as session:
        rows = (await session.execute(sql, {"q": query_vector, "k": k})).mappings().all()
    return [dict(r) for r in rows]
