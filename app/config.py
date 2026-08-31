"""Environment-based configuration (Week 1 revision: secrets & config).

No secret ever has a hard-coded default. Everything is read from environment
variables (optionally via a local ``.env`` file, see ``.env.example``), and
the app must boot and run the full offline demo with **zero** secrets set.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    app_name: str = "GridLens"
    environment: str = "development"
    max_scenario_horizon_hours: int = 168
    llm_provider: str = "local"  # "local" | "openai" (see llm/provider.py)
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    request_timeout_seconds: float = 10.0
    max_retries: int = 3
    cors_allow_origins: tuple[str, ...] = ("http://localhost:7860", "http://127.0.0.1:7860")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("GRIDLENS_APP_NAME", "GridLens"),
        environment=os.getenv("GRIDLENS_ENV", "development"),
        max_scenario_horizon_hours=int(os.getenv("GRIDLENS_MAX_HORIZON_HOURS", "168")),
        llm_provider=os.getenv("GRIDLENS_LLM_PROVIDER", "local"),
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        openai_model=os.getenv("GRIDLENS_OPENAI_MODEL", "gpt-4o-mini"),
        request_timeout_seconds=float(os.getenv("GRIDLENS_REQUEST_TIMEOUT_SECONDS", "10.0")),
        max_retries=int(os.getenv("GRIDLENS_MAX_RETRIES", "3")),
        cors_allow_origins=tuple(
            o.strip()
            for o in os.getenv(
                "GRIDLENS_CORS_ORIGINS", "http://localhost:7860,http://127.0.0.1:7860"
            ).split(",")
            if o.strip()
        ),
    )