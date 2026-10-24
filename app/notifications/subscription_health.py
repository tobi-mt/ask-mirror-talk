"""Push-subscription lifecycle helpers.

The application originally stored only an ``active`` boolean.  That made a
healthy hourly cron run indistinguishable from a broken notification system
once all browser endpoints had expired.  These helpers add a small,
backwards-compatible audit layer and expose operational counts without ever
storing an endpoint in the event ledger.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

_schema_ready = False


def ensure_push_subscription_health_schema(db: Session) -> None:
    """Install the additive lifecycle schema once per process.

    Railway cron containers are short lived, so this deliberately uses
    idempotent DDL.  It lets the API and workers deploy safely even if a manual
    migration was not run first.
    """

    global _schema_ready
    if _schema_ready:
        return

    db.execute(text("""
        ALTER TABLE push_subscriptions
          ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMPTZ,
          ADD COLUMN IF NOT EXISTS last_delivery_at TIMESTAMPTZ,
          ADD COLUMN IF NOT EXISTS last_delivery_status VARCHAR(32),
          ADD COLUMN IF NOT EXISTS last_delivery_http_status SMALLINT,
          ADD COLUMN IF NOT EXISTS consecutive_failures INTEGER NOT NULL DEFAULT 0,
          ADD COLUMN IF NOT EXISTS deactivated_at TIMESTAMPTZ,
          ADD COLUMN IF NOT EXISTS deactivation_reason VARCHAR(64)
    """))
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS push_subscription_events (
          id BIGSERIAL PRIMARY KEY,
          subscription_id INTEGER,
          endpoint_hash VARCHAR(64) NOT NULL,
          event_type VARCHAR(48) NOT NULL,
          reason VARCHAR(80),
          http_status SMALLINT,
          notification_type VARCHAR(60),
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    db.execute(text("""
        CREATE INDEX IF NOT EXISTS push_subscription_events_created_idx
          ON push_subscription_events (created_at DESC)
    """))
    db.commit()
    _schema_ready = True


def endpoint_fingerprint(endpoint: str) -> str:
    """Return a one-way identifier suitable for the lifecycle ledger."""

    return hashlib.sha256((endpoint or "").encode("utf-8")).hexdigest()


def record_subscription_event(
    db: Session,
    *,
    endpoint: str,
    event_type: str,
    subscription_id: int | None = None,
    reason: str | None = None,
    http_status: int | None = None,
    notification_type: str | None = None,
) -> None:
    ensure_push_subscription_health_schema(db)
    db.execute(
        text("""
            INSERT INTO push_subscription_events
              (subscription_id, endpoint_hash, event_type, reason, http_status,
               notification_type, created_at)
            VALUES
              (:subscription_id, :endpoint_hash, :event_type, :reason,
               :http_status, :notification_type, NOW())
        """),
        {
            "subscription_id": subscription_id,
            "endpoint_hash": endpoint_fingerprint(endpoint),
            "event_type": event_type[:48],
            "reason": reason[:80] if reason else None,
            "http_status": http_status,
            "notification_type": notification_type[:60] if notification_type else None,
        },
    )


def subscription_counts(db: Session, *, include_due: bool = False) -> dict[str, int]:
    """Return truthful system-wide counts for logs and the admin endpoint."""

    ensure_push_subscription_health_schema(db)
    row = db.execute(text("""
        SELECT
          COUNT(*) AS total,
          COUNT(*) FILTER (WHERE active = true) AS active,
          COUNT(*) FILTER (WHERE active = false) AS inactive,
          COUNT(*) FILTER (WHERE active = true AND notify_qotd = true) AS qotd_enabled,
          COUNT(*) FILTER (WHERE deactivation_reason = 'endpoint_expired') AS expired,
          COUNT(*) FILTER (WHERE deactivation_reason = 'user_unsubscribed') AS unsubscribed
        FROM push_subscriptions
    """)).mappings().one()
    counts = {key: int(value or 0) for key, value in row.items()}

    if include_due:
        counts["due_now"] = int(db.execute(text("""
            SELECT COUNT(*)
            FROM push_subscriptions w
            WHERE w.active = true
              AND w.notify_qotd = true
              AND (
                    EXTRACT(HOUR FROM (NOW() AT TIME ZONE COALESCE(w.timezone, 'UTC'))) * 60
                    + EXTRACT(MINUTE FROM (NOW() AT TIME ZONE COALESCE(w.timezone, 'UTC')))
                  ) >= (w.preferred_qotd_hour * 60)
              AND (
                    EXTRACT(HOUR FROM (NOW() AT TIME ZONE COALESCE(w.timezone, 'UTC'))) * 60
                    + EXTRACT(MINUTE FROM (NOW() AT TIME ZONE COALESCE(w.timezone, 'UTC')))
                  ) < (w.preferred_qotd_hour * 60 + 120)
              AND NOT EXISTS (
                    SELECT 1 FROM push_qotd_history h
                    WHERE h.subscription_id = w.id
                      AND (h.sent_at AT TIME ZONE COALESCE(w.timezone, 'UTC'))::date
                          = (NOW() AT TIME ZONE COALESCE(w.timezone, 'UTC'))::date
              )
        """)).scalar() or 0)
    return counts


def mark_delivery_result(
    db: Session,
    *,
    subscription_id: int,
    endpoint: str,
    result: str,
    notification_type: str,
) -> None:
    """Persist delivery health and safely retire confirmed expired endpoints."""

    ensure_push_subscription_health_schema(db)
    expired_status = None
    if result.startswith("expired_"):
        try:
            expired_status = int(result.split("_", 1)[1])
        except (TypeError, ValueError):
            expired_status = None

    if result == "sent":
        db.execute(text("""
            UPDATE push_subscriptions
            SET last_delivery_at = NOW(), last_delivery_status = 'sent',
                last_delivery_http_status = NULL, consecutive_failures = 0
            WHERE id = :subscription_id
        """), {"subscription_id": subscription_id})
        return

    if expired_status in (404, 410):
        db.execute(text("""
            UPDATE push_subscriptions
            SET active = false, updated_at = NOW(), deactivated_at = NOW(),
                deactivation_reason = 'endpoint_expired',
                last_delivery_at = NOW(), last_delivery_status = 'expired',
                last_delivery_http_status = :http_status,
                consecutive_failures = consecutive_failures + 1
            WHERE id = :subscription_id
        """), {"subscription_id": subscription_id, "http_status": expired_status})
        record_subscription_event(
            db,
            endpoint=endpoint,
            subscription_id=subscription_id,
            event_type="deactivated",
            reason="endpoint_expired",
            http_status=expired_status,
            notification_type=notification_type,
        )
        return

    db.execute(text("""
        UPDATE push_subscriptions
        SET last_delivery_at = NOW(), last_delivery_status = 'failed',
            consecutive_failures = consecutive_failures + 1
        WHERE id = :subscription_id
    """), {"subscription_id": subscription_id})


def log_subscription_health(db: Session, *, context: str) -> dict[str, Any]:
    counts = subscription_counts(db, include_due=True)
    log = logger.warning if counts["active"] == 0 else logger.info
    log(
        "Push subscription health [%s]: total=%d active=%d inactive=%d "
        "qotd_enabled=%d due_now=%d expired=%d unsubscribed=%d",
        context,
        counts["total"], counts["active"], counts["inactive"],
        counts["qotd_enabled"], counts["due_now"], counts["expired"],
        counts["unsubscribed"],
    )
    return counts
