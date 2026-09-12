---
doc_id: kb-kpi-definitions
title: KPI definitions (self-consumption, renewable fraction)
tags: [kpi, definitions, glossary]
---

# KPI definitions

## Self-consumption ratio

self_consumption_ratio = (total_solar - total_export - total_curtailment) / total_solar

The fraction of generated solar energy that is used on-site or stored,
rather than exported or curtailed. `0` means all solar left the site or was
wasted; `1` means every kWh of solar was consumed or stored locally.
Undefined (reported as `0`) when there is no solar generation at all.

## Renewable fraction

renewable_fraction = (total_demand - total_grid_import) / total_demand

The fraction of total demand met by anything *other than* grid import —
i.e. by solar (directly) or battery discharge (which itself was charged by
solar). `1` means the site imported nothing from the grid over the horizon;
`0` means every kWh of demand came from the grid.

## Why these two, and not more

These two ratios are chosen because they answer the two questions a
decision-maker most often asks first: "is my solar being used well?"
(self-consumption) and "how independent of the grid am I?" (renewable
fraction). Cost and emissions totals answer the financial and environmental
questions directly and don't need a derived ratio.

## Caveat

Both ratios are computed over whatever horizon was simulated
(`ScenarioRequest.horizon_hours`); comparing a 24-hour scenario's ratios to
a 168-hour scenario's ratios is comparing different time windows and may
not be meaningful without normalizing for season/weather variability (which
the current synthetic fixtures do not vary by season anyway).
