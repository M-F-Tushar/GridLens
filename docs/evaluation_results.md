# GridLens — Evaluation & Verification Results

This document summarizes the empirical evaluation benchmarks for GridLens' deterministic retrieval-augmented generation (RAG) system and simulation engine.

---

## 1. Test Suite Verification

GridLens includes 111 automated tests covering the deterministic calculation engine, scenario comparison deltas, baseline forecasting, vector storage, citation extraction, API endpoints, structured logging, and Gradio UI components.

To run the complete test suite:
```bash
python -m pytest -q
```

Expected result:
```text
111 passed in ~5s
```

---

## 2. RAG Evaluation Benchmark

The evaluation harness in [`evaluation/eval.py`](../evaluation/eval.py) executes against the 12-question benchmark suite in [`evaluation/eval_set.json`](../evaluation/eval_set.json).

To run the benchmark:
```bash
python -m evaluation.eval
```

### Benchmark Metrics (at default threshold = 0.30)

| Metric | Target | Measured Result | Status |
|---|---|---|---|
| **Retrieval Hit Rate** | $\ge 0.70$ | `0.8000` (80%) | PASS |
| **Mean Reciprocal Rank (MRR)** | $\ge 0.70$ | `0.8000` | PASS |
| **Citation Presence Rate** | $1.00$ | `1.0000` (100%) | PASS |
| **No-Answer Correctness Rate** | $1.00$ | `1.0000` (100%) | PASS |
| **Mean Latency** | $< 1000\text{ ms}$ | `~3 ms` | PASS |

---

## 3. Threshold Tradeoff Analysis

Because GridLens uses dependency-free 256-bucket hash embeddings, random word overlap routinely yields similarity scores between 0.10 and 0.28. 

An empirical threshold sweep reveals the following operational tradeoff:

```text
Threshold = 0.05:
  - Retrieval hit rate: 1.00 (100%)
  - No-answer correctness: 0.00 (0% — fails to abstain on unanswerable questions)

Threshold = 0.15:
  - Retrieval hit rate: 1.00 (100%)
  - No-answer correctness: 0.00 (0% — fails to abstain on unanswerable questions)

Threshold = 0.30 (Default):
  - Retrieval hit rate: 0.80 (80%)
  - No-answer correctness: 1.00 (100% — reliably triggers honest abstention)
```

By enforcing `similarity_threshold = 0.30` as the default in `domain/models.py` and `rag/retriever.py`, GridLens prioritizes grounding and honest abstention over permissive over-retrieval.
