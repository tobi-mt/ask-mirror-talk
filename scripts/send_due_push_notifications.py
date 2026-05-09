#!/usr/bin/env python3
"""
Send every due push notification for the current hour.

Use this as the preferred Railway cron entrypoint:

  Cron schedule: 0 * * * *
  Start command: python3 scripts/send_due_push_notifications.py

Each notification sender still performs its own local-time SQL filtering, so
running this hourly covers QOTD, midday nudges, streak protection, and nightly
reflection without needing four separate Railway cron services.
"""

import logging
import os
import sys
import time
from collections.abc import Callable

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


def _run_with_retries(label: str, sender: Callable, max_attempts: int = 3) -> dict:
    from app.core.db import get_session_local, safe_close_session

    SessionLocal = get_session_local()
    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        db = SessionLocal()
        try:
            result = sender(db)
            logger.info("✓ %s complete: %s", label, result)
            return result
        except Exception as exc:
            last_error = exc
            safe_close_session(db, context=f"{label}_attempt_{attempt}")
            db = None
            if not _is_transient_db_error(exc) or attempt >= max_attempts:
                break
            wait_seconds = attempt * 4
            logger.warning(
                "%s DB attempt %d/%d failed transiently: %s. Retrying in %ss...",
                label,
                attempt,
                max_attempts,
                exc,
                wait_seconds,
            )
            time.sleep(wait_seconds)
        finally:
            if db is not None:
                safe_close_session(db, context=f"{label}_attempt_{attempt}")

    if last_error and _is_transient_db_error(last_error):
        logger.error(
            "⚠ %s skipped after %d transient DB attempts: %s",
            label,
            max_attempts,
            last_error,
            exc_info=True,
        )
        return {"sent": 0, "failed": 0, "expired": 0, "total_subscribers": 0, "skipped": "transient_db"}

    logger.error("✗ %s failed: %s", label, last_error, exc_info=True)
    raise last_error or RuntimeError(f"{label} failed")


def main() -> None:
    from app.notifications.push import (
        send_midday_motivation_notification,
        send_nightly_reflection_notification,
        send_qotd_notification,
        send_streak_protection_notification,
    )

    jobs = (
        ("QOTD", send_qotd_notification),
        ("Midday motivation", send_midday_motivation_notification),
        ("Streak protection", send_streak_protection_notification),
        ("Nightly reflection", send_nightly_reflection_notification),
    )

    logger.info("🔔 Starting all due push notification checks...")
    summary = {}
    fatal_failures = 0

    for label, sender in jobs:
        try:
            summary[label] = _run_with_retries(label, sender)
        except Exception as exc:
            fatal_failures += 1
            summary[label] = {"error": str(exc)}

    logger.info("Push notification hourly summary: %s", summary)
    print(summary)

    if fatal_failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
