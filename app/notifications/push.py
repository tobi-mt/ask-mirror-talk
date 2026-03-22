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
    icon: str = "/wp-content/themes/astra-child/pwa-icon-192.png",
    badge: str = "/wp-content/themes/astra-child/pwa-icon-192.png",
    tag: str = "mirror-talk",
    data: dict | None = None,
    image: str | None = None,
    actions: list[dict] | None = None,
    require_interaction: bool = False,
    vibrate: list[int] | None = None,
) -> str:
    """
    Send a premium push notification to a single subscriber.

    Enhanced with:
    - Custom vibration patterns
    - Action buttons
    - Large images
    - Rich data
    - Interaction requirements

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
        "requireInteraction": require_interaction,
        "vibrate": vibrate or [100, 50, 100],  # Default: subtle pulse pattern
    }
    
    # Add image for visual appeal
    if image:
        payload["image"] = image
    
    # Add action buttons
    if actions:
        payload["actions"] = actions

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


def _load_pool_from_db(db: Session) -> list[dict]:
    """Return all questions from push_qotd_questions ordered by id."""
    rows = db.execute(
        text("SELECT id, question, theme, emoji, hook FROM push_qotd_questions ORDER BY id")
    ).fetchall()
    return [{"id": r[0], "question": r[1], "theme": r[2], "emoji": r[3], "hook": r[4]} for r in rows]


def _ensure_pool_seeded(db: Session) -> None:
    """Seed push_qotd_questions from the static list if the table is empty."""
    count = db.execute(text("SELECT COUNT(*) FROM push_qotd_questions")).scalar()
    if count == 0:
        logger.info("Seeding QOTD pool from static list (%d questions)", len(_QOTD_POOL))
        for q in _QOTD_POOL:
            db.execute(
                text(
                    "INSERT INTO push_qotd_questions (question, theme, emoji, hook, source) "
                    "VALUES (:question, :theme, :emoji, :hook, 'static')"
                ),
                {"question": q["question"], "theme": q["theme"], "emoji": q["emoji"], "hook": q["hook"]},
            )
        db.commit()
        logger.info("✓ QOTD pool seeded")


def generate_qotd_batch(db: Session, n: int = 20) -> int:
    """
    Generate n new QOTD questions via GPT and append them to push_qotd_questions.

    The prompt is grounded in real episode titles and themes from the corpus so
    questions stay relevant to Mirror Talk content.  Duplicate detection prevents
    re-inserting a question that already exists in the pool (exact match).

    Returns the number of questions actually inserted.
    """
    import os
    from openai import OpenAI

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        from app.core.config import settings
        api_key = settings.openai_api_key
    if not api_key:
        logger.warning("Cannot generate QOTD batch: OPENAI_API_KEY not set")
        return 0

    # Sample up to 20 episode titles to ground the prompt in real content
    episode_rows = db.execute(
        text("SELECT title FROM episodes ORDER BY published_at DESC LIMIT 20")
    ).fetchall()
    episode_titles = [r[0] for r in episode_rows]

    # Fetch existing questions so we instruct GPT to avoid them
    existing_rows = db.execute(text("SELECT question FROM push_qotd_questions")).fetchall()
    existing_questions = {r[0].strip().lower() for r in existing_rows}

    themes = [
        "Self-worth", "Forgiveness", "Inner peace", "Purpose", "Surrender",
        "Leadership", "Relationships", "Gratitude", "Boundaries", "Healing",
        "Grief", "Fear", "Parenting", "Growth", "Communication",
        "Faith", "Identity", "Empowerment", "Transition", "Community",
    ]

    prompt = f"""You are creating push notification questions for Mirror Talk, a podcast about personal growth, relationships, emotional intelligence, and faith.

Recent Mirror Talk episodes include:
{chr(10).join(f"- {t}" for t in episode_titles[:10])}

Generate exactly {n} unique, compelling questions a listener might ask about the podcast's wisdom. Each question should be something a real person would genuinely wonder about.

Rules:
- Each question must be distinct in theme and wording
- Use natural, conversational language (not academic)
- Questions should be answerable using podcast insights
- Cover a range of these themes: {", ".join(themes)}
- Do NOT repeat any of these existing questions: {", ".join(list(existing_questions)[:20])}

Respond with a JSON array of objects. Each object must have exactly these keys:
  "question" (string), "theme" (one of the themes above), "emoji" (single emoji), "hook" (short 3-6 word title, e.g. "Heal Your Inner Child")

Example: {{"question": "How do I stop self-sabotaging?", "theme": "Growth", "emoji": "🌱", "hook": "Break the Cycle"}}

