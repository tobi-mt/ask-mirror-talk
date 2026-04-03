#!/usr/bin/env python3
"""
Send Midday Motivation Push Notification.

Sends a short motivational message at local noon to subscribers who have
opted in.  Runs every hour via cron — Postgres filters to only those
subscribers whose local time is currently 12:xx.

Usage:
  python3 scripts/send_midday_motivation.py

Cron (run every hour, same job as QOTD):
  0 * * * * cd /app && python3 scripts/send_midday_motivation.py

Railway: Add as a scheduled service with cron "0 * * * *" and start
command "python3 scripts/send_midday_motivation.py", or combine with
send_daily_qotd.py in a single hourly runner script.
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
    from app.notifications.push import send_midday_motivation_notification
    from app.core.config import settings

    logger.info("☀️ Starting midday motivation push notification check...")

    SessionLocal = get_session_local()
    db = SessionLocal()

    try:
        result = send_midday_motivation_notification(db)
        logger.info("✓ Midday motivation complete: %s", result)

        if result["sent"] > 0:
            print(f"✓ Sent midday motivation to {result['sent']} subscribers")
        elif result["failed"] > 0:
            if not settings.vapid_private_key or not settings.vapid_claim_email:
                print("⚠ Midday motivation had subscribers due, but push is not configured locally (missing VAPID keys)")
            else:
                print(f"⚠ Midday motivation attempted but {result['failed']} failed")
        else:
            print("ℹ No subscribers due for midday motivation at this hour")

    except Exception as e:
        logger.error("✗ Midday motivation failed: %s", e, exc_info=True)
        print(f"✗ Failed: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
