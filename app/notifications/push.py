"""
Web Push Notifications for Ask Mirror Talk.

Sends daily QOTD notifications and new episode alerts to subscribed users.
Uses the Web Push protocol with VAPID authentication.
"""

import json
import logging
from datetime import datetime, timezone

from pywebpush import webpush, WebPushException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_push_notification(
    subscription_info: dict,
    title: str,
    body: str,
    url: str = "/",
    icon: str = "/wp-content/themes/astra/pwa-icon-192.png",
    badge: str = "/wp-content/themes/astra/pwa-icon-192.png",
    tag: str = "mirror-talk",
    data: dict | None = None,
) -> str:
    """
    Send a push notification to a single subscriber.

    Returns:
        "sent"    — delivered successfully
        "expired" — subscription is gone (404/410), should be deactivated
        "failed"  — transient error, keep subscription active
    """
    if not settings.vapid_private_key or not settings.vapid_claim_email:
        logger.warning("Push notifications not configured (missing VAPID keys)")
        return "failed"

    payload = {
        "title": title,
        "body": body,
        "icon": icon,
        "badge": badge,
        "tag": tag,
        "url": url,
        "data": data or {},
    }

    try:
        webpush(
            subscription_info=subscription_info,
            data=json.dumps(payload),
            vapid_private_key=settings.vapid_private_key,
            vapid_claims={"sub": f"mailto:{settings.vapid_claim_email}"},
        )
        return "sent"
    except WebPushException as e:
        status_code = e.response.status_code if e.response else None
        if status_code in (404, 410):
            logger.info("Push subscription expired (HTTP %s), marking for removal", status_code)
            return "expired"
        else:
            logger.warning("Push notification failed (HTTP %s): %s", status_code, e)
            return "failed"
    except Exception as e:
        logger.error("Push notification error: %s", e, exc_info=True)
        return "failed"


def send_qotd_notification(db: Session) -> dict:
    """
    Send today's Question of the Day as a push notification to all subscribers.

    Returns:
        dict with sent/failed/expired counts
    """
    # Get today's QOTD (reuse the same logic as the API endpoint)
    from app.api.main import _QOTD_POOL

    today = datetime.now(timezone.utc).date()
    index = today.toordinal() % len(_QOTD_POOL)
    qotd = _QOTD_POOL[index]

    return _broadcast_notification(
        db=db,
        title=f"✨ {qotd['theme']} — Question of the Day",
        body=qotd["question"],
        url=f"/?utm_source=push&utm_medium=qotd&utm_campaign={today.isoformat()}#ask-mirror-talk-form",
        tag="qotd",
        notification_type="qotd",
    )


def send_new_episode_notification(
    db: Session,
    episode_title: str,
    episode_id: int,
) -> dict:
    """
    Notify subscribers about a newly ingested episode.

    Returns:
        dict with sent/failed/expired counts
    """
    return _broadcast_notification(
        db=db,
        title="🎙️ New Mirror Talk Episode",
        body=f'"{episode_title}" — Ask a question about this episode now!',
        url=f"/?utm_source=push&utm_medium=new_episode&utm_campaign=ep{episode_id}#ask-mirror-talk-form",
        tag=f"new-episode-{episode_id}",
        notification_type="new_episode",
        data={"episode_id": episode_id, "episode_title": episode_title},
    )


def _broadcast_notification(
    db: Session,
    title: str,
    body: str,
    url: str,
    tag: str,
    notification_type: str,
    data: dict | None = None,
) -> dict:
    """
    Send a notification to all active push subscribers.
    Automatically cleans up expired subscriptions.
    """
    # Fetch all active subscriptions
    rows = db.execute(
        text("""
            SELECT id, endpoint, p256dh_key, auth_key
            FROM push_subscriptions
            WHERE active = true
        """)
    ).fetchall()

    if not rows:
        logger.info("No active push subscribers for %s notification", notification_type)
        return {"sent": 0, "failed": 0, "expired": 0, "total_subscribers": 0}

    logger.info("Sending %s notification to %d subscribers", notification_type, len(rows))

    sent = 0
    failed = 0
    expired_ids: list[int] = []

    for row in rows:
        sub_id, endpoint, p256dh, auth = row
        subscription_info = {
            "endpoint": endpoint,
            "keys": {"p256dh": p256dh, "auth": auth},
        }

        result = send_push_notification(
            subscription_info=subscription_info,
            title=title,
            body=body,
            url=url,
            tag=tag,
            data=data,
        )

        if result == "sent":
            sent += 1
        elif result == "expired":
            failed += 1
            expired_ids.append(sub_id)
        else:
            failed += 1

    # Deactivate expired subscriptions
    if expired_ids:
        db.execute(
            text("UPDATE push_subscriptions SET active = false WHERE id = ANY(:ids)"),
            {"ids": expired_ids},
        )
        db.commit()
        logger.info("Deactivated %d expired push subscriptions", len(expired_ids))

    result = {
        "sent": sent,
        "failed": failed,
        "expired": len(expired_ids),
        "total_subscribers": len(rows),
    }
    logger.info("Push notification result: %s", result)
    return result
