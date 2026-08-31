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


def build_provider_from_settings(
    provider_name: str,
    openai_api_key: str | None,
    openai_model: str,
    timeout_seconds: float,
    max_retries: int,
) -> LLMProvider:
    """Model routing: pick a provider by name, always falling back safely.

    Week 2 revision: this is "model routing" — one call site, provider chosen
    by configuration rather than by branching logic scattered through the app.
    """
    if provider_name == "local":
        return LocalDeterministicProvider()
    if provider_name == "openai":
        if not openai_api_key:
            return LocalDeterministicProvider()
        from llm.openai_provider import OpenAIProvider  # imported lazily: optional dependency

        return OpenAIProvider(
            api_key=openai_api_key,
            model=openai_model,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
        )
    raise ProviderError(f"Unknown llm_provider setting: {provider_name!r}")