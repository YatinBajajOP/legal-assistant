"""Dynamic loading, question extraction, and grouping for the resolution-plan template.

No individual field/question is hardcoded here: everything is derived from the
`value`/`question`/`target` shape defined in resolution_plan_template.json, so
future changes to the template do not require code changes.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

from app.core.config import settings
from app.services.resolution_plan.generator import _iter_fillable_nodes  # reused, not reimplemented


def load_template() -> Dict[str, Any]:
    """Load a fresh copy of the template JSON (safe to mutate per-generation)."""
    with open(settings.RESOLUTION_PLAN_TEMPLATE_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


FillableNode = Tuple[str, Dict[str, Any]]


def get_unanswered_nodes(template: Dict[str, Any]) -> List[FillableNode]:
    """Return (json_path, node) pairs for every question whose value is still empty."""
    nodes = []
    for path, node in _iter_fillable_nodes(template):
        value = node.get("value")
        if value in (None, "", []):
            nodes.append((path, node))
    return nodes


def is_array_target(node: Dict[str, Any]) -> bool:
    return node.get("target", {}).get("type") == "repeatable_table"


@dataclass
class QuestionGroup:
    group_id: str
    nodes: List[FillableNode] = field(default_factory=list)

    @property
    def is_array_group(self) -> bool:
        return len(self.nodes) == 1 and is_array_target(self.nodes[0][1])

    @property
    def retrieval_query(self) -> str:
        return "\n".join(node.get("question", "") for _, node in self.nodes)


def build_question_groups(nodes: List[FillableNode]) -> List[QuestionGroup]:
    """Group related, adjacent questions together to minimize retrieval/LLM calls.

    Array-valued (repeatable table) fields are answered in their own group since
    their expected response shape (a JSON list) differs from scalar fields.
    Scalar fields are batched in template order (which keeps same-row/-section
    fields adjacent) up to `QUESTION_GROUP_SIZE` per group.
    """
    groups: List[QuestionGroup] = []
    scalar_batch: List[FillableNode] = []
    group_counter = 0

    def flush_scalar_batch() -> None:
        nonlocal scalar_batch, group_counter
        if scalar_batch:
            group_counter += 1
            groups.append(QuestionGroup(group_id=f"group-{group_counter}", nodes=scalar_batch))
            scalar_batch = []

    for path, node in nodes:
        if is_array_target(node):
            flush_scalar_batch()
            group_counter += 1
            groups.append(QuestionGroup(group_id=f"group-{group_counter}", nodes=[(path, node)]))
            continue

        scalar_batch.append((path, node))
        if len(scalar_batch) >= settings.QUESTION_GROUP_SIZE:
            flush_scalar_batch()

    flush_scalar_batch()
    return groups
