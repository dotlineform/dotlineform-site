"""Runtime config for the local Studio app server."""

from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import urlsplit

STUDIO_ROUTE_REQUIRED_FIELDS: tuple[str, ...] = (
    "label",
    "title",
    "path",
    "doc_id",
    "nav",
    "shell_type",
    "ready_state_route_id",
)

STUDIO_SHELL_ROUTE_TYPES: frozenset[str] = frozenset(("javascript",))
STUDIO_SUPPORTED_SHELL_TYPES: frozenset[str] = STUDIO_SHELL_ROUTE_TYPES | frozenset(("external",))

STUDIO_SERVED_ROUTE_PATHS: dict[str, str] = {
    "studio_audits": "/studio/audits/",
    "project_state": "/studio/project-state/",
    "bulk_add_work": "/studio/bulk-add-work/",
    "activity": "/studio/activity/",
    "catalogue_field_registry": "/studio/catalogue-field-registry/",
    "catalogue_status": "/studio/catalogue-status/",
    "studio_works": "/studio/studio-works/",
    "catalogue_series_editor": "/studio/catalogue-series/",
    "catalogue_work_editor": "/studio/catalogue-work/",
    "catalogue_work_detail_editor": "/studio/catalogue-work-detail/",
    "catalogue_moment_editor": "/studio/catalogue-moment/",
}

STUDIO_ROUTE_PATHS_WITH_LEGACY_KEYS: dict[str, tuple[str, ...]] = {
    "catalogue_field_registry": ("catalogue_field_registry_review",),
}

STUDIO_ROUTE_REGISTRY_PATH = ("app", "routes")

