"""Tests for rag/answer.py: the explanation service.

Covers the core rules from the project plan: citations are required for
evidence-backed claims, no invented numbers, insufficient-evidence handling,
and fully offline operation via the local deterministic provider.
"""
from __future__ import annotations

from domain.models import ScenarioRequest
from engine.compare import compare_scenarios
from engine.scenario_engine import run_scenario
from rag.answer import INSUFFICIENT_EVIDENCE_MESSAGE, answer_question
from rag.retriever import reset_store_cache


def make_request(**overrides) -> ScenarioRequest:
    base = dict(scenario_id="test-scenario", horizon_hours=24)
    base.update(overrides)
    return ScenarioRequest(**base)


def test_answer_question_returns_insufficient_evidence_when_nothing_matches():
    reset_store_cache()
    result = answer_question("zzz gibberish query", top_k=3, similarity_threshold=0.999)
    assert result.insufficient_evidence is True
    assert result.answer == INSUFFICIENT_EVIDENCE_MESSAGE
    assert result.citations == []
    assert result.provider == "none"


def test_answer_question_returns_citations_for_knowledge_base_question():
    reset_store_cache()
    result = answer_question("How is the tariff applied?", top_k=3, similarity_threshold=0.0)
    assert result.insufficient_evidence is False
    assert len(result.citations) > 0
    for citation in result.citations:
        assert f"[{citation.chunk_id}]" in result.answer


def test_answer_question_only_uses_numbers_from_scenario_result():
    reset_store_cache()
    scenario_result = run_scenario(make_request())
    result = answer_question(
        "What was the total cost and total emissions?",
        scenario_result=scenario_result,
        top_k=0,
        similarity_threshold=0.99,
    )
    assert f"{scenario_result.totals.total_cost:.2f}" in result.answer
    assert f"{scenario_result.totals.total_emissions_kg:.2f}" in result.answer


def test_answer_question_only_uses_numbers_from_comparison():
    reset_store_cache()
    base_result = run_scenario(make_request(scenario_id="base"))
    candidate_result = run_scenario(make_request(scenario_id="candidate", solar_capacity_kwp=0))
    comparison = compare_scenarios(base_result, candidate_result)

    result = answer_question(
        "How does removing solar change the cost?",
        comparison=comparison,
        top_k=0,
        similarity_threshold=0.99,
    )
    assert result.insufficient_evidence is False
    delta_cost = comparison.kpi_deltas["total_cost"]
    assert f"{delta_cost:.4f}" in result.answer


def test_answer_question_default_provider_is_local_and_offline():
    reset_store_cache()
    result = answer_question("What are the system limitations?", top_k=2, similarity_threshold=0.0)
    assert result.provider == "local-deterministic"