#!/usr/bin/env python3
"""
Send nightly reflection push notification.

Runs hourly; SQL filters to subscribers whose local time is currently 21:xx.
This first version reuses the existing reflection-oriented opt-in instead of
introducing a new preference column.
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
    from app.notifications.push import send_nightly_reflection_notification
    from app.core.config import settings

    logger.info("🌙 Starting nightly reflection push notification check...")

    SessionLocal = get_session_local()
    max_attempts = 3
    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        db = SessionLocal()
        try:
            result = send_nightly_reflection_notification(db)
            logger.info("✓ Nightly reflection complete: %s", result)

            if result["sent"] > 0:
                print(f"✓ Sent nightly reflection to {result['sent']} subscribers")
            elif result["failed"] > 0:
                if not settings.vapid_private_key or not settings.vapid_claim_email:
                    print("⚠ Nightly reflection had subscribers due, but push is not configured locally (missing VAPID keys)")
                else:
                    print(f"⚠ Nightly reflection attempted but {result['failed']} failed")
            else:
                print("ℹ No subscribers due for nightly reflection at this hour")
            return
        except Exception as exc:
            last_error = exc
            safe_close_session(db, context=f"nightly_reflection_attempt_{attempt}")
            db = None
            if not _is_transient_db_error(exc) or attempt >= max_attempts:
                break
            wait_seconds = attempt * 4
            logger.warning(
                "Nightly reflection DB connection attempt %d/%d failed transiently: %s. Retrying in %ss...",
                attempt,
                max_attempts,
                exc,
                wait_seconds,
            )
            time.sleep(wait_seconds)
        finally:
            if db is not None:
                safe_close_session(db, context=f"nightly_reflection_attempt_{attempt}")

    if last_error and _is_transient_db_error(last_error):
        logger.error(
            "✗ Nightly reflection skipped after %d transient DB connection attempts: %s",
            max_attempts,
            last_error,
            exc_info=True,
        )
        print("⚠ Nightly reflection skipped because the database connection timed out. The next hourly run will retry.")
        return

    logger.error("✗ Nightly reflection failed: %s", last_error, exc_info=True)
    print(f"✗ Failed: {last_error}")
    sys.exit(1)


if __name__ == "__main__":
    main()
