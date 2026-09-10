"""FastAPI application: HTTP surface over the deterministic engine.

This is where "APIs" becomes concrete — a versioned,
validated HTTP contract in front of pure Python logic. The API layer never
computes anything itself; it validates input, calls the engine, and returns
the typed result.
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException

from app.config import get_settings
from app.schemas import ScenarioCompareRequest
from domain.models import ForecastMethod, ForecastResult, ScenarioComparison, ScenarioRequest, ScenarioResult
from engine.compare import compare_scenarios
from engine.forecast import run_forecast
from engine.scenario_engine import run_scenario

app = FastAPI(
    title="GridLens API",
    description="Energy-system scenario and decision engine.",
    version="1.0.0",
)


@app.get("/health")
def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "app_name": settings.app_name,
        "environment": settings.environment,
    }


@app.post("/api/scenarios/run", response_model=ScenarioResult)
def run_scenario_endpoint(request: ScenarioRequest) -> ScenarioResult:
    settings = get_settings()
    return _run_validated(request, settings)


def _run_validated(request: ScenarioRequest, settings) -> ScenarioResult:
    if request.horizon_hours > settings.max_scenario_horizon_hours:
        raise HTTPException(
            status_code=422,
            detail=(
                f"horizon_hours={request.horizon_hours} exceeds the configured "
                f"maximum of {settings.max_scenario_horizon_hours}"
            ),
        )
    try:
        return run_scenario(request)
    except (FileNotFoundError, KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/scenarios/compare", response_model=ScenarioComparison)
def compare_scenarios_endpoint(request: ScenarioCompareRequest) -> ScenarioComparison:
    """Runs both scenarios and returns a Python-computed KPI diff.

    The LLM never sees this request; every number in the response comes
    straight out of ``engine.compare.compare_scenarios``.
    """
    settings = get_settings()
    base_result = _run_validated(request.base, settings)
    candidate_result = _run_validated(request.candidate, settings)
    return compare_scenarios(base_result, candidate_result)


@app.get("/api/forecast", response_model=ForecastResult)
def forecast_endpoint(
    site: str = "campus-microgrid-a",
    horizon_hours: int = 24,
    method: ForecastMethod = ForecastMethod.SEASONAL_NAIVE,
    as_of_hour_index: int = 0,
) -> ForecastResult:
    settings = get_settings()
    if horizon_hours > settings.max_scenario_horizon_hours:
        raise HTTPException(
            status_code=422,
            detail=(
                f"horizon_hours={horizon_hours} exceeds the configured "
                f"maximum of {settings.max_scenario_horizon_hours}"
            ),
        )
    try:
        return run_forecast(
            site=site,
            horizon_hours=horizon_hours,
            method=method,
            as_of_hour_index=as_of_hour_index,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc