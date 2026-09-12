"""Tests for rag/chunking.py: front matter parsing and bounded chunking."""



from __future__ import annotations

import pytest

from rag.chunking import (
    MAX_CHUNK_CHARS,
    MAX_CHUNKS_PER_DOCUMENT,
    DocumentTooLargeError,
    chunk_text,
    parse_front_matter,
)

SAMPLE_DOC = """---
doc_id: sample-doc
title: Sample Document
tags: [alpha, beta]
---

First paragraph of the body.

Second paragraph of the body.
"""


def test_parse_front_matter_extracts_metadata():
    parsed = parse_front_matter(SAMPLE_DOC, fallback_doc_id="fallback")
    assert parsed.doc_id == "sample-doc"
    assert parsed.title == "Sample Document"
    assert parsed.tags == ("alpha", "beta")
    assert "First paragraph" in parsed.body
    assert "---" not in parsed.body


def test_parse_front_matter_falls_back_without_front_matter():
    parsed = parse_front_matter("Just plain text, no front matter.", fallback_doc_id="my-doc")
    assert parsed.doc_id == "my-doc"
    assert parsed.title == "my-doc"
    assert parsed.tags == ()
    assert parsed.body == "Just plain text, no front matter."


def test_chunk_text_keeps_small_documents_as_one_chunk():
    chunks = chunk_text("Short paragraph one.\n\nShort paragraph two.")
    assert len(chunks) == 1


def test_chunk_text_respects_max_chars():
    long_paragraph = "word " * 400  # ~2000 chars, no blank lines
    chunks = chunk_text(long_paragraph)
    assert len(chunks) > 1
    assert all(len(c) <= MAX_CHUNK_CHARS for c in chunks)


def test_chunk_text_overlaps_hard_sliced_chunks():
    long_paragraph = "x" * 2500
    chunks = chunk_text(long_paragraph, max_chars=1000, overlap_chars=100)
    assert len(chunks) >= 3
    # Consecutive hard-sliced chunks should share an overlapping tail/head.
    assert chunks[0][-100:] == chunks[1][:100]


def test_chunk_text_raises_when_too_many_chunks():
    huge_text = "\n\n".join(f"paragraph {i} " * 200 for i in range(MAX_CHUNKS_PER_DOCUMENT + 5))
    with pytest.raises(DocumentTooLargeError):
        chunk_text(huge_text)


def test_chunk_text_rejects_non_positive_max_chars():
    with pytest.raises(ValueError):
        chunk_text("hello", max_chars=0)