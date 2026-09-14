from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

from llm.provider import estimate_tokens
from rag.answer import answer_question
from rag.retriever import DEFAULT_TOP_K, retrieve

EVAL_SET_PATH = Path(__file__).resolve().parent / "eval_set.json"

# Chosen from an empirical threshold sweep (see learning.md): 0.05 (the
# system's blanket default) over-retrieves for off-topic questions, while
# 0.3 correctly rejects every "no answer" case in the eval set at the cost
# of two on-topic misses. This is the real, measured tradeoff of the
# hash-embedding retrieval baseline — not a claim that it is perfect.
EVAL_SIMILARITY_THRESHOLD = 0.3


@dataclass
class EvalCaseResult:
    case_id: str
    question: str
    answerable: bool
    retrieved_doc_ids: list[str]
    hit: bool
    reciprocal_rank: float
    citation_present: bool
    insufficient_evidence: bool
    no_answer_correct: bool
    latency_ms: float
    prompt_tokens_estimate: int


@dataclass
class EvalReport:
    cases: list[EvalCaseResult] = field(default_factory=list)

    @property
    def retrieval_hit_rate(self) -> float:
        answerable = [c for c in self.cases if c.answerable]
        if not answerable:
            return 0.0
        return sum(c.hit for c in answerable) / len(answerable)

    @property
    def mean_reciprocal_rank(self) -> float:
        answerable = [c for c in self.cases if c.answerable]
        if not answerable:
            return 0.0
        return sum(c.reciprocal_rank for c in answerable) / len(answerable)

    @property
    def citation_presence_rate(self) -> float:
        answerable = [c for c in self.cases if c.answerable]
        if not answerable:
            return 0.0
        return sum(c.citation_present for c in answerable) / len(answerable)

    @property
    def no_answer_correctness_rate(self) -> float:
        unanswerable = [c for c in self.cases if not c.answerable]
        if not unanswerable:
            return 0.0
        return sum(c.no_answer_correct for c in unanswerable) / len(unanswerable)

    @property
    def mean_latency_ms(self) -> float:
        if not self.cases:
            return 0.0
        return sum(c.latency_ms for c in self.cases) / len(self.cases)

    def as_dict(self) -> dict:
        return {
            "retrieval_hit_rate": round(self.retrieval_hit_rate, 4),
            "mean_reciprocal_rank": round(self.mean_reciprocal_rank, 4),
            "citation_presence_rate": round(self.citation_presence_rate, 4),
            "no_answer_correctness_rate": round(self.no_answer_correctness_rate, 4),
            "mean_latency_ms": round(self.mean_latency_ms, 3),
            "case_count": len(self.cases),
        }


def load_eval_set(path: Path | str = EVAL_SET_PATH) -> list[dict]:
    return json.loads(Path(path).read_text())


def _reciprocal_rank(expected_doc_ids: list[str], retrieved_doc_ids: list[str]) -> float:
    for rank, doc_id in enumerate(retrieved_doc_ids, start=1):
        if doc_id in expected_doc_ids:
            return 1.0 / rank
    return 0.0


def run_evaluation(
    eval_set: list[dict] | None = None,
    similarity_threshold: float = EVAL_SIMILARITY_THRESHOLD,
    top_k: int = DEFAULT_TOP_K,
) -> EvalReport:
    eval_set = eval_set if eval_set is not None else load_eval_set()
    report = EvalReport()

    for case in eval_set:
        start = time.perf_counter()
        search_results = retrieve(case["question"], top_k=top_k, similarity_threshold=similarity_threshold)
        retrieved_doc_ids = [r.chunk.doc_id for r in search_results]

        answer = answer_question(
            case["question"], top_k=top_k, similarity_threshold=similarity_threshold
        )
        latency_ms = (time.perf_counter() - start) * 1000

        hit = any(doc_id in case["expected_doc_ids"] for doc_id in retrieved_doc_ids)
        reciprocal_rank = _reciprocal_rank(case["expected_doc_ids"], retrieved_doc_ids)
        no_answer_correct = (not case["answerable"]) == answer.insufficient_evidence

        report.cases.append(
            EvalCaseResult(
                case_id=case["id"],
                question=case["question"],
                answerable=case["answerable"],
                retrieved_doc_ids=retrieved_doc_ids,
                hit=hit,
                reciprocal_rank=reciprocal_rank,
                citation_present=len(answer.citations) > 0,
                insufficient_evidence=answer.insufficient_evidence,
                no_answer_correct=no_answer_correct,
                latency_ms=latency_ms,
                prompt_tokens_estimate=estimate_tokens(case["question"]),
            )
        )

    return report


def sweep_similarity_thresholds(thresholds: list[float] | None = None) -> dict[float, dict]:
    """Reproduces the threshold sweep referenced in the module docstring."""
    thresholds = thresholds or [0.05, 0.15, 0.3]
    eval_set = load_eval_set()
    return {threshold: run_evaluation(eval_set, similarity_threshold=threshold).as_dict() for threshold in thresholds}


def main() -> None:
    report = run_evaluation()
    print("=== GridLens retrieval & answer-quality evaluation ===")
    print(json.dumps(report.as_dict(), indent=2))
    print("\n=== Similarity-threshold sweep ===")
    for threshold, metrics in sweep_similarity_thresholds().items():
        print(f"threshold={threshold}: {metrics}")


if __name__ == "__main__":
    main()