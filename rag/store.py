
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from rag.embeddings import cosine_similarity, embed_text, tokenize


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    doc_id: str
    title: str
    path: str
    tags: tuple[str, ...]
    text: str
    embedding: tuple[float, ...]

@dataclass
class SearchResult:
    chunk: Chunk
    score: float


def _chunk_to_json(chunk: Chunk) -> dict:
    data = asdict(chunk)
    data["tags"] = list(chunk.tags)
    data["embedding"] = list(chunk.embedding)
    return data


def _chunk_from_json(data: dict) -> Chunk:
    return Chunk(
        chunk_id=data["chunk_id"],
        doc_id=data["doc_id"],
        title=data["title"],
        path=data["path"],
        tags=tuple(data.get("tags", ())),
        text=data["text"],
        embedding=tuple(data.get("embedding", ())),
    )



@dataclass
class VectorStore:
    """
    This is the primary retrieval engine, using embeddings + cosine similarity.
    """

    chunks: dict[str, Chunk] = field(default_factory=dict)
    doc_file_hashes: dict[str, str] = field(default_factory=dict)

    def upsert_document(self, doc_id: str, file_hash: str, chunks: list[Chunk]) -> None:
        self.remove_document(doc_id)
        for chunk in chunks:
            self.chunks[chunk.chunk_id] = chunk
        self.doc_file_hashes[doc_id] = file_hash

    def remove_document(self, doc_id: str) -> None:
        for chunk_id in [cid for cid, c in self.chunks.items() if c.doc_id == doc_id]:
            del self.chunks[chunk_id]
        self.doc_file_hashes.pop(doc_id, None)

    def is_up_to_date(self, doc_id: str, file_hash: str) -> bool:
        return self.doc_file_hashes.get(doc_id) == file_hash

    def known_doc_ids(self) -> set[str]:
        return set(self.doc_file_hashes)

    def search(
        self,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.05,
        tag_filter: str | None = None,
    ) -> list[SearchResult]:
        """
        The actual retrieval function — 
        given a text query, return the most relevant stored chunks.
        """
        query_vector = embed_text(query)
        candidates = self.chunks.values()
        if tag_filter is not None:
            candidates = [c for c in candidates if tag_filter in c.tags]
        scored = [
            SearchResult(chunk=chunk, score=cosine_similarity(query_vector, list(chunk.embedding)))
            for chunk in candidates
        ]
        scored = [r for r in scored if r.score >= similarity_threshold]
        scored.sort(key=lambda r: r.score, reverse=True)
        return scored[:top_k]

    def save(self, path: str | Path) -> None:
        data = {
            "chunks": [_chunk_to_json(c) for c in self.chunks.values()],
            "doc_file_hashes": self.doc_file_hashes,
        }
        Path(path).write_text(json.dumps(data, indent=2))


    @classmethod
    def load(cls, path: str | Path) -> VectorStore:
        store = cls()
        p = Path(path)
        if not p.exists():
            return store
        data = json.loads(p.read_text())
        for chunk_data in data.get("chunks", []):
            chunk = _chunk_from_json(chunk_data)
            store.chunks[chunk.chunk_id] = chunk
        store.doc_file_hashes = data.get("doc_file_hashes", {})
        return store



@dataclass
class KeywordStore:
    """
    A much simpler, embedding-free way to search chunks, based purely on word overlap between the query (Jaccard)
    and each chunk. It exists as a safety net: if embeddings were ever unavailable, disabled, or considered 
    too unreliable in some constrained environment, the whole RAG pipeline can still function using nothing 
    but basic string tokenization — no vectors, no math beyond counting.
    """

    chunks: dict[str, Chunk] = field(default_factory=dict)

    def upsert_document(self, doc_id: str, chunks: list[Chunk]) -> None:
        for chunk_id in [cid for cid, c in self.chunks.items() if c.doc_id == doc_id]:
            del self.chunks[chunk_id]
        for chunk in chunks:
            self.chunks[chunk.chunk_id] = chunk

    def search(self, query: str, top_k: int = 5, similarity_threshold: float = 0.05) -> list[SearchResult]:
        query_tokens = set(tokenize(query))
        results: list[SearchResult] = []
        for chunk in self.chunks.values():
            chunk_tokens = set(tokenize(chunk.text))
            if not query_tokens or not chunk_tokens:
                continue
            overlap = len(query_tokens & chunk_tokens)
            union = len(query_tokens | chunk_tokens)
            score = overlap / union if union else 0.0
            if score >= similarity_threshold:
                results.append(SearchResult(chunk=chunk, score=score))
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]


def get_default_backend_name() -> str:
    try:
        import chromadb  # noqa: F401

        return "chroma-available-but-unused-by-default"
    except ImportError:
        return "hash-embedding-vector-store"