import uuid
from typing import Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.document import DocumentChunk


async def bulk_create_chunks(db: AsyncSession, chunks: Sequence[DocumentChunk]) -> None:
    db.add_all(chunks)
    await db.commit()


async def delete_chunks_for_document(db: AsyncSession, document_id: uuid.UUID) -> None:
    await db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))
    await db.commit()


async def similarity_search(
    db: AsyncSession,
    *,
    query_embedding: list[float],
    document_ids: Sequence[uuid.UUID],
    user_id: int,
    top_k: int,
) -> list[DocumentChunk]:
    """Return the top_k chunks (scoped to the given documents/user) closest to the query embedding."""
    if not document_ids:
        return []
    stmt = (
        select(DocumentChunk)
        .where(
            DocumentChunk.document_id.in_(document_ids),
            DocumentChunk.user_id == user_id,
            DocumentChunk.embedding.isnot(None),
        )
        .options(selectinload(DocumentChunk.document))
        .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
        .limit(top_k)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
