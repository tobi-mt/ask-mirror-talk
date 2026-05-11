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


def _clean_incomplete_redis_cache():
    """Clean incomplete answers from Redis cache (runs once per motivation check)."""
    try:
        from app.qa.cache import get_answer_cache, _is_incomplete_answer
        
        cache = get_answer_cache()
        
        if not cache._redis:
            # No Redis configured - skip cleanup
            return
        
        # Get all cache entry keys from Redis
        keys = cache._redis.zrange(cache._redis_index_key, 0, -1)
        
        if not keys:
            return
        
        deleted_count = 0
        
        for key in keys:
            raw = cache._redis.get(key)
            if raw is None:
                continue
            
            entry = cache._deserialize_entry(raw)
            if entry is None:
                continue
            
            answer = entry.response.get("answer", "")
            
            # Check if incomplete
            if _is_incomplete_answer(answer):
                deleted_count += 1
                logger.info("Cleaning incomplete cached answer from Redis: '%.50s...'", entry.question)
                
                # Delete from Redis
                cache._redis.delete(key)
                cache._redis.zrem(cache._redis_index_key, key)
        
        if deleted_count > 0:
            logger.info("✓ Cleaned %d incomplete answers from Redis cache", deleted_count)
    
    except Exception as e:
        logger.warning("Failed to clean incomplete Redis cache entries: %s", e)


def main():
    from app.core.db import get_session_local, safe_close_session
    from app.notifications.push import send_midday_motivation_notification
    from app.core.config import settings

    logger.info("☀️ Starting midday motivation push notification check...")
    
    # Clean incomplete answers from Redis cache (once per hour)
    _clean_incomplete_redis_cache()

    SessionLocal = get_session_local()
    max_attempts = 3
    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
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
            return
        except Exception as exc:
            last_error = exc
            safe_close_session(db, context=f"midday_motivation_attempt_{attempt}")
            db = None
            if not _is_transient_db_error(exc) or attempt >= max_attempts:
                break
            wait_seconds = attempt * 4
            logger.warning(
                "Midday motivation DB connection attempt %d/%d failed transiently: %s. Retrying in %ss...",
                attempt,
                max_attempts,
                exc,
                wait_seconds,
            )
            time.sleep(wait_seconds)
        finally:
            if db is not None:
                safe_close_session(db, context=f"midday_motivation_attempt_{attempt}")

    if last_error and _is_transient_db_error(last_error):
        logger.error(
            "✗ Midday motivation skipped after %d transient DB connection attempts: %s",
            max_attempts,
            last_error,
            exc_info=True,
        )
        print("⚠ Midday motivation skipped because the database connection timed out. The next hourly run will retry.")
        return

    logger.error("✗ Midday motivation failed: %s", last_error, exc_info=True)
    print(f"✗ Failed: {last_error}")
    sys.exit(1)


if __name__ == "__main__":
    main()
