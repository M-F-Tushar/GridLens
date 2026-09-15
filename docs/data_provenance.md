# GridLens — Data Provenance Documentation

> **Canonical Source:** The primary data provenance and synthetic dataset documentation is located at [`data/fixtures/PROVENANCE.md`](../data/fixtures/PROVENANCE.md).

---

## Overview

GridLens bundles illustrative synthetic datasets for educational microgrid simulation and evaluation. All fixture files are located under `data/fixtures/`.

### Dataset Summary

1. **Hourly Demand (`demand_hourly.csv`)**
   - **Site:** `campus-microgrid-a`
   - **Horizon:** 336 hours (14 days, hourly intervals).
   - **Characteristics:** Typical commercial/campus load profile with daytime occupancy peaks (200–450 kW) and nighttime baseloads (~80–120 kW).

2. **Hourly Solar Generation (`solar_hourly.csv`)**
   - **Site:** `campus-microgrid-a`
   - **Horizon:** 336 hours.
   - **Characteristics:** Normalized per-kWp solar generation curves capturing diurnal solar patterns, morning ramp, midday peak, and nighttime zero-generation.

3. **Hourly Carbon Intensity (`carbon_intensity_hourly.csv`)**
   - **Horizon:** 336 hours.
   - **Characteristics:** Hourly marginal carbon intensity (kg CO₂ / kWh) reflecting regional grid variations across solar hours versus peak evening hours.

4. **Tariff Schedules (`tariffs.csv` / `tariffs.json`)**
   - **Schedules:** Flat, Two-Tier Time-of-Use (TOU), and Critical Peak Pricing structures with import rates ($/kWh) and export feed-in credits ($/kWh).

5. **Weather Data (`weather_hourly.csv`)**
   - **Horizon:** 336 hours.
   - **Characteristics:** Ambient temperature and cloud cover percentages aligned with solar generation periods.

---

For detailed field schemas, assumptions, and generation scripts, refer to [`data/fixtures/PROVENANCE.md`](../data/fixtures/PROVENANCE.md).
