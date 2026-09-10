"""Tests for the forecast and compare API additions and the knowledge-base fixtures."""
from __future__ import annotations

import re
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "data" / "knowledge"

_FRONT_MATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def test_forecast_endpoint_returns_expected_shape():
    resp = client.get("/api/forecast", params={"horizon_hours": 12, "method": "seasonal_naive"})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["points"]) == 12
    assert body["method"] == "seasonal_naive"


def test_forecast_endpoint_rejects_horizon_over_max():
    resp = client.get("/api/forecast", params={"horizon_hours": 5000})
    assert resp.status_code == 422


def test_compare_endpoint_computes_deltas_in_python():
    payload = {
        "base": {"scenario_id": "cmp-base", "solar_capacity_kwp": 0},
        "candidate": {"scenario_id": "cmp-candidate", "solar_capacity_kwp": 300},
    }
    resp = client.post("/api/scenarios/compare", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["base_scenario_id"] == "cmp-base"
    assert body["candidate_scenario_id"] == "cmp-candidate"
    assert body["kpi_deltas"]["total_emissions_kg"] <= 0


def test_knowledge_base_has_at_least_ten_documents_with_front_matter():
    docs = sorted(KNOWLEDGE_DIR.glob("*.md"))
    assert len(docs) >= 10
    for doc in docs:
        text = doc.read_text()
        match = _FRONT_MATTER_RE.match(text)
        assert match, f"{doc.name} is missing YAML front matter"
        assert "doc_id:" in match.group(1)
        assert "title:" in match.group(1)