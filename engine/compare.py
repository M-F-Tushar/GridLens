from __future__ import annotations

from datetime import datetime, timezone

from domain.models import ScenarioComparison, ScenarioResult


_KPI_FIELDS = (
    "total_demand_kwh",
    "total_solar_generation_kwh",
    "total_grid_import_kwh",
    "total_grid_export_kwh",
    "total_curtailment_kwh",
    "total_cost",
    "total_emissions_kg",
    "self_consumption_ratio",
    "renewable_fraction",
)



def compare_scenarios(base: ScenarioResult, candidate: ScenarioResult) -> ScenarioComparison:
    kpi_deltas: dict[str, float] = {}
    for field in _KPI_FIELDS:
        base_value = getattr(base.totals, field)
        candidate_value = getattr(candidate.totals, field)
        kpi_deltas[field] = candidate_value - base_value

    narrative_points = _build_narrative(base, candidate, kpi_deltas)

    return ScenarioComparison(
        base_scenario_id=base.scenario_id,
        candidate_scenario_id=candidate.scenario_id,
        kpi_deltas=kpi_deltas,
        narrative_points=narrative_points,
        generated_at=datetime.now(timezone.utc),
    )


def _build_narrative(base: ScenarioResult, candidate: ScenarioResult, deltas: dict[str, float]) -> list[str]:
    points: list[str] = []
    cost_delta = deltas["total_cost"]
    if cost_delta < 0:
        points.append(
            f"'{candidate.scenario_id}' costs {abs(cost_delta):,.2f} less than '{base.scenario_id}'."
        )
    elif cost_delta > 0:
        points.append(
            f"'{candidate.scenario_id}' costs {cost_delta:,.2f} more than '{base.scenario_id}'."
        )
    else:
        points.append(f"'{candidate.scenario_id}' and '{base.scenario_id}' cost the same.")

    emissions_delta = deltas["total_emissions_kg"]
    if abs(emissions_delta) > 1e-9:
        direction = "less" if emissions_delta < 0 else "more"
        points.append(
            f"'{candidate.scenario_id}' emits {abs(emissions_delta):,.2f} kg CO2e {direction} "
            f"than '{base.scenario_id}'."
        )

    renewable_delta_pct = deltas["renewable_fraction"] * 100
    if abs(renewable_delta_pct) > 1e-6:
        direction = "higher" if renewable_delta_pct > 0 else "lower"
        points.append(
            f"Renewable fraction is {abs(renewable_delta_pct):.1f} percentage points {direction} "
            f"in '{candidate.scenario_id}'."
        )

    curtailment_delta = deltas["total_curtailment_kwh"]
    if abs(curtailment_delta) > 1e-6:
        direction = "more" if curtailment_delta > 0 else "less"
        points.append(
            f"'{candidate.scenario_id}' curtails {abs(curtailment_delta):,.1f} kWh {direction} "
            f"solar than '{base.scenario_id}'."
        )

    return points