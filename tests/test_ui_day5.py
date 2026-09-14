
from __future__ import annotations

from domain.models import ForecastMethod, ScenarioRequest
from engine.compare import compare_scenarios
from engine.forecast import run_forecast
from engine.scenario_engine import run_scenario
from rag.retriever import reset_store_cache
from ui.charts import (
    citations_markdown,
    comparison_table_markdown,
    forecast_figure,
    warnings_markdown,
)
from ui.gradio_app import _ask, _compare, _forecast, _run


def test_forecast_figure_has_demand_and_solar_traces():
    result = run_forecast(site="campus-microgrid-a", horizon_hours=24, method=ForecastMethod.SEASONAL_NAIVE)
    fig = forecast_figure(result)
    trace_names = {trace.name for trace in fig.data}
    assert {"Predicted demand (kWh)", "Predicted solar generation (kWh)"} <= trace_names


def test_warnings_markdown_reports_no_violations_for_clean_scenario():
    result = run_scenario(ScenarioRequest(scenario_id="clean-scenario", horizon_hours=24))
    assert "No constraint violations" in warnings_markdown(result)


def test_comparison_table_markdown_includes_deltas_and_narrative():
    base = run_scenario(ScenarioRequest(scenario_id="ui-base", horizon_hours=24))
    candidate = run_scenario(ScenarioRequest(scenario_id="ui-candidate", horizon_hours=24, solar_capacity_kwp=0))
    comparison = compare_scenarios(base, candidate)
    table = comparison_table_markdown(comparison)
    assert "ui-base" in table
    assert "ui-candidate" in table
    assert "total_cost" in table


def test_citations_markdown_handles_empty_list():
    assert "No citations" in citations_markdown([])


def test_gradio_run_callback_returns_charts_kpis_and_warnings():
    demand_fig, soc_fig, kpi_md, warnings_md = _run(
        "gr-run-test", 24, 200.0, 50.0, 150.0, "flat-standard", True
    )
    assert demand_fig is not None
    assert soc_fig is not None
    assert "gr-run-test" in kpi_md
    assert isinstance(warnings_md, str)


def test_gradio_forecast_callback_returns_chart_and_status():
    fig, status = _forecast("campus-microgrid-a", 24, ForecastMethod.SEASONAL_NAIVE.value, 0)
    assert fig is not None
    assert "24" in status


def test_gradio_compare_callback_returns_markdown_table():
    table = _compare("cmp-base", "cmp-candidate", 0)
    assert "cmp-base" in table
    assert "cmp-candidate" in table


def test_gradio_ask_callback_returns_answer_and_sources():
    reset_store_cache()
    answer, sources = _ask("How is battery efficiency modeled?")
    assert isinstance(answer, str) and answer
    assert isinstance(sources, str) and sources