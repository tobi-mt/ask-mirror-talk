import ipaddress
import secrets

from fastapi import HTTPException, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.core.config import settings

security = HTTPBasic()


def get_client_ip(request: Request) -> str:
    """Return the real client IP, honouring X-Forwarded-For when present."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def ip_allowed(ip: str) -> bool:
    if not settings.admin_ip_allowlist:
        return True
    ranges = [entry.strip() for entry in settings.admin_ip_allowlist.split(",") if entry.strip()]
    if not ranges:
        return True
    try:
        ip_addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    for entry in ranges:
        try:
            if ip_addr in ipaddress.ip_network(entry, strict=False):
                return True
        except ValueError:
            if entry == ip:
                return True
    return False


def admin_auth(credentials: HTTPBasicCredentials | None, request: Request):
    if not settings.admin_enabled:
        raise HTTPException(status_code=404, detail="Not found")
    if not ip_allowed(get_client_ip(request)):
        raise HTTPException(status_code=403, detail="Forbidden")
    if credentials is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    is_user = secrets.compare_digest(credentials.username, settings.admin_user)
    is_pass = secrets.compare_digest(credentials.password, settings.admin_password)
    if not (is_user and is_pass):
        raise HTTPException(status_code=401, detail="Unauthorized")
