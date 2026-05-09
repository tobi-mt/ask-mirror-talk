#!/usr/bin/env python3
"""
Send streak-protection push notification.

Run this hourly so users whose local time is currently 20:00 get a gentle
nudge before midnight resets their streak.

Cron example (every hour):
  0 * * * * cd /app && python3 scripts/send_streak_protection.py

Railway: add as a second scheduled service or combine with the QOTD cron.
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
    from app.notifications.push import send_streak_protection_notification
    from app.core.config import settings

    logger.info("🔥 Sending streak-protection push notification…")

    SessionLocal = get_session_local()
    max_attempts = 3
    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        db = SessionLocal()
        try:
            result = send_streak_protection_notification(db)
            logger.info("✓ Streak protection complete: %s", result)

            if result["sent"] > 0:
                print(f"✓ Sent streak-protection nudge to {result['sent']} subscribers")
            elif result["failed"] > 0:
                if not settings.vapid_private_key or not settings.vapid_claim_email:
                    print("⚠ Streak protection had subscribers due, but push is not configured locally (missing VAPID keys)")
                else:
                    print(f"⚠ Streak protection attempted but {result['failed']} failed")
            elif result["total_subscribers"] == 0:
                print("ℹ No streak-protection subscribers due at this hour")
            else:
                print(f"⚠ Notification attempted but {result['failed']} failed")
            return
        except Exception as exc:
            last_error = exc
            safe_close_session(db, context=f"streak_protection_attempt_{attempt}")
            db = None
            if not _is_transient_db_error(exc) or attempt >= max_attempts:
                break
            wait_seconds = attempt * 4
            logger.warning(
                "Streak protection DB connection attempt %d/%d failed transiently: %s. Retrying in %ss...",
                attempt,
                max_attempts,
                exc,
                wait_seconds,
            )
            time.sleep(wait_seconds)
        finally:
            if db is not None:
                safe_close_session(db, context=f"streak_protection_attempt_{attempt}")

    if last_error and _is_transient_db_error(last_error):
        logger.error(
            "✗ Streak protection skipped after %d transient DB connection attempts: %s",
            max_attempts,
            last_error,
            exc_info=True,
        )
        print("⚠ Streak protection skipped because the database connection timed out. The next hourly run will retry.")
        return

    logger.error("✗ Streak protection notification failed: %s", last_error, exc_info=True)
    print(f"✗ Failed: {last_error}")
    sys.exit(1)


if __name__ == "__main__":
    main()
