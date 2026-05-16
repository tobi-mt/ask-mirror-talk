"""
feedback_logger.py
Utility for logging user feedback on quote selection (shares, likes, skips).
"""
import logging

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

def log_quote_feedback(candidate, feedback_type, user_context=None):
    """
    Log user feedback for a quote candidate.
    feedback_type: 'share', 'like', 'skip', etc.
    user_context: dict with user/session info, theme, etc.
    Engagement depth is weighted for analytics.
    """
    logger = logging.getLogger("quote_feedback")
    engagement_weights = {"share": 2.0, "like": 1.0, "skip": -1.0}
    weight = engagement_weights.get(feedback_type, 0.5)
    logger.info(
        "Feedback: %s | Weight: %s | Text: %s | Meta: %s | Context: %s",
        feedback_type,
        weight,
        candidate.text,
        candidate.meta,
        user_context,
    )
    # Optionally trigger monitoring hooks.
    if user_context and user_context.get('monitoring_logger'):
        user_context['monitoring_logger']({'feedback': feedback_type, 'weight': weight, 'text': candidate.text})

def collect_feedback_for_tuning(db, days: int = 7) -> list[dict]:
    """
    Collect recent feedback logs for tuning the quote selection system.
    Returns a list of feedback dicts: {'quote_id', 'feedback_type', 'score', ...}
    Supports analytics/testing.
    """
    try:
        rows = db.execute(
            text(
                """
                SELECT qotd_id, feedback_type, score, created_at
                FROM quote_feedback
                WHERE created_at >= NOW() - make_interval(days => :days)
                """
            ),
            {"days": days},
        ).fetchall()
    except SQLAlchemyError:
        # Fail-soft so cron pipelines continue even if feedback table is absent.
        return []
    return [
        {'quote_id': r[0], 'feedback_type': r[1], 'score': r[2], 'created_at': r[3]} for r in rows
    ]
