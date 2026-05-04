"""
Web Push Notifications for Ask Mirror Talk.

Sends daily questions, reflection nudges, and episode alerts to subscribed users.
Uses the Web Push protocol with VAPID authentication.
"""

import base64
import json
import logging
import re
from datetime import datetime, timezone
from hashlib import sha256
from urllib.parse import quote

from pywebpush import webpush, WebPushException
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.openai_compat import create_chat_completion

logger = logging.getLogger(__name__)

_THEME_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Grief": ("grief", "loss", "mourning"),
    "Courage": ("courage", "fear", "brave"),
    "Relationships": ("relationship", "love", "trust", "partner", "marriage"),
    "Self-worth": ("self-worth", "compare", "comparison", "worthy", "confidence"),
    "Healing": ("healing", "trauma", "wound", "pain"),
    "Purpose": ("purpose", "calling", "direction", "meaning"),
    "Inner peace": ("peace", "stillness", "calm", "uncertain"),
    "Boundaries": ("boundaries", "people-pleasing", "guilty"),
    "Faith": ("faith", "doubt", "god", "spiritual"),
    "Gratitude": ("gratitude", "thankful", "appreciate"),
    "Growth": ("growth", "change", "learn", "becoming"),
    "Communication": ("communication", "conversation", "speak", "listen"),
    "Community": ("community", "belong", "support", "together"),
    "Leadership": ("leadership", "leader", "lead", "influence"),
    "Parenting": ("parenting", "kids", "children", "family"),
    "Identity": ("identity", "self", "voice", "authentic"),
    "Transition": ("transition", "life change", "new season", "move forward"),
    "Empowerment": ("empower", "agency", "strength", "confidence"),
}

_QOTD_TITLES: dict[str, str] = {
    "Boundaries": "Where is your yes?",
    "Communication": "Say it with care",
    "Community": "Who strengthens you?",
    "Courage": "Courage for today",
    "Empowerment": "Take your voice back",
    "Faith": "Faith in the quiet",
    "Fear": "Meet fear honestly",
    "Forgiveness": "Release with wisdom",
    "Gratitude": "Notice what remains",
    "Grief": "Hold this gently",
    "Growth": "Let growth get honest",
    "Healing": "Repair starts here",
    "Identity": "Return to yourself",
    "Inner peace": "A quieter question",
    "Leadership": "Lead from within",
    "Parenting": "Parent with presence",
    "Purpose": "What keeps calling?",
    "Relationships": "Love with clarity",
    "Self-worth": "Remember your worth",
    "Surrender": "Loosen your grip",
    "Transition": "When life shifts",
}

_THEME_REFLECTION_OPENERS: dict[str, tuple[str, ...]] = {
    "Boundaries": (
        "For the part of you learning where love ends and self-abandonment begins:",
        "A question for the places where yes has cost too much:",
    ),
    "Communication": (
        "For the conversation that needs more care:",
        "A question for speaking truth without losing tenderness:",
    ),
    "Community": (
        "For the connections shaping who you become:",
        "A question for the people who help you feel less alone:",
    ),
    "Courage": (
        "For the moment that needs honesty before confidence:",
        "A question for the brave step you keep circling:",
    ),
    "Faith": (
        "For the part of you still reaching for trust:",
        "A question for the quiet place where doubt and hope meet:",
    ),
    "Grief": (
        "For what you are still carrying gently:",
        "A question for the love that has changed shape:",
    ),
    "Gratitude": (
        "For the grace still holding part of today:",
        "A question for noticing what remains good:",
    ),
    "Growth": (
        "For the change asking you to become more honest:",
        "A question for growth that does not rush past care:",
    ),
    "Healing": (
        "For the wound that is asking for wiser attention:",
        "A question for the part of you ready to repair:",
    ),
    "Identity": (
        "For the voice underneath all the noise:",
        "A question for remembering who you are becoming:",
    ),
    "Inner peace": (
        "For the place in you that wants to stop bracing:",
        "A question for a steadier inner weather:",
    ),
    "Leadership": (
        "For the influence you want to carry with integrity:",
        "A question for leading without performing:",
    ),
    "Parenting": (
        "For the love that wants to repair and guide:",
        "A question for parenting with presence instead of pressure:",
    ),
    "Purpose": (
        "For the calling that keeps tapping your shoulder:",
        "A question for the life trying to get your attention:",
    ),
    "Relationships": (
        "For the connection you want to handle with more care:",
        "A question for the love that needs honesty and tenderness:",
    ),
    "Self-worth": (
        "For the part of you tired of proving your value:",
        "A question for returning to your own center:",
    ),
    "Surrender": (
        "For the grip you may not need to keep:",
        "A question for trusting without giving up:",
    ),
    "Transition": (
        "For the season that no longer fits the old map:",
        "A question for moving forward without abandoning yourself:",
    ),
    "Empowerment": (
        "For the strength that wants to come back online:",
        "A question for choosing with your own voice again:",
    ),
}

