"""This module is the orchestrator/entry point of the RAG pipeline — 
the thing that actually ties rag/chunking.py, rag/embeddings.py, and rag/store.py 
together into one end-to-end operation.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from rag.chunking import chunk_text, parse_front_matter
from rag.embeddings import embed_text
from rag.store import Chunk, VectorStore

DEFAULT_KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "data" / "knowledge"


@dataclass
class IngestReport:
    added_docs: list[str] = field(default_factory=list)
    updated_docs: list[str] = field(default_factory=list)
    skipped_docs: list[str] = field(default_factory=list)
    removed_docs: list[str] = field(default_factory=list)
    total_chunks_written: int = 0

    @property
    def touched_doc_count(self) -> int:
        return len(self.added_docs) + len(self.updated_docs)


def compute_file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ingest_knowledge_base(
    store: VectorStore,
    knowledge_dir: Path | str = DEFAULT_KNOWLEDGE_DIR,
) -> IngestReport:
    """
    main function — the one that that performs a full ingestion pass.
    """
    knowledge_dir = Path(knowledge_dir)
    report = IngestReport()

    seen_doc_ids: set[str] = set()
    for path in sorted(knowledge_dir.glob("*.md")):
        raw_text = path.read_text()
        file_hash = compute_file_hash(path)
        parsed = parse_front_matter(raw_text, fallback_doc_id=path.stem)
        doc_id = parsed.doc_id
        seen_doc_ids.add(doc_id)

        was_known = doc_id in store.known_doc_ids()
        if store.is_up_to_date(doc_id, file_hash):
            report.skipped_docs.append(doc_id)
            continue

        chunks = _build_chunks(parsed, file_path=str(path.relative_to(knowledge_dir.parent.parent)))
        store.upsert_document(doc_id, file_hash, chunks)
        report.total_chunks_written += len(chunks)
        (report.updated_docs if was_known else report.added_docs).append(doc_id)

    removed = store.known_doc_ids() - seen_doc_ids
    for doc_id in sorted(removed):
        store.remove_document(doc_id)
        report.removed_docs.append(doc_id)

    return report


def _build_chunks(parsed, file_path: str) -> list[Chunk]:
    pieces = chunk_text(parsed.body)
    chunks: list[Chunk] = []
    for index, piece in enumerate(pieces):
        chunk_id = f"{parsed.doc_id}::chunk-{index}"
        chunks.append(
            Chunk(
                chunk_id=chunk_id,
                doc_id=parsed.doc_id,
                title=parsed.title,
                path=file_path,
                tags=parsed.tags,
                text=piece,
                embedding=tuple(embed_text(piece)),
            )
        )
    return chunks