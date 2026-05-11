import time
import hashlib

from fastapi import HTTPException

from app.core.config import settings

_rate_limit_bucket: dict[str, list[float]] = {}
_daily_limit_bucket: dict[str, list[float]] = {}
_question_burst_tracker: dict[str, dict[str, list[float]]] = {}  # {ip: {question_hash: [timestamps]}}


def enforce_rate_limit(ip: str, question: str | None = None):
    """Enforce rate limits with bot/burst detection."""
    now = time.time()
    
    # Per-minute limit (prevents rapid bursts)
    minute_window = 60
    bucket = _rate_limit_bucket.get(ip, [])
    bucket = [timestamp for timestamp in bucket if now - timestamp < minute_window]
    if len(bucket) >= settings.rate_limit_per_minute:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please wait a minute.")
    bucket.append(now)
    if bucket:
        _rate_limit_bucket[ip] = bucket
    elif ip in _rate_limit_bucket:
        del _rate_limit_bucket[ip]
    
    # Daily limit (prevents single IP dominating usage)
    day_window = 86400  # 24 hours
    daily_bucket = _daily_limit_bucket.get(ip, [])
    daily_bucket = [timestamp for timestamp in daily_bucket if now - timestamp < day_window]
    daily_limit = getattr(settings, 'rate_limit_per_day', 100)  # Default 100/day
    if len(daily_bucket) >= daily_limit:
        raise HTTPException(status_code=429, detail="Daily question limit reached. Please try again tomorrow.")
    daily_bucket.append(now)
    if daily_bucket:
        _daily_limit_bucket[ip] = daily_bucket
    elif ip in _daily_limit_bucket:
        del _daily_limit_bucket[ip]
    
    # Bot/burst detection: same question repeated rapidly
    if question:
        _check_suspicious_burst(ip, question, now)


def _check_suspicious_burst(ip: str, question: str, now: float):
    """Detect suspicious repeated question patterns (bot behavior)."""
    burst_threshold = getattr(settings, 'rate_limit_burst_threshold', 5)
    burst_window = getattr(settings, 'rate_limit_burst_window', 300)  # 5 minutes
    
    # Hash question for tracking (normalize first)
    question_hash = hashlib.md5(question.lower().strip().encode()).hexdigest()[:8]
    
    if ip not in _question_burst_tracker:
        _question_burst_tracker[ip] = {}
    
    ip_tracker = _question_burst_tracker[ip]
    
    # Clean old timestamps
    if question_hash in ip_tracker:
        ip_tracker[question_hash] = [
            ts for ts in ip_tracker[question_hash] 
            if now - ts < burst_window
        ]
    else:
        ip_tracker[question_hash] = []
    
    # Check if burst threshold exceeded
    if len(ip_tracker[question_hash]) >= burst_threshold:
        raise HTTPException(
            status_code=429, 
            detail="Suspicious activity detected. Please vary your questions or wait a few minutes."
        )
    
    ip_tracker[question_hash].append(now)
    
    # Cleanup: remove empty trackers
    if not ip_tracker[question_hash]:
        del ip_tracker[question_hash]
    if not ip_tracker:
        del _question_burst_tracker[ip]


def clear_rate_limits():
    _rate_limit_bucket.clear()
    _daily_limit_bucket.clear()
    _question_burst_tracker.clear()
