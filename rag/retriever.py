from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from rag.ingest import ingest_knowledge_base
from rag.store import SearchResult, VectorStore


DEFAULT_TOP_K = 4
DEFAULT_SIMILARITY_THRESHOLD = 0.30

@dataclass(frozen=True)
class Citation:
    doc_id: str
    title: str
    path: str
    chunk_id: str
    score: float
    snippet: str


@lru_cache(maxsize=1)
def get_store() -> VectorStore:
    """Builds (once per process) the default vector store from the on-disk
    knowledge base. Cached so repeated calls do not re-ingest.
    """
    store = VectorStore()
    ingest_knowledge_base(store)
    return store


def reset_store_cache() -> None:
    """Test helper: clears the cached store so a fresh ingest can be forced."""
    get_store.cache_clear()


def retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    tag_filter: str | None = None,
) -> list[SearchResult]:
    store = get_store()
    return store.search(query, top_k=top_k, similarity_threshold=similarity_threshold, tag_filter=tag_filter)



def to_citation(result: SearchResult, snippet_chars: int = 220) -> Citation:
    text = result.chunk.text.strip().replace("\n", " ")
    snippet = text[:snippet_chars] + ("…" if len(text) > snippet_chars else "")
    return Citation(
        doc_id=result.chunk.doc_id,
        title=result.chunk.title,
        path=result.chunk.path,
        chunk_id=result.chunk.chunk_id,
        score=round(result.score, 4),
        snippet=snippet,
    )