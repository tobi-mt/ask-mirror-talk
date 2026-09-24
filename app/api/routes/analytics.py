from datetime import datetime, timedelta, timezone
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBasicCredentials
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.auth import admin_auth, security
from app.core.db import get_db

logger = logging.getLogger(__name__)
router = APIRouter()
INTERNAL_USER_IP = "cache-prewarm"


def _fetch_origin_cohort_metrics(db: Session, cutoff: datetime):
    return db.execute(
        text(
            """
            WITH origin_events AS (
                SELECT DISTINCT ON (qa_log_id)
                    qa_log_id,
                    COALESCE(metadata_json::jsonb->>'origin', metadata_json::jsonb->>'label', 'unknown') AS origin
                FROM product_events
                WHERE event_name IN ('question_answered', 'question_submitted')
                  AND qa_log_id IS NOT NULL
                  AND created_at >= :cutoff
                ORDER BY qa_log_id, (event_name = 'question_answered') DESC, created_at DESC
            )
            SELECT
                COALESCE(oe.origin, 'typed_or_unknown') AS origin,
                COUNT(*) AS total_questions,
                ROUND(AVG(q.latency_ms)::numeric, 2) AS avg_latency_ms,
                ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY q.latency_ms)::numeric, 2) AS p95_latency_ms,
                SUM(CASE WHEN q.is_cached THEN 1 ELSE 0 END) AS cached_questions,
                ROUND((SUM(CASE WHEN q.is_cached THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0))::numeric, 2) AS cache_hit_pct,
                SUM(
                    CASE
                        WHEN q.is_answered = FALSE OR q.episode_ids IS NULL OR q.episode_ids = '' THEN 1
                        ELSE 0
                    END
                ) AS weak_match_questions,
                ROUND(
                    (
                        SUM(
                            CASE
                                WHEN q.is_answered = FALSE OR q.episode_ids IS NULL OR q.episode_ids = '' THEN 1
                                ELSE 0
                            END
                        ) * 100.0 / NULLIF(COUNT(*), 0)
                    )::numeric,
                    2
                ) AS weak_match_pct,
                COUNT(DISTINCT q.user_ip) AS unique_users,
                COUNT(DISTINCT COALESCE(NULLIF(pe.device_id, ''), q.user_ip)) AS unique_devices
            FROM qa_logs q
            LEFT JOIN origin_events oe ON oe.qa_log_id = q.id
            LEFT JOIN product_events pe ON pe.qa_log_id = q.id
            WHERE q.created_at >= :cutoff
              AND COALESCE(q.user_ip, '') != :internal_user_ip
            GROUP BY COALESCE(oe.origin, 'typed_or_unknown')
            ORDER BY total_questions DESC, origin ASC
            """
        ),
        {"cutoff": cutoff, "internal_user_ip": INTERNAL_USER_IP},
    ).fetchall()


@router.get("/api/stats/questions-today")
def get_questions_today(db: Session = Depends(get_db)):
    """
    Public endpoint for social proof - returns count of questions asked today.
    No authentication required to support client-side widget.
    """
    try:
        # Get midnight today in UTC
        now = datetime.now(timezone.utc)
        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        count = db.execute(
            text("SELECT COUNT(*) FROM qa_logs WHERE created_at >= :midnight AND COALESCE(user_ip, '') != :internal_user_ip"),
            {"midnight": midnight, "internal_user_ip": INTERNAL_USER_IP},
        ).scalar()
        
        return {"count": count or 0, "date": midnight.isoformat()}
    except Exception as e:
        logger.error(f"Error fetching questions-today count: {e}")
        # Return a fallback value rather than error to avoid breaking widget
        return {"count": 0, "error": "unavailable"}


