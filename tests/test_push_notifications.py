from unittest.mock import MagicMock

from app.notifications.push import (
    _midday_copy,
    _night_reflection_copy,
    _qotd_copy,
    send_streak_protection_notification,
)


def test_streak_protection_skips_users_active_today():
    db = MagicMock()
    execute_result = MagicMock()
    execute_result.fetchall.return_value = []
    db.execute.return_value = execute_result

    result = send_streak_protection_notification(db)

    assert result["sent"] == 0
    statement = db.execute.call_args[0][0]
    sql_text = str(statement)
    assert "FROM qa_logs q" in sql_text
    assert "q.user_ip = w.user_ip" in sql_text
    assert "NOT EXISTS" in sql_text


def test_qotd_copy_is_human_complete_and_not_generic():
    title, body = _qotd_copy(
        "How do I stop abandoning myself just to keep the peace?",
        "Boundaries",
        "Return to Yourself",
        recent_theme=None,
        is_returning=False,
    )

    assert title == "Return to Yourself"
    assert "A grounded answer is ready" not in body
    assert "Open for" not in body
    assert body.endswith("?")
    assert "abandoning myself" in body


def test_qotd_copy_preserves_mirror_talk_question_text():
    title, body = _qotd_copy(
        "What does Mirror Talk teach about the power of community?",
        "Community",
        None,
        recent_theme=None,
        is_returning=False,
    )

    assert title == "Who strengthens you?"
    assert "What does Mirror Talk teach about the power of community?" in body
    assert "What does teach" not in body
    assert "??" not in body


def test_qotd_copy_uses_safe_teaser_for_long_questions():
    _title, body = _qotd_copy(
        "How do I stop abandoning myself to keep the peace when the people I love expect me to say yes before I have listened to myself?",
        "Boundaries",
        "Return to Yourself",
        recent_theme=None,
        is_returning=False,
    )

    assert len(body) <= 116
    assert body[-1] in ".?"
    assert "abandoning myself to keep the peace when" not in body
    assert "reflection is ready" in body.lower() or "today’s question" in body.lower()


def test_midday_copy_keeps_distinct_title_and_removes_cta():
    title, body = _midday_copy(
        "🌿 Come Back Inward",
        "You may not need more pressure today; you may need one honest pause. Ask Mirror Talk what is asking for care in me right now?",
        recent_theme="Self-worth",
        is_returning=True,
    )

    assert title == "Come Back Inward"
    assert "Ask Mirror Talk" not in body
    assert body.endswith(".")
    assert "pause Let" not in body
    assert len(body) <= 116


def test_nightly_reflection_copy_feels_complete_and_calm():
    title, body = _night_reflection_copy(recent_theme="Grief", is_returning=True)

    assert title
    assert body[-1] in ".?"
    assert len(body) <= 116
    assert "tonight" in body.lower() or "before" in body.lower()
    assert "Open for" not in body
