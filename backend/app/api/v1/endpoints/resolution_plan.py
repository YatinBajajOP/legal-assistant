import os
import uuid
from typing import Any, List, Optional

import aiofiles
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.models.document import DocumentStatus
from app.db.models.resolution_plan import ResolutionPlanGenerationStatus
from app.db.models.user import User
from app.db.session import get_db
from app.repositories import document_repository, generation_repository
from app.schemas.document import LegalDocumentPublic, LegalDocumentUploadResponse
from app.schemas.resolution_plan import (
    ResolutionPlanGenerationDetail,
    ResolutionPlanGenerationPublic,
    ResolutionPlanGenerationRequest,
)
from app.services.ingestion.pipeline import process_document
from app.services.resolution_plan.pipeline import run_generation

router = APIRouter()

_ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}


@router.post("/documents", response_model=LegalDocumentUploadResponse, status_code=202)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    document_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Upload a Resolution Plan source document. Processing (extraction, chunking,
    embedding) happens asynchronously; poll GET /documents/{id} for status."""
    if file.content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail=f"Unsupported content type: {file.content_type}")

    document_id = uuid.uuid4()
    suffix = os.path.splitext(file.filename or "")[1] or ""
    storage_path = os.path.join(settings.upload_dir_path, f"{document_id}{suffix}")

    async with aiofiles.open(storage_path, "wb") as out_file:
        while chunk := await file.read(1024 * 1024):
            await out_file.write(chunk)

    document = await document_repository.create_document(
        db,
        document_id=document_id,
        user_id=current_user.id,
        original_filename=file.filename or str(document_id),
        content_type=file.content_type,
        document_type=document_type,
        storage_path=storage_path,
    )

    background_tasks.add_task(process_document, document.id)

    return LegalDocumentUploadResponse(document=LegalDocumentPublic.model_validate(document))


@router.get("/documents", response_model=List[LegalDocumentPublic])
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    return await document_repository.list_documents(db, current_user.id)


@router.get("/documents/{document_id}", response_model=LegalDocumentPublic)
async def get_document_status(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    document = await document_repository.get_document(db, document_id, current_user.id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.post("/generations", response_model=ResolutionPlanGenerationPublic, status_code=202)
async def create_generation(
    request: ResolutionPlanGenerationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Kick off Resolution Plan generation from previously uploaded, processed documents."""
    documents = await document_repository.get_documents_by_ids(db, request.document_ids, current_user.id)
    found_ids = {doc.id for doc in documents}
    missing = [str(doc_id) for doc_id in request.document_ids if doc_id not in found_ids]
    if missing:
        raise HTTPException(status_code=404, detail=f"Documents not found: {', '.join(missing)}")

    not_ready = [doc.original_filename for doc in documents if doc.status != DocumentStatus.COMPLETED]
    if not_ready:
        raise HTTPException(
            status_code=409,
            detail=f"These documents are not finished processing yet: {', '.join(not_ready)}",
        )

    generation = await generation_repository.create_generation(
        db, user_id=current_user.id, source_documents=documents
    )
    background_tasks.add_task(run_generation, generation.id)
    return generation


@router.get("/generations/{generation_id}", response_model=ResolutionPlanGenerationDetail)
async def get_generation(
    generation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    generation = await generation_repository.get_generation(db, generation_id, current_user.id)
    if generation is None:
        raise HTTPException(status_code=404, detail="Generation not found")
    return ResolutionPlanGenerationDetail(
        **ResolutionPlanGenerationPublic.model_validate(generation).model_dump(),
        template_json=generation.template_json,
        source_document_ids=[doc.id for doc in generation.source_documents],
    )


@router.get("/generations/{generation_id}/download")
async def download_generation(
    generation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    generation = await generation_repository.get_generation(db, generation_id, current_user.id)
    if generation is None:
        raise HTTPException(status_code=404, detail="Generation not found")
    if generation.status != ResolutionPlanGenerationStatus.COMPLETED or not generation.docx_path:
        raise HTTPException(status_code=409, detail=f"Generation is not ready (status: {generation.status.value})")
    if not os.path.exists(generation.docx_path):
        raise HTTPException(status_code=410, detail="Generated document is no longer available")

    return FileResponse(
        generation.docx_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"resolution-plan-review-{generation_id}.docx",
    )
