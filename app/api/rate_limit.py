import time

from fastapi import HTTPException

from app.core.config import settings

_rate_limit_bucket: dict[str, list[float]] = {}


def enforce_rate_limit(ip: str):
    now = time.time()
    window = 60
    bucket = _rate_limit_bucket.get(ip, [])
    bucket = [timestamp for timestamp in bucket if now - timestamp < window]
    if len(bucket) >= settings.rate_limit_per_minute:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    bucket.append(now)
    if bucket:
        _rate_limit_bucket[ip] = bucket
    elif ip in _rate_limit_bucket:
        del _rate_limit_bucket[ip]


def clear_rate_limits():
    _rate_limit_bucket.clear()
