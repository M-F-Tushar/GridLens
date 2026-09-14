from __future__ import annotations

import gradio as gr

from domain.models import ForecastMethod, ScenarioRequest
from engine.compare import compare_scenarios
from engine.fixtures import load_tariffs
from engine.forecast import run_forecast
from engine.scenario_engine import run_scenario
from llm.conversation import SessionRegistry
from rag.answer import answer_question
from ui.charts import (
    battery_soc_figure,
    citations_markdown,
    comparison_table_markdown,
    demand_generation_grid_figure,
    forecast_figure,
    kpi_summary_markdown,
    warnings_markdown,
)

_SESSIONS = SessionRegistry()


def _run(
    scenario_id: str,
    horizon_hours: int,
    battery_capacity_kwh: float,
    battery_power_kw: float,
    solar_capacity_kwp: float,
    tariff_id: str,
    allow_export: bool,
):
    if not scenario_id or not scenario_id.strip():
        raise gr.Error("scenario_id must not be blank")
    request = ScenarioRequest(
        scenario_id=scenario_id.strip(),
        horizon_hours=int(horizon_hours),
        battery_capacity_kwh=float(battery_capacity_kwh),
        battery_power_kw=float(battery_power_kw),
        solar_capacity_kwp=float(solar_capacity_kwp),
        tariff_id=tariff_id,
        allow_export=allow_export,
    )
    result = run_scenario(request)
    session = _SESSIONS.get_or_create("default")
    session.remember_scenario(result)
    return (
        demand_generation_grid_figure(result),
        battery_soc_figure(result),
        kpi_summary_markdown(result),
        warnings_markdown(result),
    )


def _forecast(
    site: str,
    horizon_hours: int,
    method: str,
    as_of_hour_index: int = 0,
):
    result = run_forecast(
        site=site,
        horizon_hours=int(horizon_hours),
        method=ForecastMethod(method),
        as_of_hour_index=int(as_of_hour_index),
    )
    status = f"Forecast generated: {len(result.points)} hours using {result.method.value}"
    return forecast_figure(result), status


def _compare(
    base_id: str,
    candidate_id: str,
    battery_capacity_diff: float = 0.0,
):
    base_result = run_scenario(ScenarioRequest(scenario_id=base_id, horizon_hours=24))
    candidate_result = run_scenario(
        ScenarioRequest(
            scenario_id=candidate_id,
            horizon_hours=24,
            battery_capacity_kwh=max(0.0, 200.0 + float(battery_capacity_diff)),
        )
    )
    comparison = compare_scenarios(base_result, candidate_result)
    return comparison_table_markdown(comparison)


def _ask(question: str):
    session = _SESSIONS.get_or_create("default")
    result = answer_question(question=question, scenario_result=session.last_scenario)
    return result.answer, citations_markdown(result.citations)


def build_app() -> gr.Blocks:
    tariff_ids = sorted(load_tariffs().keys())
    with gr.Blocks(title="GridLens") as demo:
        gr.Markdown("# GridLens — Energy-System Scenario Explorer")
        gr.Markdown(
            "Configure a scenario, forecast demand/solar, compare options, and ask questions. "
            "Everything below runs fully offline against local fixture data; no API key is required."
        )

        with gr.Tabs():
            with gr.TabItem("Scenario"):
                with gr.Row():
                    with gr.Column(scale=1):
                        scenario_id = gr.Textbox(label="Scenario ID", value="baseline")
                        horizon_hours = gr.Slider(1, 168, value=24, step=1, label="Horizon (hours)")
                        battery_capacity_kwh = gr.Slider(0, 1000, value=200, step=10, label="Battery capacity (kWh)")
                        battery_power_kw = gr.Slider(0, 500, value=50, step=5, label="Battery power (kW)")
                        solar_capacity_kwp = gr.Slider(0, 1000, value=150, step=10, label="Solar capacity (kWp)")
                        tariff_id = gr.Dropdown(choices=tariff_ids, value=tariff_ids[0], label="Tariff")
                        allow_export = gr.Checkbox(value=True, label="Allow grid export")
                        run_button = gr.Button("Run scenario", variant="primary")
                    with gr.Column(scale=2):
                        kpi_output = gr.Markdown(label="KPI summary")
                        warnings_output = gr.Markdown(label="Warnings")
                        demand_chart = gr.Plot(label="Demand / generation / grid")
                        soc_chart = gr.Plot(label="Battery state of charge")

                run_button.click(
                    fn=_run,
                    inputs=[
                        scenario_id, horizon_hours, battery_capacity_kwh,
                        battery_power_kw, solar_capacity_kwp, tariff_id, allow_export,
                    ],
                    outputs=[demand_chart, soc_chart, kpi_output, warnings_output],
                )

            with gr.TabItem("Forecast"):
                with gr.Row():
                    with gr.Column(scale=1):
                        fc_site = gr.Textbox(label="Site", value="campus-microgrid-a")
                        fc_horizon = gr.Slider(1, 168, value=48, step=1, label="Forecast horizon (hours)")
                        fc_method = gr.Dropdown(
                            choices=[m.value for m in ForecastMethod],
                            value=ForecastMethod.SEASONAL_NAIVE.value,
                            label="Method",
                        )
                        fc_as_of = gr.Number(value=0, label="As of hour index")
                        fc_button = gr.Button("Generate forecast", variant="primary")
                    with gr.Column(scale=2):
                        fc_status = gr.Markdown()
                        fc_chart = gr.Plot(label="Forecasted demand & solar")

                fc_button.click(
                    fn=_forecast,
                    inputs=[fc_site, fc_horizon, fc_method, fc_as_of],
                    outputs=[fc_chart, fc_status],
                )

            with gr.TabItem("Compare"):
                with gr.Row():
                    with gr.Column(scale=1):
                        cmp_base = gr.Textbox(label="Base Scenario ID", value="no-battery")
                        cmp_cand = gr.Textbox(label="Candidate Scenario ID", value="with-battery")
                        cmp_diff = gr.Slider(-200, 800, value=300, step=50, label="Battery Capacity Delta (kWh)")
                        cmp_button = gr.Button("Compare scenarios", variant="primary")
                    with gr.Column(scale=2):
                        cmp_output = gr.Markdown()

                cmp_button.click(
                    fn=_compare,
                    inputs=[cmp_base, cmp_cand, cmp_diff],
                    outputs=[cmp_output],
                )

            with gr.TabItem("Ask GridLens"):
                with gr.Row():
                    with gr.Column(scale=1):
                        ask_input = gr.Textbox(
                            label="Question",
                            value="How is battery round-trip efficiency modeled?",
                            lines=3,
                        )
                        ask_button = gr.Button("Ask", variant="primary")
                    with gr.Column(scale=2):
                        ask_answer = gr.Markdown(label="Answer")
                        ask_sources = gr.Markdown(label="Citations & Sources")

                ask_button.click(
                    fn=_ask,
                    inputs=[ask_input],
                    outputs=[ask_answer, ask_sources],
                )

    return demo


def main() -> None:
    build_app().launch()


if __name__ == "__main__":
    main()