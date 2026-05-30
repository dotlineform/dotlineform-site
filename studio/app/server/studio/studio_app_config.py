"""Runtime config for the local Studio app server."""

from __future__ import annotations

import json
import os
from pathlib import Path

STUDIO_VIEWS: dict[str, dict[str, str]] = {
    "docs": {
        "label": "docs",
        "title": "Docs",
        "path": "/docs/?mode=manage",
    },
    "studio_audits": {
        "label": "audits",
        "title": "Studio Audits",
        "path": "/studio/audits/?mode=manage",
        "script": "/studio/app/frontend/js/studio-audits.js",
    },
    "project_state": {
        "label": "project state",
        "title": "Project State",
        "path": "/studio/project-state/?mode=manage",
        "script": "/studio/app/frontend/js/project-state.js",
    },
    "bulk_add_work": {
        "label": "bulk add",
        "title": "Bulk Add Work",
        "path": "/studio/bulk-add-work/?mode=manage",
        "script": "/studio/app/frontend/js/bulk-add-work.js",
    },
    "activity": {
        "label": "activity",
        "title": "Studio Activity",
        "path": "/studio/activity/?mode=manage",
        "script": "/studio/app/frontend/js/activity-log.js",
    },
    "catalogue_field_registry": {
        "label": "field registry",
        "title": "Catalogue Field Registry",
        "path": "/studio/catalogue-field-registry/?mode=manage",
        "script": "/studio/app/frontend/js/catalogue-field-registry-review.js",
    },
    "catalogue_status": {
        "label": "drafts",
        "title": "Catalogue Drafts",
        "path": "/studio/catalogue-status/?mode=manage",
        "script": "/studio/app/frontend/js/catalogue-status.js",
    },
    "studio_works": {
        "label": "works",
        "title": "Studio Works",
        "path": "/studio/studio-works/?mode=manage",
        "script": "/studio/app/frontend/js/studio-works.js",
    },
    "catalogue_series_editor": {
        "label": "series editor",
        "title": "Catalogue Series Editor",
        "path": "/studio/catalogue-series/?mode=manage",
        "script": "/studio/app/frontend/js/catalogue-series-editor.js",
    },
    "catalogue_work_editor": {
        "label": "work editor",
        "title": "Catalogue Work Editor",
        "path": "/studio/catalogue-work/?mode=manage",
        "script": "/studio/app/frontend/js/catalogue-work-editor.js",
    },
    "catalogue_work_detail_editor": {
        "label": "detail editor",
        "title": "Catalogue Work Detail Editor",
        "path": "/studio/catalogue-work-detail/?mode=manage",
        "script": "/studio/app/frontend/js/catalogue-work-detail-editor.js",
    },
    "catalogue_moment_editor": {
        "label": "moment editor",
        "title": "Catalogue Moment Editor",
        "path": "/studio/catalogue-moment/?mode=manage",
        "script": "/studio/app/frontend/js/catalogue-moment-editor.js",
    },
}

STUDIO_TOP_NAV_VIEW_IDS: tuple[str, ...] = (
    "docs",
)

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
    "audits": {
        "base": "/studio/api/audits",
        "health": "/studio/api/audits/health",
        "audits": "/studio/api/audits/audits",
        "run": "/studio/api/audits/audits/run",
    },
    "catalogue": {
        "base": "/studio/api/catalogue",
        "health": "/studio/api/catalogue/health",
        "read": "/studio/api/catalogue/read",
        "bulk_save": "/studio/api/catalogue/bulk-save",
        "delete_preview": "/studio/api/catalogue/delete-preview",
        "delete_apply": "/studio/api/catalogue/delete-apply",
        "publication_preview": "/studio/api/catalogue/publication-preview",
        "publication_apply": "/studio/api/catalogue/publication-apply",
        "create_work": "/studio/api/catalogue/work/create",
        "save_work": "/studio/api/catalogue/work/save",
        "create_work_detail": "/studio/api/catalogue/work-detail/create",
        "save_work_detail": "/studio/api/catalogue/work-detail/save",
        "import_preview": "/studio/api/catalogue/import-preview",
        "import_apply": "/studio/api/catalogue/import-apply",
        "create_series": "/studio/api/catalogue/series/create",
        "save_series": "/studio/api/catalogue/series/save",
        "build_preview": "/studio/api/catalogue/build-preview",
        "build_apply": "/studio/api/catalogue/build-apply",
        "prose_import_preview": "/studio/api/catalogue/prose/import-preview",
        "prose_import_apply": "/studio/api/catalogue/prose/import-apply",
        "moment_import_preview": "/studio/api/catalogue/moment/import-preview",
        "moment_import_apply": "/studio/api/catalogue/moment/import-apply",
        "moment_preview": "/studio/api/catalogue/moment/preview",
        "save_moment": "/studio/api/catalogue/moment/save",
        "project_state_report": "/studio/api/catalogue/project-state-report",
        "project_state_open_report": "/studio/api/catalogue/project-state-open-report",
    },
}

STUDIO_MODAL_EVENT = "studio:open-modal"

PRODUCTION_SITE_BASE = "https://dotlineform.com"


def load_studio_config(repo_root: Path) -> dict[str, object]:
    config_path = repo_root / "studio" / "app" / "frontend" / "config" / "studio-config.json"
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Could not read Studio config: {config_path}") from error
    if not isinstance(payload, dict):
        raise RuntimeError(f"Studio config must be a JSON object: {config_path}")
    return payload


def studio_views(_repo_root: Path) -> dict[str, dict[str, str]]:
    return {view_id: dict(view) for view_id, view in STUDIO_VIEWS.items()}


def studio_service_endpoints(_repo_root: Path) -> dict[str, object]:
    endpoints = {service: dict(values) for service, values in STUDIO_SERVICE_ENDPOINTS.items()}
    return endpoints


def asset_version(repo_root: Path) -> str:
    candidates = [
        repo_root / "studio" / "app" / "frontend" / "js" / "studio-theme.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "studio-navigation.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "studio-audits.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "project-state.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "bulk-add-work.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "activity-log.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "activity-log-modals.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "catalogue-field-registry-review.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "studio-works.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "catalogue-series-editor.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "catalogue-work-editor.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "catalogue-work-detail-editor.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "catalogue-moment-editor.js",
        repo_root / "studio" / "app" / "assets" / "css" / "studio.css",
        repo_root / "studio" / "app" / "frontend" / "config" / "studio-config.json",
    ]
    mtimes = [path.stat().st_mtime for path in candidates if path.exists()]
    return str(int(max(mtimes))) if mtimes else "1"


def runtime_config(repo_root: Path, version: str) -> dict[str, object]:
    pipeline_path = repo_root / "_data" / "pipeline.json"
    payload = load_studio_config(repo_root)
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
        "services": studio_service_endpoints(repo_root),
        "sites": runtime_site_bases(),
        "data_paths": data_paths,
        "media": STUDIO_MEDIA,
        "pipeline": {
            "variants": pipeline_variants,
        },
        "views": [
            {"id": view_id, **view}
            for view_id, view in studio_views(repo_root).items()
        ],
        "navigation": {
            "primary": list(STUDIO_TOP_NAV_VIEW_IDS),
        },
        "modals": {
            "event": STUDIO_MODAL_EVENT,
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
