from datetime import datetime, timedelta, timezone
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.db import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


QOTD_POOL = [
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

TOPIC_CATALOG = [
    {"slug": "grief",         "label": "Grief & Loss",      "icon": "💔", "query": "How do I deal with grief and loss?",
     "starters": ["How do I stay hopeful when grief feels overwhelming?", "How do I support someone who is grieving?", "What does healing look like after loss?"]},
    {"slug": "addiction",     "label": "Addiction",          "icon": "🔗", "query": "How do I break free from addiction?",
     "starters": ["What's the first step to breaking a bad habit?", "How do I stay sober when life gets hard?", "What does recovery really look like?"]},
    {"slug": "purpose",       "label": "Purpose",           "icon": "🧭", "query": "How do I find my purpose in life?",
     "starters": ["What does healthy ambition look like?", "How do I know if I'm living my calling?", "What does Mirror Talk say about money and purpose?"]},
    {"slug": "relationships", "label": "Relationships",     "icon": "❤️", "query": "What's the key to building healthy relationships?",
     "starters": ["How do I love someone without losing myself?", "How do I rebuild trust after it's been broken?", "What does it take to be a better spouse?"]},
    {"slug": "fear",          "label": "Fear & Doubt",      "icon": "🌊", "query": "How can I overcome fear and self-doubt?",
     "starters": ["What can I do when fear is holding me back?", "What does courage look like in everyday life?", "How do I stop comparing myself to others?"]},
    {"slug": "faith",         "label": "Faith",             "icon": "🙏", "query": "What role does faith play in personal growth?",
     "starters": ["How do I reconnect with my faith after doubt?", "What does alignment between faith and action look like?", "What does Mirror Talk teach about prayer?"]},
    {"slug": "leadership",    "label": "Leadership",        "icon": "🏆", "query": "What makes a great leader?",
     "starters": ["What does it look like to lead with vulnerability?", "How do I lead without burning out?", "What does Mirror Talk say about servant leadership?"]},
    {"slug": "identity",      "label": "Identity",          "icon": "🪞", "query": "How do I discover my true identity?",
     "starters": ["What does it mean to live authentically?", "How do I deal with loneliness even when I'm surrounded by people?", "How do I find my voice when I've been silenced?"]},
    {"slug": "healing",       "label": "Healing",           "icon": "🌱", "query": "How do I start the healing process?",
     "starters": ["How do I stop running from my emotions?", "What's the connection between physical health and emotional healing?", "What does Mirror Talk teach about mental health?"]},
    {"slug": "forgiveness",   "label": "Forgiveness",       "icon": "🕊️", "query": "What does Mirror Talk say about forgiveness?",
     "starters": ["What does it mean to truly forgive someone?", "How do I forgive someone who hurt me deeply?", "What's the difference between forgiveness and reconciliation?"]},
]


@router.get("/api/question-of-the-day")
def get_question_of_the_day():
    """Return a deterministic Question of the Day."""
    today = datetime.now(timezone.utc).date()
    index = today.toordinal() % len(QOTD_POOL)
    entry = QOTD_POOL[index]
    return {
        "question": entry["question"],
        "theme": entry["theme"],
        "date": today.isoformat(),
    }


@router.get("/api/suggested-questions")
def get_suggested_questions(db: Session = Depends(get_db)):
    """Return suggested starter questions for the widget."""
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        popular = db.execute(
            text("""
                SELECT question, COUNT(*) as cnt
                FROM qa_logs
                WHERE created_at >= :cutoff
                  AND LENGTH(question) > 15
                  AND question NOT LIKE '{{%'
                  AND LOWER(question) NOT IN ('test', 'test me', 'hello', 'hi')
                GROUP BY question
                ORDER BY cnt DESC
                LIMIT 6
            """),
            {"cutoff": cutoff},
        ).fetchall()
        popular_questions = [row[0] for row in popular]
    except Exception as e:
        logger.warning("Could not fetch popular questions: %s", e)
        popular_questions = []

    curated = [
        "How do I deal with grief and loss?",
        "What does Mirror Talk say about finding your purpose?",
        "How can I overcome fear and self-doubt?",
        "What's the key to building healthy relationships?",
        "How do I break free from addiction?",
        "What does alignment really mean?",
    ]

    seen = set()
    result = []
    for question in popular_questions + curated:
        normalized = question.strip().lower()
        if normalized not in seen and len(result) < 6:
            seen.add(normalized)
            result.append(question.strip())

    return {"questions": result}


@router.get("/api/topics")
def get_topics(db: Session = Depends(get_db)):
    """Return browseable topics with episode counts."""
    db_topic_to_slugs: dict[str, list[str]] = {
        "faith": ["faith"],
        "relationships": ["relationships"],
        "leadership": ["leadership", "purpose"],
        "inner life": ["fear", "identity", "healing", "grief"],
        "general": [],
    }

    try:
        rows = db.execute(
            text("""
                SELECT topic, COUNT(DISTINCT episode_id) AS ep_count
                FROM chunks
                WHERE topic IS NOT NULL AND topic != ''
                GROUP BY topic
            """)
        ).fetchall()

        db_counts: dict[str, int] = {}
        for topic_value, ep_count in rows:
            for slug in db_topic_to_slugs.get(topic_value, []):
                db_counts[slug] = db_counts.get(slug, 0) + ep_count
    except Exception as e:
        logger.warning("Could not query topic counts: %s", e)
        db_counts = {}

    return {
        "topics": [{**topic, "episode_count": db_counts.get(topic["slug"], 0)} for topic in TOPIC_CATALOG]
    }


@router.get("/api/related-questions")
def get_related_questions(qa_log_id: int, db: Session = Depends(get_db)):
    """Return up to 3 questions that other users asked about the same episodes."""
    try:
        row = db.execute(
            text("SELECT episode_ids FROM qa_logs WHERE id = :id"),
            {"id": qa_log_id},
        ).fetchone()
        if not row or not row[0]:
            return {"questions": []}

        valid_ep_ids = []
        for episode_id in row[0].split(","):
            try:
                valid_ep_ids.append(str(int(episode_id.strip())))
            except ValueError:
                pass
        if not valid_ep_ids:
            return {"questions": []}

        like_clauses = " OR ".join([f"episode_ids LIKE :ep{i}" for i in range(len(valid_ep_ids[:5]))])
        like_params = {f"ep{i}": f"%{eid}%" for i, eid in enumerate(valid_ep_ids[:5])}
        like_params["qa_log_id"] = qa_log_id

        related = db.execute(
            text(f"""
                SELECT question, COUNT(*) AS freq
                FROM qa_logs
                WHERE id != :qa_log_id
                  AND LENGTH(question) > 20
                  AND LOWER(question) NOT IN ('test', 'hello', 'hi')
                  AND episode_ids IS NOT NULL
                  AND ({like_clauses})
                GROUP BY question
                ORDER BY freq DESC
                LIMIT 5
            """),
            like_params,
        ).fetchall()
        questions = [row[0] for row in related]

        if len(questions) < 3:
            cutoff = datetime.now(timezone.utc) - timedelta(days=30)
            trending = db.execute(
                text("""
                    SELECT question, COUNT(*) AS freq
                    FROM qa_logs
                    WHERE created_at >= :cutoff
                      AND LENGTH(question) > 20
                      AND question NOT LIKE '{{%'
                      AND LOWER(question) NOT IN ('test', 'hello', 'hi')
                    GROUP BY question
                    ORDER BY freq DESC
                    LIMIT 10
                """),
                {"cutoff": cutoff},
            ).fetchall()
            existing = set(question.lower() for question in questions)
            for row in trending:
                if row[0].lower() not in existing:
                    questions.append(row[0])
                    existing.add(row[0].lower())
                if len(questions) >= 3:
                    break

        return {"questions": questions[:3]}
    except Exception as e:
        logger.error("Error fetching related questions: %s", e)
        return {"questions": []}


@router.get("/api/answer-archive")
def get_answer_archive(limit: int = 50, db: Session = Depends(get_db)):
    """Return the most-asked questions with their best answers."""
    try:
        rows = db.execute(
            text("""
                SELECT
                    question,
                    COUNT(*) AS asked_count,
                    MAX(answer) AS answer,
                    MAX(created_at) AS last_asked
                FROM qa_logs
                WHERE LENGTH(question) > 20
                  AND question NOT LIKE '{%%'
                  AND LOWER(question) NOT IN ('test', 'hello', 'hi', 'test me')
                  AND answer IS NOT NULL
                  AND LENGTH(answer) > 100
                GROUP BY question
                HAVING COUNT(*) >= 1
                ORDER BY COUNT(*) DESC, MAX(created_at) DESC
                LIMIT :limit
            """),
            {"limit": max(1, min(limit, 200))},
        ).fetchall()

        archive = [
            {
                "question": row[0],
                "asked_count": row[1],
                "answer_snippet": row[2][:400] if row[2] else "",
                "last_asked": row[3].isoformat() if row[3] else None,
            }
            for row in rows
        ]
        return {"archive": archive, "total": len(archive)}
    except Exception as e:
        logger.error("Error fetching answer archive: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch archive") from e
