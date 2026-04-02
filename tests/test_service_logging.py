from app.qa import service


class _ExactCacheOnly:
    def get_exact(self, question):
        return {
            "answer": "cached answer",
            "citations": [],
            "follow_up_questions": [],
        }


def test_answer_question_skips_logging_when_disabled(monkeypatch):
    monkeypatch.setattr(service, "get_answer_cache", lambda: _ExactCacheOnly())

    def _fail_log(*args, **kwargs):
        raise AssertionError("log_qa should not be called when log_interaction=False")

    monkeypatch.setattr(service, "log_qa", _fail_log)

    result = service.answer_question(
        db=object(),
        question="How do I heal?",
        user_ip="cache-prewarm",
        log_interaction=False,
    )

    assert result["answer"] == "cached answer"
    assert result["qa_log_id"] is None
    assert result["question"] == "How do I heal?"
