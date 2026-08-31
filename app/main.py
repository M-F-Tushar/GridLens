"""FastAPI application: HTTP surface over the deterministic engine.

Week 1 revision: this is where "APIs" becomes concrete — a versioned,
validated HTTP contract in front of pure Python logic. The API layer never
computes anything itself; it validates input, calls the engine, and returns
the typed result.
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException

from app.config import get_settings
from domain.models import ScenarioRequest, ScenarioResult
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