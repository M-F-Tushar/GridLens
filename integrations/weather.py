from __future__ import annotations

import time
from dataclasses import dataclass, replace
from datetime import UTC, datetime

import httpx
from pydantic import BaseModel, ValidationError

OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"
DEFAULT_TIMEOUT_SECONDS = 5.0
DEFAULT_MAX_RETRIES = 2
DEFAULT_CACHE_TTL_SECONDS = 600.0

# Used only if the API has never been reachable and nothing is cached yet.
FIXTURE_FALLBACK_TEMPERATURE_C = 15.0
FIXTURE_FALLBACK_CLOUD_COVER_PCT = 50.0


class _OpenMeteoResponseSchema(BaseModel):
    """Validates just the fields GridLens actually consumes."""

    current: dict


@dataclass(frozen=True)
class WeatherObservation:
    source: str
    fetched_at: datetime
    temperature_c: float
    cloud_cover_pct: float
    is_stale: bool


class WeatherAdapterError(RuntimeError):
    """
    Raised only when neither a live call, a cached value, nor the fixture
    fallback is available — should be effectively unreachable in practice.
    """


class OpenMeteoAdapter:
    def __init__(
        self,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        cache_ttl_seconds: float = DEFAULT_CACHE_TTL_SECONDS,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
        self._cache_ttl_seconds = cache_ttl_seconds
        self._transport = transport
        self._cache: dict[tuple[float, float], tuple[WeatherObservation, float]] = {}

    def fetch(self, latitude: float, longitude: float) -> WeatherObservation:
        cache_key = (round(latitude, 3), round(longitude, 3))
        cached_entry = self._cache.get(cache_key)

        if cached_entry is not None and not self._is_expired(cached_entry[1]):
            return cached_entry[0]

        try:
            observation = self._fetch_live(latitude, longitude)
            self._cache[cache_key] = (observation, time.time())
            return observation
        except (httpx.HTTPError, ValidationError, KeyError):
            if cached_entry is not None:
                return replace(cached_entry[0], is_stale=True)
            return WeatherObservation(
                source="fixture-fallback",
                fetched_at=datetime.now(UTC),
                temperature_c=FIXTURE_FALLBACK_TEMPERATURE_C,
                cloud_cover_pct=FIXTURE_FALLBACK_CLOUD_COVER_PCT,
                is_stale=True,
            )

    def _fetch_live(self, latitude: float, longitude: float) -> WeatherObservation:
        last_error: Exception | None = None
        with httpx.Client(transport=self._transport, timeout=self._timeout_seconds) as client:
            for attempt in range(1, self._max_retries + 1):
                try:
                    response = client.get(
                        OPEN_METEO_BASE_URL,
                        params={
                            "latitude": latitude,
                            "longitude": longitude,
                            "current": "temperature_2m,cloud_cover",
                        },
                    )
                    response.raise_for_status()
                    validated = _OpenMeteoResponseSchema.model_validate(response.json())
                    current = validated.current
                    return WeatherObservation(
                        source="open-meteo",
                        fetched_at=datetime.now(UTC),
                        temperature_c=float(current["temperature_2m"]),
                        cloud_cover_pct=float(current["cloud_cover"]),
                        is_stale=False,
                    )
                except (httpx.HTTPError, ValidationError, KeyError) as exc:
                    last_error = exc
                    if attempt < self._max_retries:
                        time.sleep(min(2**attempt * 0.05, 1.0))
        raise last_error  # type: ignore[misc]

    def _is_expired(self, cached_at: float) -> bool:
        return (time.time() - cached_at) > self._cache_ttl_seconds