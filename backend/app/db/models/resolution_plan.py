import enum
import uuid

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base

resolution_plan_source_documents = Table(
    "resolution_plan_source_documents",
    Base.metadata,
    Column(
        "generation_id",
        UUID(as_uuid=True),
        ForeignKey("resolutionplangeneration.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "document_id",
        UUID(as_uuid=True),
        ForeignKey("legaldocument.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class ResolutionPlanGenerationStatus(str, enum.Enum):
    PENDING = "pending"
    RETRIEVING = "retrieving"
    ANSWERING = "answering"
    RENDERING_DOCX = "rendering_docx"
    COMPLETED = "completed"
    FAILED = "failed"


class ResolutionPlanGeneration(Base):
    """A single generation run of the Resolution Plan review template."""

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)

    status = Column(
        Enum(
            ResolutionPlanGenerationStatus,
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        default=ResolutionPlanGenerationStatus.PENDING,
        nullable=False,
        index=True,
    )
    error_message = Column(Text, nullable=True)

    template_json = Column(JSONB, nullable=True)
    generation_metadata = Column(JSONB, nullable=True)

    docx_path = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="resolution_plan_generations")
    source_documents = relationship(
        "LegalDocument", secondary=resolution_plan_source_documents, lazy="selectin"
    )
