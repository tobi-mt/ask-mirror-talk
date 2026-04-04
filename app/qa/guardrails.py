from __future__ import annotations

from dataclasses import dataclass
import logging
import re

from app.core.config import settings


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GuardrailDecision:
    allowed: bool
    code: str = "allow"
    message: str = ""


_PROMPT_INJECTION_PATTERNS = [
    r"\bignore (all|any|the|your) (previous|prior|earlier) instructions\b",
    r"\breveal (your|the) (system|hidden|developer) prompt\b",
    r"\bshow (me )?(your|the) (system|hidden|developer) prompt\b",
    r"\bbypass (your|the)? ?guardrails\b",
    r"\bjailbreak\b",
    r"\bdeveloper message\b",
    r"\bsystem prompt\b",
]

_SELF_HARM_PATTERNS = [
    r"\b(how do i|how to|help me|ways to|best way to|teach me to)\b.{0,80}\b(kill myself|end my life|commit suicide|hurt myself|self harm)\b",
    r"\b(suicide method|self-harm method)\b",
]

_VIOLENT_WRONGDOING_PATTERNS = [
    r"\b(how do i|how to|help me|ways to|best way to|teach me to|show me how to)\b.{0,100}\b(kill|murder|stab|shoot|poison|bomb|attack|hurt someone|make a bomb)\b",
    r"\b(write|draft|generate)\b.{0,80}\b(death threat|violent threat)\b",
]

_ILLEGAL_WRONGDOING_PATTERNS = [
    r"\b(how do i|how to|help me|ways to|best way to|teach me to|show me how to)\b.{0,120}\b(hack|phish|scam|steal|fraud|launder money|forge|ddos|blackmail|extort)\b",
    r"\b(write|draft|generate)\b.{0,80}\b(phishing email|scam message|fraud message|blackmail message)\b",
]

_EXPLOITATIVE_PATTERNS = [
    r"\b(write|draft|generate)\b.{0,120}\b(hate speech|racist rant|abusive message|revenge porn|non-consensual sexual)\b",
    r"\b(child porn|sexual content with minors|underage sexual)\b",
    r"\bhow to manipulate\b.{0,80}\b(partner|girlfriend|boyfriend|wife|husband|someone)\b",
]


def _matches_any(question: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, question, flags=re.IGNORECASE | re.DOTALL) for pattern in patterns)


def inspect_question(question: str) -> GuardrailDecision:
    lowered = (question or "").strip().lower()
    if not lowered:
        return GuardrailDecision(allowed=True)

    if _matches_any(lowered, _PROMPT_INJECTION_PATTERNS):
        logger.info("Guardrail blocked prompt-injection style request: %.120s", question)
        return GuardrailDecision(
            allowed=False,
            code="prompt_injection",
            message="I can't help with hidden instructions, system prompts, or attempts to bypass the app.",
        )

    if _matches_any(lowered, _SELF_HARM_PATTERNS):
        logger.warning("Guardrail blocked self-harm instruction request: %.120s", question)
        return GuardrailDecision(
            allowed=False,
            code="self_harm",
            message=(
                "I can't help with instructions for self-harm. "
                "If this is personal or urgent, contact local emergency services or a crisis line right now."
            ),
        )

    if _matches_any(lowered, _VIOLENT_WRONGDOING_PATTERNS):
        logger.warning("Guardrail blocked violent wrongdoing request: %.120s", question)
        return GuardrailDecision(
            allowed=False,
            code="violent_wrongdoing",
            message="I can't help with harming someone, planning violence, or creating violent threats.",
        )

    if _matches_any(lowered, _ILLEGAL_WRONGDOING_PATTERNS):
        logger.warning("Guardrail blocked illegal wrongdoing request: %.120s", question)
        return GuardrailDecision(
            allowed=False,
            code="illegal_wrongdoing",
            message="I can't help with illegal, deceptive, or exploitative instructions like hacking, phishing, fraud, or theft.",
        )

    if _matches_any(lowered, _EXPLOITATIVE_PATTERNS):
        logger.warning("Guardrail blocked exploitative request: %.120s", question)
        return GuardrailDecision(
            allowed=False,
            code="exploitative_content",
            message="I can't help create abusive, hateful, sexually exploitative, or manipulative content.",
        )

    return GuardrailDecision(allowed=True)


def log_guardrail_block(
    *,
    question: str,
    user_ip: str,
    decision: GuardrailDecision,
    route: str,
) -> None:
    """Log blocked prompts as privacy-conscious product events."""
    if not settings.question_guardrails_enabled or decision.allowed:
        return

    try:
        from app.core.db import get_session_local, safe_close_session
        from app.storage.repository import log_product_event

        SessionLocal = get_session_local()
        db = SessionLocal()
        try:
            log_product_event(
                db,
                event_name="guardrail_blocked",
                user_ip=user_ip,
                qa_log_id=None,
                metadata={
                    "category": decision.code,
                    "route": route,
                    "question_length": len((question or "").strip()),
                },
            )
        finally:
            safe_close_session(db, context="guardrail_block_event")
    except Exception as exc:
        logger.warning("Failed to log guardrail block event: %s", exc)