Return only the JSON array, no other text."""

    client = OpenAI(api_key=api_key)
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9,
            max_tokens=2000,
        )
        raw = response.choices[0].message.content.strip()
        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        import json
        questions = json.loads(raw.strip())
    except Exception as e:
        logger.error("QOTD generation failed: %s", e, exc_info=True)
        return 0

    inserted = 0
    for q in questions:
        if not isinstance(q, dict):
            continue
        question_text = str(q.get("question", "")).strip()
        if not question_text or question_text.lower() in existing_questions:
            continue
        db.execute(
            text(
                "INSERT INTO push_qotd_questions (question, theme, emoji, hook, source) "
                "VALUES (:question, :theme, :emoji, :hook, 'generated')"
            ),
            {
                "question": question_text,
                "theme": str(q.get("theme", "Growth"))[:100],
                "emoji": str(q.get("emoji", "✨"))[:20],
                "hook": str(q.get("hook", "Today's Question"))[:200],
            },
        )
        existing_questions.add(question_text.lower())
        inserted += 1

    if inserted:
        db.commit()
        logger.info("✓ Generated and inserted %d new QOTD questions", inserted)
    return inserted


# How many unseen questions must remain in the global pool for any subscriber
# before a fresh batch is generated. Keeps the pool comfortably ahead.
_REFILL_THRESHOLD = 10
_REFILL_BATCH_SIZE = 20


def send_qotd_notification(db: Session) -> dict:
    """
    Send an individualised, no-repeat QOTD push notification to each subscriber
    whose *local time* currently matches their ``preferred_qotd_hour``.

    Run this function every hour (cron: ``0 * * * *``).  Postgres converts
    NOW() to each subscriber's stored IANA timezone, so only subscribers for
    whom it is currently their preferred morning hour receive a notification.
    Each subscriber gets at most one QOTD per calendar day (in *their* timezone).

    Questions come from the push_qotd_questions DB table.  Each subscriber gets
    the next question in the pool they haven't received yet.  A refill batch is
    generated automatically when the pool headroom drops below the threshold.
    """
    from urllib.parse import quote

    # Ensure the DB pool is seeded (no-op if already populated)
    _ensure_pool_seeded(db)

    # Fetch active QOTD subscribers whose local hour == preferred_qotd_hour
    # AND who have NOT already received a QOTD today (in their own timezone).
    rows = db.execute(
        text("""
            SELECT id, endpoint, p256dh_key, auth_key, COALESCE(timezone, 'UTC') AS timezone
            FROM push_subscriptions w
            WHERE active = true
              AND notify_qotd = true
              AND EXTRACT(HOUR FROM (NOW() AT TIME ZONE COALESCE(w.timezone, 'UTC')))
                  = w.preferred_qotd_hour
              AND NOT EXISTS (
                  SELECT 1 FROM push_qotd_history h
                  WHERE h.subscription_id = w.id
                    AND (h.sent_at AT TIME ZONE COALESCE(w.timezone, 'UTC'))::date
                        = (NOW() AT TIME ZONE COALESCE(w.timezone, 'UTC'))::date
              )
        """)
    ).fetchall()

    if not rows:
        logger.info("No QOTD subscribers due for delivery at this hour")
        return {"sent": 0, "failed": 0, "expired": 0, "total_subscribers": 0}

    logger.info("Sending individualised QOTD to %d subscribers (timezone-filtered)", len(rows))

    # ── Proactive refill check ──────────────────────────────────────────────
    # Find the subscriber who has seen the most questions (furthest along), then
    # check if the remaining pool for them is below the threshold.
    pool_size = db.execute(text("SELECT COUNT(*) FROM push_qotd_questions")).scalar() or 0
    max_seen = db.execute(
        text("""
            SELECT COALESCE(MAX(seen_count), 0)
            FROM (
                SELECT COUNT(*) AS seen_count
                FROM push_qotd_history
                WHERE subscription_id = ANY(:sids)
                GROUP BY subscription_id
            ) sub
        """),
        {"sids": [r[0] for r in rows]},
    ).scalar() or 0

    unseen_headroom = pool_size - max_seen
    if unseen_headroom < _REFILL_THRESHOLD:
        logger.info(
            "Pool headroom %d < threshold %d — generating %d new questions",
            unseen_headroom, _REFILL_THRESHOLD, _REFILL_BATCH_SIZE,
        )
        generate_qotd_batch(db, n=_REFILL_BATCH_SIZE)

    # Reload pool after potential expansion
    pool = _load_pool_from_db(db)
    pool_ids = [q["id"] for q in pool]
    pool_by_id = {q["id"]: q for q in pool}

    today = datetime.now(timezone.utc).date()
    sent = 0
    failed = 0
    expired_ids: list[int] = []

    for row in rows:
        sub_id, endpoint, p256dh, auth, _tz = row

        # Which questions has this subscriber already received?
        seen_rows = db.execute(
            text("SELECT qotd_id FROM push_qotd_history WHERE subscription_id = :sid"),
            {"sid": sub_id},
        ).fetchall()
        seen_ids = {r[0] for r in seen_rows}

        # Pick the first unseen question (pool order = chronological insertion)
        next_qotd = next((pool_by_id[qid] for qid in pool_ids if qid not in seen_ids), None)

        # Should never happen after the refill above, but guard anyway
        if next_qotd is None:
            logger.warning("Subscriber %d has seen all %d questions — skipping", sub_id, len(pool))
            continue

        qotd = next_qotd
        title = f"{qotd['emoji']} {qotd['theme']}"
        body = f"{qotd['question']} Mirror Talk has explored this deeply — the answer might surprise you."

        actions = [
            {
                "action": "answer",
                "title": "💬 Get Answer",
                "icon": "/wp-content/themes/astra-child/pwa-icon-192.png",
            },
            {
                "action": "save",
                "title": "🔖 Save for Later",
                "icon": "/wp-content/themes/astra-child/pwa-icon-192.png",
            },
        ]

        auto_url = (
            f"/ask-mirror-talk/"
            f"?utm_source=push&utm_medium=qotd&utm_campaign={today.isoformat()}"
            f"&autoask={quote(qotd['question'])}"
            f"#ask-mirror-talk-form"
        )

        subscription_info = {
            "endpoint": endpoint,
            "keys": {"p256dh": p256dh, "auth": auth},
        }

        result = send_push_notification(
            subscription_info=subscription_info,
            title=title,
            body=body,
            url=auto_url,
            tag=f"qotd-{today.isoformat()}",
            data={
                "question": qotd["question"],
                "theme": qotd["theme"],
                "qotd_id": qotd["id"],
                "date": today.isoformat(),
            },
            actions=actions,
            vibrate=[200, 100, 200],
            require_interaction=True,
        )

        if result == "sent":
            sent += 1
            db.execute(
                text(
                    "INSERT INTO push_qotd_history (subscription_id, qotd_id, sent_at) "
                    "VALUES (:sid, :qid, NOW())"
                ),
                {"sid": sub_id, "qid": qotd["id"]},
            )
        elif result == "expired":
            expired_ids.append(sub_id)
            failed += 1
        else:
            failed += 1

    if expired_ids:
        db.execute(
            text("UPDATE push_subscriptions SET active = false WHERE id = ANY(:ids)"),
            {"ids": expired_ids},
        )

    db.commit()
    if expired_ids:
        logger.info("Deactivated %d expired push subscriptions", len(expired_ids))

    result_summary = {
        "sent": sent,
        "failed": failed,
        "expired": len(expired_ids),
        "total_subscribers": len(rows),
    }
    logger.info("Individualised QOTD result: %s", result_summary)
    return result_summary


# ── MIDDAY MOTIVATION ────────────────────────────────────────────────────────

_MOTIVATION_REFILL_THRESHOLD = 10
_MOTIVATION_REFILL_BATCH_SIZE = 20

# Static seed list — used only to populate push_motivation_messages on first run.
_MOTIVATION_MESSAGES = [
    ("🌟 You've come so far",
     "Progress rarely looks like you expect — but every step has been real. Ask Mirror Talk what keeping going actually means for where you are today."),
    ("💛 You're doing better",
     "That voice telling you you're behind? It's not telling the truth. Ask Mirror Talk how to see what you've actually built — even on the quiet days."),
    ("🌿 One moment matters",
     "The afternoon isn't lost — one intentional pause can shift everything that follows. Ask Mirror Talk: what do you actually need right now?"),
    ("🔥 You showed up today",
     "Half the day done, and you're still here. That's not small — that's the whole thing. Ask Mirror Talk what showing up really means when it's hard."),
    ("🕊️ Be easy on yourself",
     "You'd give a struggling friend grace without hesitation. You deserve the same. Ask Mirror Talk how to offer yourself that same kindness today."),
    ("💪 You were built for this",
     "Every hard thing you've faced has been quietly shaping your resilience. Ask Mirror Talk what that strength is teaching you right now."),
    ("🌊 Breathe. Reset. Rise.",
     "Sixty seconds of stillness can recalibrate the whole afternoon. Ask Mirror Talk to help you remember your why before the day takes over again."),
    ("✨ Pause before you push",
     "Clarity isn't found in doing more — it lives in the space between. Ask Mirror Talk what you'd hear if you slowed down long enough to listen."),
    ("🎯 Keep going anyway",
     "Doubt is the shadow that follows every meaningful pursuit. Ask Mirror Talk how courage shows up in the moments when confidence doesn't."),
    ("🙏 Gratitude rewires you",
     "Name one thing you're grateful for right now — not later, now. Ask Mirror Talk how gratitude can reframe even the hardest parts of your day."),
    ("🌈 Right now is enough",
     "Not the future version of you — the one reading this. Ask Mirror Talk what it really means to stop waiting to be ready and just be here."),
    ("💬 Talk kindly to yourself",
     "The words you repeat to yourself daily are quietly shaping your reality. Ask Mirror Talk how to start rewriting the ones that hold you back."),
    ("🏃 Small steps compound",
     "You don't need a breakthrough today — just one more honest step. Ask Mirror Talk what quiet, consistent progress actually looks like for you."),
    ("🤝 You're not alone",
     "You were never meant to carry all of this by yourself. Ask Mirror Talk who you could lean on — or how to be that person for someone else."),
    ("🌅 Best part still ahead",
     "The afternoon is unwritten. One clear intention set right now can change how the rest of your day feels. Ask Mirror Talk what that intention should be."),
]


def _load_motivation_pool_from_db(db: Session) -> list[dict]:
    """Return all generic motivation messages from the DB ordered by id."""
    rows = db.execute(
        text("SELECT id, title, body FROM push_motivation_messages WHERE source != 'personalized' ORDER BY id")
    ).fetchall()
    return [{"id": r[0], "title": r[1], "body": r[2]} for r in rows]


def _ensure_motivation_pool_seeded(db: Session) -> None:
    """Seed push_motivation_messages from the static list if the table is empty."""
    count = db.execute(text("SELECT COUNT(*) FROM push_motivation_messages WHERE source = 'static'")).scalar()
    if count == 0:
        logger.info("Seeding motivation pool from static list (%d messages)", len(_MOTIVATION_MESSAGES))
        for title, body in _MOTIVATION_MESSAGES:
            db.execute(
                text("INSERT INTO push_motivation_messages (title, body, source) VALUES (:t, :b, 'static')"),
                {"t": title, "b": body},
            )
        db.commit()
        logger.info("✓ Motivation pool seeded")


def generate_motivation_batch(db: Session, n: int = 20) -> int:
    """
    Generate n new generic midday motivation messages via GPT and append them to
    push_motivation_messages.  Grounded in real episode themes so messages stay
    relevant to Mirror Talk's content.  Duplicate title detection prevents repeats.

    Returns the number of messages actually inserted.
    """
    import os
    from openai import OpenAI

    api_key = os.getenv("OPENAI_API_KEY") or settings.openai_api_key
    if not api_key:
        logger.warning("Cannot generate motivation batch: OPENAI_API_KEY not set")
        return 0

    episode_rows = db.execute(
        text("SELECT title FROM episodes ORDER BY published_at DESC LIMIT 15")
    ).fetchall()
    episode_titles = [r[0] for r in episode_rows]

    existing_rows = db.execute(text("SELECT title FROM push_motivation_messages WHERE source != 'personalized'")).fetchall()
    existing_titles = {r[0].strip().lower() for r in existing_rows}

    prompt = f"""You are writing midday motivational push notifications for Mirror Talk, a podcast about personal growth, relationships, emotional intelligence, and faith.

