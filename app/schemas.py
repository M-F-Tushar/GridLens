from __future__ import annotations

from pydantic import BaseModel

from domain.models import (
    ExplanationRequest,
    ExplanationResult,
    ForecastMethod,
    ScenarioCompareRequest,
    ScenarioRequest,
)


class ForecastQuery(BaseModel):
    site: str = "campus-microgrid-a"
    horizon_hours: int = 24
    method: ForecastMethod = ForecastMethod.SEASONAL_NAIVE
    as_of_hour_index: int = 0