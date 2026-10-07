import logging

import pytest

from app.qa.guardrails import inspect_question


@pytest.mark.parametrize(
    "question",
    [
        "I want to die",
        "I can't go on anymore",
        "I am planning to hurt myself",
        "Everyone would be better off dead",
        "I have a suicide plan",
    ],
)
def test_acute_distress_language_receives_immediate_support_response(question):
    decision = inspect_question(question)

    assert decision.allowed is False
    assert decision.code == "self_harm"
    assert "immediate human support" in decision.message
    assert "local emergency services" in decision.message
    assert "trusted person" in decision.message


def test_guardrail_logs_do_not_repeat_sensitive_question(caplog):
    sensitive_question = "I want to die and this exact sentence must not be logged"

    with caplog.at_level(logging.WARNING):
        decision = inspect_question(sensitive_question)

    assert decision.allowed is False
    assert sensitive_question not in caplog.text
    assert f"length={len(sensitive_question)}" in caplog.text


def test_non_crisis_reflection_remains_available():
    decision = inspect_question("How can I rebuild confidence after a difficult season?")

    assert decision.allowed is True
