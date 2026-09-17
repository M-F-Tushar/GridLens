"""FastAPI application: HTTP surface over the deterministic engine.

This is where "APIs" becomes concrete — a versioned,
validated HTTP contract in front of pure Python logic. The API layer never
computes anything itself; it validates input, calls the engine, and returns
the typed result.
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import get_settings
from app.logging_config import RequestLoggingMiddleware, configure_logging
from app.schemas import ScenarioCompareRequest
from domain.models import (
    ExplanationRequest,
    ExplanationResult,
    ForecastMethod,
    ForecastResult,
    ScenarioComparison,
    ScenarioRequest,
    ScenarioResult,
)
from engine.compare import compare_scenarios
from engine.forecast import run_forecast
from engine.scenario_engine import run_scenario
from rag.answer import answer_question

configure_logging()
settings = get_settings()

app = FastAPI(
    title="GridLens API",
    description="Energy-system scenario and decision engine.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_allow_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    req_id = getattr(request.state, "request_id", None)
    base_headers = {"X-Request-ID": req_id} if req_id else {}

    if isinstance(exc, (HTTPException, StarletteHTTPException)):
        headers = dict(getattr(exc, "headers", None) or {})
        headers.update(base_headers)
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=headers or None,
        )
    if isinstance(exc, RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors()},
            headers=base_headers or None,
        )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
        headers=base_headers or None,
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


@app.post("/api/explain", response_model=ExplanationResult)
def explain_endpoint(request: ExplanationRequest) -> ExplanationResult:
    settings = get_settings()
    scenario_result = _run_validated(request.scenario, settings) if request.scenario is not None else None
    comparison_result = None
    if request.comparison is not None:
        base = _run_validated(request.comparison.base, settings)
        candidate = _run_validated(request.comparison.candidate, settings)
        comparison_result = compare_scenarios(base, candidate)

    return answer_question(
        question=request.question,
        scenario_result=scenario_result,
        comparison=comparison_result,
        top_k=request.top_k,
        similarity_threshold=request.similarity_threshold,
        settings=settings,
        provider_name=request.provider,
        model_name=request.model,
    )