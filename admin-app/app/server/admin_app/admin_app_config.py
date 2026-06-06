"""Runtime config for the local Admin app server."""

from __future__ import annotations

import json
from pathlib import Path


ADMIN_CONFIG_PATH = Path("admin-app/app/frontend/config/admin-config.json")
ADMIN_HOME_UI_TEXT_PATH = Path("admin-app/app/frontend/config/ui-text/admin-home.json")

ADMIN_ROUTE_REQUIRED_FIELDS: tuple[str, ...] = (
    "label",
    "title",
    "path",
    "script",
    "nav",
)
ADMIN_ROUTE_COPY_FIELDS: tuple[str, ...] = ADMIN_ROUTE_REQUIRED_FIELDS
ADMIN_ROUTE_REGISTRY_PATH = ("app", "routes")
ADMIN_SERVED_ROUTE_PATHS: dict[str, str] = {
    "admin_home": "/admin/",
    "admin_audits": "/admin/audits/",
    "admin_risk": "/admin/risk/",
    "admin_activity": "/admin/activity/",
    "admin_testing": "/admin/testing/",
    "admin_ui_catalogue": "/admin/ui-catalogue/",
}

ADMIN_SERVICE_ENDPOINTS: dict[str, object] = {
    "activity": {
        "base": "/admin/api/activity",
        "health": "/admin/api/activity/health",
        "feed": "/admin/api/activity/feed",
    },
    "audits": {
        "base": "/admin/api/audits",
        "health": "/admin/api/audits/health",
        "audits": "/admin/api/audits/audits",
        "run": "/admin/api/audits/audits/run",
    },
    "risk": {
        "base": "/admin/api/risk",
        "health": "/admin/api/risk/health",
        "producers": "/admin/api/risk/producers",
        "runs": "/admin/api/risk/runs",
    },
    "testing": {
        "base": "/admin/api/testing",
        "health": "/admin/api/testing/health",
        "runs": "/admin/api/testing/runs",
    },
}


def load_admin_config(repo_root: Path) -> dict[str, object]:
    config_path = repo_root / ADMIN_CONFIG_PATH
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Could not read Admin config: {config_path}") from error
    if not isinstance(payload, dict):
        raise RuntimeError(f"Admin config must be a JSON object: {config_path}")
    validate_admin_route_registry(repo_root, payload)
    return payload


