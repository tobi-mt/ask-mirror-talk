#!/usr/bin/env python3
"""
Send streak-protection push notification.

Run this daily at ~20:00 UTC so users who haven't asked a question today
get a gentle nudge before midnight resets their streak.

Cron example (8 PM UTC daily):
  0 20 * * * cd /app && python3 scripts/send_streak_protection.py

Railway: add as a second scheduled service or combine with the QOTD cron.
"""

import sys
import os
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.logging import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


def main():
    from app.core.db import get_session_local
    from app.notifications.push import send_streak_protection_notification

    logger.info("🔥 Sending streak-protection push notification…")

    SessionLocal = get_session_local()
    db = SessionLocal()

    try:
        result = send_streak_protection_notification(db)
        logger.info("✓ Streak protection complete: %s", result)

        if result["sent"] > 0:
            print(f"✓ Sent streak-protection nudge to {result['sent']} subscribers")
        elif result["total_subscribers"] == 0:
            print("ℹ No active subscribers yet")
        else:
            print(f"⚠ Notification attempted but {result['failed']} failed")

    except Exception as e:
        logger.error("✗ Streak protection notification failed: %s", e, exc_info=True)
        print(f"✗ Failed: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
