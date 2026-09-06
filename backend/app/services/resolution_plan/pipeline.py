"""End-to-end resolution-plan generation pipeline.

load template -> RAG-answer unanswered questions -> persist JSON -> validate ->
render DOCX via the existing resolution_plan_generator.py.
"""
from __future__ import annotations

import json
import logging
import os
import uuid

from app.core.config import settings
from app.db.models.resolution_plan import ResolutionPlanGenerationStatus
from app.db.session import AsyncSessionLocal
from app.repositories import generation_repository
from app.services.resolution_plan.generator import generate_resolution_plan, validate_json_against_template
from app.services.resolution_plan.orchestrator import answer_template
from app.services.resolution_plan.template_engine import load_template

logger = logging.getLogger(__name__)


async def run_generation(generation_id: uuid.UUID) -> None:
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        from app.db.models.resolution_plan import ResolutionPlanGeneration

        result = await db.execute(
            select(ResolutionPlanGeneration)
            .options(selectinload(ResolutionPlanGeneration.source_documents))
            .where(ResolutionPlanGeneration.id == generation_id)
        )
        generation = result.scalars().first()
        if generation is None:
            logger.error("Generation %s not found", generation_id)
            return

        document_ids = [doc.id for doc in generation.source_documents]
        user_id = generation.user_id

        try:
            await generation_repository.update_generation_status(
                db, generation, status=ResolutionPlanGenerationStatus.ANSWERING
            )
            template = load_template()
            metadata = await answer_template(db, template, document_ids, user_id)

            json_path = os.path.join(settings.generated_dir_path, f"{generation_id}.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(template, f, ensure_ascii=False, indent=2)

            await generation_repository.update_generation_status(
                db, generation, status=ResolutionPlanGenerationStatus.RENDERING_DOCX
            )

            issues = validate_json_against_template(template, settings.RESOLUTION_PLAN_TEMPLATE_DOCX_PATH)
            if issues:
                raise ValueError("Generated JSON failed template validation: " + "; ".join(issues))

            docx_path = os.path.join(settings.generated_dir_path, f"{generation_id}.docx")
            generate_resolution_plan(json_path, settings.RESOLUTION_PLAN_TEMPLATE_DOCX_PATH, docx_path)

            await generation_repository.save_generation_result(
                db,
                generation,
                template_json=template,
                generation_metadata=metadata,
                docx_path=docx_path,
                status=ResolutionPlanGenerationStatus.COMPLETED,
            )
        except Exception as exc:  # noqa: BLE001 - surface any failure on the generation record
            logger.exception("Resolution plan generation failed for %s", generation_id)
            await generation_repository.update_generation_status(
                db, generation, status=ResolutionPlanGenerationStatus.FAILED, error_message=str(exc)
            )
