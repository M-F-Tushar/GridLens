---
doc_id: kb-battery-efficiency
title: Battery efficiency and dispatch assumptions
tags: [battery, storage, efficiency]
---

# Battery efficiency and dispatch assumptions

## Round-trip efficiency

`ScenarioRequest.battery_round_trip_efficiency` (default `0.90`, i.e. 90%)
represents the fraction of energy put into the battery that can later be
retrieved. The engine applies this loss on the *charge* side only:

charge_efficiency = sqrt(round_trip_efficiency) stored_kwh = battery_charge_kwh * charge_efficiency battery_loss_kwh = battery_charge_kwh - stored_kwh


Discharging is 1:1 with state-of-charge reduction. This is a simplification
(real batteries lose some energy on both charge and discharge, and losses
vary with temperature, C-rate, and state of health), chosen so the model is
easy to reason about and to test.

## Dispatch priority

Every hour, GridLens uses a strict priority order:

1. Solar generation is used to serve demand directly first.
2. If solar exceeds demand, the surplus charges the battery (bounded by
   `battery_power_kw` and remaining headroom), then exports to the grid
   (or curtails, if `allow_export` is `false`).
3. If demand exceeds solar, the battery discharges (bounded by
   `battery_power_kw` and available state of charge), then the grid imports
   the remainder.

There is no look-ahead: the battery does not "save" charge in anticipation
of a future price spike or shortfall. This is a **rule-based dispatch**, not
an optimization — it will not find the cost-minimal or emissions-minimal
dispatch schedule. Adding an optimizer (e.g. linear programming over the
horizon) is a natural, explicitly out-of-scope extension.

## Bounds enforced

State of charge is always clamped to `[0, battery_capacity_kwh]`. Charge and
discharge power are always clamped to `battery_power_kw`. These bounds are
covered by `tests/test_scenario_engine.py`.