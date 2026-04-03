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

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.logging import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


def main():
    from app.core.db import get_session_local
    from app.notifications.push import send_nightly_reflection_notification
    from app.core.config import settings

    logger.info("🌙 Starting nightly reflection push notification check...")

    SessionLocal = get_session_local()
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

    except Exception as e:
        logger.error("✗ Nightly reflection failed: %s", e, exc_info=True)
        print(f"✗ Failed: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