_QOTD_THEME_TEASERS: dict[str, tuple[str, ...]] = {
    "Boundaries": (
        "A boundaries reflection is ready. Tap for a steadier way to honor your yes and your no.",
        "Today’s question opens a wiser way to protect peace without closing your heart.",
    ),
    "Communication": (
        "A communication reflection is ready. Tap for a gentler way to say what matters.",
        "Today’s question can help you listen beneath the words and respond with care.",
    ),
    "Community": (
        "A community reflection is ready. Tap to explore the people and places that help you become whole.",
        "Today’s question looks at belonging, support, and the kind of connection that strengthens you.",
    ),
    "Courage": (
        "A courage reflection is ready. Tap for the next honest step, not the perfect one.",
        "Today’s question meets the brave part of you that is ready to move with honesty.",
    ),
    "Faith": (
        "A faith reflection is ready. Tap for a quieter way to hold doubt, trust, and hope.",
        "Today’s question meets the place where doubt and hope are still talking.",
    ),
    "Gratitude": (
        "A gratitude reflection is ready. Tap to notice what is still carrying you.",
        "Today’s question can help you find grace inside an ordinary moment.",
    ),
    "Grief": (
        "A grief reflection is ready. Tap for a gentle way to carry what still matters.",
        "Today’s question gives tenderness to the love that has changed shape.",
    ),
    "Growth": (
        "A growth reflection is ready. Tap to name what is changing and what is asking for courage.",
        "Today’s question can help you grow without rushing past what needs care.",
    ),
    "Healing": (
        "A healing reflection is ready. Tap for a wiser way to tend what still hurts.",
        "Today’s question offers gentleness for the part of you learning to repair.",
    ),
    "Inner peace": (
        "An inner peace reflection is ready. Tap to loosen what has been keeping you braced.",
        "Today’s question can help your nervous system find a little more room.",
    ),
    "Leadership": (
        "A leadership reflection is ready. Tap to lead from clarity instead of performance.",
        "Today’s question brings leadership back to presence, courage, and inner alignment.",
    ),
    "Parenting": (
        "A parenting reflection is ready. Tap for presence, repair, and steadier love.",
        "Today’s question can help you parent with honesty instead of pressure.",
    ),
    "Purpose": (
        "A purpose reflection is ready. Tap to listen to what keeps calling you forward.",
        "Today’s question helps separate pressure from the deeper pull of purpose.",
    ),
    "Relationships": (
        "A relationship reflection is ready. Tap for a clearer way to love without losing yourself.",
        "Today’s question can help you bring honesty and tenderness into connection.",
    ),
    "Self-worth": (
        "A self-worth reflection is ready. Tap to return to the value you do not have to prove.",
        "Today’s question helps you step out of comparison and back into your own center.",
    ),
}

_MIDDAY_FALLBACKS: tuple[tuple[str, str], ...] = (
    ("One honest pause", "You do not have to force the whole day into clarity; one honest pause can return you to what matters."),
    ("Come back inward", "Before the afternoon pulls you further outward, listen for the one thing in you asking to be handled with care."),
    ("Hold the next step", "Progress can be quiet and still be real; choose the next faithful step instead of measuring the whole mountain."),
    ("Make room inside", "A little space around what you feel can change how you carry the rest of today."),
    ("Begin again gently", "You are allowed to begin the day again from this moment, with more honesty and less pressure."),
)

_NIGHT_TITLES: tuple[str, ...] = (
    "Let the day settle",
    "Before you sleep",
    "Return softly",
    "What stayed with you?",
    "Close with care",
)

_NIGHT_BODY_RETURNING: tuple[str, ...] = (
    "Let one honest question gather what the day left scattered before you carry it into sleep.",
    "Before sleep, return to the insight that still feels alive and let it become wisdom.",
    "Give the unfinished part of today a softer place to land.",
    "You do not need to solve the whole day; just notice what still wants care.",
    "A quiet reflection tonight can help tomorrow begin with less noise.",
)