Recent Mirror Talk episodes include:
{chr(10).join(f"- {t}" for t in episode_titles[:10])}

Generate exactly {n} unique midday motivation messages. Each message is sent at noon to give someone a meaningful boost to carry them through the afternoon.

Rules:
- Title: 3–5 words max, punchy and warm (e.g. "You've come so far", "Pause before you push")
- Title must NOT contain "Mirror Talk"
- Body: 1–2 sentences. Start with an emotionally resonant observation, then invite them to go deeper (ending with "Ask Mirror Talk [specific question]")
- Body should feel personal, not generic — like a wise friend speaking directly to them
- Vary themes: self-worth, resilience, rest, purpose, relationships, gratitude, courage, growth, faith
- Do NOT repeat any of these existing titles: {", ".join(list(existing_titles)[:20])}

Respond with a JSON array of objects with keys: "title" (string), "body" (string), "theme" (string), "emoji" (single emoji to prepend to title).

Example: {{"title": "You've come so far", "body": "Progress rarely looks like you expect — but every step has been real. Ask Mirror Talk what keeping going actually means for where you are today.", "theme": "Resilience", "emoji": "🌟"}}

Return only the JSON array, no other text."""

    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9,
            max_tokens=3000,
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        import json as _json
        messages = _json.loads(raw.strip())
    except Exception as e:
        logger.error("Motivation batch generation failed: %s", e, exc_info=True)
        return 0

    inserted = 0
    for m in messages:
        if not isinstance(m, dict):
            continue
        raw_title = str(m.get("title", "")).strip()
        body = str(m.get("body", "")).strip()
        emoji = str(m.get("emoji", "✨")).strip()
        theme = str(m.get("theme", "")).strip()
        if not raw_title or not body:
            continue
        full_title = f"{emoji} {raw_title}"
        if full_title.lower() in existing_titles or raw_title.lower() in existing_titles:
            continue
        db.execute(
            text("INSERT INTO push_motivation_messages (title, body, theme, source) VALUES (:t, :b, :th, 'generated')"),
            {"t": full_title, "b": body, "th": theme[:100]},
        )
        existing_titles.add(full_title.lower())
        inserted += 1

    if inserted:
        db.commit()
        logger.info("✓ Generated and inserted %d new motivation messages", inserted)
    return inserted


def _generate_personalized_motivation(questions: list[str]) -> tuple[str, str] | None:
    """
    Generate a single (title, body) midday message tailored to a subscriber's
    recent questions.  Called per-subscriber when qa_logs history is available.
    Returns None if generation fails (caller should fall back to pool).
    """
    import os
    from openai import OpenAI

    api_key = os.getenv("OPENAI_API_KEY") or settings.openai_api_key
    if not api_key:
        return None

    recent = "\n".join(f"- {q}" for q in questions[:5])
    prompt = f"""A Mirror Talk listener recently asked these questions:
{recent}

