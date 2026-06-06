"""Local Admin activity feed API."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from studio.shared.python.studio_activity import FEED_REL_PATH, FEED_SCHEMA


def activity_get_payload(repo_root: Path, api_path: str) -> dict[str, Any]:
    if api_path == "/health":
        return {
            "ok": True,
            "service": "admin_activity",
            "feed_path": str(FEED_REL_PATH),
        }
    if api_path == "/feed":
        return activity_feed_payload(repo_root)
    raise FileNotFoundError(f"Unknown activity API route: {api_path}")


def activity_feed_payload(repo_root: Path) -> dict[str, Any]:
    feed_path = repo_root / FEED_REL_PATH
    if not feed_path.exists():
        return empty_feed_payload()
    try:
        payload = json.loads(feed_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Admin activity feed is invalid JSON: {FEED_REL_PATH}") from error
    if not isinstance(payload, dict):
        raise RuntimeError(f"Admin activity feed must be a JSON object: {FEED_REL_PATH}")
    payload["ok"] = True
    return payload


def empty_feed_payload() -> dict[str, Any]:
    return {
        "ok": True,
        "header": {
            "schema": FEED_SCHEMA,
            "count": 0,
        },
        "entries": [],
    }
