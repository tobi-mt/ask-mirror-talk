#!/usr/bin/env python3
"""
Send Daily QOTD Push Notification.

This script sends today's Question of the Day as a push notification
to all subscribed users. Run it daily via cron or Railway scheduled job.

Usage:
  python3 scripts/send_daily_qotd.py

Cron example (9 AM UTC daily):
  0 9 * * * cd /app && python3 scripts/send_daily_qotd.py

Railway cron: Add as a scheduled service with: python3 scripts/send_daily_qotd.py
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
    from app.notifications.push import send_qotd_notification

    logger.info("🔔 Starting daily QOTD push notification...")

    SessionLocal = get_session_local()
    db = SessionLocal()

    try:
        result = send_qotd_notification(db)
        logger.info("✓ QOTD notification complete: %s", result)

        if result["sent"] > 0:
            print(f"✓ Sent QOTD notification to {result['sent']} subscribers")
        elif result["total_subscribers"] == 0:
            print("ℹ No active subscribers yet")
        else:
            print(f"⚠ Notification attempted but {result['failed']} failed")

    except Exception as e:
        logger.error("✗ QOTD notification failed: %s", e, exc_info=True)
        print(f"✗ Failed: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
