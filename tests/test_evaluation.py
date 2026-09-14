
from __future__ import annotations

from evaluation.eval import load_eval_set, run_evaluation, sweep_similarity_thresholds
from rag.retriever import reset_store_cache


def setup_function(_):
    reset_store_cache()


def test_eval_set_has_a_mix_of_answerable_and_unanswerable_cases():
    eval_set = load_eval_set()
    assert len(eval_set) >= 10
    assert any(case["answerable"] for case in eval_set)
    assert any(not case["answerable"] for case in eval_set)


def test_run_evaluation_achieves_reasonable_retrieval_hit_rate():
    report = run_evaluation()
    assert report.retrieval_hit_rate >= 0.7


def test_run_evaluation_always_produces_citations_for_answerable_cases():
    report = run_evaluation()
    assert report.citation_presence_rate == 1.0


def test_run_evaluation_correctly_rejects_unanswerable_cases_at_default_threshold():
    report = run_evaluation()
    assert report.no_answer_correctness_rate == 1.0


def test_run_evaluation_latency_is_well_under_one_second_per_case():
    report = run_evaluation()
    assert report.mean_latency_ms < 1000


def test_threshold_sweep_shows_the_documented_tradeoff():
    results = sweep_similarity_thresholds([0.05, 0.3])
    loose, strict = results[0.05], results[0.3]
    # The loose threshold retrieves everything (high hit rate) but fails to
    # reject unanswerable questions; the strict threshold does the opposite.
    assert loose["retrieval_hit_rate"] >= strict["retrieval_hit_rate"]
    assert strict["no_answer_correctness_rate"] >= loose["no_answer_correctness_rate"]