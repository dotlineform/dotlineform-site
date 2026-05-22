"""Analytics API adapters for the local Studio app server."""

from __future__ import annotations

import json
from pathlib import Path


DATA_DIR = Path("assets/studio/data")
READ_ENDPOINTS = {
    "/tag-aliases": {
        "path": DATA_DIR / "tag_aliases.json",
        "label": "Tag Aliases",
        "required_key": "aliases",
        "required_type": dict,
    },
    "/tag-assignments": {
        "path": DATA_DIR / "tag_assignments.json",
        "label": "Tag Assignments",
        "required_key": "series",
        "required_type": dict,
    },
    "/tag-groups": {
        "path": DATA_DIR / "tag_groups.json",
        "label": "Tag Groups",
        "required_key": "groups",
        "required_type": list,
    },
    "/tag-registry": {
        "path": DATA_DIR / "tag_registry.json",
        "label": "Tag Registry",
        "required_key": "tags",
        "required_type": list,
    },
}


def analytics_health_payload() -> dict[str, object]:
    return {
        "ok": True,
        "service": "studio_analytics",
    }


def data_payload(repo_root: Path, endpoint: str) -> dict[str, object]:
    spec = READ_ENDPOINTS.get(endpoint)
    if spec is None:
        raise FileNotFoundError("Not found")
    path = repo_root / spec["path"]
    label = str(spec["label"])
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Could not read {label} data: {path}") from error
    if not isinstance(payload, dict):
        raise RuntimeError(f"{label} data must be a JSON object: {path}")
    required_value = payload.get(str(spec["required_key"]))
    required_type = spec["required_type"]
    if not isinstance(required_value, required_type):
        raise RuntimeError(f"{label} data must include {spec['required_key']} {required_type.__name__}: {path}")

    return {
        "ok": True,
        **payload,
    }


def analytics_get_payload(repo_root: Path, path: str) -> dict[str, object]:
    if path == "/health":
        return analytics_health_payload()
    return data_payload(repo_root, path)