STUDIO_ROUTE_COPY_FIELDS: tuple[str, ...] = (
    "label",
    "title",
    "path",
    "script",
    "doc_id",
    "nav",
    "shell_type",
    "ready_state_route_id",
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
    validate_studio_route_registry(repo_root, payload)
    return payload


def studio_route_registry(repo_root: Path, payload: dict[str, object] | None = None) -> dict[str, dict[str, object]]:
    source = payload if payload is not None else load_studio_config(repo_root)
    raw_routes = source
    for key in STUDIO_ROUTE_REGISTRY_PATH:
        raw_routes = raw_routes.get(key) if isinstance(raw_routes, dict) else None  # type: ignore[assignment]
    if not isinstance(raw_routes, dict):
        raise RuntimeError("Studio config app.routes must be a JSON object")

    return {
        route_id: {field: route[field] for field in STUDIO_ROUTE_COPY_FIELDS if field in route}
        for route_id, route in raw_routes.items()
        if isinstance(route_id, str) and isinstance(route, dict)
    }


def studio_top_nav_view_ids(repo_root: Path, payload: dict[str, object] | None = None) -> tuple[str, ...]:
    routes = studio_route_registry(repo_root, payload)
    return tuple(route_id for route_id, route in routes.items() if route.get("nav") is True)


def validate_studio_route_registry(repo_root: Path, payload: dict[str, object]) -> None:
    raw_routes = payload
    for key in STUDIO_ROUTE_REGISTRY_PATH:
        raw_routes = raw_routes.get(key) if isinstance(raw_routes, dict) else None  # type: ignore[assignment]
    if not isinstance(raw_routes, dict):
        raise RuntimeError("Studio config app.routes must be a JSON object")

    errors: list[str] = []
    seen_paths: dict[str, str] = {}

    for route_id, route in raw_routes.items():
        if not isinstance(route_id, str) or not route_id.strip():
            errors.append("route ids must be non-empty strings")
            continue
        if not isinstance(route, dict):
            errors.append(f"{route_id}: route must be a JSON object")
            continue

        for field in STUDIO_ROUTE_REQUIRED_FIELDS:
            if field not in route:
                errors.append(f"{route_id}: missing required field {field}")

        shell_type = route.get("shell_type")
        if shell_type not in STUDIO_SUPPORTED_SHELL_TYPES:
            errors.append(f"{route_id}: unsupported shell_type {shell_type!r}")

        path = route.get("path")
        normalized_path = normalize_route_path(str(path)) if isinstance(path, str) and path.strip() else ""
        if not normalized_path:
            errors.append(f"{route_id}: missing path")
        elif normalized_path in seen_paths:
            errors.append(f"{route_id}: duplicate path with {seen_paths[normalized_path]}: {path}")
        else:
            seen_paths[normalized_path] = route_id

        if shell_type in STUDIO_SHELL_ROUTE_TYPES:
            script = route.get("script")
            if not isinstance(script, str) or not script.strip():
                errors.append(f"{route_id}: shell route is missing script")
            elif not (repo_root / script.strip().lstrip("/")).exists():
                errors.append(f"{route_id}: script does not exist: {script}")

            served_path = STUDIO_SERVED_ROUTE_PATHS.get(route_id)
            if not served_path:
                errors.append(f"{route_id}: no current Studio route serves this shell route")
            elif normalize_route_path(served_path) != normalized_path:
                errors.append(f"{route_id}: path {path} does not match served route {served_path}")

        doc_id = route.get("doc_id")
        if not isinstance(doc_id, str) or not doc_id.strip():
            errors.append(f"{route_id}: missing doc_id")

        if not isinstance(route.get("nav"), bool):
            errors.append(f"{route_id}: nav must be boolean")

    paths_routes = payload.get("paths") if isinstance(payload.get("paths"), dict) else {}
    paths_routes = paths_routes.get("routes") if isinstance(paths_routes.get("routes"), dict) else {}
    if isinstance(paths_routes, dict):
        route_ids = set(raw_routes)
        legacy_route_keys = {
            legacy_key
            for legacy_keys in STUDIO_ROUTE_PATHS_WITH_LEGACY_KEYS.values()
            for legacy_key in legacy_keys
        }
        duplicate_keys = sorted((route_ids | legacy_route_keys) & set(paths_routes))
        for key in duplicate_keys:
            errors.append(f"{key}: Studio route metadata must live in app.routes, not paths.routes")

    if errors:
        raise RuntimeError("Invalid Studio route registry: " + "; ".join(errors))


def normalize_route_path(path: str) -> str:
    parsed = urlsplit(path)
    normalized = parsed.path.strip() or "/"
    if normalized != "/" and not normalized.endswith("/"):
        normalized = f"{normalized}/"
    return normalized


def studio_views(repo_root: Path, payload: dict[str, object] | None = None) -> dict[str, dict[str, object]]:
    return studio_route_registry(repo_root, payload)


def studio_service_endpoints(_repo_root: Path) -> dict[str, object]:
    endpoints = {service: dict(values) for service, values in STUDIO_SERVICE_ENDPOINTS.items()}
    return endpoints


def asset_version(repo_root: Path) -> str:
    candidates = [
        repo_root / "studio" / "app" / "frontend" / "js" / "studio-theme.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "studio-app.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "studio-navigation.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "studio-route-body-renderers.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "studio-route-registry.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "activity-log-shell.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "bulk-add-work-shell.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "catalogue-editor-shell-media.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "catalogue-field-registry-shell.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "catalogue-moment-shell.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "catalogue-series-shell.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "catalogue-status-shell.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "catalogue-work-detail-shell.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "catalogue-work-shell.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "project-state-shell.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "studio-works-shell.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "studio-audits-shell.js",
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
    views = studio_views(repo_root, payload)
    try:
        pipeline_payload = json.loads(pipeline_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        pipeline_payload = {}
    pipeline_variants = pipeline_payload.get("variants") if isinstance(pipeline_payload, dict) else {}
    if not isinstance(pipeline_variants, dict):
        pipeline_variants = {}
    pipeline_encoding = pipeline_payload.get("encoding") if isinstance(pipeline_payload, dict) else {}
    if not isinstance(pipeline_encoding, dict):
        pipeline_encoding = {}
    pipeline_paths = pipeline_payload.get("paths") if isinstance(pipeline_payload, dict) else {}
    if not isinstance(pipeline_paths, dict):
        pipeline_paths = {}
    pipeline_workbooks = pipeline_paths.get("workbooks") if isinstance(pipeline_paths.get("workbooks"), dict) else {}

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
            "encoding": pipeline_encoding,
            "workbooks": pipeline_workbooks,
        },
        "views": [
            {"id": view_id, **view}
            for view_id, view in views.items()
        ],
        "navigation": {
            "primary": list(studio_top_nav_view_ids(repo_root, payload)),
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
