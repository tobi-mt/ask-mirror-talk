"""First-party website intelligence and SEO reporting.

The public collector accepts a deliberately small, allow-listed event shape. It
never accepts page text, questions, email addresses, or arbitrary metadata.
Reporting routes are protected by the existing administrator authentication.
"""
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import html
import json
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasicCredentials
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.auth import admin_auth, security
from app.api.routes.interactions import get_client_ip
from app.core.db import get_db
from app.core.config import settings
from app.storage.repository import log_product_event
from app.storage.models import SearchPerformanceMetric

router = APIRouter()
_collector_windows: dict[str, list[float]] = {}

ALLOWED_EVENTS = {
    "site_page_view", "site_engaged", "site_outbound_click", "site_internal_journey",
    "podcast_play", "podcast_pause", "podcast_progress", "podcast_complete",
    "episode_discovered", "web_vital", "broken_link_seen", "seo_audit_result",
    "newsletter_subscribed",
}
ALLOWED_METADATA = {
    "path", "referrer_host", "campaign_source", "campaign_medium", "campaign_name",
    "entry_path", "previous_path", "destination_path", "link_host", "episode_id",
    "episode_title", "progress_bucket", "metric", "value", "rating", "connection",
    "device_class", "language", "timezone", "returning", "status", "target",
    "audit_type", "recommendation", "device_id",
}


class IntelligenceEvent(BaseModel):
    event_name: str = Field(min_length=1, max_length=80)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchMetricRow(BaseModel):
    date: datetime
    engine: str = Field(pattern="^(google|bing)$")
    query: str = Field(default="", max_length=500)
    page: str = Field(default="", max_length=1000)
    country: str = Field(default="", max_length=8)
    device: str = Field(default="", max_length=30)
    clicks: int = Field(default=0, ge=0)
    impressions: int = Field(default=0, ge=0)
    ctr: float = Field(default=0, ge=0)
    position: float = Field(default=0, ge=0)


