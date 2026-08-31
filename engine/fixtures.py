"""
load sample energy data from files and prepare it for the 
simulation engine.

"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "data" / "fixtures"


@dataclass(frozen=True)
# one hour of energy-related data.
class FixtureRow:
    timestamp: datetime
    demand_kwh: float
    solar_potential_kwh_per_kwp: float
    carbon_intensity_g_per_kwh: float


def _read_csv(name: str) -> list[dict[str, str]]:
    path = FIXTURES_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Missing fixture file: {path}")
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


@lru_cache(maxsize=8)
def load_site_rows(site: str) -> tuple[FixtureRow, ...]:
    """main function for loading hourly site data."""
    load_rows = _read_csv("hourly_load.csv")
    solar_rows = _read_csv("solar_profile.csv")
    carbon_rows = _read_csv("carbon_intensity.csv")

    if not (len(load_rows) == len(solar_rows) == len(carbon_rows)):
        raise ValueError("Fixture files are misaligned (row count mismatch)")

    rows: list[FixtureRow] = []
    for load_row, solar_row, carbon_row in zip(load_rows, solar_rows, carbon_rows):
        if load_row["timestamp"] != solar_row["timestamp"] != carbon_row["timestamp"]:
            raise ValueError("Fixture files are misaligned (timestamp mismatch)")
        rows.append(
            FixtureRow(
                timestamp=datetime.fromisoformat(load_row["timestamp"]),
                demand_kwh=float(load_row["demand_kwh"]),
                solar_potential_kwh_per_kwp=float(solar_row["solar_potential_kwh_per_kwp"]),
                carbon_intensity_g_per_kwh=float(carbon_row["carbon_intensity_g_per_kwh"]),
            )
        )
    return tuple(rows)


@lru_cache(maxsize=1)
def load_tariffs() -> dict:
    path = FIXTURES_DIR / "tariffs.json"
    with path.open() as f:
        return json.load(f)


def tariff_rate_for_hour(tariff_id: str, hour_of_day: int) -> float:
    """the electricity price for a particular hour."""
    tariffs = load_tariffs()
    if tariff_id not in tariffs:
        raise KeyError(f"Unknown tariff_id: {tariff_id!r}. Known: {sorted(tariffs)}")
    tariff = tariffs[tariff_id]
    if "rate_per_kwh" in tariff:
        return float(tariff["rate_per_kwh"])
    if hour_of_day in tariff.get("peak_hours", []):
        return float(tariff["peak_rate_per_kwh"])
    if hour_of_day in tariff.get("shoulder_hours", []):
        return float(tariff["shoulder_rate_per_kwh"])
    return float(tariff["off_peak_rate_per_kwh"])


def export_credit_for_tariff(tariff_id: str) -> float:
    """returns the amount credited for every kWh exported to the electricity grid."""
    tariffs = load_tariffs()
    return float(tariffs[tariff_id]["export_credit_per_kwh"])