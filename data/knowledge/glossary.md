---
doc_id: kb-glossary
title: Glossary and units
tags: [glossary, units]
---

# Glossary and units

| Term | Meaning |
|---|---|
| kWh | Kilowatt-hour — a unit of energy. All energy quantities in GridLens (demand, generation, import/export, curtailment) are in kWh. |
| kW | Kilowatt — a unit of power (rate of energy flow). Battery `battery_power_kw` and solar `solar_capacity_kwp` are power ratings. |
| kWp | Kilowatt-peak — the rated (nameplate) power output of a solar installation under standard test conditions. |
| SoC | State of charge — how much energy is currently stored in the battery, reported both in kWh (`soc_kwh`) and as a fraction of capacity (`soc_fraction`). |
| Round-trip efficiency | The fraction of energy put into a battery that can later be retrieved; see `battery_efficiency.md`. |
| Derating | A multiplier applied to a theoretical maximum to account for real-world losses; see `solar_derating.md`. |
| Curtailment | Solar generation that is deliberately not used, stored, or exported; see `energy_balance.md`. |
| Carbon intensity | Grams of CO2-equivalent emitted per kWh of grid electricity; see `carbon_factors.md`. |
| Tariff | The price structure applied to grid import/export; see `tariffs.md`. |
| Horizon | The number of hours a scenario simulates, `ScenarioRequest.horizon_hours` (max 168, one week). |
| Scenario | One fully-specified, deterministic simulation run: a `ScenarioRequest` in, a `ScenarioResult` out. |

## A note on precision

GridLens reports floating-point kWh/cost/emissions values with the
precision Python's `float` naturally provides. It does not claim
measurement-grade accuracy — see `system_limitations.md` for the broader
caveat about synthetic data and false precision.
