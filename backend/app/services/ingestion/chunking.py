"""Legal-document-aware chunking.

Chunks are built from whole paragraphs so clauses/sections are not split
mid-sentence where avoidable. A leading clause/section number (if present)
is captured as `clause_reference` metadata. Consecutive chunks overlap by a
configurable number of trailing paragraphs to preserve cross-boundary context.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

import tiktoken

from app.core.config import settings
from app.services.ingestion.extraction import ExtractedParagraph

_CLAUSE_PATTERN = re.compile(
    r"^\s*(Clause\s+\d+(\.\d+)*|Article\s+\d+(\.\d+)*|Section\s+\d+(\.\d+)*|\d+(\.\d+){1,4}\.?|\([a-zA-Z]\)|\([ivxIVX]+\))\s*[-:.]?\s"
)

_encoding = tiktoken.get_encoding("cl100k_base")


def _token_count(text: str) -> int:
    return len(_encoding.encode(text))


def _clause_reference(text: str) -> str | None:
    match = _CLAUSE_PATTERN.match(text)
    return match.group(1).strip() if match else None


@dataclass
class Chunk:
    chunk_index: int
    page_number: int | None
    paragraph_number: int | None
    clause_reference: str | None
    content: str
    token_count: int


def chunk_paragraphs(paragraphs: List[ExtractedParagraph]) -> List[Chunk]:
    target_tokens = settings.CHUNK_TARGET_TOKENS
    max_tokens = settings.CHUNK_MAX_TOKENS
    overlap_tokens = settings.CHUNK_OVERLAP_TOKENS

    # Split any oversized paragraph (rare, but possible in dense legal text) into sentence groups.
    units: List[ExtractedParagraph] = []
    for para in paragraphs:
        tokens = _token_count(para.text)
        if tokens <= max_tokens:
            units.append(para)
            continue
        for sentence_group in _split_oversized_paragraph(para.text, max_tokens):
            units.append(
                ExtractedParagraph(
                    page_number=para.page_number,
                    paragraph_number=para.paragraph_number,
                    text=sentence_group,
                )
            )

    chunks: List[Chunk] = []
    current: List[ExtractedParagraph] = []
    current_tokens = 0
    chunk_index = 0

    def flush(next_seed: List[ExtractedParagraph]) -> None:
        nonlocal current, current_tokens, chunk_index
        if not current:
            return
        content = "\n\n".join(p.text for p in current)
        first = current[0]
        chunks.append(
            Chunk(
                chunk_index=chunk_index,
                page_number=first.page_number,
                paragraph_number=first.paragraph_number,
                clause_reference=_clause_reference(first.text),
                content=content,
                token_count=_token_count(content),
            )
        )
        chunk_index += 1
        current = next_seed
        current_tokens = sum(_token_count(p.text) for p in current)

    for para in units:
        para_tokens = _token_count(para.text)
        if current and current_tokens + para_tokens > target_tokens:
            overlap_seed = _build_overlap(current, overlap_tokens)
            flush(overlap_seed)
        current.append(para)
        current_tokens += para_tokens

    flush([])
    return chunks


def _build_overlap(paragraphs: List[ExtractedParagraph], overlap_tokens: int) -> List[ExtractedParagraph]:
    """Carry trailing paragraphs into the next chunk for context continuity."""
    overlap: List[ExtractedParagraph] = []
    running = 0
    for para in reversed(paragraphs):
        tokens = _token_count(para.text)
        if running >= overlap_tokens:
            break
        overlap.insert(0, para)
        running += tokens
    return overlap


def _split_oversized_paragraph(text: str, max_tokens: int) -> List[str]:
    sentences = re.split(r"(?<=[.;])\s+", text)
    groups: List[str] = []
    current = ""
    for sentence in sentences:
        candidate = f"{current} {sentence}".strip() if current else sentence
        if current and _token_count(candidate) > max_tokens:
            groups.append(current)
            current = sentence
        else:
            current = candidate
    if current:
        groups.append(current)
    return groups or [text]
