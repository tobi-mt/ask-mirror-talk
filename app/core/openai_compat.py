"""Compatibility helpers for OpenAI chat model calls."""

from __future__ import annotations

from typing import Any


def is_reasoning_chat_model(model: str | None) -> bool:
    """Return True for newer reasoning-style chat models with stricter params."""
    name = (model or "").lower()
    return name.startswith(("gpt-5", "o1", "o3", "o4"))


def create_chat_completion(
    client: Any,
    *,
    model: str,
    messages: list[dict[str, str]],
    max_tokens: int | None = None,
    temperature: float | None = None,
    presence_penalty: float | None = None,
    frequency_penalty: float | None = None,
    stream: bool = False,
    **extra: Any,
) -> Any:
    """Create a Chat Completions response with model-compatible parameters.

    GPT-5/o-series chat models use ``max_completion_tokens`` and reject several
    older sampling controls. Older chat models keep the legacy parameters.
    """
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        **extra,
    }

    if max_tokens is not None:
        if is_reasoning_chat_model(model):
            payload["max_completion_tokens"] = max_tokens
        else:
            payload["max_tokens"] = max_tokens

    if stream:
        payload["stream"] = True

    if not is_reasoning_chat_model(model):
        if temperature is not None:
            payload["temperature"] = temperature
        if presence_penalty is not None:
            payload["presence_penalty"] = presence_penalty
        if frequency_penalty is not None:
            payload["frequency_penalty"] = frequency_penalty

    return client.chat.completions.create(**payload)
