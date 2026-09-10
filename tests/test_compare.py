"""Tests for the deterministic scenario comparison."""
from __future__ import annotations

from domain.models import ScenarioRequest
from engine.compare import compare_scenarios
from engine.scenario_engine import run_scenario


def test_compare_scenarios_deltas_match_manual_subtraction():
    base = run_scenario(ScenarioRequest(scenario_id="base", battery_capacity_kwh=0, battery_power_kw=0))
    candidate = run_scenario(ScenarioRequest(scenario_id="candidate", battery_capacity_kwh=500, battery_power_kw=200))

    comparison = compare_scenarios(base, candidate)

    assert comparison.base_scenario_id == "base"
    assert comparison.candidate_scenario_id == "candidate"
    assert comparison.kpi_deltas["total_cost"] == candidate.totals.total_cost - base.totals.total_cost
    assert (
        comparison.kpi_deltas["total_emissions_kg"]
        == candidate.totals.total_emissions_kg - base.totals.total_emissions_kg
    )
    # A bigger battery should not increase emissions in this fixture setup.
    assert comparison.kpi_deltas["total_emissions_kg"] <= 0


def test_compare_scenarios_produces_narrative_points():
    base = run_scenario(ScenarioRequest(scenario_id="base"))
    candidate = run_scenario(ScenarioRequest(scenario_id="candidate", solar_capacity_kwp=0))
    comparison = compare_scenarios(base, candidate)
    assert len(comparison.narrative_points) > 0
    assert all(isinstance(p, str) for p in comparison.narrative_points)


def test_compare_identical_scenarios_has_zero_deltas():
    a = run_scenario(ScenarioRequest(scenario_id="same-a"))
    b = run_scenario(ScenarioRequest(scenario_id="same-b"))
    comparison = compare_scenarios(a, b)
    assert all(abs(v) < 1e-9 for v in comparison.kpi_deltas.values())