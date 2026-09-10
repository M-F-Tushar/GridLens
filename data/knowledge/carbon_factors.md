---
doc_id: kb-carbon-factors
title: Carbon intensity and emissions accounting
tags: [carbon, emissions, grid]
---

# Carbon intensity and emissions accounting

## What is measured

`data/fixtures/carbon_intensity.csv` gives the grams of CO2-equivalent
emitted per kWh **imported from the grid**, varying by hour of day (dirtier
at night when more thermal generation is on the margin, cleaner mid-day).

## What is *not* measured

- **Solar generation is treated as zero-emissions** at the point of use.
  GridLens does not account for embodied/lifecycle emissions of
  manufacturing panels or batteries.
- **Exports are not credited with an emissions offset.** Exporting surplus
  solar to the grid does not reduce the scenario's own reported emissions
  figure, even though it may displace emissions elsewhere on the grid.
- The carbon intensity curve is a **synthetic, illustrative** diurnal shape,
  not a real grid-operator signal.

## Formula

emissions_kg = grid_import_kwh * carbon_intensity_g_per_kwh / 1000


summed across all hours to produce `Totals.total_emissions_kg`.

## Why this matters for interpretation

Two scenarios with identical total grid import can have different total
emissions if the *timing* of that import differs — importing at night
(dirtier) costs more emissions than importing at midday (cleaner), even for
the same number of kWh. This is exactly the kind of nuance the explanation
service (Day 5) is expected to surface with a citation back to this
document, rather than asserting it from a model's general knowledge.

