"""Unit tests for the deterministic scenario engine.

These are the Day 1 gate: they must pass with zero network access and zero
secrets configured.
"""
from __future__ import annotations

import copy

import pytest

from domain.models import ScenarioRequest
from engine.scenario_engine import run_scenario


def make_request(**overrides) -> ScenarioRequest:
    base = dict(scenario_id="test-scenario", horizon_hours=48)
    base.update(overrides)
    return ScenarioRequest(**base)


def test_energy_balance_holds_every_hour():
    result = run_scenario(make_request())
    for record in result.records:
        assert abs(record.energy_balance_error_kwh) < 1e-6, record
    assert result.diagnostics.max_abs_energy_balance_error_kwh < 1e-6
    assert result.diagnostics.total_violation_count == 0


def test_battery_never_exceeds_capacity_or_goes_negative():
    request = make_request(battery_capacity_kwh=100.0, battery_power_kw=500.0, horizon_hours=72)
    result = run_scenario(request)
    for record in result.records:
        assert -1e-9 <= record.soc_kwh <= request.battery_capacity_kwh + 1e-9
        assert 0.0 <= record.soc_fraction <= 1.0 + 1e-9


def test_zero_storage_scenario_has_no_battery_activity():
    request = make_request(battery_capacity_kwh=0.0, battery_power_kw=0.0, initial_soc_fraction=0.0)
    result = run_scenario(request)
    for record in result.records:
        assert record.battery_charge_kwh == 0.0
        assert record.battery_discharge_kwh == 0.0
        assert record.soc_kwh == 0.0
    # With no storage, all solar not immediately used must be exported or curtailed.
    for record in result.records:
        surplus = record.solar_generation_kwh - record.demand_kwh
        if surplus > 0:
            assert record.grid_export_kwh + record.curtailment_kwh == pytest.approx(surplus, abs=1e-6)


def test_zero_renewable_scenario_covers_all_demand_from_grid_or_battery():
    request = make_request(solar_capacity_kwp=0.0)
    result = run_scenario(request)
    for record in result.records:
        assert record.solar_generation_kwh == 0.0
        assert record.grid_export_kwh == 0.0
        assert record.curtailment_kwh == 0.0
        covered = record.grid_import_kwh + record.battery_discharge_kwh
        assert covered == pytest.approx(record.demand_kwh, abs=1e-6)


def test_tariff_changes_total_cost():
    flat_result = run_scenario(make_request(tariff_id="flat-standard"))
    tou_result = run_scenario(make_request(tariff_id="time-of-use-a"))
    assert flat_result.totals.total_cost != tou_result.totals.total_cost


def test_emissions_scale_with_grid_import():
    no_solar = run_scenario(make_request(solar_capacity_kwp=0.0))
    with_solar = run_scenario(make_request(solar_capacity_kwp=300.0))
    assert with_solar.totals.total_emissions_kg <= no_solar.totals.total_emissions_kg


def test_invalid_input_is_rejected_by_validation():
    with pytest.raises(Exception):
        make_request(horizon_hours=0)
    with pytest.raises(Exception):
        make_request(horizon_hours=1000)
    with pytest.raises(Exception):
        make_request(battery_round_trip_efficiency=0.0)
    with pytest.raises(Exception):
        make_request(scenario_id="   ")


def test_unknown_tariff_raises_value_error():
    with pytest.raises(KeyError):
        run_scenario(make_request(tariff_id="does-not-exist"))


def test_reproducibility_same_input_same_output():
    request = make_request()
    result_a = run_scenario(copy.deepcopy(request))
    result_b = run_scenario(copy.deepcopy(request))
    dump_a = result_a.model_dump(exclude={"generated_at"})
    dump_b = result_b.model_dump(exclude={"generated_at"})
    assert dump_a == dump_b