def load_admin_home_ui_text(repo_root: Path) -> dict[str, object]:
    ui_text_path = repo_root / ADMIN_HOME_UI_TEXT_PATH
    try:
        payload = json.loads(ui_text_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Could not read Admin home UI text: {ui_text_path}") from error
    if not isinstance(payload, dict):
        raise RuntimeError(f"Admin home UI text must be a JSON object: {ui_text_path}")
    return payload


def admin_route_registry(repo_root: Path, payload: dict[str, object] | None = None) -> dict[str, dict[str, object]]:
    source = payload if payload is not None else load_admin_config(repo_root)
    raw_routes: object = source
    for key in ADMIN_ROUTE_REGISTRY_PATH:
        raw_routes = raw_routes.get(key) if isinstance(raw_routes, dict) else None
    if not isinstance(raw_routes, dict):
        raise RuntimeError("Admin config app.routes must be a JSON object")

    return {
        route_id: {field: route[field] for field in ADMIN_ROUTE_COPY_FIELDS if field in route}
        for route_id, route in raw_routes.items()
        if isinstance(route_id, str) and isinstance(route, dict)
    }


def validate_admin_route_registry(repo_root: Path, payload: dict[str, object]) -> None:
    raw_routes: object = payload
    for key in ADMIN_ROUTE_REGISTRY_PATH:
        raw_routes = raw_routes.get(key) if isinstance(raw_routes, dict) else None
    if not isinstance(raw_routes, dict):
        raise RuntimeError("Admin config app.routes must be a JSON object")

    errors: list[str] = []
    seen_paths: dict[str, str] = {}

    for route_id, route in raw_routes.items():
        if not isinstance(route_id, str) or not route_id.strip():
            errors.append("route ids must be non-empty strings")
            continue
        if not isinstance(route, dict):
            errors.append(f"{route_id}: route must be a JSON object")
            continue

        for field in ADMIN_ROUTE_REQUIRED_FIELDS:
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

        script = route.get("script")
        if isinstance(script, str) and script.strip() and not resolve_admin_static_path(repo_root, script.strip()).exists():
            errors.append(f"{route_id}: script does not exist: {script}")
        elif not isinstance(script, str):
            errors.append(f"{route_id}: script must be a string")

        served_path = ADMIN_SERVED_ROUTE_PATHS.get(route_id)
        if served_path and normalize_route_path(served_path) != normalized_path:
            errors.append(f"{route_id}: path {path} does not match served route {served_path}")

        if not isinstance(route.get("nav"), bool):
            errors.append(f"{route_id}: nav must be boolean")

    for route_id in sorted(set(ADMIN_SERVED_ROUTE_PATHS) - set(raw_routes)):
        errors.append(f"{route_id}: missing Admin route metadata")

    if errors:
        raise RuntimeError("Invalid Admin route registry: " + "; ".join(errors))


def normalize_route_path(path: str) -> str:
    normalized = path.strip() or "/"
    if "?" in normalized:
        normalized = normalized.split("?", 1)[0]
    if normalized != "/" and not normalized.endswith("/"):
        normalized = f"{normalized}/"
    return normalized


def resolve_admin_static_path(repo_root: Path, request_path: str) -> Path:
    if request_path.startswith("/admin/app/"):
        relative = f"admin-app/app/{request_path.removeprefix('/admin/app/')}"
    else:
        relative = request_path.lstrip("/")
    return repo_root / relative


def admin_service_endpoints(_repo_root: Path) -> dict[str, object]:
    return {service: dict(values) for service, values in ADMIN_SERVICE_ENDPOINTS.items()}


def admin_views(repo_root: Path, payload: dict[str, object] | None = None) -> dict[str, dict[str, object]]:
    return admin_route_registry(repo_root, payload)


def asset_version(repo_root: Path) -> str:
    candidates = [
        repo_root / "admin-app" / "app" / "assets" / "css" / "admin.css",
        repo_root / "admin-app" / "app" / "frontend" / "config" / "admin-config.json",
        repo_root / "admin-app" / "app" / "frontend" / "config" / "ui-text" / "admin-home.json",
        repo_root / "admin-app" / "app" / "frontend" / "config" / "ui-text" / "admin-activity.json",
        repo_root / "admin-app" / "app" / "frontend" / "config" / "ui-text" / "admin-audits.json",
        repo_root / "admin-app" / "app" / "frontend" / "config" / "ui-text" / "admin-risk.json",
        repo_root / "admin-app" / "app" / "frontend" / "js" / "admin-activity.js",
        repo_root / "admin-app" / "app" / "frontend" / "js" / "admin-activity-context.js",
        repo_root / "admin-app" / "app" / "frontend" / "js" / "admin-activity-modals.js",
        repo_root / "admin-app" / "app" / "frontend" / "js" / "admin-audits.js",
        repo_root / "admin-app" / "app" / "frontend" / "js" / "admin-config.js",
        repo_root / "admin-app" / "app" / "frontend" / "js" / "admin-home.js",
        repo_root / "admin-app" / "app" / "frontend" / "js" / "admin-operational-route.js",
        repo_root / "admin-app" / "app" / "frontend" / "js" / "admin-risk.js",
        repo_root / "admin-app" / "app" / "frontend" / "js" / "admin-route-state.js",
        repo_root / "admin-app" / "app" / "frontend" / "js" / "admin-theme.js",
        repo_root / "admin-app" / "app" / "frontend" / "js" / "admin-testing.js",
        repo_root / "admin-app" / "app" / "frontend" / "js" / "admin-transport.js",
        repo_root / "admin-app" / "ui-catalogue" / "assets" / "css" / "ui-catalogue-demo.css",
        repo_root / "admin-app" / "ui-catalogue" / "assets" / "css" / "ui-catalogue-shell.css",
        repo_root / "admin-app" / "ui-catalogue" / "assets" / "js" / "ui-catalogue-demo.js",
        repo_root / "admin-app" / "ui-catalogue" / "assets" / "js" / "ui-catalogue-shell.js",
    ]
    mtimes = [path.stat().st_mtime for path in candidates if path.exists()]
    return str(int(max(mtimes))) if mtimes else "1"


def runtime_config(repo_root: Path, version: str) -> dict[str, object]:
    payload = load_admin_config(repo_root)
    payload.setdefault("app", {})
    app_config = payload["app"]
    if not isinstance(app_config, dict):
        raise RuntimeError("Admin config app must be a JSON object")

    app_config["runtime"] = {
        "host": "local-admin-app",
        "asset_version": version,
        "routes": {
            "home": "/admin/",
            "runtime_config": "/admin/runtime-config.json",
        },
        "services": admin_service_endpoints(repo_root),
        "views": [
            {"id": route_id, **route}
            for route_id, route in admin_views(repo_root, payload).items()
        ],
        "data_paths": {
            "ui_text": {
                "admin_activity": "/admin/app/frontend/config/ui-text/admin-activity.json",
                "admin_audits": "/admin/app/frontend/config/ui-text/admin-audits.json",
                "admin_home": "/admin/app/frontend/config/ui-text/admin-home.json",
                "admin_risk": "/admin/app/frontend/config/ui-text/admin-risk.json",
            },
            "activity": {
                "feed": "var/admin/activity/activity_log.json",
                "journal": "var/admin/activity/activity_log.jsonl",
            },
            "risk": {
                "runs": "var/admin/risk/runs",
            },
            "testing": {
                "runs": "var/admin/test-runs",
            },
        },
    }
    return payload