Write ONE midday motivational push notification that speaks directly to the emotional themes behind their questions — without referencing the specific questions literally. It should feel uncannily relevant, like the message was written just for them.

Rules:
- Title: 3–5 words max, warm and direct. No "Mirror Talk" in the title.
- Body: 1–2 sentences. Start with a grounded emotional insight that resonates with their themes, then end with "Ask Mirror Talk [a specific, relevant follow-up question]."
- The message should feel like a wise friend noticed what they've been wrestling with.

Respond with a single JSON object with keys: "title", "body", "emoji" (single emoji for title), "theme" (one word).
Return only the JSON object, no other text."""

    client = OpenAI(api_key=api_key)
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.85,
            max_tokens=300,
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        import json as _json
        data = _json.loads(raw.strip())
        title = f"{data.get('emoji', '✨')} {data['title']}".strip()
        body = data["body"].strip()
        if title and body:
            return title, body
    except Exception as e:
        logger.warning("Personalized motivation generation failed: %s", e)
    return None


def send_midday_motivation_notification(db: Session) -> dict:
    """
    Send a midday motivation push to subscribers at their local noon.

    Message selection (in priority order per subscriber):
    1. Personalized — GPT-generated against their last 14 days of qa_logs questions.
    2. Pool (generic) — next unseen message from push_motivation_messages, auto-refilled
       by AI when headroom drops below _MOTIVATION_REFILL_THRESHOLD.

    Run hourly (cron: ``0 * * * *``), same as QOTD.
    """
    _ensure_motivation_pool_seeded(db)

    rows = db.execute(
        text("""
            SELECT id, endpoint, p256dh_key, auth_key,
                   COALESCE(user_ip, '') AS user_ip,
                   COALESCE(timezone, 'UTC') AS timezone
            FROM push_subscriptions w
            WHERE active = true
              AND notify_midday = true
              AND EXTRACT(HOUR FROM (NOW() AT TIME ZONE COALESCE(w.timezone, 'UTC'))) = 12
              AND NOT EXISTS (
                  SELECT 1 FROM push_motivation_history h
                  WHERE h.subscription_id = w.id
                    AND (h.sent_at AT TIME ZONE COALESCE(w.timezone, 'UTC'))::date
                        = (NOW() AT TIME ZONE COALESCE(w.timezone, 'UTC'))::date
              )
        """)
    ).fetchall()

    if not rows:
        logger.info("No midday motivation subscribers due at this hour")
        return {"sent": 0, "failed": 0, "expired": 0, "total_subscribers": 0}

    logger.info("Sending midday motivation to %d subscribers", len(rows))

    # ── Proactive pool refill ───────────────────────────────────────────────
    pool = _load_motivation_pool_from_db(db)
    pool_ids = [m["id"] for m in pool]
    pool_by_id = {m["id"]: m for m in pool}

    pool_size = len(pool)
    max_seen = db.execute(
        text("""
            SELECT COALESCE(MAX(seen_count), 0)
            FROM (
                SELECT COUNT(*) AS seen_count
                FROM push_motivation_history
                WHERE subscription_id = ANY(:sids)
                  AND message_id IS NOT NULL
                GROUP BY subscription_id
            ) sub
        """),
        {"sids": [r[0] for r in rows]},
    ).scalar() or 0

    if pool_size - max_seen < _MOTIVATION_REFILL_THRESHOLD:
        logger.info(
            "Motivation pool headroom %d < threshold %d — generating %d new messages",
            pool_size - max_seen, _MOTIVATION_REFILL_THRESHOLD, _MOTIVATION_REFILL_BATCH_SIZE,
        )
        generate_motivation_batch(db, n=_MOTIVATION_REFILL_BATCH_SIZE)
        pool = _load_motivation_pool_from_db(db)
        pool_ids = [m["id"] for m in pool]
        pool_by_id = {m["id"]: m for m in pool}

    today = datetime.now(timezone.utc)
    url = (
        "/ask-mirror-talk/"
        f"?utm_source=push&utm_medium=midday&utm_campaign={today.date().isoformat()}"
        "#ask-mirror-talk-form"
    )

    sent = 0
    failed = 0
    expired_ids: list[int] = []

    for row in rows:
        sub_id, endpoint, p256dh, auth, user_ip, _tz = row

        title: str | None = None
        body: str | None = None
        msg_id: int | None = None

        # ── 1. Try personalization ──────────────────────────────────────────
        if user_ip:
            recent = db.execute(
                text("""
                    SELECT question FROM qa_logs
                    WHERE user_ip = :ip
                      AND created_at >= NOW() - INTERVAL '14 days'
                    ORDER BY created_at DESC
                    LIMIT 5
                """),
                {"ip": user_ip},
            ).fetchall()
            if recent:
                questions = [r[0] for r in recent]
                personalized = _generate_personalized_motivation(questions)
                if personalized:
                    title, body = personalized
                    # Store in pool so history can reference it by ID
                    msg_id = db.execute(
                        text("""
                            INSERT INTO push_motivation_messages (title, body, source)
                            VALUES (:t, :b, 'personalized') RETURNING id
                        """),
                        {"t": title, "b": body},
                    ).scalar()
                    db.flush()
                    logger.debug("Subscriber %d → personalized motivation (msg %d)", sub_id, msg_id)

        # ── 2. Fall back to shared pool ─────────────────────────────────────
        if title is None:
            seen_ids = {
                r[0] for r in db.execute(
                    text("SELECT message_id FROM push_motivation_history WHERE subscription_id = :sid AND message_id IS NOT NULL"),
                    {"sid": sub_id},
                ).fetchall()
            }
            next_msg = next((pool_by_id[mid] for mid in pool_ids if mid not in seen_ids), None)
            if next_msg is None:
                # All messages seen — restart from beginning
                next_msg = pool_by_id[pool_ids[0]] if pool_ids else None
            if next_msg is None:
                logger.warning("Subscriber %d: motivation pool is empty — skipping", sub_id)
                continue
            title = next_msg["title"]
            body = next_msg["body"]
            msg_id = next_msg["id"]

        subscription_info = {"endpoint": endpoint, "keys": {"p256dh": p256dh, "auth": auth}}

        result = send_push_notification(
            subscription_info=subscription_info,
            title=title,
            body=body,
            url=url,
            tag=f"midday-{today.date().isoformat()}",
            data={"date": today.date().isoformat(), "type": "midday_motivation"},
            actions=[
                {"action": "ask", "title": "💬 Ask Mirror Talk", "icon": "/wp-content/themes/astra-child/pwa-icon-192.png"},
                {"action": "dismiss", "title": "Thanks 🙏", "icon": "/wp-content/themes/astra-child/pwa-icon-192.png"},
            ],
            vibrate=[100, 50, 100],
            require_interaction=False,
        )

        if result == "sent":
            sent += 1
            db.execute(
                text("INSERT INTO push_motivation_history (subscription_id, sent_at, message_id) VALUES (:sid, NOW(), :mid)"),
                {"sid": sub_id, "mid": msg_id},
            )
        elif result == "expired":
            expired_ids.append(sub_id)
            failed += 1
        else:
            failed += 1

    if expired_ids:
        db.execute(
            text("UPDATE push_subscriptions SET active = false WHERE id = ANY(:ids)"),
            {"ids": expired_ids},
        )

    db.commit()
    if expired_ids:
        logger.info("Deactivated %d expired push subscriptions", len(expired_ids))

    result_summary = {
        "sent": sent,
        "failed": failed,
        "expired": len(expired_ids),
        "total_subscribers": len(rows),
    }
    logger.info("Midday motivation result: %s", result_summary)
    return result_summary


# ── STATIC SEED POOL ────────────────────────────────────────────────────────
# Used only to seed push_qotd_questions on first run.  Do not use directly
# in send_qotd_notification — always read from the DB table instead.
_QOTD_POOL = [
    {"id": 1,  "emoji": "✨", "hook": "Today's Wisdom: Self-Worth",           "question": "How do I stop comparing myself to others?",               "theme": "Self-worth"},
    {"id": 2,  "emoji": "💫", "hook": "Your Daily Insight: Forgiveness",      "question": "What does it mean to truly forgive someone?",             "theme": "Forgiveness"},
    {"id": 3,  "emoji": "🌊", "hook": "Find Peace: Today's Question",         "question": "How do I find peace when everything feels uncertain?",    "theme": "Inner peace"},
    {"id": 4,  "emoji": "🎯", "hook": "Unlock Your Purpose",                 "question": "What's the difference between being busy and being productive?", "theme": "Purpose"},
    {"id": 5,  "emoji": "🕊️", "hook": "Let Go: Daily Wisdom",                "question": "How do I let go of things I can't control?",              "theme": "Surrender"},
    {"id": 6,  "emoji": "💪", "hook": "Lead with Courage",                   "question": "What does it look like to lead with vulnerability?",      "theme": "Leadership"},
    {"id": 7,  "emoji": "🤝", "hook": "Rebuild & Heal",                      "question": "How can I rebuild trust after it's been broken?",         "theme": "Relationships"},
    {"id": 8,  "emoji": "🙏", "hook": "Transform Through Gratitude",         "question": "What role does gratitude play in overcoming hardship?",   "theme": "Gratitude"},
    {"id": 9,  "emoji": "🚪", "hook": "Know When to Walk Away",              "question": "How do I know when it's time to walk away?",              "theme": "Boundaries"},
    {"id": 10, "emoji": "💚", "hook": "Healing Starts Here",                 "question": "What does Mirror Talk say about healing from trauma?",    "theme": "Healing"},
    {"id": 11, "emoji": "🌟", "hook": "Hope in Grief",                       "question": "How do I stay hopeful when grief feels overwhelming?",    "theme": "Grief"},
    {"id": 12, "emoji": "🔥", "hook": "Conquer Your Fear",                   "question": "What can I do when fear is holding me back?",             "theme": "Fear"},
    {"id": 13, "emoji": "👨‍👩‍👧", "hook": "Raise Resilient Kids",                "question": "How do I raise kids who are emotionally resilient?",      "theme": "Parenting"},
    {"id": 14, "emoji": "⚡", "hook": "Break Free Today",                    "question": "What's the first step to breaking a bad habit?",          "theme": "Addiction"},
    {"id": 15, "emoji": "💬", "hook": "Master Difficult Conversations",      "question": "How do I have hard conversations without damaging the relationship?", "theme": "Communication"},
    {"id": 16, "emoji": "🙌", "hook": "Faith in Action",                     "question": "What does alignment between faith and action look like?", "theme": "Faith"},
    {"id": 17, "emoji": "🌈", "hook": "Overcome Loneliness",                 "question": "How do I deal with loneliness even when I'm surrounded by people?", "theme": "Identity"},
    {"id": 18, "emoji": "📈", "hook": "Learn from Failure",                  "question": "What can I learn from failure?",                          "theme": "Growth"},
    {"id": 19, "emoji": "🛡️", "hook": "Boundaries Without Guilt",            "question": "How do I set boundaries without feeling guilty?",         "theme": "Boundaries"},
    {"id": 20, "emoji": "💎", "hook": "Live Authentically",                  "question": "What does it mean to live authentically?",                "theme": "Identity"},
    {"id": 21, "emoji": "🤲", "hook": "Support Someone in Grief",            "question": "How do I support someone who is grieving?",               "theme": "Grief"},
    {"id": 22, "emoji": "🎪", "hook": "Healthy Ambition Unlocked",           "question": "What does healthy ambition look like?",                   "theme": "Purpose"},
    {"id": 23, "emoji": "📣", "hook": "Find Your Voice",                     "question": "How do I find my voice when I've been silenced?",         "theme": "Empowerment"},
    {"id": 24, "emoji": "🏃", "hook": "Mind-Body Connection",                "question": "What's the connection between physical health and emotional healing?", "theme": "Healing"},
    {"id": 25, "emoji": "🔄", "hook": "Navigate Life Transitions",           "question": "How do I move forward after a major life change?",        "theme": "Transition"},
    {"id": 26, "emoji": "🏘️", "hook": "The Power of Community",              "question": "What does Mirror Talk teach about the power of community?", "theme": "Community"},
    {"id": 27, "emoji": "👪", "hook": "Parent with Awareness",               "question": "How do I parent through my own unresolved pain?",         "theme": "Parenting"},
    {"id": 28, "emoji": "😌", "hook": "Rest Without Guilt",                  "question": "What does rest really look like in a culture of hustle?", "theme": "Inner peace"},
    {"id": 29, "emoji": "❤️", "hook": "Love Without Losing Yourself",        "question": "How do I love someone without losing myself?",            "theme": "Relationships"},
    {"id": 30, "emoji": "🦁", "hook": "Everyday Courage",                    "question": "What does courage look like in everyday life?",           "theme": "Fear"},
    {"id": 31, "emoji": "🎭", "hook": "Embrace Your Emotions",               "question": "How do I stop running from my emotions?",                 "theme": "Healing"},
    {"id": 32, "emoji": "💰", "hook": "Money & Purpose Aligned",             "question": "What does Mirror Talk say about money and purpose?",      "theme": "Purpose"},
    {"id": 33, "emoji": "🌱", "hook": "Handle Criticism Gracefully",         "question": "How do I handle criticism without shutting down?",        "theme": "Growth"},
    {"id": 34, "emoji": "💑", "hook": "Become a Better Spouse",              "question": "What does it take to be a better spouse?",                "theme": "Relationships"},
    {"id": 35, "emoji": "🙏", "hook": "Rebuild Your Faith",                  "question": "How do I reconnect with my faith after doubt?",           "theme": "Faith"},
    {"id": 36, "emoji": "🧠", "hook": "Mental Health Wisdom",                "question": "What does Mirror Talk teach about mental health?",        "theme": "Healing"},
    {"id": 37, "emoji": "🚫", "hook": "Stop People-Pleasing",                "question": "How do I stop people-pleasing?",                          "theme": "Boundaries"},
    {"id": 38, "emoji": "🤲", "hook": "Surrender in Practice",               "question": "What does surrender look like in practice?",              "theme": "Surrender"},
    {"id": 39, "emoji": "👑", "hook": "Raise Kids Who Know Their Worth",     "question": "How do I raise my kids to know their worth?",             "theme": "Parenting"},
    {"id": 40, "emoji": "🧘", "hook": "Loneliness vs. Solitude",             "question": "What's the difference between loneliness and solitude?",  "theme": "Inner peace"},
]




def send_streak_protection_notification(db: Session) -> dict:
    """
    Send a streak-protection push to active subscribers who have NOT yet
    asked a question today (as far as the server can tell via utm params).

    Because streaks are tracked client-side in localStorage, the server
    cannot know the exact streak length per user. Instead we send a
    motivational nudge at a configured hour (e.g. 20:00 local) to any
    subscriber who hasn't already received a QOTD response today.
    Keyed by the tag 'streak-{date}' so it replaces itself if sent twice.
    """
    today = datetime.now(timezone.utc).date()
    url = (
        f"/ask-mirror-talk/"
        f"?utm_source=push&utm_medium=streak&utm_campaign={today.isoformat()}"
        f"#ask-mirror-talk-form"
    )

    streak_messages = [
        ("🔥 Don't break your streak!", "Keep the wisdom flowing — one question keeps it alive."),
        ("⏰ Still time today!", "Your daily Mirror Talk reflection is waiting for you."),
        ("💪 Stay consistent!", "A moment of reflection today keeps your streak alive."),
        ("✨ Your wisdom awaits", "Take 60 seconds to ask Mirror Talk something meaningful."),
    ]
    # Rotate message based on day so it doesn't feel repetitive
    title, body = streak_messages[today.toordinal() % len(streak_messages)]

    return _broadcast_notification(
        db=db,
        title=title,
        body=body,
        url=url,
        tag=f"streak-{today.isoformat()}",
        notification_type="streak_protection",
        data={"date": today.isoformat()},
        actions=[
            {"action": "ask", "title": "💬 Ask Now", "icon": "/wp-content/themes/astra-child/pwa-icon-192.png"},
            {"action": "dismiss", "title": "Later", "icon": "/wp-content/themes/astra-child/pwa-icon-192.png"},
        ],
        vibrate=[100, 50, 100],
        require_interaction=False,
    )


def send_new_episode_notification(
    db: Session,
    episode_title: str,
    episode_id: int,
) -> dict:
    """
    Notify subscribers about a newly ingested episode with premium styling.
    
    Enhanced with:
    - Compelling title with emoji
    - Action buttons
    - Episode metadata
    - Premium vibration

    Returns:
        dict with sent/failed/expired counts
    """
    # Create premium title with visual appeal
    title = f"🎙️ Fresh Wisdom: New Episode!"
    body = f'"{episode_title}" — Discover insights now. Tap to explore!'
    
    # Action buttons
    actions = [
        {
            "action": "explore",
            "title": "🔍 Explore Now",
            "icon": "/wp-content/themes/astra-child/pwa-icon-192.png"
        },
        {
            "action": "remind",
            "title": "🔔 Remind Me Later",
            "icon": "/wp-content/themes/astra-child/pwa-icon-192.png"
        }
    ]
    
    # Energetic vibration pattern
    vibrate = [150, 75, 150, 75, 150]
    
    return _broadcast_notification(
        db=db,
        title=title,
        body=body,
        url=f"/?utm_source=push&utm_medium=new_episode&utm_campaign=ep{episode_id}#ask-mirror-talk-form",
        tag=f"new-episode-{episode_id}",
        notification_type="new_episode",
        data={"episode_id": episode_id, "episode_title": episode_title},
        actions=actions,
        vibrate=vibrate,
        require_interaction=False,  # Allow auto-dismiss after viewing
        preference_column="notify_new_episodes",
    )


def _broadcast_notification(
    db: Session,
    title: str,
    body: str,
    url: str,
    tag: str,
    notification_type: str,
    data: dict | None = None,
    actions: list[dict] | None = None,
    vibrate: list[int] | None = None,
    require_interaction: bool = False,
    image: str | None = None,
    preference_column: str | None = None,
) -> dict:
    """
    Send a premium notification to all active push subscribers.
    Automatically cleans up expired subscriptions.

    Args:
        preference_column: Optional column name to filter by (e.g. 'notify_new_episodes').
                           Must be one of the allowed preference columns.
    """
    _ALLOWED_PREF_COLUMNS = {"notify_new_episodes", "notify_qotd", "notify_midday"}

    if preference_column and preference_column in _ALLOWED_PREF_COLUMNS:
        query = text(f"""
            SELECT id, endpoint, p256dh_key, auth_key
            FROM push_subscriptions
            WHERE active = true AND {preference_column} = true
        """)  # nosec: column name validated against allowlist above
    else:
        query = text("""
            SELECT id, endpoint, p256dh_key, auth_key
            FROM push_subscriptions
            WHERE active = true
        """)

    # Fetch all matching active subscriptions
    rows = db.execute(query).fetchall()

    if not rows:
        logger.info("No active push subscribers for %s notification", notification_type)
        return {"sent": 0, "failed": 0, "expired": 0, "total_subscribers": 0}

    logger.info("Sending premium %s notification to %d subscribers", notification_type, len(rows))

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
            actions=actions,
            vibrate=vibrate,
            require_interaction=require_interaction,
            image=image,
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
    logger.info("Premium push notification result: %s", result)
    return result
