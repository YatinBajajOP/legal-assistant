import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.resolution_plan import ResolutionPlanGenerationStatus


class ResolutionPlanGenerationRequest(BaseModel):
    document_ids: List[uuid.UUID] = Field(
        ..., min_length=1, description="IDs of previously uploaded, fully processed source documents."
    )


class ResolutionPlanGenerationPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: ResolutionPlanGenerationStatus
    error_message: Optional[str] = None
    generation_metadata: Optional[Dict[str, Any]] = None
    docx_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ResolutionPlanGenerationDetail(ResolutionPlanGenerationPublic):
    template_json: Optional[Dict[str, Any]] = None
    source_document_ids: List[uuid.UUID] = Field(default_factory=list)
