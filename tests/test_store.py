"""Tests for rag/store.py: VectorStore and KeywordStore."""


from __future__ import annotations

from rag.embeddings import embed_text
from rag.store import Chunk, KeywordStore, VectorStore, get_default_backend_name


def _make_chunk(chunk_id: str, doc_id: str, text: str, tags: tuple[str, ...] = ()) -> Chunk:
    return Chunk(
        chunk_id=chunk_id,
        doc_id=doc_id,
        title=doc_id,
        path=f"data/knowledge/{doc_id}.md",
        tags=tags,
        text=text,
        embedding=tuple(embed_text(text)),
    )


def test_vector_store_upsert_and_search():
    store = VectorStore()
    chunk = _make_chunk("doc-a::chunk-0", "doc-a", "battery efficiency and state of charge limits")
    store.upsert_document("doc-a", file_hash="hash-1", chunks=[chunk])

    results = store.search("battery state of charge", top_k=5, similarity_threshold=0.0)
    assert len(results) == 1
    assert results[0].chunk.chunk_id == "doc-a::chunk-0"


def test_vector_store_similarity_threshold_filters_unrelated_results():
    store = VectorStore()
    chunk = _make_chunk("doc-a::chunk-0", "doc-a", "battery efficiency and state of charge limits")
    store.upsert_document("doc-a", file_hash="hash-1", chunks=[chunk])

    results = store.search("completely unrelated query about zoo animals", top_k=5, similarity_threshold=0.9)
    assert results == []


def test_vector_store_is_up_to_date_and_upsert_replaces_old_chunks():
    store = VectorStore()
    chunk_v1 = _make_chunk("doc-a::chunk-0", "doc-a", "version one content")
    store.upsert_document("doc-a", file_hash="hash-1", chunks=[chunk_v1])
    assert store.is_up_to_date("doc-a", "hash-1") is True
    assert store.is_up_to_date("doc-a", "hash-2") is False

    chunk_v2 = _make_chunk("doc-a::chunk-0", "doc-a", "version two content")
    store.upsert_document("doc-a", file_hash="hash-2", chunks=[chunk_v2])
    assert len(store.chunks) == 1
    assert store.chunks["doc-a::chunk-0"].text == "version two content"


def test_vector_store_remove_document_clears_its_chunks():
    store = VectorStore()
    chunk = _make_chunk("doc-a::chunk-0", "doc-a", "some content")
    store.upsert_document("doc-a", file_hash="hash-1", chunks=[chunk])
    store.remove_document("doc-a")
    assert store.chunks == {}
    assert "doc-a" not in store.known_doc_ids()


def test_vector_store_tag_filter():
    store = VectorStore()
    tagged = _make_chunk("doc-a::chunk-0", "doc-a", "tariff pricing information", tags=("tariffs",))
    untagged = _make_chunk("doc-b::chunk-0", "doc-b", "tariff pricing information too", tags=("battery",))
    store.upsert_document("doc-a", "hash-1", [tagged])
    store.upsert_document("doc-b", "hash-2", [untagged])

    results = store.search("tariff pricing", top_k=5, similarity_threshold=0.0, tag_filter="tariffs")
    assert len(results) == 1
    assert results[0].chunk.doc_id == "doc-a"


def test_vector_store_save_and_load_round_trip(tmp_path):
    store = VectorStore()
    chunk = _make_chunk("doc-a::chunk-0", "doc-a", "round trip persistence test content")
    store.upsert_document("doc-a", file_hash="hash-1", chunks=[chunk])

    path = tmp_path / "store.json"
    store.save(path)

    loaded = VectorStore.load(path)
    assert loaded.is_up_to_date("doc-a", "hash-1")
    assert loaded.chunks["doc-a::chunk-0"].text == "round trip persistence test content"


def test_vector_store_load_missing_file_returns_empty_store(tmp_path):
    loaded = VectorStore.load(tmp_path / "does-not-exist.json")
    assert loaded.chunks == {}


def test_keyword_store_matches_on_token_overlap():
    store = KeywordStore()
    chunk = _make_chunk("doc-a::chunk-0", "doc-a", "battery efficiency and state of charge limits")
    store.upsert_document("doc-a", [chunk])

    results = store.search("battery state of charge", top_k=5, similarity_threshold=0.0)
    assert len(results) == 1


def test_keyword_store_upsert_replaces_prior_chunks_for_doc():
    store = KeywordStore()
    chunk_v1 = _make_chunk("doc-a::chunk-0", "doc-a", "old content")
    store.upsert_document("doc-a", [chunk_v1])
    chunk_v2 = _make_chunk("doc-a::chunk-0", "doc-a", "new content")
    store.upsert_document("doc-a", [chunk_v2])
    assert len(store.chunks) == 1
    assert store.chunks["doc-a::chunk-0"].text == "new content"


def test_get_default_backend_name_returns_a_string():
    assert isinstance(get_default_backend_name(), str)