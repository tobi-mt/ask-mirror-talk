import time

from fastapi import HTTPException

from app.core.config import settings

_rate_limit_bucket: dict[str, list[float]] = {}
_daily_limit_bucket: dict[str, list[float]] = {}


def enforce_rate_limit(ip: str):
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


def clear_rate_limits():
    _rate_limit_bucket.clear()
    _daily_limit_bucket.clear()
