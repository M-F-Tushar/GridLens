"""Provider-agnostic LLM access layer.

Week 1 revision: this is the "provider abstraction" pattern — application
code (Day 2+ tool-calling, Day 5 explanation service) depends only on the
``LLMProvider`` interface, never on a concrete SDK. Swapping hosted <-> local
models, or adding a new vendor, never requires touching call sites.

Nothing in ``engine/`` imports this module. The numerical scenario engine is
and must remain fully independent of any LLM.
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass


class ProviderError(RuntimeError):
    """Raised when a provider call fails after all retries."""


@dataclass(frozen=True)
class CompletionRequest:
    system_prompt: str
    user_prompt: str
    max_tokens: int = 512
    temperature: float = 0.0


@dataclass(frozen=True)
class CompletionResponse:
    text: str
    model: str
    provider: str
    prompt_tokens_estimate: int
    completion_tokens_estimate: int


def estimate_tokens(text: str) -> int:
    """Very rough token estimate (~4 chars/token) with no external dependency.

    Good enough for logging/budgeting; not a substitute for a real tokenizer.
    """
    return max(1, len(text) // 4)


class LLMProvider(ABC):
    """Common interface every provider (hosted or local) must implement."""

    name: str = "base"

    @abstractmethod
    def complete(self, request: CompletionRequest) -> CompletionResponse:
        raise NotImplementedError


class LocalDeterministicProvider(LLMProvider):
    """A provider that requires no API key and no network access.

    It does not "understand" language; it deterministically echoes a
    templated response built from the prompts. This is what lets GridLens
    boot and demo fully offline (Day 5 release gate), and it is exactly what
    every fallback path in the RAG/explanation layers uses when no hosted
    provider is configured.
    """

    name = "local-deterministic"

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        text = (
            "[local-deterministic-provider] "
            f"Instruction: {request.system_prompt.strip()[:200]} | "
            f"Input: {request.user_prompt.strip()[:400]}"
        )
        return CompletionResponse(
            text=text,
            model="local-deterministic-v1",
            provider=self.name,
            prompt_tokens_estimate=estimate_tokens(request.system_prompt + request.user_prompt),
            completion_tokens_estimate=estimate_tokens(text),
        )


class RetryingRemoteProvider(LLMProvider):
    """Base class for hosted providers: bounded retries + timeout, no secret
    ever logged or included in an exception message.
    """

    name = "remote-base"

    def __init__(self, api_key: str, model: str, timeout_seconds: float = 10.0, max_retries: int = 3):
        if not api_key:
            raise ProviderError(f"{self.name} requires an API key but none was configured")
        self._api_key = api_key  # never logged, never included in errors/exceptions
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                return self._call(request)
            except Exception as exc:  # noqa: BLE001 - intentionally broad, retried below
                last_error = exc
                if attempt < self.max_retries:
                    time.sleep(min(2 ** attempt * 0.1, 2.0))
        raise ProviderError(
            f"{self.name} failed after {self.max_retries} attempts"
        ) from last_error

    @abstractmethod
    def _call(self, request: CompletionRequest) -> CompletionResponse:
        raise NotImplementedError


PROVIDER_MODELS: dict[str, list[str]] = {
    "Local (Offline)": [
        "local-deterministic",
    ],
    "OpenRouter (Free)": [
        "meta-llama/llama-3.3-70b-instruct:free",
        "google/gemini-2.0-flash-exp:free",
        "deepseek/deepseek-r1:free",
    ],
    "Groq (Free Tier)": [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
    ],
}

PROVIDER_DESCRIPTIONS: dict[str, str] = {
    "Local (Offline)": "🔒 **Offline Mode:** Uses local deterministic fact-and-citation template. No API key or network required.",
    "OpenRouter (Free)": "🌐 **OpenRouter Free Models:** Free access to high-capability models (Llama 3.3 70B, Gemini 2.0 Flash, DeepSeek R1). Requires `OPENROUTER_API_KEY` (or enter key below).",
    "Groq (Free Tier)": "⚡ **Groq Free Tier:** Ultra-fast LPU inference on open models (Llama 3.3 70B, 8B, Mixtral). Requires `GROQ_API_KEY` (or enter key below).",
}


def normalize_provider_key(name: str | None) -> str:
    if not name:
        return "local"
    lower = name.lower().strip()
    if "openrouter" in lower:
        return "openrouter"
    if "groq" in lower:
        return "groq"
    if "openai" in lower:
        return "openai"
    if "local" in lower or lower in ("none", "offline"):
        return "local"
    return lower


def build_provider_from_settings(
    provider_name: str,
    openai_api_key: str | None = None,
    openai_model: str = "gpt-4o-mini",
    timeout_seconds: float = 10.0,
    max_retries: int = 3,
    api_key: str | None = None,
    model: str | None = None,
    base_url: str | None = None,
) -> LLMProvider:
    """Model routing: pick a provider by name, always falling back safely.

    Supports local offline execution, OpenAI, OpenRouter, Groq, and Grok (xAI).
    If an external provider is chosen but no API key is supplied, safely falls back
    to LocalDeterministicProvider to preserve offline resilience.
    """
    key_provider = normalize_provider_key(provider_name)
    if key_provider == "local":
        return LocalDeterministicProvider()

    from app.config import get_settings
    settings = get_settings()

    if key_provider == "openrouter":
        effective_key = api_key or settings.openrouter_api_key
        if not effective_key:
            return LocalDeterministicProvider()
        from llm.openai_provider import OpenAIProvider

        return OpenAIProvider(
            api_key=effective_key,
            model=model or settings.openrouter_model,
            base_url=base_url or settings.openrouter_base_url,
            provider_name="openrouter",
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            extra_headers={
                "HTTP-Referer": "https://github.com/M-F-Tushar/GridLens",
                "X-Title": "GridLens",
            },
        )

    if key_provider == "groq":
        effective_key = api_key or settings.groq_api_key
        if not effective_key:
            return LocalDeterministicProvider()
        from llm.openai_provider import OpenAIProvider

        return OpenAIProvider(
            api_key=effective_key,
            model=model or settings.groq_model,
            base_url=base_url or settings.groq_base_url,
            provider_name="groq",
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
        )

    if key_provider == "openai":
        effective_key = api_key or openai_api_key or settings.openai_api_key
        if not effective_key:
            return LocalDeterministicProvider()
        from llm.openai_provider import OpenAIProvider

        return OpenAIProvider(
            api_key=effective_key,
            model=model or openai_model or settings.openai_model,
            base_url=base_url or settings.openai_base_url,
            provider_name="openai",
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
        )

    raise ProviderError(f"Unknown llm_provider setting: {provider_name!r}")