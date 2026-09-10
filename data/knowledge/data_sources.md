---
doc_id: kb-data-sources
title: Data sources and provenance
tags: [data, provenance, fixtures]
---

# Data sources and provenance

All numeric inputs to GridLens's default demo come from synthetic fixtures
generated deterministically for this project (see
`data/fixtures/PROVENANCE.md` for full generation details):

| Data | File | Real-world source? |
|---|---|---|
| Hourly demand | `data/fixtures/hourly_load.csv` | No — synthetic sinusoidal pattern |
| Solar potential | `data/fixtures/solar_profile.csv` | No — synthetic daylight-hours sine curve |
| Grid carbon intensity | `data/fixtures/carbon_intensity.csv` | No — synthetic diurnal curve |
| Tariffs | `data/fixtures/tariffs.json` | No — hand-authored illustrative rate cards |

## Optional external adapters

Later revisions add optional adapters for `Open-Meteo` (weather/solar
irradiance) and `PVGIS` (solar production estimates). When configured, they
fetch real data over the network, validate its schema, cache it, and tag it
with a source timestamp. If the network call fails, is slow, or is
unavailable (e.g. fully offline demo mode), GridLens always falls back to
the fixture data above and marks the result as stale/fixture-derived rather
than failing outright.

## Why this distinction matters

Anyone reading a GridLens result should be able to tell, for any given
number, whether it came from a real external source or from a synthetic
fixture. The explanation service (Day 5) is required to cite `data_source`
for every scenario result it discusses.