_NIGHT_BODY_NEW: tuple[str, ...] = (
    "Before sleep, ask one question that helps the day become wisdom.",
    "Let the day settle by naming what mattered, what hurt, and what still hopes.",
    "A quiet question tonight can turn a crowded day into a clearer one.",
    "Pause before rest and listen for the one truth the day is still offering.",
    "Give yourself one unhurried moment to meet the day honestly.",
)


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


def _recent_user_questions(db: Session, user_ip: str | None, days: int = 21, limit: int = 5) -> list[str]:
    if not user_ip:
        return []
    rows = db.execute(
        text("""
            SELECT question
            FROM qa_logs
            WHERE user_ip = :ip
              AND created_at >= NOW() - make_interval(days => :days)
            ORDER BY created_at DESC
            LIMIT :limit
        """),
        {"ip": user_ip, "days": days, "limit": limit},
    ).fetchall()
    return [str(r[0]).strip() for r in rows if r and r[0]]


def _primary_theme_from_questions(questions: list[str]) -> str | None:
    scores: dict[str, int] = {}
    haystack = " \n".join(questions).lower()
    for theme, keywords in _THEME_KEYWORDS.items():
        hits = sum(haystack.count(keyword) for keyword in keywords)
        if hits:
            scores[theme] = hits
    if not scores:
        return None
    return max(scores, key=scores.get)


def _strip_midday_cta(body: str) -> str:
    clean = re.sub(r'\s*[Aa]sk Mirror Talk .+?[\.\!\?]*\s*$', '', body or '').strip()
    return clean or (body or '').strip()


def _stable_variant(*parts: object, modulo: int) -> int:
    seed = sha256("|".join(str(part or "") for part in parts).encode("utf-8")).hexdigest()
    return int(seed[:8], 16) % max(1, modulo)


def _clip_sentence(text_value: str, max_len: int = 118, *, allow_ellipsis: bool = False) -> str:
    text_value = re.sub(r"\s+", " ", (text_value or "").strip())
    if len(text_value) <= max_len:
        return text_value
    if allow_ellipsis:
        clipped = text_value[: max_len - 1].rsplit(" ", 1)[0].rstrip(" ,;:-")
        return f"{clipped}…"
    sentence_matches = list(re.finditer(r"[^.!?]+[.!?]", text_value))
    best = ""
    for match in sentence_matches:
        candidate = text_value[: match.end()].strip()
        if len(candidate) <= max_len:
            best = candidate
        else:
            break
    if best:
        return best
    clipped = text_value[: max_len - 1].rsplit(" ", 1)[0].rstrip(" ,;:-")
    return f"{clipped}."


