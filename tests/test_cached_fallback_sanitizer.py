from app.qa.cache import AnswerCache
from app.qa.service import _ensure_answer_status_fields, _is_degraded_cached_answer


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
    assert _is_degraded_cached_answer(sanitized)


def test_answer_cache_does_not_store_generation_failed_responses():
    cache = AnswerCache()

    cache.put(
        "what's the first step to breaking a bad habit",
        [1.0, 0.0],
        {
            "answer": "I found related Mirror Talk material, but I could not generate the polished reflection answer cleanly just now.",
            "answer_source": "basic_fallback",
            "answer_status": "generation_failed",
            "citations": [],
        },
    )

    assert cache.stats()["entries"] == 0


def test_answer_cache_does_not_store_degraded_text_without_metadata():
    cache = AnswerCache()

    cache.put(
        "what's the first step to breaking a bad habit",
        [1.0, 0.0],
        {
            "answer": "I found related Mirror Talk material, but I could not generate the polished reflection answer cleanly just now.",
            "citations": [{"episode_id": 1}],
        },
    )

    assert cache.stats()["entries"] == 0
