# Fixture Data Provenance

All data in this folder is **synthetic**, generated deterministically for a
`campus-microgrid-a` demo site. It is not measured/real-world data. This is
intentional: GridLens must be runnable fully offline, with no API key and no
network access, and must produce reproducible results for tests and demos.

| File | Units | Rows | Generation method | Version |
|---|---|---|---|---|
| `hourly_load.csv` | kWh per hour | 336 (14 days, hourly, from 2024-01-01T00:00) | Deterministic sinusoidal daytime/evening bump with a weekend discount factor | v1 |
| `solar_profile.csv` | kWh generated per kWp of installed capacity, per hour | 336 | Deterministic daylight-hours (06:00-18:00) sine curve, zero at night | v1 |
| `carbon_intensity.csv` | grams CO2e per kWh imported from the grid | 336 | Deterministic diurnal curve: dirtier at night, cleaner mid-day | v1 |
| `tariffs.json` | currency-per-kWh rates, keyed by `tariff_id` | 2 tariffs | Hand-authored synthetic rate cards (`flat-standard`, `time-of-use-a`) | v1 |

## Timestamps

All timestamps are naive ISO-8601 (`YYYY-MM-DDTHH:MM:SS`), hourly-stepped,
starting at `2024-01-01T00:00:00`. The engine always looks up rows by
`hour_index` modulo the number of fixture rows, so any `horizon_hours` up to
168 (one week) is safe, and the data wraps predictably if a longer horizon is
requested later.

## Units contract

- Energy: kWh (kilowatt-hours) everywhere.
- Power: kW (kilowatts) for battery/interconnect limits.
- Carbon: grams CO2-equivalent per kWh (`g/kWh`).
- Money: tariff currency (`USD` in these fixtures) per kWh.

## Why this matters (Week 1 revision: secrets, reliability, reproducibility)

Because these fixtures are checked into the repo and loaded from disk (no
network, no API key), the engine's output for a fixed `ScenarioRequest` is
byte-for-byte reproducible across machines and across time. That
reproducibility is what the Day 1 unit tests rely on, and it is what lets the
whole system boot with zero secrets configured.