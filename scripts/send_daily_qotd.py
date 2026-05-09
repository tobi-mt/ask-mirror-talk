#!/usr/bin/env python3
"""
Send Daily QOTD Push Notification.

This script sends the Question of the Day as a push notification to
subscribers whose *local time* currently matches their preferred QOTD hour
(default: 8 AM).  Run it **every hour** — Postgres handles the timezone
filtering so each subscriber receives exactly one QOTD per calendar day.

Usage:
  python3 scripts/send_daily_qotd.py

Cron example (every hour):
  0 * * * * cd /app && python3 scripts/send_daily_qotd.py

Railway cron: Set schedule to "0 * * * *" (hourly), start command above.
"""

import sys
import os
import logging
import time

from sqlalchemy.exc import DBAPIError, OperationalError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.logging import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


def _is_transient_db_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return isinstance(exc, (OperationalError, DBAPIError)) or any(
        marker in message
        for marker in (
            "connection timeout",
            "connection refused",
            "server closed the connection",
            "could not connect",
            "timeout expired",
            "consuming input failed",
        )
    )


def main():
    from app.core.db import get_session_local, safe_close_session
    from app.notifications.push import send_qotd_notification
    from app.core.config import settings

    logger.info("🔔 Starting daily QOTD push notification...")

    SessionLocal = get_session_local()
    max_attempts = 3
    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        db = SessionLocal()
        try:
            result = send_qotd_notification(db)
            logger.info("✓ QOTD notification complete: %s", result)

            if result["sent"] > 0:
                print(f"✓ Sent QOTD notification to {result['sent']} subscribers")
            elif result["failed"] > 0:
                if not settings.vapid_private_key or not settings.vapid_claim_email:
                    print("⚠ QOTD had subscribers due, but push is not configured locally (missing VAPID keys)")
                else:
                    print(f"⚠ QOTD attempted but {result['failed']} failed")
            elif result["total_subscribers"] == 0:
                print("ℹ No QOTD subscribers due at this hour")
            else:
                print(f"⚠ Notification attempted but {result['failed']} failed")
            return
        except Exception as exc:
            last_error = exc
            safe_close_session(db, context=f"qotd_attempt_{attempt}")
            db = None
            if not _is_transient_db_error(exc) or attempt >= max_attempts:
                break
            wait_seconds = attempt * 4
            logger.warning(
                "QOTD DB connection attempt %d/%d failed transiently: %s. Retrying in %ss...",
                attempt,
                max_attempts,
                exc,
                wait_seconds,
            )
            time.sleep(wait_seconds)
        finally:
            if db is not None:
                safe_close_session(db, context=f"qotd_attempt_{attempt}")

    if last_error and _is_transient_db_error(last_error):
        logger.error(
            "✗ QOTD skipped after %d transient DB connection attempts: %s",
            max_attempts,
            last_error,
            exc_info=True,
        )
        print("⚠ QOTD skipped because the database connection timed out. The next hourly run will retry.")
        return

    logger.error("✗ QOTD notification failed: %s", last_error, exc_info=True)
    print(f"✗ Failed: {last_error}")
    sys.exit(1)


if __name__ == "__main__":
    main()