def _remove_brand_mentions(text_value: str) -> str:
    clean = re.sub(r"\bAsk Mirror Talk\b", "", text_value or "", flags=re.IGNORECASE)
    clean = re.sub(r"\bMirror Talk\b", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\s+", " ", clean).strip(" ,;:.-")
    return clean


def _question_text_only(question: str) -> str:
    clean = re.sub(r"\s+", " ", (question or "").strip())
    return clean.rstrip(" .?!")


def _clean_push_title(title: str, fallback: str = "Pause here") -> str:
    clean = _remove_brand_mentions(title)
    clean = re.sub(r"^[^\wA-Za-z]+", "", clean).strip()
    return _clip_sentence(clean or fallback, 42)


def _clean_qotd_title(hook: str | None, theme: str) -> str:
    hook_text = re.sub(r"\s+", " ", (hook or "").strip())
    generic_hooks = {"", "today's question", "todays question", "question of the day"}
    if hook_text.lower() not in generic_hooks:
        return _clean_push_title(hook_text, fallback=_QOTD_TITLES.get(theme or "", "Today's question"))
    return _QOTD_TITLES.get(theme or "", "Today's question")


def _premium_push_body(body: str, max_len: int = 118, *, remove_brand_mentions: bool = True) -> str:
    clean = _remove_brand_mentions(body) if remove_brand_mentions else (body or "")
    clean = re.sub(r"\s+", " ", clean).strip(" ,;:-")
    if not clean:
        return ""
    if clean[-1] not in ".!?":
        clean = f"{clean}."
    return _clip_sentence(clean, max_len)


def _qotd_theme_teaser(theme: str, base_question: str) -> str:
    options = _QOTD_THEME_TEASERS.get(theme or "")
    if options:
        return options[_stable_variant(theme, base_question, "qotd-teaser", modulo=len(options))]
    theme_label = (theme or "reflection").strip().lower()
    return f"Today’s {theme_label} reflection is ready. Tap to open the question and carry one clear insight with you."


def _qotd_copy(question: str, theme: str, hook: str | None, recent_theme: str | None, is_returning: bool) -> tuple[str, str]:
    title = _clean_qotd_title(hook, theme)
    base_question = _question_text_only(question)
    openers = _THEME_REFLECTION_OPENERS.get(theme or "", ())
    opener = openers[_stable_variant(base_question, theme, modulo=len(openers))] if openers else "A question worth carrying today:"
    if is_returning and recent_theme and recent_theme.lower() != (theme or "").lower():
        opener = f"Your recent thread was {recent_theme.lower()}; today, widen the lens:"
    body = f"{opener} {base_question}?"
    if len(body) > 116:
        body = f"Today's question: {base_question}?"
    if len(body) > 116:
        body = _qotd_theme_teaser(theme, base_question)
    return title, _premium_push_body(body, 116, remove_brand_mentions=False)


def _midday_copy(title: str, body: str, recent_theme: str | None, is_returning: bool) -> tuple[str, str]:
    final_title = _clean_push_title(title, fallback="Pause here")
    clean_body = _remove_brand_mentions(_strip_midday_cta(body))
    if not clean_body or len(clean_body) < 36:
        variant = _stable_variant(title, body, recent_theme, modulo=len(_MIDDAY_FALLBACKS))
        final_title, clean_body = _MIDDAY_FALLBACKS[variant]
    elif is_returning and recent_theme:
        if clean_body[-1] not in ".!?":
            clean_body = f"{clean_body}."
        clean_body = f"{clean_body} Let it meet what you are carrying in {recent_theme.lower()}."
    return final_title, _premium_push_body(clean_body, 116)


def _streak_copy(recent_theme: str | None, is_returning: bool) -> tuple[str, str]:
    seed_parts = [datetime.now(timezone.utc).date().isoformat(), recent_theme or "", "returning" if is_returning else "new"]
    seed = sha256("|".join(seed_parts).encode("utf-8")).hexdigest()
    variant = int(seed[:8], 16) % 5

    theme_phrase = (recent_theme or "").strip().lower()
    theme_suffix = f" in {theme_phrase}" if theme_phrase else ""

    title_options = [
        "Keep this alive",
        "Stay with it tonight",
        "Hold the thread",
        "Return before today closes",
        "One more honest moment",
    ]

    if is_returning and recent_theme:
        body_options = [
            f"You were already moving through{theme_suffix}. One honest question tonight keeps that thread alive.",
            f"Come back to what still feels unfinished{theme_suffix}. A quiet return tonight is enough.",
            f"Don't let today's reflection fade{theme_suffix}. One more honest question can keep it open.",
            f"There may still be something waiting for you{theme_suffix}. Return for one clear question tonight.",
            f"If {theme_phrase} still lingers, follow it a little further tonight.",
        ]
    elif is_returning:
        body_options = [
            "You already opened something worth keeping. One honest question tonight keeps that rhythm alive.",
            "Come back before the day closes. One thoughtful question is enough to keep the thread going.",
            "Don't let today's reflection end half-finished. Return for one clear question tonight.",
            "A quiet return tonight can keep your reflection rhythm alive.",
            "If something from today is still with you, follow it with one honest question tonight.",
        ]
    else:
        body_options = [
            "One thoughtful question tonight can start a steadier reflection rhythm.",
            "Before today ends, ask one honest question and let the thread begin.",
            "A single quiet question tonight can open more than you expect.",
            "Start small tonight. One honest question is enough.",
            "Come back for one thoughtful question before the day slips away.",
        ]

    title = title_options[variant]
    body = body_options[variant]
    return title, _clip_sentence(body, 102)


def _night_reflection_copy(recent_theme: str | None, is_returning: bool) -> tuple[str, str]:
    variant = _stable_variant(datetime.now(timezone.utc).date().isoformat(), recent_theme, "night", is_returning, modulo=5)

    theme_phrase = (recent_theme or "").strip().lower()

    if is_returning and recent_theme:
        body_options = [
            f"Before sleep, let one quiet question meet what is still moving in {theme_phrase}.",
            f"Let tonight hold the part of {theme_phrase} that still wants gentleness.",
            f"Return to {theme_phrase} for one honest moment before the day closes.",
            f"Before sleep, what did {theme_phrase} teach you today that deserves not to be rushed past?",
            f"There may be one more tender truth inside {theme_phrase} before tomorrow begins.",
        ]
    elif is_returning:
        body_options = list(_NIGHT_BODY_RETURNING)
    else:
        body_options = list(_NIGHT_BODY_NEW)

    title = _NIGHT_TITLES[variant]
    body = body_options[variant]
    return title, _premium_push_body(body, 116)


def _new_episode_copy(episode_title: str) -> tuple[str, str]:
    title = "Fresh listening"
    body = f"{episode_title} is ready. Open the episode and carry one clear insight with you."
    return title, _clip_sentence(body, 128)


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

    prompt = f"""You are creating premium Question of the Day prompts for Mirror Talk, a podcast about personal growth, relationships, emotional intelligence, and faith.

Recent Mirror Talk episodes include:
{chr(10).join(f"- {t}" for t in episode_titles[:10])}

Generate exactly {n} unique, emotionally intelligent questions a listener might genuinely ask when they are trying to understand themselves, their relationships, their faith, or their next step.

Rules:
- Each question must be distinct in theme, emotional situation, and wording
- Use natural, human language, like a thoughtful friend would actually ask it
- Questions should be answerable using podcast insights
- Questions must be self-contained, specific, and emotionally clear
- Avoid generic self-help phrasing such as "embrace your journey", "unlock your potential", "become your best self", or "level up"
- Avoid questions that sound like marketing copy, therapy worksheets, or search-engine prompts
- Each hook should feel editorial and premium, not clickbait
- Cover a range of these themes: {", ".join(themes)}
- Do NOT repeat any of these existing questions: {", ".join(list(existing_questions)[:20])}

Respond with a JSON array of objects. Each object must have exactly these keys:
  "question" (string), "theme" (one of the themes above), "emoji" (single emoji), "hook" (short 3-6 word title, e.g. "Heal Your Inner Child")

Example: {{"question": "How do I stop abandoning myself just to keep the peace?", "theme": "Boundaries", "emoji": "🌿", "hook": "Return to Yourself"}}

Return only the JSON array, no other text."""

    client = OpenAI(api_key=api_key)
    try:
        response = create_chat_completion(
            client,
            model=settings.notification_generation_model,
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
    # Ensure the DB pool is seeded (no-op if already populated)
    _ensure_pool_seeded(db)

    # Fetch active QOTD subscribers whose local hour == preferred_qotd_hour
    # AND who have NOT already received a QOTD today (in their own timezone).
    rows = db.execute(
        text("""
            SELECT id, endpoint, p256dh_key, auth_key,
                   COALESCE(user_ip, '') AS user_ip,
                   COALESCE(timezone, 'UTC') AS timezone
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
        sub_id, endpoint, p256dh, auth, user_ip, _tz = row

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
        recent_questions = _recent_user_questions(db, user_ip, days=21, limit=5)
        recent_theme = _primary_theme_from_questions(recent_questions)
        is_returning = bool(recent_questions)
        title, body = _qotd_copy(
            question=qotd["question"],
            theme=qotd["theme"],
            hook=qotd.get("hook"),
            recent_theme=recent_theme,
            is_returning=is_returning,
        )

        actions = [
            {
                "action": "answer",
                "title": "Get today’s answer",
                "icon": "/wp-content/themes/astra-child/pwa-icon-192.png",
            },
            {
                "action": "save",
                "title": "Save for later",
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
                "type": "qotd",
            },
            actions=actions,
            vibrate=[160, 60, 180],
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

    prompt = f"""You are writing premium midday reflection notifications for Mirror Talk, a podcast about personal growth, relationships, emotional intelligence, and faith.

Recent Mirror Talk episodes include:
{chr(10).join(f"- {t}" for t in episode_titles[:10])}

Generate exactly {n} unique midday messages. Each message should feel like a meaningful interruption in the middle of a real day: thoughtful, emotionally precise, and useful without sounding like generic motivation.

Rules:
- Title: 2–5 words max, calm, premium, and memorable
- Title must NOT contain "Mirror Talk"
- Body: 1–2 complete sentences. Start with an emotionally resonant observation, then invite them to go deeper by ending with "Ask Mirror Talk [specific question]"
- Body should feel personal, grounded, and human — like a wise friend who notices what the user may be carrying
- The body must be complete and must not end mid-thought
- Avoid clichés: "you got this", "keep pushing", "trust the process", "everything happens for a reason", "embrace the journey"
- Avoid productivity hustle language unless the message is gently challenging it
- Vary themes: self-worth, resilience, rest, purpose, relationships, gratitude, courage, growth, faith
- Do NOT repeat any of these existing titles: {", ".join(list(existing_titles)[:20])}

Respond with a JSON array of objects with keys: "title" (string), "body" (string), "theme" (string), "emoji" (single emoji to prepend to title).

Example: {{"title": "Come Back Inward", "body": "You may not need more pressure today; you may need one honest pause. Ask Mirror Talk what is asking for care in me right now?", "theme": "Rest", "emoji": "🌿"}}

Return only the JSON array, no other text."""

    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    try:
        response = create_chat_completion(
            client,
            model=settings.notification_generation_model,
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


def _generate_personalized_motivation(questions: list[str]) -> dict | None:
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

Write ONE premium midday reflection notification that speaks directly to the emotional themes behind their questions without quoting or naming the questions literally. It should feel uncannily relevant, like a wise friend noticed the deeper pattern.

Rules:
- Title: 2–4 words max, calm, premium, and emotionally precise. No "Mirror Talk" in the title.
- Body: 1 complete sentence only, emotionally clear and grounded. No hashtags. No exclamation marks unless absolutely necessary.
- Question: one clear follow-up question that naturally continues the emotional theme.
- Avoid clichés, vague encouragement, and pressure language.
- The overall tone should feel warm, thoughtful, and deeply human.

Respond with a single JSON object with keys: "title", "body", "question", "emoji" (single emoji for title), "theme" (one word).
Return only the JSON object, no other text."""

    client = OpenAI(api_key=api_key)
    try:
        response = create_chat_completion(
            client,
            model=settings.notification_generation_model,
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
        title = f"{data.get('emoji', '☀️')} {data['title']}".strip()
        body = data["body"].strip()
        question = data.get("question", "").strip()
        if title and body and question:
            return {"title": title, "body": body, "question": question, "theme": data.get("theme")}
    except Exception as e:
        logger.warning("Personalized motivation generation failed: %s", e)
    return None


def _extract_question_from_body(body: str) -> str | None:
    """Extract the 'Ask Mirror Talk <question>' suggestion embedded in a motivation body.

    Motivation bodies are authored to end with a call-to-action of the form:
    '...Ask Mirror Talk <question text>."
    Extracting that question lets us include it in the notification data so
    the SW can auto-submit it when the user taps the notification.
    """
    match = re.search(r'[Aa]sk Mirror Talk (.+?)[\.!?]*\s*$', body)
    if match:
        q = match.group(1).strip().rstrip('.!?')
        return (q[0].upper() + q[1:]) if q else None
    return None


def _fallback_midday_question(title: str, body: str) -> str:
    """Return a gentle, askable question when a midday message lacks an explicit CTA."""
    haystack = f"{title} {body}".lower()
    theme_prompts = [
        (("grief", "loss"), "What would support me most as I move through grief today?"),
        (("fear", "courage", "brave"), "What does courage look like in this moment of my life?"),
        (("relationship", "love", "trust"), "What would help me show up more honestly in my relationships today?"),
        (("self-worth", "compare", "comparison"), "How do I return to my own worth instead of comparing myself to others?"),
        (("peace", "stillness", "calm"), "How do I find peace when life feels noisy or uncertain?"),
        (("purpose", "direction", "calling"), "What small step would move me closer to purpose today?"),
        (("healing", "trauma", "wound"), "What is one gentle way I can support my own healing today?"),
    ]
    for keywords, question in theme_prompts:
        if any(keyword in haystack for keyword in keywords):
            return question
    return "What is this message inviting me to notice in my life today?"


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
        question_for_open: str | None = None
        msg_id: int | None = None
        recent_questions = _recent_user_questions(db, user_ip, days=14, limit=5)
        recent_theme = _primary_theme_from_questions(recent_questions)
        is_returning = bool(recent_questions)

        # ── 1. Try personalization ──────────────────────────────────────────
        if recent_questions:
            personalized = _generate_personalized_motivation(recent_questions)
            if personalized:
                title = personalized["title"]
                body = personalized["body"]
                question_for_open = personalized["question"]
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

        # Try to extract a question from the body (messages authored with
        # "Ask Mirror Talk <question>" CTAs).  When present, pack it into
        # data.question and bake it into the notification URL as ?autoask=
        # so the SW can auto-submit it whether the tab is open or not.
        extracted_q = question_for_open or _extract_question_from_body(body or "") or _fallback_midday_question(title or "", body or "")
        title, body = _midday_copy(title or "", body or "", recent_theme=recent_theme, is_returning=is_returning)
        notify_data: dict = {"date": today.date().isoformat(), "type": "midday_motivation"}
        notify_url = url
        notify_data["question"] = extracted_q
        clean = url.split('#')[0].rstrip('&?')
        sep = '&' if '?' in clean else '?'
        hash_part = '#ask-mirror-talk-form'
        notify_url = f"{clean}{sep}autoask={quote(extracted_q)}&midday_reflection=1{hash_part}"

        result = send_push_notification(
            subscription_info=subscription_info,
            title=title,
            body=body,
            url=notify_url,
            tag=f"midday-{today.date().isoformat()}",
            data=notify_data,
            actions=[
                {"action": "ask", "title": "Reflect now", "icon": "/wp-content/themes/astra-child/pwa-icon-192.png"},
                {"action": "dismiss", "title": "Later", "icon": "/wp-content/themes/astra-child/pwa-icon-192.png"},
            ],
            vibrate=[90, 40, 90],
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
    Send a streak-protection nudge to subscribers at their local 20:00 (8 PM).

    Runs hourly (same as QOTD/midday). The SQL filter ensures each subscriber
    is targeted only during the one hour their local clock reads 20:xx, so
    users in different timezones receive the nudge at a sensible evening hour
    rather than all at the same UTC instant.

    Keyed by tag 'streak-{date}' so duplicate sends within the same local day
    replace each other silently.
    """
    today = datetime.now(timezone.utc).date()

    # Only target subscribers whose local clock is at 20:00 (8 PM)
    rows = db.execute(
        text("""
            SELECT w.id, w.endpoint, w.p256dh_key, w.auth_key,
                   COALESCE(w.user_ip, '') AS user_ip,
                   COALESCE(w.timezone, 'UTC') AS timezone_name,
                   w.updated_at
            FROM push_subscriptions w
            WHERE w.active = true
              AND EXTRACT(HOUR FROM (NOW() AT TIME ZONE COALESCE(w.timezone, 'UTC'))) = 20
              AND (w.updated_at AT TIME ZONE COALESCE(w.timezone, 'UTC'))::date
                    < (NOW() AT TIME ZONE COALESCE(w.timezone, 'UTC'))::date
              AND NOT EXISTS (
                    SELECT 1
                    FROM qa_logs q
                    WHERE q.user_ip = w.user_ip
                      AND (q.created_at AT TIME ZONE COALESCE(w.timezone, 'UTC'))::date
                          = (NOW() AT TIME ZONE COALESCE(w.timezone, 'UTC'))::date
              )
        """)
    ).fetchall()

    if not rows:
        logger.info("No streak-protection subscribers due at this hour")
        return {"sent": 0, "failed": 0, "expired": 0, "total_subscribers": 0}

    logger.info("Sending streak-protection notification to %d subscribers", len(rows))

    url = (
        f"/ask-mirror-talk/"
        f"?utm_source=push&utm_medium=streak&utm_campaign={today.isoformat()}"
        f"#ask-mirror-talk-form"
    )
    tag = f"streak-{today.isoformat()}"
    actions = [
        {"action": "ask", "title": "Keep streak alive", "icon": "/wp-content/themes/astra-child/pwa-icon-192.png"},
        {"action": "dismiss", "title": "Later", "icon": "/wp-content/themes/astra-child/pwa-icon-192.png"},
    ]

    sent = 0
    failed = 0
    expired_ids: list[int] = []

    for row in rows:
        sub_id, endpoint, p256dh, auth, user_ip, timezone_name, updated_at = row
        recent_questions = _recent_user_questions(db, user_ip, days=21, limit=5)
        recent_theme = _primary_theme_from_questions(recent_questions)
        is_returning = bool(recent_questions)
        title, body = _streak_copy(recent_theme=recent_theme, is_returning=is_returning)
        subscription_info = {"endpoint": endpoint, "keys": {"p256dh": p256dh, "auth": auth}}
        result = send_push_notification(
            subscription_info=subscription_info,
            title=title,
            body=body,
            url=url,
            tag=tag,
            data={"date": today.isoformat(), "type": "streak"},
            actions=actions,
            vibrate=[120, 40, 120],
            require_interaction=False,
        )
        if result == "sent":
            sent += 1
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
        logger.info("Deactivated %d expired push subscriptions", len(expired_ids))

    result_summary = {
        "sent": sent,
        "failed": failed,
        "expired": len(expired_ids),
        "total_subscribers": len(rows),
    }
    logger.info("Streak protection result: %s", result_summary)
    return result_summary


def send_nightly_reflection_notification(db: Session) -> dict:
    """
    Send a nightly reflection nudge at local 21:00 (9 PM).

    This first version intentionally reuses the existing reflection-oriented
    opt-in (notify_midday) instead of adding a new preference column, so the
    feature can ship without a schema change. The app resolves the actual
    prompt locally after open using same-day history, weekly recap, or QOTD.
    """
    today = datetime.now(timezone.utc).date()

    rows = db.execute(
        text("""
            SELECT w.id, w.endpoint, w.p256dh_key, w.auth_key,
                   COALESCE(w.user_ip, '') AS user_ip
            FROM push_subscriptions w
            WHERE w.active = true
              AND w.notify_midday = true
              AND EXTRACT(HOUR FROM (NOW() AT TIME ZONE COALESCE(w.timezone, 'UTC'))) = 21
        """)
    ).fetchall()

    if not rows:
        logger.info("No nightly reflection subscribers due at this hour")
        return {"sent": 0, "failed": 0, "expired": 0, "total_subscribers": 0}

    logger.info("Sending nightly reflection notification to %d subscribers", len(rows))

    base_url = (
        f"/ask-mirror-talk/"
        f"?utm_source=push&utm_medium=night_reflection&utm_campaign={today.isoformat()}"
        f"&night_reflection=1"
        f"#ask-mirror-talk-form"
    )
    tag = f"night-reflection-{today.isoformat()}"
    actions = [
        {"action": "ask", "title": "Return now", "icon": "/wp-content/themes/astra-child/pwa-icon-192.png"},
        {"action": "dismiss", "title": "Later", "icon": "/wp-content/themes/astra-child/pwa-icon-192.png"},
    ]

    sent = 0
    failed = 0
    expired_ids: list[int] = []

    for row in rows:
        sub_id, endpoint, p256dh, auth, user_ip = row
        recent_questions = _recent_user_questions(db, user_ip, days=21, limit=5)
        recent_theme = _primary_theme_from_questions(recent_questions)
        is_returning = bool(recent_questions)
        title, body = _night_reflection_copy(recent_theme=recent_theme, is_returning=is_returning)
        subscription_info = {"endpoint": endpoint, "keys": {"p256dh": p256dh, "auth": auth}}

        result = send_push_notification(
            subscription_info=subscription_info,
            title=title,
            body=body,
            url=base_url,
            tag=tag,
            data={"date": today.isoformat(), "type": "night_reflection"},
            actions=actions,
            vibrate=[70, 35, 70],
            require_interaction=False,
        )
        if result == "sent":
            sent += 1
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
        logger.info("Deactivated %d expired push subscriptions", len(expired_ids))

    result_summary = {
        "sent": sent,
        "failed": failed,
        "expired": len(expired_ids),
        "total_subscribers": len(rows),
    }
    logger.info("Nightly reflection result: %s", result_summary)
    return result_summary


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
    title, body = _new_episode_copy(episode_title)
    
    # Action buttons
    actions = [
        {
            "action": "explore",
            "title": "Open episode",
            "icon": "/wp-content/themes/astra-child/pwa-icon-192.png"
        },
        {
            "action": "remind",
            "title": "Save for later",
            "icon": "/wp-content/themes/astra-child/pwa-icon-192.png"
        }
    ]
    
    # Energetic vibration pattern
    vibrate = [140, 60, 140, 60, 140]
    
    return _broadcast_notification(
        db=db,
        title=title,
        body=body,
        url=f"/?utm_source=push&utm_medium=new_episode&utm_campaign=ep{episode_id}#ask-mirror-talk-form",
        tag=f"new-episode-{episode_id}",
        notification_type="new_episode",
        data={"type": "new_episode", "episode_id": episode_id, "episode_title": episode_title},
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
