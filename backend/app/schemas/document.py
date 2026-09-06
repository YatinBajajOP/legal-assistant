import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.db.models.document import DocumentStatus


class LegalDocumentPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    original_filename: str
    content_type: Optional[str] = None
    document_type: Optional[str] = None
    status: DocumentStatus
    error_message: Optional[str] = None
    page_count: Optional[int] = None
    chunk_count: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class LegalDocumentUploadResponse(BaseModel):
    document: LegalDocumentPublic
    message: str = "Document accepted and queued for processing."
