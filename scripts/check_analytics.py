#!/usr/bin/env python3
"""Quick analytics health check."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from datetime import datetime, timedelta, timezone
from app.core.db import get_session_local

db = get_session_local()()
cutoff = datetime.now(timezone.utc) - timedelta(days=7)
try:
    total    = db.execute(text("SELECT COUNT(*) FROM qa_logs WHERE created_at >= :c"), {"c": cutoff}).scalar()
    users    = db.execute(text("SELECT COUNT(DISTINCT user_ip) FROM qa_logs WHERE created_at >= :c"), {"c": cutoff}).scalar()
    avg_lat  = db.execute(text("SELECT AVG(latency_ms) FROM qa_logs WHERE created_at >= :c"), {"c": cutoff}).scalar()
    unanswered = db.execute(text("SELECT COUNT(*) FROM qa_logs WHERE created_at >= :c AND is_answered = FALSE"), {"c": cutoff}).scalar()
    cached   = db.execute(text("SELECT COUNT(*) FROM qa_logs WHERE created_at >= :c AND is_cached = TRUE"), {"c": cutoff}).scalar()
    clicks   = db.execute(text("SELECT COUNT(*) FROM citation_clicks WHERE clicked_at >= :c"), {"c": cutoff}).scalar()
    fb       = db.execute(text("SELECT feedback_type, COUNT(*) FROM user_feedback GROUP BY feedback_type")).fetchall()

    print(f"Total questions (7d) : {total}")
    print(f"Unique users   (7d)  : {users}")
    print(f"Avg latency          : {round(avg_lat or 0)} ms")
    print(f"Is_answered=False    : {unanswered}")
    print(f"Is_cached=True       : {cached}")
    print(f"Citation clicks (7d) : {clicks}")
    print(f"Feedback (all time)  : {dict(fb)}")
    print("All queries OK ✅")
finally:
    db.close()
