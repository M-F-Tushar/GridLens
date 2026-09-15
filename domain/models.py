"""Core Pydantic data contracts shared by the engine, API, RAG and UI layers.

Design rule (Week 1 revision - provider abstraction & structured data):
    These models are the single source of truth for what a "scenario" is.
    The deterministic engine, the FastAPI layer, the RAG layer and the UI
    all import from here instead of re-declaring shapes. This is the same
    "define the contract once" idea used for tool-calling schemas in Week 2.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ForecastMethod(str, Enum):
    """Supported forecast baselines (Week 3: model tradeoffs)."""

    SEASONAL_NAIVE = "seasonal_naive"
    ROLLING_MEAN = "rolling_mean"


class ScenarioRequest(BaseModel):
    """Everything needed to deterministically run one scenario.

    All fields have explicit bounds so the engine never has to guess and so
    the API can reject bad input with a clear 422 error (Week 1: robust API
    design; Day 3 production hardening: capacity/horizon limits).
    """

    scenario_id: str = Field(
        ..., min_length=1, max_length=64,
        description="Caller-supplied identifier, echoed back on the result.",
    )
    site: str = Field(
        default="campus-microgrid-a",
        description="Which fixture site/profile to load demand & solar from.",
    )
    horizon_hours: int = Field(
        default=24, ge=1, le=168,
        description="Number of hourly steps to simulate (max 1 week).",
    )
    battery_capacity_kwh: float = Field(default=200.0, ge=0, le=100_000)
    battery_power_kw: float = Field(default=50.0, ge=0, le=100_000)
    battery_round_trip_efficiency: float = Field(default=0.90, gt=0, le=1.0)
    initial_soc_fraction: float = Field(default=0.5, ge=0.0, le=1.0)
    solar_capacity_kwp: float = Field(default=150.0, ge=0, le=100_000)
    solar_derate: float = Field(
        default=0.85, gt=0, le=1.0,
        description="Inverter/soiling/temperature derating factor.",
    )
    tariff_id: str = Field(default="flat-standard")
    carbon_source: str = Field(default="default-grid")
    allow_export: bool = Field(
        default=True,
        description="If False, unstored surplus solar is curtailed, not exported.",
    )
    forecast_method: ForecastMethod = Field(default=ForecastMethod.SEASONAL_NAIVE)

    @field_validator("scenario_id")
    @classmethod
    def _no_whitespace_only(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("scenario_id must not be blank")
        return value.strip()


class HourlyRecord(BaseModel):
    """One simulated hour of a scenario. This is the atomic, chart-ready row."""

    timestamp: datetime
    hour_index: int = Field(ge=0)
    demand_kwh: float
    solar_generation_kwh: float
    battery_charge_kwh: float = Field(ge=0)
    battery_discharge_kwh: float = Field(ge=0)
    battery_loss_kwh: float = Field(ge=0)
    soc_kwh: float = Field(ge=0)
    soc_fraction: float = Field(ge=0)
    grid_import_kwh: float = Field(ge=0)
    grid_export_kwh: float = Field(ge=0)
    curtailment_kwh: float = Field(ge=0)
    tariff_rate_per_kwh: float = Field(ge=0)
    cost: float
    carbon_intensity_g_per_kwh: float = Field(ge=0)
    emissions_kg: float
    energy_balance_error_kwh: float
    violations: list[str] = Field(default_factory=list)


class Totals(BaseModel):
    """Scenario-level KPIs, all computed in Python from the hourly records."""

    total_demand_kwh: float
    total_solar_generation_kwh: float
    total_grid_import_kwh: float
    total_grid_export_kwh: float
    total_curtailment_kwh: float
    total_cost: float
    total_emissions_kg: float
    self_consumption_ratio: float = Field(
        ge=0, le=1, description="Solar used on-site or stored / total solar."
    )
    renewable_fraction: float = Field(
        ge=0, le=1, description="Demand met by solar+battery / total demand."
    )


class Diagnostics(BaseModel):
    """Engine self-checks, surfaced so failures are never silent."""

    max_abs_energy_balance_error_kwh: float
    total_violation_count: int
    engine_version: str


class ScenarioResult(BaseModel):
    """Full, reproducible output of running one scenario."""

    scenario_id: str
    request: ScenarioRequest
    records: list[HourlyRecord]
    totals: Totals
    diagnostics: Diagnostics
    generated_at: datetime


class ForecastPoint(BaseModel):
    timestamp: datetime
    hour_index: int = Field(ge=0)
    predicted_demand_kwh: float
    predicted_solar_generation_kwh: float


class ForecastResult(BaseModel):
    site: str
    method: ForecastMethod
    horizon_hours: int = Field(ge=1, le=168)
    points: list[ForecastPoint]
    generated_at: datetime


class ScenarioComparison(BaseModel):
    """Deterministic diff between two already-computed scenario results.

    The LLM never computes these numbers; it may only narrate them later
    (Day 2 production hardening rule: comparisons are calculated in Python).
    """

    base_scenario_id: str
    candidate_scenario_id: str
    kpi_deltas: dict[str, float]
    narrative_points: list[str]
    generated_at: datetime


class ScenarioCompareRequest(BaseModel):
    base: ScenarioRequest
    candidate: ScenarioRequest


class SourceReference(BaseModel):
    """A citation pointing back at a retrieved knowledge-base chunk (RAG)."""

    doc_id: str
    title: str
    path: str
    chunk_id: str
    score: float
    snippet: str

    model_config = ConfigDict(frozen=True)


class ExplanationRequest(BaseModel):
    """Request payload for the cited explanation endpoint."""

    question: str = Field(..., min_length=1, description="Question to answer.")
    scenario: ScenarioRequest | None = None
    comparison: ScenarioCompareRequest | None = None
    top_k: int = Field(default=4, ge=0)
    similarity_threshold: float = Field(default=0.30, ge=0.0, le=1.0)

    @field_validator("question")
    @classmethod
    def _no_blank_question(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("question must not be blank")
        return value.strip()


class ExplanationResult(BaseModel):
    """Full cited explanation result."""

    question: str
    answer: str
    citations: list[SourceReference] = Field(default_factory=list)
    insufficient_evidence: bool = False
    provider: str = "none"
    generated_at: datetime