"""Tests for app/logging_config.py: secret redaction and structured events."""
from __future__ import annotations

import json
import logging

from app.logging_config import log_event, redact_secrets


def test_redact_secrets_masks_sensitive_keys():
    payload = {
        "openai_api_key": "sk-super-secret",
        "authorization": "******",
        "request_id": "abc-123",
        "scenario_id": "demo",
    }
    redacted = redact_secrets(payload)
    assert redacted["openai_api_key"] == "***redacted***"
    assert redacted["authorization"] == "***redacted***"
    assert redacted["request_id"] == "abc-123"
    assert redacted["scenario_id"] == "demo"


def test_redact_secrets_is_case_insensitive():
    payload = {"API_KEY": "value", "MySecretToken": "value"}
    redacted = redact_secrets(payload)
    assert redacted["API_KEY"] == "***redacted***"
    assert redacted["MySecretToken"] == "***redacted***"


def test_log_event_emits_valid_json_with_no_secret_leakage(caplog):
    caplog.set_level(logging.INFO, logger="gridlens")
    log_event(request_id="r1", operation="GET /health", openai_api_key="sk-should-not-leak")
    assert len(caplog.records) == 1
    parsed = json.loads(caplog.records[0].message)
    assert parsed["request_id"] == "r1"
    assert parsed["openai_api_key"] == "***redacted***"
    assert "sk-should-not-leak" not in caplog.records[0].message