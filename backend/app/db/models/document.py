import enum
import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.config import settings
from app.db.base import Base


class DocumentStatus(str, enum.Enum):
    PENDING = "pending"
    EXTRACTING = "extracting"
    EMBEDDING = "embedding"
    COMPLETED = "completed"
    FAILED = "failed"


class LegalDocument(Base):
    """Metadata for a single uploaded source document (Resolution Plan, RFRP, etc.)."""

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)

    original_filename = Column(String, nullable=False)
    content_type = Column(String, nullable=True)
    document_type = Column(String, nullable=True)  # e.g. "resolution_plan", "rfrp", "annexure"
    storage_path = Column(String, nullable=False)

    status = Column(
        Enum(DocumentStatus, values_callable=lambda enum_cls: [e.value for e in enum_cls]),
        default=DocumentStatus.PENDING,
        nullable=False,
        index=True,
    )
    error_message = Column(Text, nullable=True)

    page_count = Column(Integer, nullable=True)
    chunk_count = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    """A single legal-aware chunk of a document with its embedding vector."""

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("legaldocument.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)

    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, nullable=True)
    paragraph_number = Column(Integer, nullable=True)
    clause_reference = Column(String, nullable=True)

    content = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=True)

    embedding = Column(Vector(settings.EMBEDDING_DIMENSIONS), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    document = relationship("LegalDocument", back_populates="chunks")

    __table_args__ = (
        UniqueConstraint("document_id", "chunk_index", name="uq_document_chunk_index"),
        Index("ix_document_chunk_user_id", "user_id"),
    )
