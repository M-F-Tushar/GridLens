
from __future__ import annotations

import gradio as gr

from domain.models import ScenarioRequest
from engine.fixtures import load_tariffs
from engine.scenario_engine import run_scenario
from llm.conversation import SessionRegistry
from ui.charts import battery_soc_figure, demand_generation_grid_figure, kpi_summary_markdown

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
    )


def build_app() -> gr.Blocks:
    tariff_ids = sorted(load_tariffs().keys())
    with gr.Blocks(title="GridLens") as demo:
        gr.Markdown("# GridLens — Energy-System Scenario Explorer")
        gr.Markdown(
            "Configure a scenario and run it. Everything below runs fully "
            "offline against local fixture data; no API key is required."
        )
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
                demand_chart = gr.Plot(label="Demand / generation / grid")
                soc_chart = gr.Plot(label="Battery state of charge")

        run_button.click(
            fn=_run,
            inputs=[
                scenario_id, horizon_hours, battery_capacity_kwh,
                battery_power_kw, solar_capacity_kwp, tariff_id, allow_export,
            ],
            outputs=[demand_chart, soc_chart, kpi_output],
        )
    return demo


def main() -> None:
    build_app().launch()


if __name__ == "__main__":
    main()