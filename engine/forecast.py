"""
Two deliverately simple, fully Fully deterministic baselines are implemented:

1. Seasonal naïve: “Use the value from the same hour yesterday.”
2. Rolling mean: “Use the average from the most recent 24 hours for every future hour.”

"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from domain.models import ForecastMethod, ForecastPoint, ForecastResult
from engine.fixtures import load_site_rows


SEASONAL_PERIOD_HOURS = 24
DEFAULT_ROLLING_WINDOW_HOURS = 24
REFERENCE_SOLAR_CAPACITY_KWP = 1.0


def run_forecast(
    site: str,
    horizon_hours: int,
    method: ForecastMethod = ForecastMethod.SEASONAL_NAIVE,
    as_of_hour_index: int = 0,
    rolling_window_hours: int = DEFAULT_ROLLING_WINDOW_HOURS,
) -> ForecastResult:
    rows = load_site_rows(site)
    if not rows:
        raise ValueError(f"No fixture data available for site {site!r}")
    n = len(rows)

    if method == ForecastMethod.SEASONAL_NAIVE:
        predicted_demand = [
            rows[(as_of_hour_index + h - SEASONAL_PERIOD_HOURS) % n].demand_kwh
            for h in range(horizon_hours)
        ]
        predicted_solar = [
            rows[(as_of_hour_index + h - SEASONAL_PERIOD_HOURS) % n].solar_potential_kwh_per_kwp
            * REFERENCE_SOLAR_CAPACITY_KWP
            for h in range(horizon_hours)
        ]
    elif method == ForecastMethod.ROLLING_MEAN:
        window_indices = [(as_of_hour_index - 1 - i) % n for i in range(rolling_window_hours)]
        mean_demand = sum(rows[i].demand_kwh for i in window_indices) / rolling_window_hours
        mean_solar = (
            sum(rows[i].solar_potential_kwh_per_kwp for i in window_indices)
            / rolling_window_hours
            * REFERENCE_SOLAR_CAPACITY_KWP
        )
        predicted_demand = [mean_demand] * horizon_hours
        predicted_solar = [mean_solar] * horizon_hours
    else:
        raise ValueError(f"Unsupported forecast method: {method!r}")

    base_ts = rows[as_of_hour_index % n].timestamp
    points = [
        ForecastPoint(
            timestamp=base_ts + timedelta(hours=h),
            hour_index=h,
            predicted_demand_kwh=predicted_demand[h],
            predicted_solar_generation_kwh=predicted_solar[h],
        )
        for h in range(horizon_hours)
    ]
    return ForecastResult(
        site=site,
        method=method,
        horizon_hours=horizon_hours,
        points=points,
        generated_at=datetime.now(timezone.utc),
    )