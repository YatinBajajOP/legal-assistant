# Resolution Plan JSON -> Word Generator

## Files
- `resolution_plan_template.json` — semantic JSON representation of the supplied Word template.
- `resolution_plan_generator.py` — validates the JSON and fills the original `.docx` template.
- `ResolutionPlanTemplate.docx` — keep the supplied template beside the script (or provide its path explicitly).

## JSON convention
Static content:
```json
{
  "value": "Compliance Check & Legal Review of Resolution Plan",
  "static": true
}
```

Fillable content:
```json
{
  "value": "",
  "question": "Who submitted the Resolution Plan? ...",
  "target": {
    "type": "paragraph_token",
    "paragraph_index": 2,
    "token": "<Resolution Applicant>"
  }
}
```

Your LLM/orchestration layer should place its answer in the `value` key. The `target` is internal rendering metadata and should not be changed.

For best token efficiency, send the LLM:
1. the field's `question`,
2. static values in the same JSON row/section,
3. the relevant retrieved chunks from the source Resolution Plan.

Do not send the complete JSON for every field.

## Variable-length sections
Three sections use array answers and can add/remove Word table rows automatically:
- `feasibility_and_viability_queries.items.value`
- `post_approval_steps.items.value`
- `relevant_approvals.items.value`

Example:
```json
"value": [
  {
    "relevant_clause_no": "Clause 6.11",
    "page_no": "71",
    "relevant_extract": "...",
    "remarks": "..."
  }
]
```

## Generate Word
```bash
python resolution_plan_generator.py \
  populated_resolution_plan.json \
  ResolutionPlanTemplate.docx \
  generated_resolution_plan.docx
```

## Validate before generation
```bash
python resolution_plan_generator.py \
  populated_resolution_plan.json \
  ResolutionPlanTemplate.docx \
  generated_resolution_plan.docx \
  --validate-only
```

## Get unanswered LLM prompts
```bash
python resolution_plan_generator.py \
  populated_resolution_plan.json \
  ResolutionPlanTemplate.docx \
  generated_resolution_plan.docx \
  --list-unanswered
```

Or import directly:
```python
from resolution_plan_generator import (
    generate_resolution_plan,
    unanswered_questions,
    validate_json_against_template,
)

generate_resolution_plan(
    "populated_resolution_plan.json",
    "ResolutionPlanTemplate.docx",
    "generated_resolution_plan.docx",
)
```

## Important behavior
- The generator modifies a copy of the supplied Word template instead of rebuilding the document, preserving its table/cell formatting and document structure.
- Empty unanswered scalar fields are left unchanged in the template.
- Repeatable tables are only replaced when their `value` arrays contain items.
- Static legal/RFRP wording is not rewritten by the generator.
