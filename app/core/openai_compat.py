"""Compatibility helpers for OpenAI chat model calls."""

from __future__ import annotations

import logging
from functools import lru_cache
from importlib import import_module
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

_semantic_model_state: dict[str, str | None] = {"disabled_reason": None}

@lru_cache(maxsize=1)
def _load_primary_model():
    pipeline = getattr(import_module("transformers"), "pipeline")
    return pipeline(
        "sentiment-analysis",
        model="distilbert-base-uncased-finetuned-sst-2-english",
    )


@lru_cache(maxsize=1)
def _load_secondary_model():
    pipeline = getattr(import_module("transformers"), "pipeline")
    return pipeline(
        "sentiment-analysis",
        model="cardiffnlp/twitter-roberta-base-sentiment-latest",
    )

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
                if is_reasoning_chat_model(model):
                    # Do not downgrade reasoning/newer models to max_tokens; the API
                    # rejects that parameter and this would mask the real SDK mismatch.
                    logger.warning(
                        "OpenAI SDK rejected max_completion_tokens for model %s; "
                        "upgrade the OpenAI SDK to support this model family.",
                        model,
                    )
                    raise
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
        # Handle API-level parameter errors (BadRequestError from OpenAI)
        error_msg = str(exc).lower()
        
        # Check if it's a max_tokens/max_completion_tokens parameter error
        is_max_tokens_error = (
            "max_tokens" in error_msg 
            and ("max_completion_tokens" in error_msg or "unsupported parameter" in error_msg)
        )
        is_max_completion_tokens_error = (
            "max_completion_tokens" in error_msg 
            and ("max_tokens" in error_msg or "unsupported parameter" in error_msg)
        )
        
        # If API says max_tokens is not supported, use max_completion_tokens
        if is_max_tokens_error and "max_tokens" in payload:
            retry_payload = dict(payload)
            token_value = retry_payload.pop("max_tokens")
            retry_payload["max_completion_tokens"] = token_value
            logger.info(
                "OpenAI API rejected max_tokens for model %s, retrying with max_completion_tokens",
                model
            )
            return client.chat.completions.create(**retry_payload)
        
        # If API says max_completion_tokens is not supported, use max_tokens
        if is_max_completion_tokens_error and "max_completion_tokens" in payload:
            retry_payload = dict(payload)
            token_value = retry_payload.pop("max_completion_tokens")
            retry_payload["max_tokens"] = token_value
            logger.info(
                "OpenAI API rejected max_completion_tokens for model %s, retrying with max_tokens",
                model
            )
            return client.chat.completions.create(**retry_payload)
        
        # Re-raise if it's not a parameter compatibility issue
        raise


def openai_semantic_score(text: str, context: dict = None) -> float:
    """
    Use a transformer model to score the semantic/emotional resonance of the text.
    Returns a float between 0 and 1 (higher is more positive/engaging).
    """
    _ = context
    if not settings.quote_selector_model_enabled:
        return 0.5

    if _semantic_model_state["disabled_reason"]:
        return 0.5

    if not text or not text.strip():
        return 0.0

    try:
        result = _load_primary_model()(text)
        label = str(result[0]["label"]).upper()
        score = float(result[0]["score"])
        primary_score = score if "POS" in label else 1.0 - score

        if settings.quote_selector_ensemble_enabled:
            second = _load_secondary_model()(text)
            label2 = str(second[0]["label"]).upper()
            score2 = float(second[0]["score"])
            secondary_score = score2 if "POS" in label2 else 1.0 - score2
            return (primary_score * 0.7) + (secondary_score * 0.3)

        return primary_score
    except ModuleNotFoundError as exc:
        if settings.quote_selector_fallback_enabled:
            _semantic_model_state["disabled_reason"] = str(exc)
            logger.warning(
                "Transformers unavailable; semantic scoring disabled for this process: %s",
                exc,
            )
            return 0.5
        raise
    except NameError as exc:
        if settings.quote_selector_fallback_enabled:
            _semantic_model_state["disabled_reason"] = str(exc)
            logger.warning(
                "Semantic model dependency missing; semantic scoring disabled for this process: %s",
                exc,
            )
            return 0.5
        raise
    except Exception as exc:
        if settings.quote_selector_fallback_enabled:
            _semantic_model_state["disabled_reason"] = str(exc)
            logger.warning(
                "Semantic model failed; semantic scoring disabled for this process: %s",
                exc,
            )
            return 0.5
        raise
