import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBasicCredentials
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.auth import admin_auth, get_client_ip, security
from app.core.config import settings
from app.core.db import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


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

    p256dh = payload.keys.get("p256dh", "")
    auth = payload.keys.get("auth", "")
    if not p256dh or not auth:
        raise HTTPException(status_code=400, detail="Missing p256dh or auth key")

    try:
        tz = payload.timezone if payload.timezone and len(payload.timezone) <= 100 else "UTC"
        qotd_hour = max(0, min(23, payload.preferred_qotd_hour))

        db.execute(
            text("""
                INSERT INTO push_subscriptions (endpoint, p256dh_key, auth_key, user_ip,
                                                 active, notify_qotd, notify_new_episodes,
                                                 notify_midday, timezone, preferred_qotd_hour,
                                                 created_at, updated_at)
                VALUES (:endpoint, :p256dh, :auth, :ip, true, :qotd, :episodes,
                        :midday, :tz, :qotd_hour, NOW(), NOW())
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
                    updated_at = NOW()
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
        db.execute(
            text("UPDATE push_subscriptions SET active = false, updated_at = NOW() WHERE endpoint = :endpoint"),
            {"endpoint": endpoint},
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
        result = db.execute(
            text("""
                UPDATE push_subscriptions
                SET user_ip = :ip,
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

    total = db.execute(text("SELECT COUNT(*) FROM push_subscriptions")).scalar() or 0
    active = db.execute(text("SELECT COUNT(*) FROM push_subscriptions WHERE active = true")).scalar() or 0
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
    }
