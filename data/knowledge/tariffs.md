---
doc_id: kb-tariffs
title: Tariff structures used in GridLens
tags: [tariffs, cost, billing]
---

# Tariff structures used in GridLens

GridLens ships two synthetic tariff structures in `data/fixtures/tariffs.json`:

## `flat-standard`

A single rate (`0.18` currency units per kWh) applied to every hour of
grid import, with a flat export credit of `0.06` per kWh exported. This is
the simplest possible tariff and is the default for new scenarios.

## `time-of-use-a`

A three-tier time-of-use (TOU) tariff:

- **Peak** (17:00–20:00): `0.32` per kWh — the most expensive hours, chosen
  to coincide with the evening demand bump in the fixture data.
- **Shoulder** (07:00–16:00, 21:00–22:00): `0.20` per kWh.
- **Off-peak** (all remaining hours, i.e. 23:00–06:00): `0.11` per kWh.
- Export credit: `0.05` per kWh.

## How the engine applies a tariff

For every simulated hour, `engine.fixtures.tariff_rate_for_hour(tariff_id,
hour_of_day)` looks up the rate for that hour, and
`cost = grid_import_kwh * rate - grid_export_kwh * export_credit`. Cost can
be negative in an hour with heavy export and light import.

## Limitations

These are **synthetic, illustrative tariffs**, not real utility rate cards.
They do not model demand charges, seasonal rate changes, minimum bills, or
tiered/inclining-block pricing. A production deployment would replace
`data/fixtures/tariffs.json` with a validated, versioned real tariff
schedule and keep the same lookup interface.