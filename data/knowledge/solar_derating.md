---
doc_id: kb-solar-derating
title: Solar generation model and derating
tags: [solar, derating, generation]
---

# Solar generation model and derating

## From "potential" to "generation"

`data/fixtures/solar_profile.csv` stores `solar_potential_kwh_per_kwp`: an
hourly, unconstrained irradiance-driven potential, normalized per kWp
(kilowatt-peak) of installed capacity. The engine converts this to an actual
generation figure with:


solar_generation_kwh = solar_potential_kwh_per_kwp * solar_capacity_kwp * solar_derate


## What `solar_derate` represents

`ScenarioRequest.solar_derate` (default `0.85`) is a single lumped factor
standing in for everything that reduces real-world output below the
theoretical panel rating: inverter conversion losses, soiling (dust, dirt),
temperature derating, wiring losses, and shading. Real solar-design tools
(e.g. PVWatts, PVsyst) break this into several separate multipliers; GridLens
intentionally lumps them into one number to keep the model easy to reason
about and to explain.

## Daylight-only profile

The synthetic profile is zero outside 06:00–18:00 and follows a sine curve
peaking at midday — a reasonable stand-in for a clear-sky day, but it does
not model cloud cover, seasonal day-length changes, or panel tilt/azimuth.

## Limitation

Because the profile is the same every day, GridLens's fixture data cannot
demonstrate weather variability. The optional `Open-Meteo`/`PVGIS` adapters
(added later, in the production-hardening pass) are the path to real,
time-varying solar and weather data, with the fixture profile remaining as
the offline fallback.