def _clean_metadata(raw: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in raw.items():
        if key not in ALLOWED_METADATA or isinstance(value, (dict, list)):
            continue
        cleaned[key] = str(value)[:500] if value is not None else None
    return cleaned


def _anonymous_network_id(request: Request) -> str:
    """One-way daily network token: useful for abuse diagnosis, not an IP log."""
    raw = get_client_ip(request)
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    digest = hmac.new(settings.analytics_hash_salt.encode(), f"{day}:{raw}".encode(), hashlib.sha256).hexdigest()
    return f"anon:{digest[:24]}"


def _enforce_collector_origin_and_rate(request: Request) -> str:
    origin = (request.headers.get("origin") or "").rstrip("/")
    configured = {item.strip().rstrip("/") for item in settings.allowed_origins.split(",") if item.strip()}
    accepted = configured | {item.replace("://www.", "://") for item in configured} | {item.replace("://", "://www.") for item in configured if "://www." not in item}
    if configured and origin not in accepted:
        raise HTTPException(status_code=403, detail="Origin not allowed")
    network_id = _anonymous_network_id(request)
    now = time.time()
    recent = [stamp for stamp in _collector_windows.get(network_id, []) if now - stamp < 60]
    if len(recent) >= 120:
        raise HTTPException(status_code=429, detail="Collector rate limit exceeded")
    recent.append(now)
    _collector_windows[network_id] = recent
    if len(_collector_windows) > 10000:
        cutoff = now - 60
        for key in list(_collector_windows)[:2000]:
            if not any(stamp >= cutoff for stamp in _collector_windows[key]):
                _collector_windows.pop(key, None)
    return network_id


@router.post("/api/intelligence/event")
def collect_intelligence_event(payload: IntelligenceEvent, request: Request, db: Session = Depends(get_db)):
    if payload.event_name not in ALLOWED_EVENTS:
        raise HTTPException(status_code=400, detail="Unsupported intelligence event")
    network_id = _enforce_collector_origin_and_rate(request)
    metadata = _clean_metadata(payload.metadata)
    device_id = str(metadata.pop("device_id", ""))[:64] or None
    log_product_event(
        db,
        event_name=payload.event_name,
        user_ip=network_id,
        metadata=metadata,
        device_id=device_id,
    )
    return {"status": "ok"}


def _period_days(period: str) -> int:
    return {"7d": 7, "30d": 30, "90d": 90}.get(period, 30)


def _intelligence_snapshot(db: Session, days: int) -> dict[str, Any]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    totals = db.execute(text("""
        SELECT
          COUNT(*) FILTER (WHERE event_name='site_page_view') AS page_views,
          COUNT(DISTINCT device_id) FILTER (WHERE event_name='site_page_view') AS visitors,
          COUNT(*) FILTER (WHERE event_name='podcast_play') AS plays,
          COUNT(*) FILTER (WHERE event_name='podcast_complete') AS completions,
          COUNT(*) FILTER (WHERE event_name='broken_link_seen') AS broken_links
        FROM product_events WHERE created_at >= :cutoff
    """), {"cutoff": cutoff}).mappings().one()
    top_pages = db.execute(text("""
        SELECT COALESCE(metadata_json::jsonb->>'path','unknown') path, COUNT(*) views,
               COUNT(DISTINCT device_id) visitors
        FROM product_events WHERE created_at >= :cutoff AND event_name='site_page_view'
        GROUP BY 1 ORDER BY views DESC LIMIT 20
    """), {"cutoff": cutoff}).mappings().all()
    campaigns = db.execute(text("""
        SELECT COALESCE(metadata_json::jsonb->>'campaign_source','direct') source, COUNT(*) visits
        FROM product_events WHERE created_at >= :cutoff AND event_name='site_page_view'
        GROUP BY 1 ORDER BY visits DESC LIMIT 15
    """), {"cutoff": cutoff}).mappings().all()
    episodes = db.execute(text("""
        SELECT COALESCE(metadata_json::jsonb->>'episode_title','Unknown episode') episode,
          COUNT(*) FILTER (WHERE event_name='podcast_play') plays,
          COUNT(*) FILTER (WHERE event_name='podcast_complete') completions
        FROM product_events WHERE created_at >= :cutoff
          AND event_name IN ('podcast_play','podcast_complete')
        GROUP BY 1 ORDER BY plays DESC LIMIT 20
    """), {"cutoff": cutoff}).mappings().all()
    vitals = db.execute(text("""
        SELECT metadata_json::jsonb->>'metric' metric,
          ROUND(AVG((metadata_json::jsonb->>'value')::numeric),2) average,
          metadata_json::jsonb->>'rating' rating, COUNT(*) samples
        FROM product_events WHERE created_at >= :cutoff AND event_name='web_vital'
        GROUP BY 1,3 ORDER BY 1,3
    """), {"cutoff": cutoff}).mappings().all()
    return {"days": days, "totals": dict(totals), "top_pages": [dict(r) for r in top_pages],
            "campaigns": [dict(r) for r in campaigns], "episodes": [dict(r) for r in episodes],
            "web_vitals": [dict(r) for r in vitals]}


@router.get("/api/intelligence/overview")
def intelligence_overview(period: str = "30d", request: Request = None,
                          credentials: HTTPBasicCredentials = Depends(security), db: Session = Depends(get_db)):
    admin_auth(credentials, request)
    return _intelligence_snapshot(db, _period_days(period))


@router.post("/api/intelligence/search-performance/import")
def import_search_performance(rows: list[SearchMetricRow], request: Request,
                              credentials: HTTPBasicCredentials = Depends(security), db: Session = Depends(get_db)):
    """Connector target for scheduled Google Search Console/Bing exports."""
    admin_auth(credentials, request)
    if len(rows) > 10000:
        raise HTTPException(status_code=413, detail="Maximum 10,000 rows per import")
    for row in rows:
        db.add(SearchPerformanceMetric(metric_date=row.date, engine=row.engine, query=row.query,
                                       page=row.page, country=row.country, device=row.device,
                                       clicks=row.clicks, impressions=row.impressions,
                                       ctr=row.ctr, position=row.position))
    db.commit()
    return {"status": "ok", "imported": len(rows)}


@router.get("/api/intelligence/search-performance")
def search_performance(days: int = 30, request: Request = None,
                       credentials: HTTPBasicCredentials = Depends(security), db: Session = Depends(get_db)):
    admin_auth(credentials, request)
    cutoff = datetime.now(timezone.utc) - timedelta(days=max(1, min(days, 365)))
    totals = db.execute(text("""SELECT COALESCE(SUM(clicks),0) clicks, COALESCE(SUM(impressions),0) impressions,
      ROUND(AVG(position)::numeric,2) average_position FROM search_performance_metrics WHERE metric_date >= :cutoff"""), {"cutoff": cutoff}).mappings().one()
    queries = db.execute(text("""SELECT query, SUM(clicks) clicks, SUM(impressions) impressions,
      ROUND(AVG(position)::numeric,2) position FROM search_performance_metrics WHERE metric_date >= :cutoff
      GROUP BY query ORDER BY impressions DESC LIMIT 50"""), {"cutoff": cutoff}).mappings().all()
    return {"days": days, "totals": dict(totals), "queries": [dict(row) for row in queries]}


@router.get("/api/intelligence/weekly-report")
def weekly_report(request: Request, credentials: HTTPBasicCredentials = Depends(security),
                  db: Session = Depends(get_db)):
    admin_auth(credentials, request)
    snapshot = _intelligence_snapshot(db, 7)
    totals = snapshot["totals"]
    plays = int(totals.get("plays") or 0)
    completions = int(totals.get("completions") or 0)
    snapshot["generated_at"] = datetime.now(timezone.utc).isoformat()
    snapshot["insights"] = [
        f"Podcast completion rate: {round(completions / plays * 100, 1) if plays else 0}%.",
        f"Broken-link observations: {int(totals.get('broken_links') or 0)}.",
        "Connect Google Search Console to add verified impressions, queries, positions and indexing data.",
    ]
    return snapshot


@router.get("/admin/intelligence", response_class=HTMLResponse)
def intelligence_dashboard(request: Request, credentials: HTTPBasicCredentials = Depends(security),
                           db: Session = Depends(get_db)):
    admin_auth(credentials, request)
    data = _intelligence_snapshot(db, 30)
    cards = "".join(f"<article><small>{html.escape(k.replace('_',' ').title())}</small><strong>{v or 0}</strong></article>" for k, v in data["totals"].items())
    pages = "".join(f"<tr><td>{html.escape(str(r['path']))}</td><td>{r['views']}</td><td>{r['visitors']}</td></tr>" for r in data["top_pages"])
    episodes = "".join(f"<tr><td>{html.escape(str(r['episode']))}</td><td>{r['plays']}</td><td>{r['completions']}</td></tr>" for r in data["episodes"])
    return HTMLResponse(f"""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'>
    <title>Mirror Talk Intelligence</title><style>body{{margin:0;padding:32px;background:#100d14;color:#fffaf3;font:16px system-ui}}main{{max-width:1200px;margin:auto}}h1{{font:clamp(42px,7vw,82px) Georgia}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px}}article,section{{padding:22px;border:1px solid #433847;border-radius:20px;background:#1b1620}}article strong{{display:block;font-size:34px;margin-top:8px;color:#f4c967}}table{{width:100%;border-collapse:collapse}}td,th{{padding:12px;border-bottom:1px solid #433847;text-align:left}}section{{margin-top:20px;overflow:auto}}a{{color:#ff9678}}</style></head>
    <body><main><p>MIRROR TALK</p><h1>Intelligence &amp; SEO</h1><div class='grid'>{cards}</div>
    <section><h2>Top pages · 30 days</h2><table><tr><th>Page</th><th>Views</th><th>Visitors</th></tr>{pages}</table></section>
    <section><h2>Podcast listening</h2><table><tr><th>Episode</th><th>Plays</th><th>Completed</th></tr>{episodes}</table></section>
    <section><h2>Search performance</h2><p>Verified Google/Bing metrics appear after their scheduled connector imports data. The protected import and reporting APIs are ready.</p><a href='/api/intelligence/search-performance'>Search performance</a> · <a href='/api/intelligence/weekly-report'>Weekly report</a></section></main></body></html>""")
