from fastapi import HTTPException
from fastapi.security import HTTPBasicCredentials
from starlette.requests import Request

from app.api.auth import admin_auth
from app.api.routes import push as push_routes
from app.core.config import settings


class DummyExecuteResult:
    def __init__(self, scalar_value=None, rowcount=1):
        self._scalar_value = scalar_value
        self.rowcount = rowcount

    def scalar(self):
        return self._scalar_value


class DummyPushDb:
    def __init__(self, execute_results=None):
        self.execute_results = list(execute_results or [])
        self.executed = []
        self.commits = 0
        self.rollbacks = 0

    def execute(self, statement, params=None):
        self.executed.append((str(statement), params or {}))
        if self.execute_results:
            return self.execute_results.pop(0)
        return DummyExecuteResult()

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


def _request(ip="127.0.0.1"):
    return Request({"type": "http", "headers": [], "client": (ip, 1234)})


def test_push_subscribe_requires_vapid_key(monkeypatch):
    monkeypatch.setattr(settings, "vapid_public_key", "")
    payload = push_routes.PushSubscriptionRequest(endpoint="https://example.com", keys={"p256dh": "x", "auth": "y"})

    try:
        push_routes.push_subscribe(payload, _request(), DummyPushDb())
    except HTTPException as exc:
        assert exc.status_code == 503
        assert exc.detail == "Push notifications not configured"
    else:
        raise AssertionError("Expected HTTPException")


def test_push_subscribe_rejects_missing_keys(monkeypatch):
    monkeypatch.setattr(settings, "vapid_public_key", "public-key")
    payload = push_routes.PushSubscriptionRequest(endpoint="https://example.com", keys={"p256dh": ""})

    try:
        push_routes.push_subscribe(payload, _request(), DummyPushDb())
    except HTTPException as exc:
        assert exc.status_code == 400
        assert exc.detail == "Missing p256dh or auth key"
    else:
        raise AssertionError("Expected HTTPException")


def test_push_subscribe_persists_sanitized_values(monkeypatch):
    monkeypatch.setattr(settings, "vapid_public_key", "public-key")
    db = DummyPushDb(execute_results=[DummyExecuteResult(), DummyExecuteResult(scalar_value=4)])
    payload = push_routes.PushSubscriptionRequest(
        endpoint="https://example.com/sub",
        keys={"p256dh": "key-a", "auth": "key-b"},
        timezone="X" * 150,
        preferred_qotd_hour=99,
    )

    response = push_routes.push_subscribe(payload, _request("10.0.0.5"), db)

    assert response == {"status": "subscribed", "total_subscribers": 4}
    assert db.commits == 1
    _, params = db.executed[0]
    assert params["tz"] == "UTC"
    assert params["qotd_hour"] == 23
    assert params["ip"] == "10.0.0.5"


def test_push_preferences_returns_not_found_when_subscription_missing():
    db = DummyPushDb(execute_results=[DummyExecuteResult(rowcount=0)])
    payload = push_routes.PushPreferencesRequest(endpoint="missing-endpoint")

    try:
        push_routes.update_push_preferences(payload, _request(), db)
    except HTTPException as exc:
        assert exc.status_code == 404
        assert exc.detail == "Subscription not found"
    else:
        raise AssertionError("Expected HTTPException")


def test_admin_auth_rejects_disallowed_ip(monkeypatch):
    monkeypatch.setattr(settings, "admin_enabled", True)
    monkeypatch.setattr(settings, "admin_ip_allowlist", "10.0.0.0/24")
    monkeypatch.setattr(settings, "admin_user", "admin")
    monkeypatch.setattr(settings, "admin_password", "secret")

    try:
        admin_auth(HTTPBasicCredentials(username="admin", password="secret"), _request("127.0.0.1"))
    except HTTPException as exc:
        assert exc.status_code == 403
        assert exc.detail == "Forbidden"
    else:
        raise AssertionError("Expected HTTPException")


def test_admin_auth_rejects_bad_credentials(monkeypatch):
    monkeypatch.setattr(settings, "admin_enabled", True)
    monkeypatch.setattr(settings, "admin_ip_allowlist", "")
    monkeypatch.setattr(settings, "admin_user", "admin")
    monkeypatch.setattr(settings, "admin_password", "secret")

    try:
        admin_auth(HTTPBasicCredentials(username="admin", password="wrong"), _request())
    except HTTPException as exc:
        assert exc.status_code == 401
        assert exc.detail == "Unauthorized"
    else:
        raise AssertionError("Expected HTTPException")
