"""Text extraction that preserves page and paragraph boundaries for legal documents."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class ExtractedParagraph:
    page_number: int | None
    paragraph_number: int
    text: str


@dataclass
class ExtractedDocument:
    paragraphs: List[ExtractedParagraph]
    page_count: int | None


def extract_document(file_path: str, content_type: str | None) -> ExtractedDocument:
    suffix = Path(file_path).suffix.lower()
    if suffix == ".pdf" or content_type == "application/pdf":
        return _extract_pdf(file_path)
    if suffix == ".docx" or content_type in (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ):
        return _extract_docx(file_path)
    if suffix in (".txt", ".md") or (content_type or "").startswith("text/"):
        return _extract_plain_text(file_path)
    raise ValueError(f"Unsupported document type for extraction: {suffix or content_type}")


def _extract_pdf(file_path: str) -> ExtractedDocument:
    from pypdf import PdfReader

    reader = PdfReader(file_path)
    paragraphs: List[ExtractedParagraph] = []
    paragraph_number = 0
    for page_index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        for raw_para in _split_into_paragraphs(text):
            paragraph_number += 1
            paragraphs.append(
                ExtractedParagraph(page_number=page_index, paragraph_number=paragraph_number, text=raw_para)
            )
    return ExtractedDocument(paragraphs=paragraphs, page_count=len(reader.pages))


def _extract_docx(file_path: str) -> ExtractedDocument:
    from docx import Document as DocxDocument
    from docx.oxml.ns import qn

    doc = DocxDocument(file_path)
    paragraphs: List[ExtractedParagraph] = []
    paragraph_number = 0
    page_number = 1
    max_page = 1
    for para in doc.paragraphs:
        text = para.text.strip()
        # Explicit page breaks are represented as <w:br w:type="page"/> inside runs.
        has_page_break = any(
            br.get(qn("w:type")) == "page"
            for run in para.runs
            for br in run._element.findall(qn("w:br"))
        )
        if text:
            paragraph_number += 1
            paragraphs.append(
                ExtractedParagraph(page_number=page_number, paragraph_number=paragraph_number, text=text)
            )
        if has_page_break:
            page_number += 1
            max_page = max(max_page, page_number)
    return ExtractedDocument(paragraphs=paragraphs, page_count=max_page)


def _extract_plain_text(file_path: str) -> ExtractedDocument:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    paragraphs = [
        ExtractedParagraph(page_number=None, paragraph_number=i + 1, text=p)
        for i, p in enumerate(_split_into_paragraphs(text))
    ]
    return ExtractedDocument(paragraphs=paragraphs, page_count=None)


def _split_into_paragraphs(text: str) -> List[str]:
    # Normalize line endings, then split on blank lines (paragraph breaks).
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    raw_blocks = re.split(r"\n\s*\n+", normalized)
    paragraphs = []
    for block in raw_blocks:
        cleaned = re.sub(r"[ \t]+", " ", block).strip()
        if cleaned:
            paragraphs.append(cleaned)
    return paragraphs
