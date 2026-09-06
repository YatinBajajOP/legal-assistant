import uuid
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.document import DocumentStatus, LegalDocument


async def create_document(
    db: AsyncSession,
    *,
    document_id: uuid.UUID,
    user_id: int,
    original_filename: str,
    content_type: Optional[str],
    document_type: Optional[str],
    storage_path: str,
) -> LegalDocument:
    document = LegalDocument(
        id=document_id,
        user_id=user_id,
        original_filename=original_filename,
        content_type=content_type,
        document_type=document_type,
        storage_path=storage_path,
        status=DocumentStatus.PENDING,
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)
    return document


async def get_document(db: AsyncSession, document_id: uuid.UUID, user_id: int) -> Optional[LegalDocument]:
    result = await db.execute(
        select(LegalDocument).where(LegalDocument.id == document_id, LegalDocument.user_id == user_id)
    )
    return result.scalars().first()


async def get_documents_by_ids(
    db: AsyncSession, document_ids: Sequence[uuid.UUID], user_id: int
) -> list[LegalDocument]:
    result = await db.execute(
        select(LegalDocument).where(
            LegalDocument.id.in_(document_ids), LegalDocument.user_id == user_id
        )
    )
    return list(result.scalars().all())


async def list_documents(db: AsyncSession, user_id: int) -> list[LegalDocument]:
    result = await db.execute(
        select(LegalDocument)
        .where(LegalDocument.user_id == user_id)
        .order_by(LegalDocument.created_at.desc())
    )
    return list(result.scalars().all())


async def update_document_status(
    db: AsyncSession,
    document: LegalDocument,
    *,
    status: DocumentStatus,
    error_message: Optional[str] = None,
    page_count: Optional[int] = None,
    chunk_count: Optional[int] = None,
) -> LegalDocument:
    document.status = status
    if error_message is not None:
        document.error_message = error_message
    if page_count is not None:
        document.page_count = page_count
    if chunk_count is not None:
        document.chunk_count = chunk_count
    db.add(document)
    await db.commit()
    await db.refresh(document)
    return document
