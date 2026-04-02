from unittest.mock import MagicMock

from app.notifications.push import send_streak_protection_notification


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
