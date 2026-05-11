"""Compatibility helpers for OpenAI chat model calls."""

from __future__ import annotations

from typing import Any


def is_reasoning_chat_model(model: str | None) -> bool:
    """Return True for newer reasoning-style chat models with stricter params."""
    name = (model or "").lower()
    return name.startswith(("gpt-5", "o1", "o3", "o4"))


def uses_max_completion_tokens(model: str | None) -> bool:
    """
    Return True for models that require max_completion_tokens instead of max_tokens.
    This includes reasoning models and newer GPT-4 models.
    """
    name = (model or "").lower()
    # Reasoning models (GPT-5, o1, o3, o4)
    if name.startswith(("gpt-5", "o1", "o3", "o4")):
        return True
    # Newer GPT-4 models that require max_completion_tokens
    if name.startswith(("gpt-4o", "gpt-4.1", "gpt-4-2024", "gpt-4-turbo-2024")):
        return True
    return False


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

    Newer models (GPT-5/o-series, GPT-4o, GPT-4.1+) use ``max_completion_tokens``
    and may reject older sampling controls. Older models keep legacy parameters.
    """
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        **extra,
    }

    if max_tokens is not None:
        if uses_max_completion_tokens(model):
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

    try:
        return client.chat.completions.create(**payload)
    except TypeError as exc:
        # Handle SDK compatibility issues with parameter names
        error_msg = str(exc)
        
        # If SDK rejects max_completion_tokens, retry with max_tokens
        if "max_completion_tokens" in error_msg and "unexpected keyword" in error_msg.lower():
            if "max_completion_tokens" in payload:
                legacy_payload = dict(payload)
                legacy_payload["max_tokens"] = legacy_payload.pop("max_completion_tokens")
                return client.chat.completions.create(**legacy_payload)
        
        # If SDK rejects max_tokens, retry with max_completion_tokens
        if "max_tokens" in error_msg and "unexpected keyword" in error_msg.lower():
            if "max_tokens" in payload:
                legacy_payload = dict(payload)
                legacy_payload["max_completion_tokens"] = legacy_payload.pop("max_tokens")
                return client.chat.completions.create(**legacy_payload)
        
        # Re-raise if it's not a parameter compatibility issue
        raise
    except Exception as exc:
        # Handle API-level parameter errors
        error_msg = str(exc)
        
        # If API says it wants the other parameter name
        if "max_tokens" in error_msg and "max_completion_tokens" in error_msg:
            if "max_tokens" in payload and "max_completion_tokens" not in payload:
                retry_payload = dict(payload)
                retry_payload["max_completion_tokens"] = retry_payload.pop("max_tokens")
                return client.chat.completions.create(**retry_payload)
            elif "max_completion_tokens" in payload and "max_tokens" not in payload:
                retry_payload = dict(payload)
                retry_payload["max_tokens"] = retry_payload.pop("max_completion_tokens")
                return client.chat.completions.create(**retry_payload)
        
        # Re-raise if it's not a parameter compatibility issue
        raise
