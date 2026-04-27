from app.qa.service import _ensure_answer_status_fields


def test_cached_basic_fallback_answer_is_rewritten_for_users():
    response = {
        "question": "What's the first step to breaking a bad habit?",
        "answer": "I found a few Mirror Talk moments connected to your question, but the match is not strong enough.",
    }

    sanitized = _ensure_answer_status_fields(response)

    assert sanitized["answer_status"] == "generation_failed"
    assert sanitized["answer_source"] == "basic_fallback"
    assert "I found a few Mirror Talk moments" not in sanitized["answer"]
    assert "polished reflection answer" in sanitized["answer"]
