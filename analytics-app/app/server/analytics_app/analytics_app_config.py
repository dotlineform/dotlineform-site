"""Runtime config for the local Analytics app server."""

from __future__ import annotations

import json
import os
from pathlib import Path

try:
    from analytics_data_sharing_api import service_endpoints as data_sharing_service_endpoints
except ModuleNotFoundError:  # pragma: no cover - supports package-style imports in tests/tools.
    from .analytics_data_sharing_api import service_endpoints as data_sharing_service_endpoints


ANALYTICS_VIEWS: dict[str, dict[str, str]] = {
    "tag_groups": {
        "label": "tag groups",
        "title": "Tag Groups",
        "path": "/analytics/tag-groups/",
        "script": "/analytics/app/frontend/js/tag-groups.js",
    },
    "tag_registry": {
        "label": "registry",
        "title": "Tag Registry",
        "path": "/analytics/tag-registry/",
        "script": "/analytics/app/frontend/js/tag-registry.js",
    },
    "tag_aliases": {
        "label": "aliases",
        "title": "Tag Aliases",
        "path": "/analytics/tag-aliases/",
        "script": "/analytics/app/frontend/js/tag-aliases.js",
    },
    "series_tags": {
        "label": "series tags",
        "title": "Series Tags",
        "path": "/analytics/series-tags/",
        "script": "/analytics/app/frontend/js/series-tags.js",
    },
    "series_tag_editor": {
        "label": "tag editor",
        "title": "Series Tag Editor",
        "path": "/analytics/series-tag-editor/",
        "script": "/analytics/app/frontend/js/series-tag-editor-page.js",
        "nav": "false",
    },
    "data_sharing_prepare": {
        "label": "prepare share",
        "title": "Prepare Share Package",
        "path": "/analytics/data-sharing/prepare/?mode=manage",
        "script": "/analytics/app/frontend/js/data-sharing-prepare.js",
    },
    "data_sharing_review": {
        "label": "review share",
        "title": "Review Returned Package",
        "path": "/analytics/data-sharing/review/?mode=manage",
        "script": "/analytics/app/frontend/js/data-sharing-review.js",
    },
}

ANALYTICS_TOP_NAV_VIEW_IDS: tuple[str, ...] = ()

