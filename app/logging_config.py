from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

LOGGER_NAME = "gridlens"

_SENSITIVE_KEY_FRAGMENTS = ("key", "token", "secret", "authorization", "password")


def configure_logging(level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = True
    return logger


def redact_secrets(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Replaces any value whose key looks sensitive with a fixed placeholder.

    Defense in depth: log context is normally built from safe, already
    -typed fields, but this guards against a future call site accidentally
    passing something secret-shaped straight through to the logger.
    """
    redacted = {}
    for key, value in payload.items():
        if any(fragment in key.lower() for fragment in _SENSITIVE_KEY_FRAGMENTS):
            redacted[key] = "***redacted***"
        else:
            redacted[key] = value
    return redacted


def log_event(**fields: Any) -> None:
    logger = logging.getLogger(LOGGER_NAME)
    logger.info(json.dumps(redact_secrets(fields), default=str, sort_keys=True))


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Assigns a request ID, times the request, and logs one structured
    line per request. Endpoint handlers may enrich the log line by writing
    to ``request.state.log_context`` (a plain dict) before returning.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        request.state.log_context = {}
        start = time.perf_counter()
        status_code = 500
        error_category: str | None = None
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception as exc:
            error_category = type(exc).__name__
            raise
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            log_event(
                request_id=request_id,
                operation=f"{request.method} {request.url.path}",
                duration_ms=duration_ms,
                status_code=status_code,
                error_category=error_category,
                **request.state.log_context,
            )