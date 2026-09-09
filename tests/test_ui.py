from __future__ import annotations

from domain.models import ScenarioRequest
from engine.scenario_engine import run_scenario
from ui.charts import battery_soc_figure, demand_generation_grid_figure, kpi_summary_markdown
from ui.gradio_app import build_app


def test_gradio_app_builds_without_launching():
    demo = build_app()
    assert demo is not None
    assert demo.title == "GridLens"


def test_demand_chart_has_expected_traces():
    result = run_scenario(ScenarioRequest(scenario_id="chart-test", horizon_hours=12))
    fig = demand_generation_grid_figure(result)
    trace_names = {trace.name for trace in fig.data}
    assert {"Demand (kWh)", "Solar generation (kWh)", "Grid import (kWh)", "Grid export (kWh)"} <= trace_names


def test_soc_chart_stays_within_0_100_percent():
    result = run_scenario(ScenarioRequest(scenario_id="soc-test", horizon_hours=24))
    fig = battery_soc_figure(result)
    y_values = fig.data[0].y
    assert all(0 - 1e-6 <= y <= 100 + 1e-6 for y in y_values)


def test_kpi_summary_contains_scenario_id_and_key_numbers():
    result = run_scenario(ScenarioRequest(scenario_id="kpi-test", horizon_hours=24))
    summary = kpi_summary_markdown(result)
    assert "kpi-test" in summary
    assert "Total demand" in summary
    assert "Renewable fraction" in summary