"""Persistent state management for quote selector weights."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


def get_active_weights(db: Session) -> dict[str, float] | None:
    row = db.execute(
        text(
            """
            SELECT weights_json
            FROM quote_selector_weight_versions
            WHERE is_active = true
            ORDER BY version DESC, id DESC
            LIMIT 1
            """
        )
    ).fetchone()
    if not row:
        return None
    return json.loads(row[0])


def get_active_version(db: Session) -> int | None:
    row = db.execute(
        text(
            """
            SELECT version
            FROM quote_selector_weight_versions
            WHERE is_active = true
            ORDER BY version DESC, id DESC
            LIMIT 1
            """
        )
    ).fetchone()
    return int(row[0]) if row else None


def save_new_weight_version(
    db: Session,
    *,
    weights: dict[str, float],
    metrics: dict[str, Any] | None = None,
    rollback_from_version: int | None = None,
    activate: bool = True,
) -> int:
    current_version = get_active_version(db) or 0
    next_version = current_version + 1

    if activate:
        db.execute(text("UPDATE quote_selector_weight_versions SET is_active = false WHERE is_active = true"))

    db.execute(
        text(
            """
            INSERT INTO quote_selector_weight_versions
                (version, weights_json, metrics_json, is_active, rollback_from_version, created_at)
            VALUES
                (:version, :weights_json, :metrics_json, :is_active, :rollback_from_version, NOW())
            """
        ),
        {
            "version": next_version,
            "weights_json": json.dumps(weights),
            "metrics_json": json.dumps(metrics or {}),
            "is_active": activate,
            "rollback_from_version": rollback_from_version,
        },
    )
    return next_version


def rollback_to_previous_version(db: Session) -> int | None:
    current = db.execute(
        text(
            """
            SELECT version, weights_json
            FROM quote_selector_weight_versions
            WHERE is_active = true
            ORDER BY version DESC, id DESC
            LIMIT 1
            """
        )
    ).fetchone()
    previous = db.execute(
        text(
            """
            SELECT version, weights_json
            FROM quote_selector_weight_versions
            WHERE version < COALESCE((SELECT MAX(version) FROM quote_selector_weight_versions WHERE is_active = true), 999999)
            ORDER BY version DESC, id DESC
            LIMIT 1
            """
        )
    ).fetchone()

    if not current or not previous:
        return None

    db.execute(text("UPDATE quote_selector_weight_versions SET is_active = false WHERE is_active = true"))
    save_new_weight_version(
        db,
        weights=json.loads(previous[1]),
        metrics={"rollback": True, "source_version": int(previous[0]), "from_version": int(current[0])},
        rollback_from_version=int(current[0]),
        activate=True,
    )
    return int(previous[0])
