from app.api.routes.intelligence import ALLOWED_EVENTS, SearchMetricRow, _clean_metadata, _period_days
from app.api.routes import intelligence
from starlette.requests import Request
from fastapi import HTTPException


def test_intelligence_collector_allowlists_events_and_metadata():
    assert "site_page_view" in ALLOWED_EVENTS
    assert "podcast_complete" in ALLOWED_EVENTS
    assert "web_vital" in ALLOWED_EVENTS
    cleaned = _clean_metadata({"path": "/hello", "question": "private", "nested": {"no": "thanks"}})
    assert cleaned == {"path": "/hello"}


def test_intelligence_period_is_bounded_to_known_windows():
    assert _period_days("7d") == 7
    assert _period_days("90d") == 90
    assert _period_days("forever") == 30


def test_search_metrics_validate_engine_and_nonnegative_counts():
    row = SearchMetricRow(date="2026-10-02T00:00:00Z", engine="google", clicks=2, impressions=20, ctr=0.1, position=4.2)
    assert row.engine == "google"
    assert row.clicks == 2


def test_collector_rejects_unconfigured_origin(monkeypatch):
    monkeypatch.setattr(intelligence.settings, "allowed_origins", "https://mirrortalkpodcast.com")
    request = Request({"type": "http", "method": "POST", "path": "/api/intelligence/event", "headers": [(b"origin", b"https://spam.invalid")], "client": ("203.0.113.10", 443)})
    try:
        intelligence._enforce_collector_origin_and_rate(request)
        assert False, "untrusted origin was accepted"
    except HTTPException as exc:
        assert exc.status_code == 403
