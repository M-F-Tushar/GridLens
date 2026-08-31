"""API-level tests using FastAPI's TestClient (no network, no server process)."""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["app_name"] == "GridLens"


def test_run_scenario_endpoint_returns_reproducible_result():
    payload = {"scenario_id": "api-test", "horizon_hours": 24}
    resp_a = client.post("/api/scenarios/run", json=payload)
    resp_b = client.post("/api/scenarios/run", json=payload)
    assert resp_a.status_code == 200
    assert resp_b.status_code == 200
    body_a = resp_a.json()
    body_b = resp_b.json()
    assert len(body_a["records"]) == 24
    assert body_a["totals"] == body_b["totals"]
    assert body_a["diagnostics"]["total_violation_count"] == 0


def test_run_scenario_rejects_horizon_over_max():
    resp = client.post(
        "/api/scenarios/run",
        json={"scenario_id": "too-long", "horizon_hours": 5000},
    )
    assert resp.status_code == 422


def test_run_scenario_rejects_unknown_tariff():
    resp = client.post(
        "/api/scenarios/run",
        json={"scenario_id": "bad-tariff", "tariff_id": "not-a-real-tariff"},
    )
    assert resp.status_code == 400