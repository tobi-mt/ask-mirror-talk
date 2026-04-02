from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import html

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasicCredentials
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.auth import admin_auth, security
from app.core.db import get_db

router = APIRouter()

_ADMIN_CSS = """
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
       margin: 0; padding: 24px; background: #f5f5f5; }
.container { max-width: 1400px; margin: 0 auto; }
h1 { color: #333; margin-bottom: 8px; }
.subtitle { color: #666; margin-bottom: 32px; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
         gap: 16px; margin-bottom: 32px; }
.stat-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.stat-card h3 { margin: 0 0 8px 0; color: #666; font-size: 14px; font-weight: 500; }
.stat-card .value { font-size: 32px; font-weight: 700; color: #333; }
.stat-card .label { font-size: 12px; color: #999; margin-top: 4px; }
.section { background: white; padding: 24px; border-radius: 8px;
           box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 24px; }
h2 { margin: 0 0 16px 0; font-size: 18px; color: #333; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
th { background: #f9f9f9; font-weight: 600; font-size: 13px; color: #666; }
td { font-size: 14px; color: #333; }
tr:hover { background: #f9f9f9; }
.api-links { margin-bottom: 24px; }
.api-links a { display: inline-block; margin-right: 16px; padding: 8px 16px;
               background: #007bff; color: white; text-decoration: none;
               border-radius: 4px; font-size: 14px; }
.api-links a:hover { background: #0056b3; }
"""


@dataclass
class AdminDashboardData:
    total_questions: int
    unique_users: int
    avg_latency: float
    fb_positive: int
    fb_negative: int
    fb_total: int
    fb_pct: int | None
    unanswered_count: int | None
    cached_count: int | None
    top_unanswered: list
    top_episodes: list
    runs: list
    logs: list


def _table_rows(rows: list[tuple], builders: list) -> str:
    return "".join(
        "<tr>" + "".join(f"<td>{builder(row)}</td>" for builder in builders) + "</tr>"
        for row in rows
    )


def _stat_card(title: str, value: str, label: str) -> str:
    return f"""
    <div class="stat-card">
      <h3>{title}</h3>
      <div class="value">{value}</div>
      <div class="label">{label}</div>
    </div>"""


def render_admin_dashboard_html(data: AdminDashboardData) -> str:
    runs_rows = _table_rows(
        data.runs,
        [
            lambda row: html.escape(str(row[0])),
            lambda row: html.escape(str(row[1])),
            lambda row: html.escape(str(row[2] or "")),
            lambda row: html.escape(str(row[3])),
            lambda row: html.escape(str(row[4])[:100]),
        ],
    )
    logs_rows = _table_rows(
        data.logs,
        [
            lambda row: html.escape(str(row[0])),
            lambda row: html.escape(str(row[1])),
            lambda row: html.escape(str(row[2])[:100]),
            lambda row: html.escape(str(row[3])),
            lambda row: html.escape(str(row[4])),
        ],
    )
    top_episodes_rows = _table_rows(
        data.top_episodes,
        [
            lambda row: html.escape(str(row[0])),
            lambda row: html.escape(str(row[1])[:100]),
            lambda row: html.escape(str(row[2])),
        ],
    )
    unanswered_rows = _table_rows(
        data.top_unanswered,
        [
            lambda row: html.escape(str(row[0])[:120]),
            lambda row: html.escape(str(row[1])),
        ],
    )

    feedback_card = ""
    if data.fb_total > 0:
        pct_display = f"{data.fb_pct}%" if data.fb_pct is not None else "n/a"
        feedback_card = _stat_card(
            "User Satisfaction",
            pct_display,
            f"👍 {data.fb_positive} &nbsp; 👎 {data.fb_negative} &nbsp; ({data.fb_total} total)",
        )

    unanswered_card = ""
    if data.unanswered_count is not None:
        cache_pct = round(data.cached_count / data.total_questions * 100) if data.total_questions else 0
        unanswered_card = (
            _stat_card("Unanswered", str(data.unanswered_count), "No matching episodes found")
            + _stat_card("Cache Hits", f"{cache_pct}%", f"{data.cached_count} of {data.total_questions} served from cache")
        )

    unanswered_section = ""
    if data.top_unanswered:
        unanswered_section = f"""
          <div class="section">
            <h2>❓ Top Unanswered Questions (7 days)</h2>
            <table>
              <thead><tr><th>Question</th><th>Asked</th></tr></thead>
              <tbody>{unanswered_rows}</tbody>
            </table>
          </div>"""

    return f"""
    <html>
      <head>
        <title>Ask Mirror Talk Admin</title>
        <style>{_ADMIN_CSS}</style>
      </head>
      <body>
        <div class="container">
          <h1>📊 Ask Mirror Talk Admin</h1>
          <div class="subtitle">Analytics & System Dashboard</div>

          <div class="api-links">
            <a href="/api/analytics/summary?days=7" target="_blank">📊 Analytics API</a>
            <a href="/api/analytics/episodes" target="_blank">📚 Episode Analytics</a>
            <a href="/status" target="_blank">⚙️ System Status</a>
          </div>

          <div class="stats">
            {_stat_card("Questions (7 days)", str(data.total_questions), "Total queries")}
            {_stat_card("Unique Users", str(data.unique_users), "Last 7 days")}
            {_stat_card("Avg Response Time", f"{int(data.avg_latency)}ms", "Answer latency")}
            {feedback_card}
            {unanswered_card}
          </div>

          <div class="section">
            <h2>🔥 Top Cited Episodes (7 days)</h2>
            <table>
              <thead><tr><th>ID</th><th>Episode Title</th><th>Citations</th></tr></thead>
              <tbody>{top_episodes_rows if data.top_episodes else '<tr><td colspan="3">No data yet</td></tr>'}</tbody>
            </table>
          </div>

          {unanswered_section}

          <div class="section">
            <h2>💬 Recent Questions</h2>
            <table>
              <thead><tr><th>ID</th><th>Time</th><th>Question</th><th>Latency (ms)</th><th>IP</th></tr></thead>
              <tbody>{logs_rows if data.logs else '<tr><td colspan="5">No questions yet</td></tr>'}</tbody>
            </table>
          </div>

          <div class="section">
            <h2>🔄 Recent Ingestion Runs</h2>
            <table>
              <thead><tr><th>ID</th><th>Started</th><th>Finished</th><th>Status</th><th>Message</th></tr></thead>
              <tbody>{runs_rows if data.runs else '<tr><td colspan="5">No ingestion runs yet</td></tr>'}</tbody>
            </table>
          </div>
        </div>
      </body>
    </html>
    """


