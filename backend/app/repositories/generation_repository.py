import uuid
from typing import Any, Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.document import LegalDocument
from app.db.models.resolution_plan import ResolutionPlanGeneration, ResolutionPlanGenerationStatus


async def create_generation(
    db: AsyncSession, *, user_id: int, source_documents: list[LegalDocument]
) -> ResolutionPlanGeneration:
    generation = ResolutionPlanGeneration(
        user_id=user_id,
        status=ResolutionPlanGenerationStatus.PENDING,
        source_documents=source_documents,
    )
    db.add(generation)
    await db.commit()
    await db.refresh(generation, attribute_names=["source_documents"])
    return generation


async def get_generation(
    db: AsyncSession, generation_id: uuid.UUID, user_id: int
) -> Optional[ResolutionPlanGeneration]:
    result = await db.execute(
        select(ResolutionPlanGeneration)
        .options(selectinload(ResolutionPlanGeneration.source_documents))
        .where(ResolutionPlanGeneration.id == generation_id, ResolutionPlanGeneration.user_id == user_id)
    )
    return result.scalars().first()


async def update_generation_status(
    db: AsyncSession,
    generation: ResolutionPlanGeneration,
    *,
    status: ResolutionPlanGenerationStatus,
    error_message: Optional[str] = None,
) -> ResolutionPlanGeneration:
    generation.status = status
    if error_message is not None:
        generation.error_message = error_message
    db.add(generation)
    await db.commit()
    await db.refresh(generation)
    return generation


async def save_generation_result(
    db: AsyncSession,
    generation: ResolutionPlanGeneration,
    *,
    template_json: dict[str, Any],
    generation_metadata: dict[str, Any],
    docx_path: Optional[str],
    status: ResolutionPlanGenerationStatus,
    error_message: Optional[str] = None,
) -> ResolutionPlanGeneration:
    generation.template_json = template_json
    generation.generation_metadata = generation_metadata
    generation.docx_path = docx_path
    generation.status = status
    generation.error_message = error_message
    db.add(generation)
    await db.commit()
    await db.refresh(generation)
    return generation
