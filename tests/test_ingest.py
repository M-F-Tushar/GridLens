"""Tests for rag/ingest.py: knowledge-base ingestion and incremental hashing."""



from __future__ import annotations

from rag.ingest import DEFAULT_KNOWLEDGE_DIR, compute_file_hash, ingest_knowledge_base
from rag.store import VectorStore

EXPECTED_KNOWLEDGE_DOC_COUNT = 12


def test_default_knowledge_dir_has_expected_number_of_documents():
    md_files = list(DEFAULT_KNOWLEDGE_DIR.glob("*.md"))
    assert len(md_files) == EXPECTED_KNOWLEDGE_DOC_COUNT


def test_ingest_knowledge_base_adds_every_document():
    store = VectorStore()
    report = ingest_knowledge_base(store)

    assert len(report.added_docs) == EXPECTED_KNOWLEDGE_DOC_COUNT
    assert report.updated_docs == []
    assert report.skipped_docs == []
    assert report.total_chunks_written > 0
    assert len(store.known_doc_ids()) == EXPECTED_KNOWLEDGE_DOC_COUNT


def test_ingest_knowledge_base_is_idempotent_on_second_run():
    store = VectorStore()
    ingest_knowledge_base(store)
    second_report = ingest_knowledge_base(store)

    assert second_report.added_docs == []
    assert second_report.updated_docs == []
    assert len(second_report.skipped_docs) == EXPECTED_KNOWLEDGE_DOC_COUNT
    assert second_report.total_chunks_written == 0


def test_ingest_knowledge_base_reingests_changed_file(tmp_path):
    doc_path = tmp_path / "one.md"
    doc_path.write_text("---\ndoc_id: one\ntitle: One\ntags: [demo]\n---\n\nOriginal content here.\n")

    store = VectorStore()
    first_report = ingest_knowledge_base(store, knowledge_dir=tmp_path)
    assert first_report.added_docs == ["one"]

    doc_path.write_text("---\ndoc_id: one\ntitle: One\ntags: [demo]\n---\n\nChanged content here.\n")
    second_report = ingest_knowledge_base(store, knowledge_dir=tmp_path)
    assert second_report.updated_docs == ["one"]
    assert second_report.added_docs == []

    results = store.search("changed content", top_k=5, similarity_threshold=0.0)
    assert any("Changed content" in r.chunk.text for r in results)


def test_ingest_knowledge_base_removes_deleted_documents(tmp_path):
    doc_a = tmp_path / "a.md"
    doc_b = tmp_path / "b.md"
    doc_a.write_text("---\ndoc_id: a\ntitle: A\ntags: []\n---\n\nContent A.\n")
    doc_b.write_text("---\ndoc_id: b\ntitle: B\ntags: []\n---\n\nContent B.\n")

    store = VectorStore()
    ingest_knowledge_base(store, knowledge_dir=tmp_path)
    assert store.known_doc_ids() == {"a", "b"}

    doc_b.unlink()
    report = ingest_knowledge_base(store, knowledge_dir=tmp_path)
    assert report.removed_docs == ["b"]
    assert store.known_doc_ids() == {"a"}


def test_compute_file_hash_changes_when_content_changes(tmp_path):
    path = tmp_path / "file.md"
    path.write_text("version one")
    hash_one = compute_file_hash(path)
    path.write_text("version two")
    hash_two = compute_file_hash(path)
    assert hash_one != hash_two


def test_ingested_chunks_preserve_doc_metadata():
    store = VectorStore()
    ingest_knowledge_base(store)
    results = store.search("tariff", top_k=1, similarity_threshold=0.0, tag_filter=None)
    assert results
    chunk = results[0].chunk
    assert chunk.title
    assert chunk.path.startswith("data/knowledge/")