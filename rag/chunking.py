"""
Front-matter parsing and bounded chunking for the knowledge base.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_FRONT_MATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)

MAX_CHUNK_CHARS = 900
CHUNK_OVERLAP_CHARS = 120
MAX_CHUNKS_PER_DOCUMENT = 50 


class DocumentTooLargeError(ValueError):
    """
    A custom exception raised when a document would need more than 50 chunks. 
    This lets callers (like rag/ingest.py) catch this specific failure mode 
    distinctly from generic ValueErrors.
    """


@dataclass(frozen=True)
class ParsedDocument:
    doc_id: str
    title: str
    tags: tuple[str, ...]
    body: str


def parse_front_matter(raw_text: str, fallback_doc_id: str) -> ParsedDocument:
    """
    Extract metadata (doc_id, title, tags) from a small YAML-like front-matter 
    block without using a full YAML parser.
    """
    match = _FRONT_MATTER_RE.match(raw_text)
    if not match:
        return ParsedDocument(doc_id=fallback_doc_id, title=fallback_doc_id, tags=(), body=raw_text)

    front_matter_block, body = match.groups()
    metadata: dict[str, str] = {}
    for line in front_matter_block.splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        metadata[key.strip()] = value.strip()

    tags_raw = metadata.get("tags", "")
    tags = tuple(t.strip() for t in tags_raw.strip("[]").split(",") if t.strip())

    return ParsedDocument(
        doc_id=metadata.get("doc_id", fallback_doc_id),
        title=metadata.get("title", fallback_doc_id),
        tags=tags,
        body=body.strip(),
    )


def chunk_text(text: str, max_chars: int = MAX_CHUNK_CHARS, overlap_chars: int = CHUNK_OVERLAP_CHARS) -> list[str]:
    """
    Split a document body into a list of bounded, paragraph-aware chunks suitable for embedding.
    """
    if max_chars <= 0:
        raise ValueError("max_chars must be positive")

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            chunks.append(current)
        if len(paragraph) <= max_chars:
            current = paragraph
        else:
            # A single paragraph longer than max_chars: hard-slice it with overlap.
            start = 0
            while start < len(paragraph):
                end = min(start + max_chars, len(paragraph))
                chunks.append(paragraph[start:end])
                start = end - overlap_chars if end < len(paragraph) else end
            current = ""

    if current:
        chunks.append(current)

    if len(chunks) > MAX_CHUNKS_PER_DOCUMENT:
        raise DocumentTooLargeError(
            f"Document would produce {len(chunks)} chunks, exceeding the "
            f"safety cap of {MAX_CHUNKS_PER_DOCUMENT}"
        )
    return chunks