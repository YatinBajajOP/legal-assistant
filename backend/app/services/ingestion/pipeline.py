"""End-to-end ingestion pipeline: extract -> chunk -> embed -> persist.

Runs as a background task after a document upload so the upload request
itself returns immediately.
"""
from __future__ import annotations

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.document import DocumentChunk, DocumentStatus, LegalDocument
from app.db.session import AsyncSessionLocal
from app.repositories import chunk_repository, document_repository
from app.services.embeddings import embed_texts
from app.services.ingestion.chunking import chunk_paragraphs
from app.services.ingestion.extraction import extract_document

logger = logging.getLogger(__name__)


async def process_document(document_id: uuid.UUID) -> None:
    """Runs the full ingestion pipeline for a single document in its own DB session."""
    async with AsyncSessionLocal() as db:
        document = await _load_document(db, document_id)
        if document is None:
            logger.error("Document %s not found for ingestion", document_id)
            return

        try:
            await document_repository.update_document_status(db, document, status=DocumentStatus.EXTRACTING)
            extracted = extract_document(document.storage_path, document.content_type)

            chunks = chunk_paragraphs(extracted.paragraphs)
            if not chunks:
                await document_repository.update_document_status(
                    db,
                    document,
                    status=DocumentStatus.FAILED,
                    error_message="No extractable text was found in the document.",
                )
                return

            await document_repository.update_document_status(db, document, status=DocumentStatus.EMBEDDING)
            embeddings = await embed_texts([c.content for c in chunks])

            db_chunks = [
                DocumentChunk(
                    document_id=document.id,
                    user_id=document.user_id,
                    chunk_index=chunk.chunk_index,
                    page_number=chunk.page_number,
                    paragraph_number=chunk.paragraph_number,
                    clause_reference=chunk.clause_reference,
                    content=chunk.content,
                    token_count=chunk.token_count,
                    embedding=embedding,
                )
                for chunk, embedding in zip(chunks, embeddings)
            ]
            await chunk_repository.delete_chunks_for_document(db, document.id)
            await chunk_repository.bulk_create_chunks(db, db_chunks)

            await document_repository.update_document_status(
                db,
                document,
                status=DocumentStatus.COMPLETED,
                page_count=extracted.page_count,
                chunk_count=len(db_chunks),
            )
        except Exception as exc:  # noqa: BLE001 - surface any failure on the document record
            logger.exception("Ingestion failed for document %s", document_id)
            await document_repository.update_document_status(
                db, document, status=DocumentStatus.FAILED, error_message=str(exc)
            )


async def _load_document(db: AsyncSession, document_id: uuid.UUID) -> LegalDocument | None:
    from sqlalchemy import select

    result = await db.execute(select(LegalDocument).where(LegalDocument.id == document_id))
    return result.scalars().first()
