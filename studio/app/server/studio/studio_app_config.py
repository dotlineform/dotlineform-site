"""Runtime config for the local Studio app server."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast
from urllib.parse import urlsplit

from studio.shared.python.studio_python_paths import ensure_studio_python_paths

ensure_studio_python_paths(__file__)

from catalogue.catalogue_output_paths import catalogue_workspace_config  # noqa: E402
from catalogue.catalogue_staged_media import catalogue_staging_assets  # noqa: E402

STUDIO_ROUTE_REQUIRED_FIELDS: tuple[str, ...] = (
    "label",
    "title",
    "path",
    "template",
    "script",
    "nav",
    "shell_type",
    "ready_state_route_id",
)

STUDIO_SHELL_ROUTE_TYPES: frozenset[str] = frozenset(("html-template",))

STUDIO_ROUTE_REGISTRY_PATH = ("app", "routes")

STUDIO_ROUTE_COPY_FIELDS: tuple[str, ...] = (
    "label",
    "title",
    "path",
    "template",
    "script",
    "nav",
    "shell_type",
    "ready_state_route_id",
)

def studio_media_config(repo_root: Path) -> dict[str, object]:
    """Project independent staging/Working families into Studio's media readers."""
    assets = catalogue_workspace_config(repo_root).assets
    staging = catalogue_staging_assets(repo_root)
    return {
        "thumbs": {"base": "", "works": assets.url(assets.work_thumbnails)},
        "media": {"base": "", "works_images": assets.url(assets.work_primary), "works_files": assets.url(assets.work_files)},
        "staged": {"works_images": staging.url(staging.work_primary), "works_thumbs": staging.url(staging.work_thumbnails),
                   "works_files": staging.url(staging.work_files)},
    }


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
        if shell_type not in STUDIO_SHELL_ROUTE_TYPES:
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
            template = route.get("template")
            if not isinstance(template, str) or not template.strip():
                errors.append(f"{route_id}: shell route is missing template")
            elif not template.strip().startswith("/studio/app/frontend/routes/"):
                errors.append(f"{route_id}: shell route template must be under /studio/app/frontend/routes/: {template}")
            elif not (repo_root / template.strip().lstrip("/")).exists():
                errors.append(f"{route_id}: template does not exist: {template}")

            script = route.get("script")
            if not isinstance(script, str) or not script.strip():
                errors.append(f"{route_id}: shell route is missing script")
            elif not (repo_root / script.strip().lstrip("/")).exists():
                errors.append(f"{route_id}: script does not exist: {script}")

            if not normalized_path.startswith("/studio/"):
                errors.append(f"{route_id}: shell route path must be under /studio/: {path}")

        if not isinstance(route.get("nav"), bool):
            errors.append(f"{route_id}: nav must be boolean")

    paths_routes = payload.get("paths") if isinstance(payload.get("paths"), dict) else {}
    paths_routes = paths_routes.get("routes") if isinstance(paths_routes.get("routes"), dict) else {}
    if isinstance(paths_routes, dict):
        duplicate_keys = sorted(set(raw_routes) & set(paths_routes))
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


def studio_shell_route_paths(repo_root: Path, payload: dict[str, object] | None = None) -> frozenset[str]:
    routes = studio_route_registry(repo_root, payload)
    return frozenset(
        normalize_route_path(route["path"])
        for route in routes.values()
        if route.get("shell_type") in STUDIO_SHELL_ROUTE_TYPES
        and isinstance(route.get("path"), str)
        and str(route.get("path")).strip()
    )


def asset_version(repo_root: Path) -> str:
    candidates = [
        repo_root / "shared" / "frontend" / "js" / "search-list.js",
        repo_root / "shared" / "frontend" / "css" / "search-list.css",
        repo_root / "shared" / "frontend" / "js" / "file-picker.js",
        repo_root / "shared" / "frontend" / "css" / "file-picker.css",
        repo_root / "shared" / "frontend" / "js" / "record-list.js",
        repo_root / "shared" / "frontend" / "css" / "record-list.css",
        repo_root / "studio" / "app" / "frontend" / "studio-shell.html",
        repo_root / "studio" / "app" / "frontend" / "js" / "studio-theme.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "studio-app.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "studio-route-registry.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "studio-route-templates.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "catalogue-editor-shell-media.js",
        repo_root / "studio" / "app" / "frontend" / "routes" / "catalogue-work.html",
        repo_root / "studio" / "app" / "frontend" / "js" / "catalogue-project-media-picker.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "catalogue-work-editor.js",
        repo_root / "studio" / "app" / "assets" / "css" / "studio.css",
        repo_root / "studio" / "app" / "frontend" / "config" / "studio-config.json",
    ]
    mtimes = [path.stat().st_mtime for path in candidates if path.exists()]
    return str(int(max(mtimes))) if mtimes else "1"


def runtime_config(repo_root: Path) -> dict[str, object]:
    pipeline_path = repo_root / "_data" / "pipeline.json"
    payload = load_studio_config(repo_root)
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

    app_config = cast("dict[str, object]", payload["app"])
    app_config["runtime"] = {
        "media": studio_media_config(repo_root),
        "pipeline": {
            "variants": pipeline_variants,
            "encoding": pipeline_encoding,
        },
    }
    return payload
