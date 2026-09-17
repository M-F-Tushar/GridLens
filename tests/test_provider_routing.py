from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from llm.openai_provider import OpenAIProvider
from llm.provider import (
    PROVIDER_MODELS,
    CompletionRequest,
    LocalDeterministicProvider,
    build_provider_from_settings,
    normalize_provider_key,
)
from rag.answer import answer_question
from rag.retriever import reset_store_cache
from ui.gradio_app import _ask, build_app

client = TestClient(app)


def setup_function(_):
    reset_store_cache()


def test_provider_models_registry_contains_only_local_openrouter_groq():
    assert "Local (Offline)" in PROVIDER_MODELS
    assert "OpenRouter (Free)" in PROVIDER_MODELS
    assert "Groq (Free Tier)" in PROVIDER_MODELS
    assert "Grok (xAI)" not in PROVIDER_MODELS
    assert "OpenAI" not in PROVIDER_MODELS
    assert len(PROVIDER_MODELS) == 3

    assert len(PROVIDER_MODELS["OpenRouter (Free)"]) == 3
    assert "meta-llama/llama-3.3-70b-instruct:free" in PROVIDER_MODELS["OpenRouter (Free)"]

    assert len(PROVIDER_MODELS["Groq (Free Tier)"]) == 3
    assert "llama-3.3-70b-versatile" in PROVIDER_MODELS["Groq (Free Tier)"]


def test_normalize_provider_key():
    assert normalize_provider_key("OpenRouter (Free)") == "openrouter"
    assert normalize_provider_key("Groq (Free Tier)") == "groq"
    assert normalize_provider_key("Local (Offline)") == "local"
    assert normalize_provider_key(None) == "local"


def test_build_provider_without_key_falls_back_to_local_deterministic():
    for prov in ("openrouter", "groq"):
        provider = build_provider_from_settings(prov, api_key=None)
        assert isinstance(provider, LocalDeterministicProvider)
        assert provider.name == "local-deterministic"


def test_build_provider_openrouter_with_key():
    provider = build_provider_from_settings(
        "openrouter",
        api_key="test-key-or",
        model="meta-llama/llama-3.3-70b-instruct:free",
    )
    assert isinstance(provider, OpenAIProvider)
    assert provider.name == "openrouter"
    assert provider.model == "meta-llama/llama-3.3-70b-instruct:free"
    assert provider.base_url == "https://openrouter.ai/api/v1/chat/completions"
    assert "HTTP-Referer" in provider.extra_headers


def test_build_provider_groq_with_key():
    provider = build_provider_from_settings(
        "groq",
        api_key="test-key-groq",
        model="llama-3.3-70b-versatile",
    )
    assert isinstance(provider, OpenAIProvider)
    assert provider.name == "groq"
    assert provider.model == "llama-3.3-70b-versatile"
    assert provider.base_url == "https://api.groq.com/openai/v1/chat/completions"


def test_openai_provider_call_mocked():
    provider = OpenAIProvider(
        api_key="test-key",
        model="meta-llama/llama-3.3-70b-instruct:free",
        base_url="https://openrouter.ai/api/v1/chat/completions",
        provider_name="openrouter",
        extra_headers={"HTTP-Referer": "https://example.com"},
    )
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(
        {
            "choices": [{"message": {"content": "This is a mocked explanation answer."}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 8},
        }
    ).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        completion = provider.complete(
            CompletionRequest(
                system_prompt="sys",
                user_prompt="user question",
            )
        )
        assert completion.text == "This is a mocked explanation answer."
        assert completion.provider == "openrouter"
        req = mock_urlopen.call_args[0][0]
        assert req.full_url == "https://openrouter.ai/api/v1/chat/completions"
        assert req.headers["Authorization"] == "Bearer test-key"
        assert req.headers["Http-referer"] == "https://example.com"


def test_answer_question_with_remote_provider_without_key_includes_offline_notice():
    result = answer_question(
        "How is battery efficiency modeled?",
        provider_name="OpenRouter (Free)",
        model_name="meta-llama/llama-3.3-70b-instruct:free",
    )
    assert result.provider == "local-deterministic"
    assert (
        "Offline fallback: No API key was configured for provider 'OpenRouter (Free)'"
        in result.answer
    )
    assert len(result.citations) > 0


def test_ui_ask_callback_with_provider_and_model():
    answer, sources = _ask(
        question="How is battery efficiency modeled?",
        provider="Groq (Free Tier)",
        model="llama-3.3-70b-versatile",
    )
    assert isinstance(answer, str) and len(answer) > 0
    assert "Offline fallback" in answer
    assert isinstance(sources, str) and len(sources) > 0


def test_explain_api_endpoint_accepts_provider_and_model():
    resp = client.post(
        "/api/explain",
        json={
            "question": "How is battery efficiency modeled?",
            "provider": "openrouter",
            "model": "meta-llama/llama-3.3-70b-instruct:free",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["provider"] == "local-deterministic"
    assert "Offline fallback" in body["answer"]


def test_gradio_app_builds_with_new_dropdowns():
    demo = build_app()
    assert demo is not None