@router.get("/api/analytics/summary")
def get_analytics_summary(
    days: int = 7,
    request: Request = None,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    admin_auth(credentials, request)
    days = max(1, min(days, 365))

    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        total_questions = db.execute(
            text("SELECT COUNT(*) FROM qa_logs WHERE created_at >= :cutoff AND COALESCE(user_ip, '') != :internal_user_ip"),
            {"cutoff": cutoff, "internal_user_ip": INTERNAL_USER_IP},
        ).scalar()
        unique_users = db.execute(
            text("SELECT COUNT(DISTINCT user_ip) FROM qa_logs WHERE created_at >= :cutoff AND COALESCE(user_ip, '') != :internal_user_ip"),
            {"cutoff": cutoff, "internal_user_ip": INTERNAL_USER_IP},
        ).scalar()
        avg_latency = db.execute(
            text("SELECT AVG(latency_ms) FROM qa_logs WHERE created_at >= :cutoff AND COALESCE(user_ip, '') != :internal_user_ip"),
            {"cutoff": cutoff, "internal_user_ip": INTERNAL_USER_IP},
        ).scalar()
        top_questions = db.execute(
            text("""
                SELECT question, COUNT(*) as count
                FROM qa_logs
                WHERE created_at >= :cutoff
                  AND COALESCE(user_ip, '') != :internal_user_ip
                GROUP BY question
                ORDER BY count DESC
                LIMIT 10
            """),
            {"cutoff": cutoff, "internal_user_ip": INTERNAL_USER_IP},
        ).fetchall()
        most_cited = db.execute(
            text("""
                SELECT
                    e.id,
                    e.title,
                    COUNT(*) as citation_count
                FROM qa_logs q
                CROSS JOIN LATERAL UNNEST(STRING_TO_ARRAY(q.episode_ids, ',')) AS episode_id
                JOIN episodes e ON e.id = episode_id::int
                WHERE q.created_at >= :cutoff
                  AND COALESCE(q.user_ip, '') != :internal_user_ip
                GROUP BY e.id, e.title
                ORDER BY citation_count DESC
                LIMIT 10
            """),
            {"cutoff": cutoff, "internal_user_ip": INTERNAL_USER_IP},
        ).fetchall()

        try:
            total_citations = db.execute(
                text("""
                    SELECT COUNT(*)
                    FROM qa_logs q
                    CROSS JOIN LATERAL UNNEST(STRING_TO_ARRAY(q.episode_ids, ',')) AS episode_id
                    WHERE q.created_at >= :cutoff
                      AND COALESCE(q.user_ip, '') != :internal_user_ip
                """),
                {"cutoff": cutoff, "internal_user_ip": INTERNAL_USER_IP},
            ).scalar()
            total_clicks = db.execute(
                text("SELECT COUNT(*) FROM citation_clicks WHERE clicked_at >= :cutoff"),
                {"cutoff": cutoff},
            ).scalar()
            ctr = (total_clicks / total_citations * 100) if total_citations > 0 else 0
        except Exception:
            db.rollback()
            ctr = None

        try:
            feedback_rows = db.execute(
                text("""
                    SELECT feedback_type, COUNT(*) as cnt
                    FROM user_feedback uf
                    JOIN qa_logs q ON q.id = uf.qa_log_id
                    WHERE q.created_at >= :cutoff
                    GROUP BY feedback_type
                """),
                {"cutoff": cutoff},
            ).fetchall()
            feedback_counts = {row[0]: row[1] for row in feedback_rows}
            positive = feedback_counts.get("positive", 0)
            negative = feedback_counts.get("negative", 0)
            total_feedback = positive + negative + feedback_counts.get("neutral", 0)
            satisfaction_pct = round(positive / (positive + negative) * 100, 1) if (positive + negative) > 0 else None
        except Exception:
            db.rollback()
            positive = negative = total_feedback = 0
            satisfaction_pct = None

        try:
            unanswered = db.execute(
                text("SELECT COUNT(*) FROM qa_logs WHERE created_at >= :cutoff AND is_answered = FALSE AND COALESCE(user_ip, '') != :internal_user_ip"),
                {"cutoff": cutoff, "internal_user_ip": INTERNAL_USER_IP},
            ).scalar() or 0
            cached_count = db.execute(
                text("SELECT COUNT(*) FROM qa_logs WHERE created_at >= :cutoff AND is_cached = TRUE AND COALESCE(user_ip, '') != :internal_user_ip"),
                {"cutoff": cutoff, "internal_user_ip": INTERNAL_USER_IP},
            ).scalar() or 0
        except Exception:
            db.rollback()
            unanswered = None
            cached_count = None

        try:
            guardrail_total = db.execute(
                text("""
                    SELECT COUNT(*)
                    FROM product_events
                    WHERE created_at >= :cutoff
                      AND event_name = 'guardrail_blocked'
                """),
                {"cutoff": cutoff},
            ).scalar() or 0
            guardrail_rows = db.execute(
                text("""
                    SELECT
                        COALESCE(metadata_json::json->>'category', 'unknown') AS category,
                        COUNT(*) AS count
                    FROM product_events
                    WHERE created_at >= :cutoff
                      AND event_name = 'guardrail_blocked'
                    GROUP BY COALESCE(metadata_json::json->>'category', 'unknown')
                    ORDER BY count DESC, category ASC
                """),
                {"cutoff": cutoff},
            ).fetchall()
        except Exception:
            db.rollback()
            guardrail_total = 0
            guardrail_rows = []

        try:
            origin_rows = _fetch_origin_cohort_metrics(db, cutoff)
        except Exception:
            db.rollback()
            origin_rows = []

        return {
            "period_days": days,
            "total_questions": total_questions or 0,
            "unique_users": unique_users or 0,
            "avg_latency_ms": round(avg_latency, 2) if avg_latency else 0,
            "citation_ctr_percent": round(ctr, 2) if ctr is not None else None,
            "feedback": {
                "positive": positive,
                "negative": negative,
                "total": total_feedback,
                "satisfaction_percent": satisfaction_pct,
            },
            "unanswered_questions": unanswered,
            "cached_questions": cached_count,
            "guardrails": {
                "blocked_total": guardrail_total,
                "by_category": [{"category": row[0], "count": row[1]} for row in guardrail_rows],
            },
            "top_questions": [{"question": q[0], "count": q[1]} for q in top_questions],
            "most_cited_episodes": [
                {"id": episode[0], "title": episode[1], "citations": episode[2]}
                for episode in most_cited
            ],
            "origin_cohorts": [
                {
                    "origin": row[0],
                    "total_questions": row[1],
                    "avg_latency_ms": float(row[2] or 0),
                    "p95_latency_ms": float(row[3] or 0),
                    "cached_questions": int(row[4] or 0),
                    "cache_hit_pct": float(row[5] or 0),
                    "weak_match_questions": int(row[6] or 0),
                    "weak_match_pct": float(row[7] or 0),
                    "unique_users": int(row[8] or 0),
                    "unique_devices": int(row[9] or 0),
                }
                for row in origin_rows
            ],
        }
    except Exception as e:
        logger.error("Error getting analytics summary: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/analytics/origins")
def get_origin_cohort_analytics(
    days: int = 30,
    request: Request = None,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Per-origin cohort analytics for latency, cache hit rate, and weak-match rate."""
    admin_auth(credentials, request)
    days = max(1, min(days, 365))
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    rows = _fetch_origin_cohort_metrics(db, cutoff)
    return {
        "period_days": days,
        "origins": [
            {
                "origin": row[0],
                "total_questions": int(row[1] or 0),
                "avg_latency_ms": float(row[2] or 0),
                "p95_latency_ms": float(row[3] or 0),
                "cached_questions": int(row[4] or 0),
                "cache_hit_pct": float(row[5] or 0),
                "weak_match_questions": int(row[6] or 0),
                "weak_match_pct": float(row[7] or 0),
                "unique_users": int(row[8] or 0),
                "unique_devices": int(row[9] or 0),
            }
            for row in rows
        ],
    }


@router.get("/api/analytics/overview")
def get_analytics_overview(
    period: str = "all",
    days: int = 30,
    request: Request = None,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Return comprehensive analytics with explicit coverage and definitions."""
    admin_auth(credentials, request)
    if period not in {"all", "days"}:
        raise HTTPException(status_code=400, detail="period must be 'all' or 'days'")
    days = max(1, min(days, 3650))
    cutoff = None if period == "all" else datetime.now(timezone.utc) - timedelta(days=days)
    q_filter = "" if cutoff is None else "AND q.created_at >= :cutoff"
    p_filter = "" if cutoff is None else "AND p.created_at >= :cutoff"
    params = {"internal_user_ip": INTERNAL_USER_IP, "cutoff": cutoff}

    totals = db.execute(text(f"""
        SELECT COUNT(*) AS questions,
               COUNT(DISTINCT NULLIF(q.user_ip, '')) AS unique_ip_addresses,
               MIN(q.created_at) AS first_seen_at, MAX(q.created_at) AS last_seen_at,
               ROUND(AVG(q.latency_ms)::numeric, 2) AS avg_latency_ms,
               ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY q.latency_ms)::numeric, 2) AS p95_latency_ms,
               COUNT(*) FILTER (WHERE q.is_answered = FALSE OR NULLIF(q.episode_ids, '') IS NULL) AS weak_matches,
               COUNT(*) FILTER (WHERE q.is_cached = TRUE) AS cached_questions
        FROM qa_logs q
        WHERE COALESCE(q.user_ip, '') != :internal_user_ip {q_filter}
    """), params).mappings().one()
    devices = db.execute(text(f"""
        SELECT COUNT(*) AS events,
               COUNT(DISTINCT NULLIF(p.device_id, '')) AS unique_devices,
               COUNT(*) FILTER (WHERE NULLIF(p.device_id, '') IS NOT NULL) AS events_with_device,
               MIN(p.created_at) AS first_seen_at, MAX(p.created_at) AS last_seen_at
        FROM product_events p
        WHERE COALESCE(p.user_ip, '') != :internal_user_ip {p_filter}
    """), params).mappings().one()
    top_questions = db.execute(text(f"""
        SELECT LOWER(REGEXP_REPLACE(BTRIM(q.question), '\\s+', ' ', 'g')) AS question,
               COUNT(*) AS asks,
               COUNT(DISTINCT NULLIF(q.user_ip, '')) AS unique_ip_addresses
        FROM qa_logs q
        WHERE COALESCE(q.user_ip, '') != :internal_user_ip
          AND BTRIM(q.question) != ''
          AND BTRIM(q.question) NOT LIKE '{{{{%}}}}' {q_filter}
        GROUP BY 1 HAVING COUNT(*) >= 2
        ORDER BY asks DESC, question ASC LIMIT 25
    """), params).mappings().all()
    hourly = db.execute(text(f"""
        SELECT EXTRACT(HOUR FROM q.created_at)::int AS hour_utc,
               COUNT(*) AS questions,
               COUNT(DISTINCT NULLIF(q.user_ip, '')) AS unique_ip_addresses
        FROM qa_logs q
        WHERE COALESCE(q.user_ip, '') != :internal_user_ip {q_filter}
        GROUP BY 1 ORDER BY 1
    """), params).mappings().all()
    weekdays = db.execute(text(f"""
        SELECT EXTRACT(ISODOW FROM q.created_at)::int AS iso_weekday,
               COUNT(*) AS questions,
               COUNT(DISTINCT NULLIF(q.user_ip, '')) AS unique_ip_addresses
        FROM qa_logs q
        WHERE COALESCE(q.user_ip, '') != :internal_user_ip {q_filter}
        GROUP BY 1 ORDER BY 1
    """), params).mappings().all()
    daily = db.execute(text(f"""
        SELECT DATE(q.created_at) AS activity_date,
               COUNT(*) AS questions,
               COUNT(DISTINCT NULLIF(q.user_ip, '')) AS unique_ip_addresses
        FROM qa_logs q
        WHERE COALESCE(q.user_ip, '') != :internal_user_ip {q_filter}
        GROUP BY 1 ORDER BY 1
    """), params).mappings().all()
    event_mix = db.execute(text(f"""
        SELECT p.event_name, COUNT(*) AS events,
               COUNT(DISTINCT NULLIF(p.device_id, '')) AS unique_devices
        FROM product_events p
        WHERE COALESCE(p.user_ip, '') != :internal_user_ip {p_filter}
        GROUP BY p.event_name ORDER BY events DESC, p.event_name ASC
    """), params).mappings().all()

    dimensions = {}
    for dimension in ("country_code", "timezone", "language", "platform", "display_mode"):
        rows = db.execute(text(f"""
            WITH latest_device AS (
                SELECT DISTINCT ON (p.device_id) p.device_id,
                       NULLIF(p.metadata_json::jsonb->>:dimension, '') AS value
                FROM product_events p
                WHERE COALESCE(p.user_ip, '') != :internal_user_ip
                  AND NULLIF(p.device_id, '') IS NOT NULL {p_filter}
                ORDER BY p.device_id, p.created_at DESC
            )
            SELECT value, COUNT(*) AS devices FROM latest_device
            WHERE value IS NOT NULL GROUP BY value
            ORDER BY devices DESC, value ASC LIMIT 30
        """), {**params, "dimension": dimension}).mappings().all()
        dimensions[dimension] = [dict(row) for row in rows]

    question_count = int(totals["questions"] or 0)
    event_count = int(devices["events"] or 0)
    weak_matches = int(totals["weak_matches"] or 0)
    cached = int(totals["cached_questions"] or 0)
    device_coverage = int(devices["events_with_device"] or 0)
    return {
        "period": {"type": period, "days": days if period == "days" else None},
        "coverage": {
            "questions_first_seen_at": totals["first_seen_at"], "questions_last_seen_at": totals["last_seen_at"],
            "events_first_seen_at": devices["first_seen_at"], "events_last_seen_at": devices["last_seen_at"],
        },
        "audience": {
            "unique_users_proxy": int(totals["unique_ip_addresses"] or 0),
            "unique_devices": int(devices["unique_devices"] or 0),
            "unique_user_definition": "Distinct IP addresses that asked a question; a proxy, not an account-level user count.",
            "unique_device_definition": "Distinct first-party browser IDs in product events; available only after instrumentation began.",
        },
        "usage": {
            "questions": question_count, "events": event_count,
            "avg_latency_ms": float(totals["avg_latency_ms"] or 0),
            "p95_latency_ms": float(totals["p95_latency_ms"] or 0),
            "weak_matches": weak_matches,
            "weak_match_percent": round(weak_matches / question_count * 100, 2) if question_count else None,
            "cached_questions": cached,
            "cache_hit_percent": round(cached / question_count * 100, 2) if question_count else None,
        },
        "top_questions": [dict(row) for row in top_questions],
        "daily": [dict(row) for row in daily],
        "time_of_day_utc": [dict(row) for row in hourly],
        "weekday_utc": [dict(row) for row in weekdays],
        "event_mix": [dict(row) for row in event_mix],
        "geography": {"countries": dimensions["country_code"], "timezones": dimensions["timezone"]},
        "technology": {"platforms": dimensions["platform"], "display_modes": dimensions["display_mode"], "languages": dimensions["language"]},
        "demography": {"available": False, "reason": "Age, gender, and other demographics are not collected and are not inferred from private questions."},
        "data_quality": {
            "device_id_event_coverage_percent": round(device_coverage / event_count * 100, 2) if event_count else None,
            "top_questions_minimum_aggregate_count": 2,
            "known_limitations": [
                "IP addresses can merge people on shared networks and split one person across changing networks.",
                "Browser device IDs reset when storage is cleared or another browser/device is used.",
                "Historical time-of-day is UTC; local-time analysis becomes available as timezone metadata accumulates.",
                "Country is populated only when a trusted reverse proxy supplies a country header.",
            ],
        },
    }


@router.get("/api/analytics/growth")
def get_growth_analytics(
    days: int = 30,
    request: Request = None,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Return the acquisition-to-value scorecard used for the 10k DAU milestone."""
    admin_auth(credentials, request)
    days = max(7, min(days, 365))
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    daily_rows = db.execute(
        text(
            """
            WITH activity AS (
                SELECT
                    DATE(created_at) AS activity_date,
                    COALESCE(NULLIF(device_id, ''), NULLIF(user_ip, '')) AS actor_id,
                    event_name
                FROM product_events
                WHERE created_at >= :cutoff
                  AND COALESCE(user_ip, '') != :internal_user_ip
            )
            SELECT
                activity_date,
                COUNT(DISTINCT actor_id) FILTER (WHERE event_name = 'app_opened') AS dau,
                COUNT(DISTINCT actor_id) FILTER (WHERE event_name = 'question_submitted') AS askers,
                COUNT(DISTINCT actor_id) FILTER (WHERE event_name = 'question_answered') AS answered_users,
                COUNT(DISTINCT actor_id) FILTER (
                    WHERE event_name IN ('reflection_note_saved', 'share_cta_used', 'citation_action_used')
                ) AS value_users,
                COUNT(DISTINCT actor_id) FILTER (WHERE event_name = 'referral_cta_used') AS referrers
            FROM activity
            WHERE actor_id IS NOT NULL
            GROUP BY activity_date
            ORDER BY activity_date
            """
        ),
        {"cutoff": cutoff, "internal_user_ip": INTERNAL_USER_IP},
    ).fetchall()

    retention = db.execute(
        text(
            """
            WITH opens AS (
                SELECT DISTINCT
                    DATE(created_at) AS activity_date,
                    COALESCE(NULLIF(device_id, ''), NULLIF(user_ip, '')) AS actor_id
                FROM product_events
                WHERE created_at >= :cutoff
                  AND event_name = 'app_opened'
                  AND COALESCE(user_ip, '') != :internal_user_ip
            )
            SELECT
                COUNT(*) FILTER (WHERE next_day.actor_id IS NOT NULL) AS retained_users,
                COUNT(*) AS eligible_users
            FROM opens cohort
            LEFT JOIN opens next_day
              ON next_day.actor_id = cohort.actor_id
             AND next_day.activity_date = cohort.activity_date + 1
            WHERE cohort.activity_date < CURRENT_DATE
            """
        ),
        {"cutoff": cutoff, "internal_user_ip": INTERNAL_USER_IP},
    ).one()

    series = [
        {
            "date": row[0].isoformat(),
            "dau": int(row[1] or 0),
            "askers": int(row[2] or 0),
            "answered_users": int(row[3] or 0),
            "value_users": int(row[4] or 0),
            "referrers": int(row[5] or 0),
        }
        for row in daily_rows
    ]
    latest = series[-1] if series else {"dau": 0, "askers": 0, "answered_users": 0, "value_users": 0, "referrers": 0}
    dau = latest["dau"]
    eligible = int(retention[1] or 0)

    return {
        "period_days": days,
        "milestone_dau": 10000,
        "latest": {
            **latest,
            "progress_percent": round(dau / 10000 * 100, 2),
            "visitor_to_question_percent": round(latest["askers"] / dau * 100, 2) if dau else None,
            "visitor_to_value_percent": round(latest["value_users"] / dau * 100, 2) if dau else None,
        },
        "day_1_retention_percent": round(int(retention[0] or 0) / eligible * 100, 2) if eligible else None,
        "daily": series,
        "definitions": {
            "dau": "Distinct device IDs opening Ask Mirror Talk on a UTC calendar day; IP is fallback only.",
            "value_user": "A daily active user who saves a note, shares, or opens a cited source.",
            "day_1_retention": "Eligible daily openers who also open the product on the following UTC day.",
        },
    }


@router.get("/api/analytics/episodes")
def get_episode_analytics(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Get detailed episode analytics."""
    admin_auth(credentials, request)
    try:
        results = db.execute(
            text("""
                WITH episode_citations AS (
                    SELECT
                        e.id,
                        e.title,
                        e.published_at,
                        COUNT(DISTINCT q.id) as total_citations
                    FROM episodes e
                    LEFT JOIN (
                        SELECT id, UNNEST(STRING_TO_ARRAY(episode_ids, ','))::int as episode_id
                        FROM qa_logs
                        WHERE COALESCE(user_ip, '') != :internal_user_ip
                    ) q ON q.episode_id = e.id
                    GROUP BY e.id, e.title, e.published_at
                ),
                episode_clicks AS (
                    SELECT
                        episode_id,
                        COUNT(*) as total_clicks
                    FROM citation_clicks
                    GROUP BY episode_id
                )
                SELECT
                    ec.id,
                    ec.title,
                    ec.published_at,
                    ec.total_citations,
                    COALESCE(eck.total_clicks, 0) as total_clicks,
                    CASE
                        WHEN ec.total_citations > 0 THEN
                            ROUND((COALESCE(eck.total_clicks, 0)::float / ec.total_citations * 100), 2)
                        ELSE 0
                    END as ctr_percent
                FROM episode_citations ec
                LEFT JOIN episode_clicks eck ON eck.episode_id = ec.id
                ORDER BY ec.total_citations DESC
                LIMIT 50
            """),
            {"internal_user_ip": INTERNAL_USER_IP},
        ).fetchall()

        return {
            "episodes": [
                {
                    "id": row[0],
                    "title": row[1],
                    "published_at": row[2].isoformat() if row[2] else None,
                    "citations": row[3],
                    "clicks": row[4],
                    "ctr_percent": row[5],
                }
                for row in results
            ]
        }
    except Exception as e:
        logger.error("Error getting episode analytics: %s", e)
        db.rollback()
        try:
            results = db.execute(
                text("""
                    SELECT
                        e.id,
                        e.title,
                        e.published_at,
                        COUNT(DISTINCT q.id) as total_citations
                    FROM episodes e
                    LEFT JOIN (
                        SELECT id, UNNEST(STRING_TO_ARRAY(episode_ids, ','))::int as episode_id
                        FROM qa_logs
                        WHERE COALESCE(user_ip, '') != :internal_user_ip
                    ) q ON q.episode_id = e.id
                    GROUP BY e.id, e.title, e.published_at
                    ORDER BY total_citations DESC
                    LIMIT 50
                """),
                {"internal_user_ip": INTERNAL_USER_IP},
            ).fetchall()
            return {
                "episodes": [
                    {
                        "id": row[0],
                        "title": row[1],
                        "published_at": row[2].isoformat() if row[2] else None,
                        "citations": row[3],
                        "clicks": None,
                        "ctr_percent": None,
                    }
                    for row in results
                ]
            }
        except Exception as e2:
            logger.error("Error getting simplified episode analytics: %s", e2)
            raise HTTPException(status_code=500, detail=str(e2))


@router.get("/api/admin/episodes/export")
def export_episode_catalog(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
    limit: int = 500,
    search: str = "",
    include_transcript: bool = True,
):
    """Admin endpoint: export episode metadata and latest transcript for internal tools."""
    admin_auth(credentials, request)

    safe_limit = max(1, min(int(limit or 500), 2000))
    normalized_search = search.strip().lower()
    pattern = f"%{normalized_search}%" if normalized_search else ""

    results = db.execute(
        text(
            """
            SELECT
                e.id,
                e.guid,
                e.title,
                e.description,
                e.published_at,
                e.audio_url,
                t.raw_text,
                t.provider,
                t.created_at
            FROM episodes e
            LEFT JOIN LATERAL (
                SELECT raw_text, provider, created_at
                FROM transcripts
                WHERE episode_id = e.id
                ORDER BY created_at DESC, id DESC
                LIMIT 1
            ) t ON TRUE
            WHERE (
                :pattern = ''
                OR LOWER(e.title) LIKE :pattern
                OR LOWER(COALESCE(e.guid, '')) LIKE :pattern
            )
            ORDER BY e.published_at DESC NULLS LAST, e.id DESC
            LIMIT :limit
            """
        ),
        {"pattern": pattern, "limit": safe_limit},
    ).fetchall()

    episodes = []
    for row in results:
        transcript_text = row[6] if include_transcript else None
        episodes.append(
            {
                "id": row[0],
                "guid": row[1],
                "title": row[2],
                "description": row[3],
                "published_at": row[4].isoformat() if row[4] else None,
                "audio_url": row[5],
                "transcript_text": transcript_text,
                "transcript_provider": row[7],
                "transcript_created_at": row[8].isoformat() if row[8] else None,
            }
        )

    return {
        "count": len(episodes),
        "limit": safe_limit,
        "search": normalized_search,
        "include_transcript": include_transcript,
        "episodes": episodes,
    }