ANALYTICS_MEDIA: dict[str, object] = {
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

ANALYTICS_SERVICE_ENDPOINTS: dict[str, object] = {
    "analytics": {
        "base": "/analytics/api",
        "health": "/analytics/api/health",
        "delete_tag_alias": "/analytics/api/delete-tag-alias",
        "demote_tag": "/analytics/api/demote-tag",
        "demote_tag_preview": "/analytics/api/demote-tag-preview",
        "import_tag_assignments": "/analytics/api/import-tag-assignments",
        "import_tag_assignments_preview": "/analytics/api/import-tag-assignments-preview",
        "import_tag_aliases": "/analytics/api/import-tag-aliases",
        "import_tag_registry": "/analytics/api/import-tag-registry",
        "mutate_tag_alias": "/analytics/api/mutate-tag-alias",
        "mutate_tag_alias_preview": "/analytics/api/mutate-tag-alias-preview",
        "mutate_tag": "/analytics/api/mutate-tag",
        "mutate_tag_preview": "/analytics/api/mutate-tag-preview",
        "promote_tag_alias": "/analytics/api/promote-tag-alias",
        "promote_tag_alias_preview": "/analytics/api/promote-tag-alias-preview",
        "tag_aliases": "/analytics/api/tag-aliases",
        "tag_assignments": "/analytics/api/tag-assignments",
        "tag_groups": "/analytics/api/tag-groups",
        "tag_registry": "/analytics/api/tag-registry",
        "save_tags": "/analytics/api/save-tags",
    },
    "data_sharing": {},
}

ANALYTICS_MODAL_EVENT = "studio:open-modal"
PRODUCTION_SITE_BASE = "https://dotlineform.com"


def load_analytics_config(repo_root: Path) -> dict[str, object]:
    config_path = repo_root / "analytics-app" / "app" / "frontend" / "config" / "analytics-config.json"
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Could not read Analytics config: {config_path}") from error
    if not isinstance(payload, dict):
        raise RuntimeError(f"Analytics config must be a JSON object: {config_path}")
    return payload


def analytics_views(_repo_root: Path) -> dict[str, dict[str, str]]:
    return {view_id: dict(view) for view_id, view in ANALYTICS_VIEWS.items()}


def analytics_service_endpoints(_repo_root: Path) -> dict[str, object]:
    endpoints = {service: dict(values) for service, values in ANALYTICS_SERVICE_ENDPOINTS.items()}
    endpoints["data_sharing"] = data_sharing_service_endpoints()
    return endpoints


def asset_version(repo_root: Path) -> str:
    candidates = [
        repo_root / "analytics-app" / "app" / "frontend" / "js" / "studio-theme.js",
        repo_root / "analytics-app" / "app" / "frontend" / "js" / "studio-navigation.js",
        repo_root / "analytics-app" / "app" / "frontend" / "js" / "tag-groups.js",
        repo_root / "analytics-app" / "app" / "frontend" / "js" / "tag-registry.js",
        repo_root / "analytics-app" / "app" / "frontend" / "js" / "tag-aliases.js",
        repo_root / "analytics-app" / "app" / "frontend" / "js" / "series-tags.js",
        repo_root / "analytics-app" / "app" / "frontend" / "js" / "series-tag-editor-page.js",
        repo_root / "analytics-app" / "app" / "frontend" / "js" / "data-sharing-prepare.js",
        repo_root / "analytics-app" / "app" / "frontend" / "js" / "data-sharing-review.js",
        repo_root / "analytics-app" / "app" / "frontend" / "js" / "catalogue-public-links.js",
        repo_root / "analytics-app" / "app" / "frontend" / "js" / "tag-studio.js",
        repo_root / "analytics-app" / "app" / "assets" / "css" / "analytics.css",
        repo_root / "analytics-app" / "app" / "frontend" / "config" / "analytics-config.json",
    ]
    mtimes = [path.stat().st_mtime for path in candidates if path.exists()]
    return str(int(max(mtimes))) if mtimes else "1"


def runtime_config(repo_root: Path, version: str) -> dict[str, object]:
    pipeline_path = repo_root / "_data" / "pipeline.json"
    payload = load_analytics_config(repo_root)
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
        "host": "local-analytics-app",
        "asset_version": version,
        "routes": {
            "health": "/health",
            "runtime_config": "/analytics/runtime-config.json",
        },
        "services": analytics_service_endpoints(repo_root),
        "sites": runtime_site_bases(),
        "data_paths": data_paths,
        "media": ANALYTICS_MEDIA,
        "pipeline": {
            "variants": pipeline_variants,
        },
        "views": [
            {"id": view_id, **view}
            for view_id, view in analytics_views(repo_root).items()
        ],
        "navigation": {
            "primary": list(ANALYTICS_TOP_NAV_VIEW_IDS),
        },
        "modals": {
            "event": ANALYTICS_MODAL_EVENT,
            "registered": [],
        },
    }
    return payload


def runtime_site_bases() -> dict[str, object]:
    jekyll_host = os.environ.get("JEKYLL_HOST", "127.0.0.1").strip() or "127.0.0.1"
    jekyll_port = os.environ.get("JEKYLL_PORT", "4000").strip() or "4000"
    public_preview_base = os.environ.get("PUBLIC_SITE_PREVIEW_BASE", "").strip()
    if not public_preview_base:
        public_preview_base = f"http://{jekyll_host}:{jekyll_port}"
    production_base = os.environ.get("PRODUCTION_SITE_BASE", PRODUCTION_SITE_BASE).strip() or PRODUCTION_SITE_BASE

    return {
        "public_preview": {
            "base": normalize_base_url(public_preview_base),
        },
        "production": {
            "base": normalize_base_url(production_base),
        },
    }


def normalize_base_url(value: str) -> str:
    normalized = value.strip().rstrip("/")
    return normalized or "/"
