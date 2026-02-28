"""
Web Push Notifications for Ask Mirror Talk.

Sends daily QOTD notifications and new episode alerts to subscribed users.
Uses the Web Push protocol with VAPID authentication.
"""

import base64
import json
import logging
from datetime import datetime, timezone

from pywebpush import webpush, WebPushException
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_vapid_private_key_b64() -> str:
    """
    Convert PEM-encoded VAPID private key to raw base64url format
    that pywebpush expects.

    pywebpush's webpush(vapid_private_key=...) expects a raw 32-byte
    EC private key encoded as base64url, NOT a PEM string.
    """
    pem_str = settings.vapid_private_key
    if not pem_str:
        return ""

    # If it's already base64url (no PEM markers), return as-is
    if not pem_str.strip().startswith("-----"):
        return pem_str

    # Parse PEM → extract raw 32-byte private number → base64url encode
    private_key = load_pem_private_key(pem_str.encode(), password=None)
    private_numbers = private_key.private_numbers()
    raw_bytes = private_numbers.private_value.to_bytes(32, byteorder="big")
    return base64.urlsafe_b64encode(raw_bytes).decode().rstrip("=")


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
        private_key_b64 = _get_vapid_private_key_b64()
        if not private_key_b64:
            logger.warning("Could not convert VAPID private key")
            return "failed"

        webpush(
            subscription_info=subscription_info,
            data=json.dumps(payload),
            vapid_private_key=private_key_b64,
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
    today = datetime.now(timezone.utc).date()
    index = today.toordinal() % len(_QOTD_POOL)
    qotd = _QOTD_POOL[index]

    return _broadcast_notification(
        db=db,
        title=f"\u2728 {qotd['theme']} \u2014 Question of the Day",
        body=qotd["question"],
        url=f"/ask-mirror-talk/?utm_source=push&utm_medium=qotd&utm_campaign={today.isoformat()}#ask-mirror-talk-form",
        tag="qotd",
        notification_type="qotd",
    )


# ── QOTD pool (self-contained so we don't need to import app.api.main) ──
_QOTD_POOL = [
    {"question": "How do I stop comparing myself to others?",               "theme": "Self-worth"},
    {"question": "What does it mean to truly forgive someone?",             "theme": "Forgiveness"},
    {"question": "How do I find peace when everything feels uncertain?",    "theme": "Inner peace"},
    {"question": "What's the difference between being busy and being productive?", "theme": "Purpose"},
    {"question": "How do I let go of things I can't control?",              "theme": "Surrender"},
    {"question": "What does it look like to lead with vulnerability?",      "theme": "Leadership"},
    {"question": "How can I rebuild trust after it's been broken?",         "theme": "Relationships"},
    {"question": "What role does gratitude play in overcoming hardship?",   "theme": "Gratitude"},
    {"question": "How do I know when it's time to walk away?",              "theme": "Boundaries"},
    {"question": "What does Mirror Talk say about healing from trauma?",    "theme": "Healing"},
    {"question": "How do I stay hopeful when grief feels overwhelming?",    "theme": "Grief"},
    {"question": "What can I do when fear is holding me back?",             "theme": "Fear"},
    {"question": "How do I raise kids who are emotionally resilient?",      "theme": "Parenting"},
    {"question": "What's the first step to breaking a bad habit?",          "theme": "Addiction"},
    {"question": "How do I have hard conversations without damaging the relationship?", "theme": "Communication"},
    {"question": "What does alignment between faith and action look like?", "theme": "Faith"},
    {"question": "How do I deal with loneliness even when I'm surrounded by people?", "theme": "Identity"},
    {"question": "What can I learn from failure?",                          "theme": "Growth"},
    {"question": "How do I set boundaries without feeling guilty?",         "theme": "Boundaries"},
    {"question": "What does it mean to live authentically?",                "theme": "Identity"},
    {"question": "How do I support someone who is grieving?",               "theme": "Grief"},
    {"question": "What does healthy ambition look like?",                   "theme": "Purpose"},
    {"question": "How do I find my voice when I've been silenced?",         "theme": "Empowerment"},
    {"question": "What's the connection between physical health and emotional healing?", "theme": "Healing"},
    {"question": "How do I move forward after a major life change?",        "theme": "Transition"},
    {"question": "What does Mirror Talk teach about the power of community?", "theme": "Community"},
    {"question": "How do I parent through my own unresolved pain?",         "theme": "Parenting"},
    {"question": "What does rest really look like in a culture of hustle?", "theme": "Inner peace"},
    {"question": "How do I love someone without losing myself?",            "theme": "Relationships"},
    {"question": "What does courage look like in everyday life?",           "theme": "Fear"},
    {"question": "How do I stop running from my emotions?",                 "theme": "Healing"},
    {"question": "What does Mirror Talk say about money and purpose?",       "theme": "Purpose"},
    {"question": "How do I handle criticism without shutting down?",         "theme": "Growth"},
    {"question": "What does it take to be a better spouse?",                "theme": "Relationships"},
    {"question": "How do I reconnect with my faith after doubt?",           "theme": "Faith"},
    {"question": "What does Mirror Talk teach about mental health?",        "theme": "Healing"},
    {"question": "How do I stop people-pleasing?",                          "theme": "Boundaries"},
    {"question": "What does surrender look like in practice?",              "theme": "Surrender"},
    {"question": "How do I raise my kids to know their worth?",             "theme": "Parenting"},
    {"question": "What's the difference between loneliness and solitude?",  "theme": "Inner peace"},
]


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
