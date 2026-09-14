"""API-level tests for Day 5 endpoints: /api/explain, request-ID logging,
CORS, and the generic error handler.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from rag.retriever import reset_store_cache

client = TestClient(app)


def setup_function(_):
    reset_store_cache()


def test_explain_endpoint_returns_citations_for_knowledge_question():
    resp = client.post("/api/explain", json={"question": "How is battery efficiency modeled?"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["insufficient_evidence"] is False
    assert len(body["citations"]) > 0
    assert body["provider"] == "local-deterministic"


def test_explain_endpoint_returns_insufficient_evidence_with_high_threshold():
    resp = client.post(
        "/api/explain",
        json={"question": "totally unrelated gibberish", "similarity_threshold": 0.999},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["insufficient_evidence"] is True
    assert body["citations"] == []


def test_explain_endpoint_runs_scenario_first_and_cites_its_numbers():
    resp = client.post(
        "/api/explain",
        json={
            "question": "What was the total cost?",
            "scenario": {"scenario_id": "explain-demo", "horizon_hours": 24},
            "top_k": 1,
            "similarity_threshold": 0.99,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "total_cost=" in body["answer"]


def test_explain_endpoint_rejects_invalid_input():
    resp = client.post("/api/explain", json={"question": ""})
    assert resp.status_code == 422


def test_every_response_carries_a_request_id_header():
    resp = client.get("/health")
    assert "x-request-id" in resp.headers


def test_cors_preflight_allows_configured_origin():
    resp = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:7860",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert resp.status_code in (200, 204)
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:7860"


def test_cors_rejects_unconfigured_origin():
    resp = client.options(
        "/health",
        headers={
            "Origin": "http://evil.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert resp.headers.get("access-control-allow-origin") is None