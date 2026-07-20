"""Runtime config for the local Analytics app server."""

from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import urlsplit


ANALYTICS_ROUTE_REQUIRED_FIELDS: tuple[str, ...] = (
    "label",
    "title",
    "path",
    "template",
    "script",
    "shell_type",
    "nav",
)

ANALYTICS_ROUTE_COPY_FIELDS: tuple[str, ...] = (
    "label",
    "title",
    "path",
    "template",
    "script",
    "shell_type",
    "nav",
)

ANALYTICS_ROUTE_REGISTRY_PATH = ("app", "routes")
ANALYTICS_HTML_TEMPLATE_SHELL_TYPE = "html-template"

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
}

ANALYTICS_MODAL_EVENT = "analytics:open-modal"
PRODUCTION_SITE_BASE = "https://dotlineform.com"


def load_analytics_config(repo_root: Path) -> dict[str, object]:
    config_path = repo_root / "analytics-app" / "app" / "frontend" / "config" / "analytics-config.json"
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Could not read Analytics config: {config_path}") from error
    if not isinstance(payload, dict):
        raise RuntimeError(f"Analytics config must be a JSON object: {config_path}")
    validate_analytics_route_registry(repo_root, payload)
    return payload


def analytics_route_registry(repo_root: Path, payload: dict[str, object] | None = None) -> dict[str, dict[str, object]]:
    source = payload if payload is not None else load_analytics_config(repo_root)
    raw_routes: object = source
    for key in ANALYTICS_ROUTE_REGISTRY_PATH:
        raw_routes = raw_routes.get(key) if isinstance(raw_routes, dict) else None
    if not isinstance(raw_routes, dict):
        raise RuntimeError("Analytics config app.routes must be a JSON object")

    return {
        route_id: {field: route[field] for field in ANALYTICS_ROUTE_COPY_FIELDS if field in route}
        for route_id, route in raw_routes.items()
        if isinstance(route_id, str) and isinstance(route, dict)
    }


def validate_analytics_route_registry(repo_root: Path, payload: dict[str, object]) -> None:
    raw_routes: object = payload
    for key in ANALYTICS_ROUTE_REGISTRY_PATH:
        raw_routes = raw_routes.get(key) if isinstance(raw_routes, dict) else None
    if not isinstance(raw_routes, dict):
        raise RuntimeError("Analytics config app.routes must be a JSON object")

    errors: list[str] = []
    seen_paths: dict[str, str] = {}

    for route_id, route in raw_routes.items():
        if not isinstance(route_id, str) or not route_id.strip():
            errors.append("route ids must be non-empty strings")
            continue
        if not isinstance(route, dict):
            errors.append(f"{route_id}: route must be a JSON object")
            continue

        for field in ANALYTICS_ROUTE_REQUIRED_FIELDS:
            if field not in route:
                errors.append(f"{route_id}: missing required field {field}")

        path = route.get("path")
        normalized_path = normalize_route_path(str(path)) if isinstance(path, str) and path.strip() else ""
        if not normalized_path:
            errors.append(f"{route_id}: missing path")
        elif normalized_path in seen_paths:
            errors.append(f"{route_id}: duplicate path with {seen_paths[normalized_path]}: {path}")
        else:
            seen_paths[normalized_path] = route_id

        template = route.get("template")
        if not isinstance(template, str) or not template.strip():
            errors.append(f"{route_id}: missing template")
        elif not resolve_analytics_static_path(repo_root, template.strip()).exists():
            errors.append(f"{route_id}: template does not exist: {template}")

        script = route.get("script")
        if not isinstance(script, str):
            errors.append(f"{route_id}: script must be a string")
        elif script.strip() and not resolve_analytics_static_path(repo_root, script.strip()).exists():
            errors.append(f"{route_id}: script does not exist: {script}")

        shell_type = route.get("shell_type")
        if shell_type != ANALYTICS_HTML_TEMPLATE_SHELL_TYPE:
            errors.append(f"{route_id}: shell_type must be {ANALYTICS_HTML_TEMPLATE_SHELL_TYPE}")

        if not isinstance(route.get("nav"), bool):
            errors.append(f"{route_id}: nav must be boolean")

    paths_routes = payload.get("paths") if isinstance(payload.get("paths"), dict) else {}
    paths_routes = paths_routes.get("routes") if isinstance(paths_routes.get("routes"), dict) else {}
    if isinstance(paths_routes, dict):
        duplicate_keys = sorted(set(raw_routes) & set(paths_routes))
        for key in duplicate_keys:
            errors.append(f"{key}: Analytics route metadata must live in app.routes, not paths.routes")

    if errors:
        raise RuntimeError("Invalid Analytics route registry: " + "; ".join(errors))


def normalize_route_path(path: str) -> str:
    parsed = urlsplit(path)
    normalized = parsed.path.strip() or "/"
    if normalized != "/" and not normalized.endswith("/"):
        normalized = f"{normalized}/"
    return normalized


def resolve_analytics_static_path(repo_root: Path, request_path: str) -> Path:
    if request_path.startswith("/analytics/app/"):
        relative = f"analytics-app/app/{request_path.removeprefix('/analytics/app/')}"
    elif request_path.startswith("/analytics/data/"):
        relative = f"analytics-app/data/{request_path.removeprefix('/analytics/data/')}"
    else:
        relative = request_path.lstrip("/")
    return repo_root / relative


def analytics_views(repo_root: Path, payload: dict[str, object] | None = None) -> dict[str, dict[str, object]]:
    return analytics_route_registry(repo_root, payload)


