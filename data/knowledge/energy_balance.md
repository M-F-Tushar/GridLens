---
doc_id: kb-energy-balance
title: Energy balance and curtailment
tags: [energy-balance, curtailment, diagnostics]
---

# Energy balance and curtailment

## The balance invariant

Every simulated hour must satisfy:

solar_generation + grid_import + battery_discharge == demand + battery_charge + grid_export + curtailment


`HourlyRecord.energy_balance_error_kwh` reports the (signed) discrepancy,
and `Diagnostics.max_abs_energy_balance_error_kwh` reports the worst hour in
a scenario. In a correctly functioning engine this is always effectively
zero (within floating-point tolerance, `< 1e-6` kWh); `tests/
test_scenario_engine.py::test_energy_balance_holds_every_hour` enforces this
on every commit.

## What curtailment means

Curtailment is solar generation that is neither consumed on-site, stored in
the battery, nor exported to the grid — it is "wasted" (the physical
equivalent of the inverter being told to produce less, or the surplus
simply not being usable). It only occurs when `ScenarioRequest.allow_export`
is `False` and the battery is already full; with export allowed (the
default), surplus solar is exported instead of curtailed.

## Reading a violation

If `HourlyRecord.violations` is non-empty for any hour, treat every number
in that scenario's result with suspicion — it means either the engine has a
bug, or (more likely if you are extending the fixtures) the input data is
internally inconsistent. `Diagnostics.total_violation_count` at zero is a
precondition for trusting a scenario's cost and emissions totals.