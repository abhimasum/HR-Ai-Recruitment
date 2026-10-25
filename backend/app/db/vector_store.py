"""Custom pgvector store built directly on SQLAlchemy (no managed vector DB)."""
import logging
from sqlalchemy import text

from app.core.config import settings
from app.db.session import SessionLocal, engine
from app.services.embeddings import get_embeddings

logger = logging.getLogger(__name__)


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
        
        # Check if embedding dimension matches the current configuration
        try:
            res = await conn.execute(text("""
                SELECT atttypmod 
                FROM pg_attribute 
                WHERE attrelid = 'policy_chunks'::regclass 
                  AND attname = 'embedding'
            """))
            row = res.fetchone()
            if row and row[0] != -1 and row[0] != settings.embedding_dim:
                logger.info(
                    f"Embedding dimension changed from {row[0]} to {settings.embedding_dim}. "
                    "Updating policy_chunks table schema."
                )
                await conn.execute(text("TRUNCATE TABLE policy_chunks"))
                await conn.execute(text(f"""
                    ALTER TABLE policy_chunks 
                    ALTER COLUMN embedding TYPE vector({settings.embedding_dim})
                """))
        except Exception as e:
            logger.debug(f"Dimension check skipped or table new: {e}")


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
