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
            "top_questions": [{"question": q[0], "count": q[1]} for q in top_questions],
            "most_cited_episodes": [
                {"id": episode[0], "title": episode[1], "citations": episode[2]}
                for episode in most_cited
            ],
        }
    except Exception as e:
        logger.error("Error getting analytics summary: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


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