def analytics_shell_route_paths(repo_root: Path, payload: dict[str, object] | None = None) -> dict[str, str]:
    return {
        normalize_route_path(str(route["path"])): route_id
        for route_id, route in analytics_route_registry(repo_root, payload).items()
        if route.get("shell_type") == ANALYTICS_HTML_TEMPLATE_SHELL_TYPE and isinstance(route.get("path"), str)
    }


def analytics_service_endpoints(_repo_root: Path) -> dict[str, object]:
    return {service: dict(values) for service, values in ANALYTICS_SERVICE_ENDPOINTS.items()}


def asset_version(repo_root: Path) -> str:
    candidates = [
        repo_root / "analytics-app" / "app" / "frontend" / "analytics-shell.html",
        repo_root / "analytics-app" / "app" / "frontend" / "js" / "analytics-app.js",
        repo_root / "analytics-app" / "app" / "frontend" / "js" / "analytics-route-registry.js",
        repo_root / "analytics-app" / "app" / "frontend" / "js" / "analytics-route-templates.js",
        repo_root / "analytics-app" / "app" / "frontend" / "js" / "analytics-theme.js",
        repo_root / "analytics-app" / "app" / "frontend" / "js" / "analytics-navigation.js",
        repo_root / "analytics-app" / "app" / "frontend" / "js" / "tag-groups.js",
        repo_root / "analytics-app" / "app" / "frontend" / "js" / "tag-registry.js",
        repo_root / "analytics-app" / "app" / "frontend" / "js" / "tag-aliases.js",
        repo_root / "analytics-app" / "app" / "frontend" / "js" / "series-tags.js",
        repo_root / "analytics-app" / "app" / "frontend" / "js" / "series-tag-editor-page.js",
        repo_root / "analytics-app" / "app" / "frontend" / "js" / "catalogue-public-links.js",
        repo_root / "analytics-app" / "app" / "frontend" / "js" / "analytics-tag-editor.js",
        repo_root / "analytics-app" / "app" / "frontend" / "js" / "analytics-ui-text.js",
        repo_root / "analytics-app" / "app" / "assets" / "css" / "analytics.css",
        repo_root / "analytics-app" / "app" / "frontend" / "config" / "analytics-config.json",
        repo_root / "shared" / "frontend" / "js" / "selectable-list.js",
        repo_root / "shared" / "frontend" / "css" / "selectable-list.css",
    ]
    routes_dir = repo_root / "analytics-app" / "app" / "frontend" / "routes"
    if routes_dir.exists():
        candidates.extend(sorted(routes_dir.glob("*.html")))
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
        "series_tag_editor": series_tag_editor_runtime_settings(repo_root, payload, pipeline_payload),
        "views": [
            {"id": view_id, **view}
            for view_id, view in analytics_views(repo_root, payload).items()
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
    public_site_host = os.environ.get("SITE_HOST", "127.0.0.1").strip() or "127.0.0.1"
    public_site_port = os.environ.get("SITE_PORT", "4000").strip() or "4000"
    public_preview_base = os.environ.get("SITE_PREVIEW_BASE", "").strip()
    if not public_preview_base:
        public_preview_base = f"http://{public_site_host}:{public_site_port}"
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


def series_tag_editor_runtime_settings(
    _repo_root: Path,
    payload: dict[str, object],
    pipeline_payload: dict[str, object],
) -> dict[str, object]:
    variants = pipeline_payload.get("variants") if isinstance(pipeline_payload.get("variants"), dict) else {}
    primary_variants = variants.get("primary") if isinstance(variants.get("primary"), dict) else {}
    compatibility_variants = variants.get("compatibility") if isinstance(variants.get("compatibility"), dict) else {}
    encoding = pipeline_payload.get("encoding") if isinstance(pipeline_payload.get("encoding"), dict) else {}
    render_widths = compatibility_variants.get("render_widths") or primary_variants.get("widths") or [800, 1200, 1600]
    if not isinstance(render_widths, list):
        render_widths = [800, 1200, 1600]
    render_widths = [
        int(value)
        for value in render_widths
        if isinstance(value, int) or (isinstance(value, float) and value > 0 and value.is_integer())
    ] or [800, 1200, 1600]
    display_width = render_widths[-1]
    preferred_width = primary_variants.get("preferred_width")
    full_width = preferred_width if isinstance(preferred_width, int) and preferred_width > 0 else display_width
    media_config = ANALYTICS_MEDIA.get("media") if isinstance(ANALYTICS_MEDIA.get("media"), dict) else {}
    media_base = str(media_config.get("base") or "")
    media_works = str(media_config.get("works_images") or "/works/img")
    data_paths = payload.get("paths") if isinstance(payload.get("paths"), dict) else {}
    data_paths = data_paths.get("data") if isinstance(data_paths.get("data"), dict) else {}
    site_paths = data_paths.get("site") if isinstance(data_paths.get("site"), dict) else {}

    return {
        "baseurl": "",
        "media_image_works_base": f"{media_base}{media_works}/",
        "primary_render_widths": render_widths,
        "primary_display_width": display_width,
        "primary_full_width": full_width,
        "primary_suffix": str(primary_variants.get("suffix") or "primary"),
        "asset_format": str(encoding.get("format") or "webp"),
        "series_index_url": str(site_paths.get("series_index") or "/assets/data/series_index.json"),
        "analytics_tag_editor_module_url": "/analytics/app/frontend/js/analytics-tag-editor.js",
    }
