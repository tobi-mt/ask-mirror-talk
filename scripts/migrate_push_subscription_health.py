#!/usr/bin/env python3
"""Install the additive push-subscription lifecycle and audit schema."""

from app.core.db import get_session_local, safe_close_session
from app.notifications.subscription_health import ensure_push_subscription_health_schema


def main() -> None:
    db = get_session_local()()
    try:
        ensure_push_subscription_health_schema(db)
        print("Push subscription health schema is ready")
    finally:
        safe_close_session(db, context="push_health_migration")


if __name__ == "__main__":
    main()
