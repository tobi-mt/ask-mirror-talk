import logging
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBasicCredentials
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.auth import admin_auth, get_client_ip, security
from app.core.config import settings
from app.core.db import get_db
from app.notifications.subscription_health import (
    ensure_push_subscription_health_schema,
    record_subscription_event,
    subscription_counts,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _sanitize_timezone(raw_timezone: str | None) -> str:
    """Return a safe IANA timezone string, defaulting to UTC when invalid."""
    candidate = (raw_timezone or "").strip()
    if not candidate or len(candidate) > 100:
        return "UTC"
    try:
        ZoneInfo(candidate)
        return candidate
    except (ZoneInfoNotFoundError, ValueError):
        return "UTC"


class PushSubscriptionRequest(BaseModel):
    endpoint: str
    keys: dict
    notify_qotd: bool = True
    notify_new_episodes: bool = True
    notify_midday: bool = True
    timezone: str = "UTC"
    preferred_qotd_hour: int = 8


class PushPreferencesRequest(BaseModel):
    endpoint: str
    notify_qotd: bool = True
    notify_new_episodes: bool = True
    notify_midday: bool = True


class PushHeartbeatRequest(BaseModel):
    endpoint: str


class PushRecoveryRequest(BaseModel):
    endpoint: str
    keys: dict
    timezone: str = "UTC"
    preferred_qotd_hour: int = 8


@router.get("/api/push/vapid-key")
def get_vapid_public_key():
    """Return the VAPID public key so the browser can subscribe."""
    if not settings.vapid_public_key:
        raise HTTPException(status_code=503, detail="Push notifications not configured")
    return {"public_key": settings.vapid_public_key}


@router.post("/api/push/subscribe")
def push_subscribe(
    payload: PushSubscriptionRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Register or reactivate a browser push subscription."""
    if not settings.vapid_public_key:
        raise HTTPException(status_code=503, detail="Push notifications not configured")

    ensure_push_subscription_health_schema(db)

    p256dh = payload.keys.get("p256dh", "")
    auth = payload.keys.get("auth", "")
    if not p256dh or not auth:
        raise HTTPException(status_code=400, detail="Missing p256dh or auth key")

    try:
        tz = _sanitize_timezone(payload.timezone)
        qotd_hour = max(0, min(23, payload.preferred_qotd_hour))

        subscription_id = db.execute(
            text("""
                INSERT INTO push_subscriptions (endpoint, p256dh_key, auth_key, user_ip,
                                                 active, notify_qotd, notify_new_episodes,
                                                 notify_midday, timezone, preferred_qotd_hour,
                                                 created_at, updated_at, last_seen_at)
                VALUES (:endpoint, :p256dh, :auth, :ip, true, :qotd, :episodes,
                        :midday, :tz, :qotd_hour, NOW(), NOW(), NOW())
                ON CONFLICT (endpoint)
                DO UPDATE SET
                    p256dh_key = :p256dh,
                    auth_key = :auth,
                    user_ip = :ip,
                    active = true,
                    notify_qotd = :qotd,
                    notify_new_episodes = :episodes,
                    notify_midday = :midday,
                    timezone = :tz,
                    preferred_qotd_hour = :qotd_hour,
                    last_seen_at = NOW(),
                    deactivated_at = NULL,
                    deactivation_reason = NULL,
                    consecutive_failures = 0,
                    updated_at = NOW()
                RETURNING id
            """),
            {
                "endpoint": payload.endpoint,
                "p256dh": p256dh,
                "auth": auth,
                "ip": get_client_ip(request),
                "qotd": payload.notify_qotd,
                "episodes": payload.notify_new_episodes,
                "midday": payload.notify_midday,
                "tz": tz,
                "qotd_hour": qotd_hour,
            },
        ).scalar()
        record_subscription_event(
            db,
            endpoint=payload.endpoint,
            subscription_id=subscription_id,
            event_type="subscribed",
            reason="explicit_browser_consent",
        )
        db.commit()

        subscriber_count = db.execute(
            text("SELECT COUNT(*) FROM push_subscriptions WHERE active = true")
        ).scalar()

        logger.info(
            "Push subscription registered from %s (total active: %d)",
            get_client_ip(request),
            subscriber_count,
        )
        return {"status": "subscribed", "total_subscribers": subscriber_count}
    except Exception as e:
        db.rollback()
        logger.error("Push subscription error: %s", e)
        raise HTTPException(status_code=500, detail="Failed to save subscription") from e


@router.post("/api/push/recover")
def recover_push_subscription(
    payload: PushRecoveryRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Recover a browser-confirmed subscription without overwriting preferences.

    This endpoint is intentionally separate from ``subscribe``.  Existing
    notification choices are retained, explicit opt-outs are respected, and a
    provider-confirmed expired endpoint must be renewed in the browser first.
    """

    if not settings.vapid_public_key:
        raise HTTPException(status_code=503, detail="Push notifications not configured")
    p256dh = payload.keys.get("p256dh", "")
    auth = payload.keys.get("auth", "")
    if not p256dh or not auth:
        raise HTTPException(status_code=400, detail="Missing p256dh or auth key")

    ensure_push_subscription_health_schema(db)
    existing = db.execute(
        text("""
            SELECT id, active, deactivation_reason, p256dh_key, auth_key
            FROM push_subscriptions
            WHERE endpoint = :endpoint
        """),
        {"endpoint": payload.endpoint},
    ).mappings().first()
    if existing and not existing["active"]:
        reason = existing["deactivation_reason"] or "legacy_inactive"
        if reason == "user_unsubscribed":
            raise HTTPException(status_code=409, detail="User opted out")
        renewed_keys = existing["p256dh_key"] != p256dh or existing["auth_key"] != auth
        if reason == "endpoint_expired" and not renewed_keys:
            raise HTTPException(status_code=409, detail="Browser subscription must be renewed")

    tz = _sanitize_timezone(payload.timezone)
    qotd_hour = max(0, min(23, payload.preferred_qotd_hour))
    try:
        subscription_id = db.execute(text("""
            INSERT INTO push_subscriptions
              (endpoint, p256dh_key, auth_key, user_ip, active, notify_qotd,
               notify_new_episodes, notify_midday, timezone,
               preferred_qotd_hour, created_at, updated_at, last_seen_at)
            VALUES
              (:endpoint, :p256dh, :auth, :ip, true, true, false, false,
               :tz, :qotd_hour, NOW(), NOW(), NOW())
            ON CONFLICT (endpoint)
            DO UPDATE SET
              p256dh_key = :p256dh,
              auth_key = :auth,
              user_ip = :ip,
              active = true,
              timezone = :tz,
              preferred_qotd_hour = :qotd_hour,
              updated_at = NOW(),
              last_seen_at = NOW(),
              deactivated_at = NULL,
              deactivation_reason = NULL,
              consecutive_failures = 0
            RETURNING id
        """), {
            "endpoint": payload.endpoint,
            "p256dh": p256dh,
            "auth": auth,
            "ip": get_client_ip(request),
            "tz": tz,
            "qotd_hour": qotd_hour,
        }).scalar()
        record_subscription_event(
            db,
            endpoint=payload.endpoint,
            subscription_id=subscription_id,
            event_type="recovered",
            reason="browser_subscription_confirmed",
        )
        db.commit()
        return {"status": "recovered"}
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        logger.error("Push recovery error: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to recover subscription") from exc


@router.post("/api/push/unsubscribe")
def push_unsubscribe(
    payload: dict,
    request: Request,
    db: Session = Depends(get_db),
):
    """Deactivate a push subscription."""
    endpoint = payload.get("endpoint", "")
    if not endpoint:
        raise HTTPException(status_code=400, detail="Missing endpoint")

    try:
        ensure_push_subscription_health_schema(db)
        subscription_id = db.execute(
            text("SELECT id FROM push_subscriptions WHERE endpoint = :endpoint"),
            {"endpoint": endpoint},
        ).scalar()
        db.execute(
            text("""
                UPDATE push_subscriptions
                SET active = false, updated_at = NOW(), deactivated_at = NOW(),
                    deactivation_reason = 'user_unsubscribed'
                WHERE endpoint = :endpoint
            """),
            {"endpoint": endpoint},
        )
        record_subscription_event(
            db,
            endpoint=endpoint,
            subscription_id=subscription_id,
            event_type="deactivated",
            reason="user_unsubscribed",
        )
        db.commit()
        logger.info("Push subscription deactivated from %s", get_client_ip(request))
        return {"status": "unsubscribed"}
    except Exception as e:
        db.rollback()
        logger.error("Push unsubscribe error: %s", e)
        raise HTTPException(status_code=500, detail="Failed to unsubscribe") from e


@router.put("/api/push/preferences")
def update_push_preferences(
    payload: PushPreferencesRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Update notification preferences for an existing subscription."""
    try:
        result = db.execute(
            text("""
                UPDATE push_subscriptions
                SET notify_qotd = :qotd,
                    notify_new_episodes = :episodes,
                    notify_midday = :midday,
                    user_ip = :ip,
                    updated_at = NOW()
                WHERE endpoint = :endpoint AND active = true
            """),
            {
                "endpoint": payload.endpoint,
                "qotd": payload.notify_qotd,
                "episodes": payload.notify_new_episodes,
                "midday": payload.notify_midday,
                "ip": get_client_ip(request),
            },
        )
        db.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Subscription not found")

        logger.info("Push preferences updated from %s", get_client_ip(request))
        return {"status": "updated"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Push preferences error: %s", e)
        raise HTTPException(status_code=500, detail="Failed to update preferences") from e


@router.post("/api/push/heartbeat")
def push_heartbeat(
    payload: PushHeartbeatRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Refresh last-seen activity for an existing subscription."""
    try:
        ensure_push_subscription_health_schema(db)
        result = db.execute(
            text("""
                UPDATE push_subscriptions
                SET user_ip = :ip,
                    last_seen_at = NOW(),
                    updated_at = NOW()
                WHERE endpoint = :endpoint AND active = true
            """),
            {
                "endpoint": payload.endpoint,
                "ip": get_client_ip(request),
            },
        )
        db.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Subscription not found")

        return {"status": "ok"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Push heartbeat error: %s", e)
        raise HTTPException(status_code=500, detail="Failed to refresh push heartbeat") from e


@router.post("/api/push/send-qotd")
def send_qotd_push(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Admin endpoint: send today's QOTD push notification."""
    admin_auth(credentials, request)

    from app.notifications.push import send_qotd_notification

    return send_qotd_notification(db)


@router.post("/api/push/send-new-episode")
def send_new_episode_push(
    payload: dict,
    request: Request,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Admin endpoint: notify subscribers about a new episode."""
    admin_auth(credentials, request)

    title = payload.get("episode_title", "")
    episode_id = payload.get("episode_id", 0)
    if not title or not episode_id:
        raise HTTPException(status_code=400, detail="Missing episode_title or episode_id")

    from app.notifications.push import send_new_episode_notification

    return send_new_episode_notification(db, title, episode_id)


@router.post("/api/push/send-midday")
def send_midday_push(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Admin endpoint: send midday motivation push notification."""
    admin_auth(credentials, request)

    from app.notifications.push import send_midday_motivation_notification

    return send_midday_motivation_notification(db)


@router.post("/api/push/send-nightly")
def send_nightly_push(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Admin endpoint: send nightly reflection push notification."""
    admin_auth(credentials, request)

    from app.notifications.push import send_nightly_reflection_notification

    return send_nightly_reflection_notification(db)


@router.get("/api/push/stats")
def get_push_stats(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Admin endpoint: get push subscription statistics."""
    admin_auth(credentials, request)

    counts = subscription_counts(db, include_due=True)
    total = counts["total"]
    active = counts["active"]
    qotd_enabled = db.execute(
        text("SELECT COUNT(*) FROM push_subscriptions WHERE active = true AND notify_qotd = true")
    ).scalar() or 0
    episodes_enabled = db.execute(
        text("SELECT COUNT(*) FROM push_subscriptions WHERE active = true AND notify_new_episodes = true")
    ).scalar() or 0
    reflections_enabled = db.execute(
        text("SELECT COUNT(*) FROM push_subscriptions WHERE active = true AND notify_midday = true")
    ).scalar() or 0

    return {
        "total_subscriptions": total,
        "active": active,
        "inactive": total - active,
        "qotd_enabled": qotd_enabled,
        "reflection_nudges_enabled": reflections_enabled,
        "new_episodes_enabled": episodes_enabled,
        "due_qotd_now": counts["due_now"],
        "expired": counts["expired"],
        "user_unsubscribed": counts["unsubscribed"],
    }
