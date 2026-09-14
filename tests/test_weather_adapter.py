"""Tests for integrations/weather.py using httpx.MockTransport (fully offline,
no real network access)."""
from __future__ import annotations

import httpx

from integrations.weather import OpenMeteoAdapter


def _mock_transport(handler):
    return httpx.MockTransport(handler)


def test_fetch_returns_live_observation_on_success():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"current": {"temperature_2m": 21.5, "cloud_cover": 40}})

    adapter = OpenMeteoAdapter(transport=_mock_transport(handler))
    observation = adapter.fetch(latitude=51.5, longitude=-0.1)
    assert observation.source == "open-meteo"
    assert observation.temperature_c == 21.5
    assert observation.cloud_cover_pct == 40
    assert observation.is_stale is False


def test_fetch_uses_cache_on_second_call_without_hitting_transport():
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(200, json={"current": {"temperature_2m": 10.0, "cloud_cover": 5}})

    adapter = OpenMeteoAdapter(transport=_mock_transport(handler), cache_ttl_seconds=600)
    first = adapter.fetch(latitude=1.0, longitude=2.0)
    second = adapter.fetch(latitude=1.0, longitude=2.0)
    assert call_count == 1
    assert first == second


def test_fetch_falls_back_to_stale_cache_on_transport_failure():
    responses = iter(
        [
            httpx.Response(200, json={"current": {"temperature_2m": 18.0, "cloud_cover": 20}}),
        ]
    )

    def handler(request: httpx.Request) -> httpx.Response:
        try:
            return next(responses)
        except StopIteration:
            raise httpx.ConnectError("simulated network failure", request=request)

    adapter = OpenMeteoAdapter(transport=_mock_transport(handler), cache_ttl_seconds=0)
    first = adapter.fetch(latitude=5.0, longitude=6.0)
    assert first.is_stale is False

    second = adapter.fetch(latitude=5.0, longitude=6.0)
    assert second.is_stale is True
    assert second.temperature_c == first.temperature_c


def test_fetch_falls_back_to_fixture_when_nothing_cached_and_transport_fails():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("simulated network failure", request=request)

    adapter = OpenMeteoAdapter(transport=_mock_transport(handler), max_retries=1)
    observation = adapter.fetch(latitude=9.0, longitude=9.0)
    assert observation.source == "fixture-fallback"
    assert observation.is_stale is True


def test_fetch_retries_before_succeeding():
    attempts = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        if attempts["count"] < 2:
            raise httpx.ConnectError("simulated transient failure", request=request)
        return httpx.Response(200, json={"current": {"temperature_2m": 12.0, "cloud_cover": 60}})

    adapter = OpenMeteoAdapter(transport=_mock_transport(handler), max_retries=3)
    observation = adapter.fetch(latitude=3.0, longitude=4.0)
    assert observation.source == "open-meteo"
    assert attempts["count"] == 2


def test_fetch_rejects_malformed_response_schema():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"unexpected": "shape"})

    adapter = OpenMeteoAdapter(transport=_mock_transport(handler), max_retries=1)
    observation = adapter.fetch(latitude=7.0, longitude=8.0)
    assert observation.source == "fixture-fallback"