def _fetch_admin_dashboard_data(db: Session) -> AdminDashboardData:
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)

    total_questions = db.execute(
        text("SELECT COUNT(*) FROM qa_logs WHERE created_at >= :cutoff"),
        {"cutoff": cutoff},
    ).scalar() or 0
    unique_users = db.execute(
        text("SELECT COUNT(DISTINCT user_ip) FROM qa_logs WHERE created_at >= :cutoff"),
        {"cutoff": cutoff},
    ).scalar() or 0
    avg_latency = db.execute(
        text("SELECT AVG(latency_ms) FROM qa_logs WHERE created_at >= :cutoff"),
        {"cutoff": cutoff},
    ).scalar() or 0

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
        fb_positive = feedback_counts.get("positive", 0)
        fb_negative = feedback_counts.get("negative", 0)
        fb_total = sum(feedback_counts.values())
        fb_pct = round(fb_positive / (fb_positive + fb_negative) * 100) if (fb_positive + fb_negative) > 0 else None
    except Exception:
        db.rollback()
        fb_positive = fb_negative = fb_total = 0
        fb_pct = None

    try:
        unanswered_count = db.execute(
            text("SELECT COUNT(*) FROM qa_logs WHERE created_at >= :cutoff AND is_answered = FALSE"),
            {"cutoff": cutoff},
        ).scalar() or 0
        cached_count = db.execute(
            text("SELECT COUNT(*) FROM qa_logs WHERE created_at >= :cutoff AND is_cached = TRUE"),
            {"cutoff": cutoff},
        ).scalar() or 0
        top_unanswered = db.execute(
            text("""
                SELECT question, COUNT(*) as cnt
                FROM qa_logs
                WHERE created_at >= :cutoff AND is_answered = FALSE
                GROUP BY question
                ORDER BY cnt DESC
                LIMIT 10
            """),
            {"cutoff": cutoff},
        ).fetchall()
    except Exception:
        db.rollback()
        unanswered_count = cached_count = None
        top_unanswered = []

    top_episodes = db.execute(
        text("""
            SELECT
                e.id,
                e.title,
                COUNT(*) as citation_count
            FROM qa_logs q
            CROSS JOIN LATERAL UNNEST(STRING_TO_ARRAY(q.episode_ids, ',')) AS episode_id
            JOIN episodes e ON e.id = episode_id::int
            WHERE q.created_at >= :cutoff
            GROUP BY e.id, e.title
            ORDER BY citation_count DESC
            LIMIT 10
        """),
        {"cutoff": cutoff},
    ).fetchall()
    runs = db.execute(
        text("SELECT id, started_at, finished_at, status, message FROM ingest_runs ORDER BY started_at DESC LIMIT 10")
    ).all()
    logs = db.execute(
        text("SELECT id, created_at, question, latency_ms, user_ip FROM qa_logs ORDER BY created_at DESC LIMIT 15")
    ).all()

    return AdminDashboardData(
        total_questions=total_questions,
        unique_users=unique_users,
        avg_latency=avg_latency,
        fb_positive=fb_positive,
        fb_negative=fb_negative,
        fb_total=fb_total,
        fb_pct=fb_pct,
        unanswered_count=unanswered_count,
        cached_count=cached_count,
        top_unanswered=top_unanswered,
        top_episodes=top_episodes,
        runs=runs,
        logs=logs,
    )


@router.get("/admin", response_class=HTMLResponse)
def admin_dashboard(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    admin_auth(credentials, request)
    return HTMLResponse(content=render_admin_dashboard_html(_fetch_admin_dashboard_data(db)))
