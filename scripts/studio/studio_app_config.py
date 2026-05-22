"""Runtime config for the local Studio app server."""

from __future__ import annotations

import json
from pathlib import Path


STUDIO_VIEWS: dict[str, dict[str, str]] = {
    "docs": {
        "label": "docs",
        "title": "Docs",
        "path": "/docs/",
        "doc_href": "/docs/?scope=studio&doc=docs-viewer",
        "script": "/assets/docs-viewer/js/docs-viewer.js",
    },
    "tag_groups": {
        "label": "tag groups",
        "title": "Tag Groups",
        "path": "/studio/analytics/tag-groups/",
        "doc_href": "/docs/?scope=studio&doc=tag-groups",
        "script": "/assets/studio/js/tag-groups.js",
    },
}


def asset_version(repo_root: Path) -> str:
    candidates = [
        repo_root / "_includes" / "docs_viewer_shell.html",
        repo_root / "assets" / "docs-viewer" / "js" / "docs-viewer.js",
        repo_root / "assets" / "docs-viewer" / "css" / "docs-viewer.css",
        repo_root / "assets" / "docs-viewer" / "css" / "docs-viewer-management.css",
        repo_root / "assets" / "docs-viewer" / "data" / "docs-viewer-config.json",
        repo_root / "assets" / "studio" / "js" / "studio-navigation.js",
        repo_root / "assets" / "studio" / "js" / "tag-groups.js",
        repo_root / "assets" / "studio" / "css" / "studio.css",
        repo_root / "assets" / "studio" / "data" / "studio_config.json",
    ]
    mtimes = [path.stat().st_mtime for path in candidates if path.exists()]
    return str(int(max(mtimes))) if mtimes else "1"


def runtime_config(repo_root: Path, version: str) -> dict[str, object]:
    config_path = repo_root / "assets" / "studio" / "data" / "studio_config.json"
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Could not read Studio config: {config_path}") from error
    if not isinstance(payload, dict):
        raise RuntimeError(f"Studio config must be a JSON object: {config_path}")

    payload.setdefault("app", {})
    app_config = payload["app"]
    if not isinstance(app_config, dict):
        app_config = {}
        payload["app"] = app_config
    app_config["runtime"] = {
        "host": "local-studio-app",
        "asset_version": version,
        "routes": {
            "health": "/health",
            "runtime_config": "/studio/runtime-config.json",
        },
        "views": [
            {"id": view_id, **view}
            for view_id, view in STUDIO_VIEWS.items()
        ],
        "navigation": {
            "primary": list(STUDIO_VIEWS.keys()),
        },
    }
    return payload
