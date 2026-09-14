"""Chart-building helpers, kept separate from ``ui/gradio_app.py`` so they can
be unit-tested without importing or launching Gradio itself.
"""
from __future__ import annotations

import plotly.graph_objects as go

from domain.models import ForecastResult, ScenarioComparison, ScenarioResult


def demand_generation_grid_figure(result: ScenarioResult) -> go.Figure:
    hours = [r.hour_index for r in result.records]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hours, y=[r.demand_kwh for r in result.records], name="Demand (kWh)", mode="lines"))
    fig.add_trace(go.Scatter(x=hours, y=[r.solar_generation_kwh for r in result.records], name="Solar generation (kWh)", mode="lines"))
    fig.add_trace(go.Bar(x=hours, y=[r.grid_import_kwh for r in result.records], name="Grid import (kWh)"))
    fig.add_trace(go.Bar(x=hours, y=[-r.grid_export_kwh for r in result.records], name="Grid export (kWh)"))
    fig.update_layout(
        title="Demand, solar generation and grid exchange",
        xaxis_title="Hour",
        yaxis_title="kWh",
        barmode="relative",
        legend=dict(orientation="h"),
    )
    return fig


def battery_soc_figure(result: ScenarioResult) -> go.Figure:
    hours = [r.hour_index for r in result.records]
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=hours,
            y=[r.soc_fraction * 100 for r in result.records],
            name="State of charge (%)",
            mode="lines",
            fill="tozeroy",
        )
    )
    fig.update_layout(
        title="Battery state of charge",
        xaxis_title="Hour",
        yaxis_title="SoC (%)",
        yaxis_range=[0, 100],
    )
    return fig


def kpi_summary_markdown(result: ScenarioResult) -> str:
    t = result.totals
    d = result.diagnostics
    return (
        f"**Scenario:** `{result.scenario_id}`  \n"
        f"**Total demand:** {t.total_demand_kwh:,.1f} kWh &nbsp;|&nbsp; "
        f"**Total solar:** {t.total_solar_generation_kwh:,.1f} kWh  \n"
        f"**Grid import:** {t.total_grid_import_kwh:,.1f} kWh &nbsp;|&nbsp; "
        f"**Grid export:** {t.total_grid_export_kwh:,.1f} kWh &nbsp;|&nbsp; "
        f"**Curtailed:** {t.total_curtailment_kwh:,.1f} kWh  \n"
        f"**Cost:** {t.total_cost:,.2f} &nbsp;|&nbsp; "
        f"**Emissions:** {t.total_emissions_kg:,.2f} kg CO2e  \n"
        f"**Self-consumption ratio:** {t.self_consumption_ratio:.0%} &nbsp;|&nbsp; "
        f"**Renewable fraction:** {t.renewable_fraction:.0%}  \n"
        f"**Diagnostics:** max energy-balance error "
        f"{d.max_abs_energy_balance_error_kwh:.6f} kWh, "
        f"{d.total_violation_count} violation(s), engine v{d.engine_version}"
    )


def forecast_figure(result: ForecastResult) -> go.Figure:
    hours = [p.hour_index for p in result.points]
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=hours,
            y=[p.predicted_demand_kwh for p in result.points],
            name="Predicted demand (kWh)",
            mode="lines",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=hours,
            y=[p.predicted_solar_generation_kwh for p in result.points],
            name="Predicted solar generation (kWh)",
            mode="lines",
        )
    )
    fig.update_layout(
        title="Forecast",
        xaxis_title="Hour",
        yaxis_title="kWh",
        legend=dict(orientation="h"),
    )
    return fig


def warnings_markdown(result: ScenarioResult) -> str:
    violations: list[str] = []
    for r in result.records:
        if r.violations:
            violations.extend(f"Hour {r.hour_index}: {v}" for v in r.violations)
    if not violations:
        return "No constraint violations detected."
    return "### Warnings & Constraint Violations\n" + "\n".join(f"- {v}" for v in violations)


def comparison_table_markdown(comparison: ScenarioComparison) -> str:
    lines = [
        f"### Scenario Comparison: `{comparison.base_scenario_id}` vs `{comparison.candidate_scenario_id}`",
        "",
        "| Metric | Delta (candidate - base) |",
        "|---|---|",
    ]
    for k, v in comparison.kpi_deltas.items():
        lines.append(f"| {k} | {v:+.4f} |")
    if comparison.narrative_points:
        lines.append("")
        lines.append("### Key Takeaways")
        for point in comparison.narrative_points:
            lines.append(f"- {point}")
    return "\n".join(lines)


def citations_markdown(citations: list) -> str:
    if not citations:
        return "No citations available."
    lines = ["### Citations & Supporting Evidence"]
    for c in citations:
        chunk_id = getattr(c, "chunk_id", "")
        title = getattr(c, "title", "")
        snippet = getattr(c, "snippet", "")
        lines.append(f"- **[{chunk_id}] {title}**: {snippet}")
    return "\n".join(lines)