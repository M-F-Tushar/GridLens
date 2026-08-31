"""Optional hosted provider: OpenAI-compatible chat completions.

This module is imported lazily (see ``llm.provider.build_provider_from_settings``)
so that the rest of GridLens never depends on it. It uses only the Python
standard library (``urllib``) so no extra SDK is required to keep the
provider abstraction meaningful. Never logs or raises the API key.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request

from llm.provider import CompletionRequest, CompletionResponse, ProviderError, RetryingRemoteProvider, estimate_tokens

_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"


class OpenAIProvider(RetryingRemoteProvider):
    name = "openai"

    def _call(self, request: CompletionRequest) -> CompletionResponse:
        payload = {
            "model": self.model,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "messages": [
                {"role": "system", "content": request.system_prompt},
                {"role": "user", "content": request.user_prompt},
            ],
        }
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            _CHAT_COMPLETIONS_URL,
            data=body,
            method="POST",
            headers={
                "Authorization": "Bearer " + self._api_key,
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            # Re-raise without ever including headers/body that could contain the key.
            raise ProviderError(f"{self.name} request failed: {exc.reason}") from exc

        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return CompletionResponse(
            text=text,
            model=self.model,
            provider=self.name,
            prompt_tokens_estimate=usage.get("prompt_tokens", estimate_tokens(request.system_prompt + request.user_prompt)),
            completion_tokens_estimate=usage.get("completion_tokens", estimate_tokens(text)),
        )