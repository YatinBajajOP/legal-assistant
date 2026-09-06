"""RAG orchestration: answer grouped resolution-plan template questions.

For each question group, the most relevant chunks are retrieved via pgvector
similarity search, then a single structured LLM call answers every question in
the group at once. Independent groups run concurrently.
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any, Dict, List, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models.document import DocumentChunk
from app.repositories import chunk_repository
from app.services.embeddings import embed_query
from app.services.llm_client import complete_json
from app.services.resolution_plan.template_engine import (
    QuestionGroup,
    build_question_groups,
    get_unanswered_nodes,
)

logger = logging.getLogger(__name__)

_NOT_PROVIDED = "--"

_SYSTEM_PROMPT = """You are a legal analyst assistant answering structured questions about an Insolvency Resolution Plan using **ONLY the provided source excerpts**.
### Rules
* **DO NOT HALLUCINATE.** Never invent, assume, infer, or fabricate facts, amounts, dates, clause numbers, commitments, definitions, or compliance.
* Answer strictly from the provided context. **If the context does not explicitly support an answer, return `--`** (or an empty list for list-type answers).
* Client instructions below are **mandatory requirements**. Check the provided documents against them, but **do not treat the instruction itself as evidence that the requirement is satisfied**.
* Flag contradictions or clauses inconsistent with these requirements only when supported by the provided context.
* Preserve exact clause numbers, page numbers, dates, amounts, names, and defined terms from the source.
* Definitions must follow the RFRP definitions.
* No contradictory or conditional clauses should exist.
* Resolution Plan amount must not be reduced under any condition.
* Net-worth certificate must be provided and demonstrate liquidity.
* Clearly identify capital infusion amount and timeline.
* Plan must include definite investment/business strategy, expansion, client acquisition and capital investment where applicable.
* Identify RA's past business-revival experience.
* RA shall not extend charge on existing assets until final implementation.
* No alteration after CoC approval.
* Monitoring Committee: formation within 7 days of AA/NCLT approval; dissolution only after all plan payments to creditors; RP remains Chairman; Chairman remuneration remains as decided for RP before approval.
* Address treatment of Avoidance Transaction proceeds and related expenses.
* No deemed inference.
* Identify whether equity share capital is offered to creditors.
* IBC and applicable regulations prevail in case of inconsistency.
* Include applicable IBBI regulatory fee provision (0.25% of Resolution Plan amount, or the applicable amended percentage at approval).
* Identify required supporting documents such as projections, credit rating, bank comfort/commitment letters, sanction letters, bank certificates and experience proofs.
### Output
Return **ONLY a valid JSON object in the exact structure requested**.
**Never use outside knowledge to fill gaps. When in doubt, return `--` rather than guessing.**
"""


def _format_context(chunks: Sequence[DocumentChunk]) -> str:
    if not chunks:
        return "(No relevant source excerpts were found for this group.)"
    parts = []
    for chunk in chunks:
        location = []
        if chunk.page_number is not None:
            location.append(f"Page {chunk.page_number}")
        if chunk.paragraph_number is not None:
            location.append(f"Paragraph {chunk.paragraph_number}")
        if chunk.clause_reference:
            location.append(f"Clause {chunk.clause_reference}")
        location_str = ", ".join(location) if location else "Location unknown"
        parts.append(f"[{location_str}]\n{chunk.content}")
    return "\n\n---\n\n".join(parts)


async def _retrieve_context(
    db: AsyncSession, group: QuestionGroup, document_ids: Sequence[uuid.UUID], user_id: int
) -> List[DocumentChunk]:
    query_embedding = await embed_query(group.retrieval_query)
    return await chunk_repository.similarity_search(
        db,
        query_embedding=query_embedding,
        document_ids=document_ids,
        user_id=user_id,
        top_k=settings.RETRIEVAL_TOP_K,
    )


def _build_scalar_prompt(group: QuestionGroup, context: str, llm_instructions: List[str]) -> str:
    questions_block = "\n".join(
        f'- id="{idx}": {node.get("question", "")}' for idx, (_, node) in enumerate(group.nodes)
    )
    instructions_block = "\n".join(f"- {instr}" for instr in llm_instructions)
    return f"""General instructions:
{instructions_block}

Source excerpts (Resolution Plan and related documents):
{context}

Answer each of the following questions using only the excerpts above.
{questions_block}

Respond with a JSON object of exactly this shape:
{{"answers": {{"0": "<answer text or \\"--\\">", "1": "<answer text or \\"--\\">", ...}}}}
Every question id above must be present as a key.
"""


def _build_array_prompt(group: QuestionGroup, context: str, llm_instructions: List[str]) -> str:
    _, node = group.nodes[0]
    column_keys = node["target"].get("column_keys", [])
    instructions_block = "\n".join(f"- {instr}" for instr in llm_instructions)
    return f"""General instructions:
{instructions_block}

Source excerpts (Resolution Plan and related documents):
{context}

Task: {node.get("question", "")}

Respond with a JSON object of exactly this shape:
{{"answers": {{"items": [{{{", ".join(f'"{k}": "..."' for k in column_keys)}}}, ...]}}}}
If no items are supported by the excerpts, return {{"answers": {{"items": []}}}}.
Do not fabricate rows; only include items clearly supported by the source excerpts.
"""


async def _answer_group(
    db: AsyncSession,
    group: QuestionGroup,
    document_ids: Sequence[uuid.UUID],
    user_id: int,
    llm_instructions: List[str],
    semaphore: asyncio.Semaphore,
) -> None:
    chunks = await _retrieve_context(db, group, document_ids, user_id)
    context = _format_context(chunks)

    if group.is_array_group:
        prompt = _build_array_prompt(group, context, llm_instructions)
    else:
        prompt = _build_scalar_prompt(group, context, llm_instructions)

    async with semaphore:
        try:
            result = await complete_json(system_prompt=_SYSTEM_PROMPT, user_prompt=prompt)
        except Exception:
            logger.exception("LLM call failed for group %s", group.group_id)
            result = {"answers": {}}

    answers: Dict[str, Any] = result.get("answers", {})

    if group.is_array_group:
        _, node = group.nodes[0]
        node["value"] = answers.get("items", []) or []
        return

    for idx, (_, node) in enumerate(group.nodes):
        answer = answers.get(str(idx))
        node["value"] = answer if answer not in (None, "") else _NOT_PROVIDED


async def answer_template(
    db: AsyncSession,
    template: Dict[str, Any],
    document_ids: Sequence[uuid.UUID],
    user_id: int,
) -> Dict[str, Any]:
    """Answer every unanswered question in `template` in place. Returns run metadata."""
    nodes = get_unanswered_nodes(template)
    groups = build_question_groups(nodes)
    llm_instructions = template.get("llm_instructions", [])

    semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_LLM_CALLS)
    await asyncio.gather(
        *(
            _answer_group(db, group, document_ids, user_id, llm_instructions, semaphore)
            for group in groups
        )
    )

    return {
        "question_count": len(nodes),
        "group_count": len(groups),
        "llm_model": settings.LLM_MODEL,
        "embedding_model": settings.EMBEDDING_MODEL,
        "retrieval_top_k": settings.RETRIEVAL_TOP_K,
    }
