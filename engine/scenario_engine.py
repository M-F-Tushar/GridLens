"""Deterministic hour-by-hour dispatch simulation.

Physical model (kept intentionally simple and explicit so it is easy to test
and to explain):

Each hour, unconstrained solar potential is scaled by installed capacity and
a derating factor to get ``solar_generation_kwh``. Net load is then

    net = demand_kwh - solar_generation_kwh

* If ``net > 0`` (solar does not cover demand): the battery discharges up to
  its power limit and available state of charge to cover as much of the
  deficit as possible; any remainder is imported from the grid.
* If ``net < 0`` (solar exceeds demand): the battery charges up to its power
  limit and remaining headroom; any remainder is exported to the grid, or
  curtailed if ``allow_export`` is False.

Round-trip efficiency is applied on the *charge* side only: ``battery_charge_kwh``
is the energy drawn from the bus to charge the battery, and only
``battery_charge_kwh * sqrt(efficiency)`` of it actually lands in the state of
charge; the remainder, ``battery_loss_kwh``, is dissipated as heat. Because
``battery_charge_kwh`` already represents *all* of the energy removed from the
bus (whether it is ultimately stored or lost), the hourly bus-level energy
balance does not need a separate loss term:

    solar_generation + grid_import + battery_discharge
        == demand + battery_charge + grid_export + curtailment

``battery_loss_kwh`` is still tracked and returned for diagnostics/reporting,
it is simply not an additional term in the balance check above.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone

from domain.models import Diagnostics, HourlyRecord, ScenarioRequest, ScenarioResult, Totals
from engine.fixtures import export_credit_for_tariff, load_site_rows, tariff_rate_for_hour

ENGINE_VERSION = "1.0.0"
_BALANCE_EPSILON_KWH = 1e-6


def run_scenario(request: ScenarioRequest) -> ScenarioResult:
    """Run a full scenario deterministically. Same input -> same output, always."""
    rows = load_site_rows(request.site)
    if not rows:
        raise ValueError(f"No fixture data available for site {request.site!r}")

    soc_kwh = request.initial_soc_fraction * request.battery_capacity_kwh
    charge_efficiency = math.sqrt(request.battery_round_trip_efficiency)

    records: list[HourlyRecord] = []
    total_violation_count = 0
    max_abs_balance_error = 0.0

    for hour_index in range(request.horizon_hours):
        row = rows[hour_index % len(rows)]
        hour_of_day = row.timestamp.hour

        demand_kwh = row.demand_kwh
        solar_generation_kwh = (
            row.solar_potential_kwh_per_kwp * request.solar_capacity_kwp * request.solar_derate
        )

        battery_charge_kwh = 0.0
        battery_discharge_kwh = 0.0
        grid_import_kwh = 0.0
        grid_export_kwh = 0.0
        curtailment_kwh = 0.0
        violations: list[str] = []

        net = demand_kwh - solar_generation_kwh

        if net > 0:
            deficit = net
            max_discharge_by_power = request.battery_power_kw
            max_discharge_by_soc = soc_kwh
            battery_discharge_kwh = min(deficit, max_discharge_by_power, max_discharge_by_soc)
            battery_discharge_kwh = max(0.0, battery_discharge_kwh)
            soc_kwh -= battery_discharge_kwh
            grid_import_kwh = deficit - battery_discharge_kwh
        else:
            surplus = -net
            max_charge_by_power = request.battery_power_kw
            headroom_kwh = request.battery_capacity_kwh - soc_kwh
            max_charge_by_headroom = headroom_kwh / charge_efficiency if charge_efficiency > 0 else 0.0
            battery_charge_kwh = min(surplus, max_charge_by_power, max_charge_by_headroom)
            battery_charge_kwh = max(0.0, battery_charge_kwh)
            stored_kwh = battery_charge_kwh * charge_efficiency
            soc_kwh += stored_kwh
            remainder = surplus - battery_charge_kwh
            if request.allow_export:
                grid_export_kwh = remainder
            else:
                curtailment_kwh = remainder

        soc_kwh = min(max(soc_kwh, 0.0), request.battery_capacity_kwh)
        soc_fraction = (
            soc_kwh / request.battery_capacity_kwh if request.battery_capacity_kwh > 0 else 0.0
        )

        battery_loss_kwh = battery_charge_kwh * (1 - charge_efficiency)

        balance_error = (
            (solar_generation_kwh + grid_import_kwh + battery_discharge_kwh)
            - (demand_kwh + battery_charge_kwh + grid_export_kwh + curtailment_kwh)
        )
        if abs(balance_error) > max_abs_balance_error:
            max_abs_balance_error = abs(balance_error)
        if abs(balance_error) > 1e-6:
            violations.append(f"energy_balance_error={balance_error:.6f}kwh")

        if soc_fraction < -1e-9 or soc_fraction > 1 + 1e-9:
            violations.append(f"soc_out_of_bounds={soc_fraction:.6f}")

        tariff_rate = tariff_rate_for_hour(request.tariff_id, hour_of_day)
        export_credit = export_credit_for_tariff(request.tariff_id)
        cost = grid_import_kwh * tariff_rate - grid_export_kwh * export_credit
        emissions_kg = grid_import_kwh * row.carbon_intensity_g_per_kwh / 1000.0

        total_violation_count += len(violations)

        records.append(
            HourlyRecord(
                timestamp=row.timestamp,
                hour_index=hour_index,
                demand_kwh=demand_kwh,
                solar_generation_kwh=solar_generation_kwh,
                battery_charge_kwh=battery_charge_kwh,
                battery_discharge_kwh=battery_discharge_kwh,
                battery_loss_kwh=battery_loss_kwh,
                soc_kwh=soc_kwh,
                soc_fraction=soc_fraction,
                grid_import_kwh=grid_import_kwh,
                grid_export_kwh=grid_export_kwh,
                curtailment_kwh=curtailment_kwh,
                tariff_rate_per_kwh=tariff_rate,
                cost=cost,
                carbon_intensity_g_per_kwh=row.carbon_intensity_g_per_kwh,
                emissions_kg=emissions_kg,
                energy_balance_error_kwh=balance_error,
                violations=violations,
            )
        )

    totals = _totals_from_records(records)
    diagnostics = Diagnostics(
        max_abs_energy_balance_error_kwh=max_abs_balance_error,
        total_violation_count=total_violation_count,
        engine_version=ENGINE_VERSION,
    )
    return ScenarioResult(
        scenario_id=request.scenario_id,
        request=request,
        records=records,
        totals=totals,
        diagnostics=diagnostics,
        generated_at=datetime.now(timezone.utc),
    )


def _totals_from_records(records: list[HourlyRecord]) -> Totals:
    total_demand = sum(r.demand_kwh for r in records)
    total_solar = sum(r.solar_generation_kwh for r in records)
    total_import = sum(r.grid_import_kwh for r in records)
    total_export = sum(r.grid_export_kwh for r in records)
    total_curtailment = sum(r.curtailment_kwh for r in records)
    total_cost = sum(r.cost for r in records)
    total_emissions = sum(r.emissions_kg for r in records)

    solar_self_consumed = max(0.0, total_solar - total_export - total_curtailment)
    self_consumption_ratio = (solar_self_consumed / total_solar) if total_solar > 0 else 0.0

    demand_met_by_renewables = max(0.0, total_demand - total_import)
    renewable_fraction = (demand_met_by_renewables / total_demand) if total_demand > 0 else 0.0

    return Totals(
        total_demand_kwh=total_demand,
        total_solar_generation_kwh=total_solar,
        total_grid_import_kwh=total_import,
        total_grid_export_kwh=total_export,
        total_curtailment_kwh=total_curtailment,
        total_cost=total_cost,
        total_emissions_kg=total_emissions,
        self_consumption_ratio=min(1.0, self_consumption_ratio),
        renewable_fraction=min(1.0, renewable_fraction),
    )