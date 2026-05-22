"""Runtime config for the local Studio app server."""

from __future__ import annotations

import json
from pathlib import Path


STUDIO_VIEWS: dict[str, dict[str, str]] = {
    "docs": {
        "label": "docs",
        "title": "Docs",
        "path": "/docs/?mode=manage",
        "doc_href": "/docs/?scope=studio&doc=docs-viewer&mode=manage",
        "script": "/assets/docs-viewer/js/docs-viewer.js",
    },
    "tag_groups": {
        "label": "tag groups",
        "title": "Tag Groups",
        "path": "/studio/analytics/tag-groups/",
        "doc_href": "/docs/?scope=studio&doc=tag-groups&mode=manage",
        "script": "/assets/studio/js/tag-groups.js",
    },
}

STUDIO_MEDIA: dict[str, object] = {
    "thumbs": {
        "base": "",
        "works": "/assets/works/img",
        "work_details": "/assets/work_details/img",
        "moments": "/assets/moments/img",
    },
    "media": {
        "base": "https://media.dotlineform.com",
        "works_images": "/works/img",
        "works_files": "/works/files",
        "work_details_images": "/work_details/img",
        "moments_images": "/moments/img",
    },
}

STUDIO_SERVICE_ENDPOINTS: dict[str, object] = {
    "analytics": {
        "base": "/studio/api/analytics",
        "health": "/studio/api/analytics/health",
        "tag_aliases": "/studio/api/analytics/tag-aliases",
        "tag_assignments": "/studio/api/analytics/tag-assignments",
        "tag_groups": "/studio/api/analytics/tag-groups",
        "tag_registry": "/studio/api/analytics/tag-registry",
    },
    "docs": {
        "base": "/studio/api/docs",
        "capabilities": "/studio/api/docs/capabilities",
    },
}

STUDIO_STATE_CONFIG: dict[str, object] = {
    "initial_state_source": "url-query",
    "return_context_storage_key": "dlf.studio.returnContext",
    "modal_event": "studio:open-modal",
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
    pipeline_path = repo_root / "_data" / "pipeline.json"
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Could not read Studio config: {config_path}") from error
    if not isinstance(payload, dict):
        raise RuntimeError(f"Studio config must be a JSON object: {config_path}")
    try:
        pipeline_payload = json.loads(pipeline_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        pipeline_payload = {}
    pipeline_variants = pipeline_payload.get("variants") if isinstance(pipeline_payload, dict) else {}
    if not isinstance(pipeline_variants, dict):
        pipeline_variants = {}

    payload.setdefault("app", {})
    app_config = payload["app"]
    if not isinstance(app_config, dict):
        app_config = {}
        payload["app"] = app_config
    paths_config = payload.get("paths") if isinstance(payload.get("paths"), dict) else {}
    data_paths = paths_config.get("data") if isinstance(paths_config, dict) and isinstance(paths_config.get("data"), dict) else {}
    app_config["runtime"] = {
        "host": "local-studio-app",
        "asset_version": version,
        "routes": {
            "health": "/health",
            "runtime_config": "/studio/runtime-config.json",
        },
        "services": STUDIO_SERVICE_ENDPOINTS,
        "data_paths": data_paths,
        "media": STUDIO_MEDIA,
        "pipeline": {
            "variants": pipeline_variants,
        },
        "state": STUDIO_STATE_CONFIG,
        "views": [
            {"id": view_id, **view}
            for view_id, view in STUDIO_VIEWS.items()
        ],
        "navigation": {
            "primary": list(STUDIO_VIEWS.keys()),
        },
        "modals": {
            "event": STUDIO_STATE_CONFIG["modal_event"],
            "registered": [],
        },
    }
    return payload
