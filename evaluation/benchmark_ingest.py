"""
This file is a measurement script, not a test. 
Its purpose is to answer questions like: How fast is ingestion, 
actually and does the incremental-hashing optimization in ingest.py 
genuinely make re-ingestion faster 

"""


from __future__ import annotations

import time

from rag.ingest import ingest_knowledge_base
from rag.store import VectorStore


def benchmark_full_ingest(runs: int = 3) -> dict:
    """
    Measure how long a full injection from scratch takes, 
    averaged over several repeated runs to smooth out 
    the random noise 
    """
    durations_ms = []
    chunk_counts = []
    for _ in range(runs):
        store = VectorStore()
        start = time.perf_counter()
        report = ingest_knowledge_base(store)
        elapsed_ms = (time.perf_counter() - start) * 1000
        durations_ms.append(elapsed_ms)
        chunk_counts.append(len(store.chunks))

    return {
        "runs": runs,
        "durations_ms": durations_ms,
        "mean_duration_ms": sum(durations_ms) / runs,
        "min_duration_ms": min(durations_ms),
        "max_duration_ms": max(durations_ms),
        "chunk_count": chunk_counts[-1],
        "last_report_added": report.added_docs,
    }


def benchmark_incremental_reingest() -> float:
    """
    This file demonstrates the incremental hashing story, 
    meaning that ingesting the same file a second time 
    is dramatically faster than the first time because
    the file hashes match and nothing needs to be reprocessed 
    """
    store = VectorStore()
    ingest_knowledge_base(store)  # cold ingest, populates the store
    start = time.perf_counter()
    ingest_knowledge_base(store)  # warm re-ingest, everything should be skipped
    return (time.perf_counter() - start) * 1000


def main() -> None:
    cold = benchmark_full_ingest()
    warm_ms = benchmark_incremental_reingest()
    print("=== GridLens RAG ingestion benchmark ===")
    print(f"Cold ingest, mean of {cold['runs']} runs: {cold['mean_duration_ms']:.2f} ms")
    print(f"Cold ingest range: {cold['min_duration_ms']:.2f}-{cold['max_duration_ms']:.2f} ms")
    print(f"Chunks produced: {cold['chunk_count']}")
    print(f"Warm re-ingest (should skip everything): {warm_ms:.2f} ms")


if __name__ == "__main__":
    main()

    