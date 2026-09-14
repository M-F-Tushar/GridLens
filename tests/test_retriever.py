"""Tests for rag/retriever.py: cached singleton store + retrieval."""
from __future__ import annotations

from rag.retriever import get_store, reset_store_cache, retrieve, to_citation


def test_get_store_is_cached_across_calls():
    reset_store_cache()
    store_a = get_store()
    store_b = get_store()
    assert store_a is store_b
    reset_store_cache()


def test_retrieve_returns_relevant_results_for_known_topic():
    reset_store_cache()
    results = retrieve("battery round trip efficiency", top_k=3, similarity_threshold=0.0)
    assert results
    assert any("battery" in r.chunk.doc_id for r in results)


def test_retrieve_respects_top_k():
    reset_store_cache()
    results = retrieve("tariff cost pricing", top_k=1, similarity_threshold=0.0)
    assert len(results) <= 1


def test_to_citation_truncates_long_snippets():
    reset_store_cache()
    results = retrieve("tariff", top_k=1, similarity_threshold=0.0)
    citation = to_citation(results[0], snippet_chars=20)
    assert len(citation.snippet) <= 21  # 20 chars + ellipsis
    assert citation.doc_id == results[0].chunk.doc_id