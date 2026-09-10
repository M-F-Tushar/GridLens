"""Tests for the forecast baselines."""
from __future__ import annotations

import pytest

from domain.models import ForecastMethod
from engine.forecast import run_forecast


def test_seasonal_naive_forecast_has_correct_shape():
    result = run_forecast("campus-microgrid-a", horizon_hours=48, method=ForecastMethod.SEASONAL_NAIVE)
    assert result.method == ForecastMethod.SEASONAL_NAIVE
    assert len(result.points) == 48
    assert result.points[0].hour_index == 0
    assert result.points[-1].hour_index == 47
    assert all(p.predicted_demand_kwh >= 0 for p in result.points)
    assert all(p.predicted_solar_generation_kwh >= 0 for p in result.points)


def test_rolling_mean_forecast_is_flat_across_horizon():
    result = run_forecast("campus-microgrid-a", horizon_hours=24, method=ForecastMethod.ROLLING_MEAN)
    demands = {round(p.predicted_demand_kwh, 6) for p in result.points}
    solars = {round(p.predicted_solar_generation_kwh, 6) for p in result.points}
    assert len(demands) == 1, "rolling_mean should predict the same demand for every horizon hour"
    assert len(solars) == 1, "rolling_mean should predict the same solar for every horizon hour"


def test_forecast_is_reproducible():
    a = run_forecast("campus-microgrid-a", horizon_hours=24)
    b = run_forecast("campus-microgrid-a", horizon_hours=24)
    dump_a = a.model_dump(exclude={"generated_at"})
    dump_b = b.model_dump(exclude={"generated_at"})
    assert dump_a == dump_b


def test_forecast_unknown_site_raises():
    with pytest.raises((FileNotFoundError, ValueError)):
        run_forecast("does-not-exist", horizon_hours=24)