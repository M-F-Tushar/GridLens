
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from rag.retriever import reset_store_cache

client = TestClient(app)


def setup_function(_):
    reset_store_cache()


def test_smoke_health_check_is_first_and_fast():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_smoke_full_lifecycle_scenario_forecast_compare_explain():
    # 1. Deterministic scenario run (data source -> validation -> calculation).
    run_resp = client.post(
        "/api/scenarios/run",
        json={"scenario_id": "smoke-run", "horizon_hours": 48, "solar_capacity_kwp": 250},
    )
    assert run_resp.status_code == 200
    run_body = run_resp.json()
    assert run_body["diagnostics"]["total_violation_count"] == 0
    request_id = run_resp.headers.get("x-request-id")
    assert request_id, "structured logging must attach a request id header"

    # 2. Forecast (independent deterministic baseline).
    forecast_resp = client.get("/api/forecast", params={"horizon_hours": 24})
    assert forecast_resp.status_code == 200
    assert len(forecast_resp.json()["points"]) == 24

    # 3. Scenario comparison (KPI deltas computed in Python).
    compare_resp = client.post(
        "/api/scenarios/compare",
        json={
            "base": {"scenario_id": "smoke-base", "battery_capacity_kwh": 0},
            "candidate": {"scenario_id": "smoke-candidate", "battery_capacity_kwh": 500},
        },
    )
    assert compare_resp.status_code == 200
    assert "kpi_deltas" in compare_resp.json()

    # 4. Cited explanation (retrieval -> explanation, offline fallback).
    explain_resp = client.post(
        "/api/explain",
        json={"question": "How is battery efficiency modeled in GridLens?"},
    )
    assert explain_resp.status_code == 200
    explain_body = explain_resp.json()
    assert explain_body["provider"] == "local-deterministic"
    assert explain_body["insufficient_evidence"] is False
    assert len(explain_body["citations"]) > 0


def test_smoke_offline_fallback_never_requires_an_api_key():
    # No OPENAI_API_KEY is set in this test environment; the explanation
    # service must still answer using the local deterministic provider.
    import os

    assert os.environ.get("OPENAI_API_KEY") in (None, "")
    resp = client.post("/api/explain", json={"question": "What tariff model does GridLens use?"})
    assert resp.status_code == 200
    assert resp.json()["provider"] == "local-deterministic"


def test_smoke_invalid_input_is_rejected_before_any_calculation():
    resp = client.post("/api/scenarios/run", json={"scenario_id": "bad", "horizon_hours": -5})
    assert resp.status_code == 422


def test_smoke_unhandled_error_returns_generic_response_without_internals():
    resp = client.get("/api/forecast", params={"horizon_hours": 24, "method": "not-a-real-method"})
    assert resp.status_code in (400, 422)
    assert "Traceback" not in resp.text