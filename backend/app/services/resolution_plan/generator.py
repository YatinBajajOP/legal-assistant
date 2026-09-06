"""Generate a Resolution Plan legal-review DOCX from resolution_plan_template.json.

Usage:
  python resolution_plan_generator.py input.json ResolutionPlanTemplate.docx output.docx

Fillable JSON objects contain:
  {"value": <LLM answer>, "question": "...", "target": {...}}
The LLM should write its answer into `value`. Static nodes are ignored by the writer.
"""
from __future__ import annotations

import argparse
import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from docx import Document
from docx.table import _Row


def load_json(path: str | Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _iter_fillable_nodes(obj: Any, path: str = "") -> Iterable[Tuple[str, Dict[str, Any]]]:
    """Yield every dict that has both `target` and `question`."""
    if isinstance(obj, dict):
        if "target" in obj and "question" in obj:
            yield path, obj
        for key, value in obj.items():
            child = f"{path}.{key}" if path else key
            yield from _iter_fillable_nodes(value, child)
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            yield from _iter_fillable_nodes(value, f"{path}[{i}]")


# Bold (**text**) is tried before italic (*text*) so "**x**" is never misread as
# an empty italic span followed by literal asterisks.
_INLINE_MARKDOWN_RE = re.compile(r"\*\*(.+?)\*\*|\*(.+?)\*", re.DOTALL)


def _parse_inline_markdown(text: str) -> List[Tuple[str, bool, bool]]:
    """Split `text` into (segment_text, is_bold, is_italic) runs, converting
    **bold** and *italic* markers instead of leaving the literal asterisks."""
    segments: List[Tuple[str, bool, bool]] = []
    pos = 0
    for match in _INLINE_MARKDOWN_RE.finditer(text):
        if match.start() > pos:
            segments.append((text[pos : match.start()], False, False))
        bold_content, italic_content = match.groups()
        if bold_content is not None:
            segments.append((bold_content, True, False))
        else:
            segments.append((italic_content, False, True))
        pos = match.end()
    if pos < len(text):
        segments.append((text[pos:], False, False))
    return [seg for seg in segments if seg[0]]


def _insert_run_after(paragraph, after_run, text: str, template_run=None):
    """Add a run with `text`, positioned immediately after `after_run` in document
    order (or simply appended if `after_run` is None, e.g. an originally-empty paragraph)."""
    new_run = paragraph.add_run(text)
    if template_run is not None:
        new_run.font.name = template_run.font.name
        new_run.font.size = template_run.font.size
        new_run.underline = template_run.underline
    if after_run is not None:
        after_run._r.addnext(new_run._r)
    return new_run


def _write_formatted_text_to_paragraph(paragraph, text: str) -> None:
    """Render `text` into `paragraph`, converting **bold**/*italic* markdown into
    real run formatting instead of leaving literal asterisks, while reusing the
    paragraph's existing runs (and their formatting) wherever possible."""
    segments = _parse_inline_markdown(text)
    runs = list(paragraph.runs)

    for run in runs:
        run.text = ""

    if not segments:
        return

    template_run = runs[0] if runs else None
    anchor = None
    for i, (seg_text, seg_bold, seg_italic) in enumerate(segments):
        if i < len(runs):
            run = runs[i]
            run.text = seg_text
        else:
            run = _insert_run_after(paragraph, anchor, seg_text, template_run)
        if seg_bold:
            run.bold = True
        if seg_italic:
            run.italic = True
        anchor = run


def _replace_token_preserve_runs(paragraph, token: str, replacement: str) -> None:
    """Replace token even if Word split it across runs, preserving surrounding run
    formatting, and converting any **bold**/*italic* markdown in the replacement
    into real Word formatting rather than literal asterisks."""
    replacement = "" if replacement is None else str(replacement)
    while token in paragraph.text:
        runs = paragraph.runs
        if not runs:
            paragraph.text = paragraph.text.replace(token, replacement, 1)
            return

        full = "".join(run.text for run in runs)
        start = full.find(token)
        if start < 0:
            # paragraph.text can include non-run constructs; conservative fallback.
            paragraph.text = paragraph.text.replace(token, replacement, 1)
            return
        end = start + len(token)

        positions = []
        cursor = 0
        for i, run in enumerate(runs):
            positions.append((i, cursor, cursor + len(run.text)))
            cursor += len(run.text)

        first_i = last_i = None
        for i, a, b in positions:
            if first_i is None and start < b and end > a:
                first_i = i
            if start < b and end > a:
                last_i = i
        if first_i is None:
            paragraph.text = paragraph.text.replace(token, replacement, 1)
            return

        first_run = runs[first_i]
        first_a = positions[first_i][1]
        last_a = positions[last_i][1]
        before = first_run.text[: max(0, start - first_a)]
        after = runs[last_i].text[max(0, end - last_a):]

        segments = _parse_inline_markdown(replacement)
        has_formatting = any(bold or italic for _, bold, italic in segments)

        if not has_formatting:
            first_run.text = before + replacement + after
            for i in range(first_i + 1, last_i + 1):
                runs[i].text = ""
            continue

        template_run = first_run
        first_run.text = before
        for i in range(first_i + 1, last_i + 1):
            runs[i].text = ""

        anchor = first_run
        for seg_text, seg_bold, seg_italic in segments:
            new_run = _insert_run_after(paragraph, anchor, seg_text, template_run)
            if seg_bold:
                new_run.bold = True
            if seg_italic:
                new_run.italic = True
            anchor = new_run
        if after:
            _insert_run_after(paragraph, anchor, after, template_run)


def _set_cell_text_preserve_format(cell, value: Any) -> None:
    """Replace cell visible text while retaining cell/table formatting and first
    paragraph/run formatting, converting **bold**/*italic* markdown into real
    Word formatting rather than literal asterisks."""
    text = "" if value is None else str(value)
    if not cell.paragraphs:
        cell.add_paragraph()
    p = cell.paragraphs[0]
    _write_formatted_text_to_paragraph(p, text)
    # Clear text from additional paragraphs but retain paragraph properties.
    for extra in cell.paragraphs[1:]:
        for run in extra.runs:
            run.text = ""


def _apply_table_cell(doc: Document, target: Dict[str, Any], value: Any) -> None:
    ti = int(target["table_index"])
    ri = int(target["row_index"])
    ci = int(target["column_index"])
    _set_cell_text_preserve_format(doc.tables[ti].cell(ri, ci), value)


def _replace_repeatable_rows(doc: Document, target: Dict[str, Any], items: list[dict]) -> None:
    """Replace placeholder rows with a variable-length list while cloning the template row's formatting."""
    if not items:
        return  # Keep the untouched template rows until the section has actual LLM output.

    table = doc.tables[int(target["table_index"])]
    start = int(target["start_row"])
    template_idx = int(target.get("template_row_index", start))
    keys = list(target["column_keys"])

    template_tr = deepcopy(table.rows[template_idx]._tr)

    # Remove all placeholder/example rows from `start` onward.
    tbl = table._tbl
    for row in list(table.rows)[start:]:
        tbl.remove(row._tr)

    for item in items:
        new_tr = deepcopy(template_tr)
        tbl.append(new_tr)
        row = _Row(new_tr, table)
        for ci, key in enumerate(keys):
            if ci >= len(row.cells):
                break
            _set_cell_text_preserve_format(row.cells[ci], item.get(key, ""))


def validate_json_against_template(data: Dict[str, Any], template_path: str | Path) -> list[str]:
    """Return validation issues; an empty list means the JSON can be applied safely."""
    doc = Document(str(template_path))
    issues = []
    expected = data.get("template", {})
    if expected.get("expected_tables") is not None and len(doc.tables) != expected["expected_tables"]:
        issues.append(f"Template table count mismatch: expected {expected['expected_tables']}, found {len(doc.tables)}")
    if expected.get("expected_paragraphs") is not None and len(doc.paragraphs) != expected["expected_paragraphs"]:
        issues.append(f"Template paragraph count mismatch: expected {expected['expected_paragraphs']}, found {len(doc.paragraphs)}")

    for json_path, node in _iter_fillable_nodes(data):
        t = node.get("target", {})
        typ = t.get("type")
        try:
            if typ == "paragraph_token":
                p = doc.paragraphs[int(t["paragraph_index"])]
                if t["token"] not in p.text:
                    issues.append(f"{json_path}: token {t['token']!r} not found in paragraph {t['paragraph_index']}")
            elif typ == "table_cell":
                _ = doc.tables[int(t["table_index"])].cell(int(t["row_index"]), int(t["column_index"]))
            elif typ == "repeatable_table":
                table = doc.tables[int(t["table_index"])]
                _ = table.rows[int(t.get("template_row_index", t["start_row"]))]
            else:
                issues.append(f"{json_path}: unknown target type {typ!r}")
        except (IndexError, KeyError, ValueError) as e:
            issues.append(f"{json_path}: invalid target ({e})")
    return issues


def generate_resolution_plan(json_path: str | Path, template_path: str | Path, output_path: str | Path) -> Path:
    """Main function: JSON in -> populated Word template out."""
    data = load_json(json_path)
    issues = validate_json_against_template(data, template_path)
    if issues:
        raise ValueError("JSON/template validation failed:\n- " + "\n- ".join(issues))

    doc = Document(str(template_path))

    # Apply scalar/token fields first.
    repeatables = []
    for _, node in _iter_fillable_nodes(data):
        target = node["target"]
        value = node.get("value", "")
        typ = target["type"]
        if typ == "paragraph_token":
            _replace_token_preserve_runs(
                doc.paragraphs[int(target["paragraph_index"])], target["token"], value
            )
        elif typ == "table_cell":
            # Empty value means "not answered yet": leave the pristine template cell untouched.
            if value not in (None, ""):
                _apply_table_cell(doc, target, value)
        elif typ == "repeatable_table":
            repeatables.append((target, value))

    # Do repeatable row operations after fixed cells to avoid row-index movement.
    for target, value in repeatables:
        if not isinstance(value, list):
            raise TypeError(f"Repeatable table value must be a list, got {type(value).__name__}")
        _replace_repeatable_rows(doc, target, value)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out))
    return out


def unanswered_questions(json_path: str | Path) -> list[dict[str, str]]:
    """Return prompts that still need an LLM answer. Useful for your orchestration layer."""
    data = load_json(json_path)
    result = []
    for json_path_str, node in _iter_fillable_nodes(data):
        value = node.get("value")
        if value in (None, "", []):
            result.append({"json_path": json_path_str, "question": node["question"]})
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Populate the Resolution Plan Word review template from JSON")
    parser.add_argument("json_path")
    parser.add_argument("template_path")
    parser.add_argument("output_path")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--list-unanswered", action="store_true")
    args = parser.parse_args()

    if args.list_unanswered:
        print(json.dumps(unanswered_questions(args.json_path), indent=2, ensure_ascii=False))
        return

    issues = validate_json_against_template(load_json(args.json_path), args.template_path)
    if issues:
        print(json.dumps({"valid": False, "issues": issues}, indent=2))
        raise SystemExit(1)
    if args.validate_only:
        print(json.dumps({"valid": True, "issues": []}, indent=2))
        return

    out = generate_resolution_plan(args.json_path, args.template_path, args.output_path)
    print(out)


if __name__ == "__main__":
    main()
