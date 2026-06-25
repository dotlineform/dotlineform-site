#!/usr/bin/env python3
"""Public route lifecycle helpers for Docs Viewer scope management."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from docs_lifecycle_paths import load_json_object, path_record, render_json, write_text_atomic
from docs_scope_config import DocsScopeConfig, default_repo_root


SAFE_ROUTE_PART_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
PUBLIC_ROUTE_TEMPLATE_REL_PATH = Path("docs-viewer/templates/public-route/index.html")
ROUTE_CONFIG_REL_PATH = Path("docs-viewer/config/routes/docs-viewer-routes.json")
DOCS_MANAGEMENT_ROUTE_PATH = "/docs/"
PUBLIC_ROUTE_CONFIG_REL_PATHS = (
    Path("site/docs-viewer/config/routes/docs-viewer-public-routes.json"),
)


def normalize_route_path(value: Any) -> str:
    route = str(value or "").strip()
    if not route:
        raise ValueError("public_route_path is required for public read-only scopes")
    if not route.startswith("/"):
        route = f"/{route}"
    if not route.endswith("/"):
        route = f"{route}/"
    route_parts = [part for part in route.strip("/").split("/") if part]
    if not route_parts:
        raise ValueError("public_route_path must include a route segment")
    if any(part in {".", ".."} or not SAFE_ROUTE_PART_PATTERN.match(part) for part in route_parts):
        raise ValueError("public_route_path must use lowercase route segments with hyphens")
    return "/" + "/".join(route_parts) + "/"


def route_file_for_config(repo_root: Path, config: DocsScopeConfig) -> Path:
    route_base = config.viewer_base_url.strip("/")
    if config.scope_type == "public" or (not config.include_scope_param and route_base and config.viewer_base_url != "/docs/"):
        return repo_root / "site" / route_base / "index.html"
    route_rel = Path(route_base) / "index.md" if route_base else Path("index.md")
    return repo_root / route_rel


def route_is_readonly(route_path: Path) -> bool:
    if not route_path.exists() or not route_path.is_file():
        return False
    try:
        text = route_path.read_text(encoding="utf-8")
    except OSError:
        return False
    return "docs_viewer_readonly_route.html" in text or 'data-route-config-url="/docs-viewer/config/routes/docs-viewer-public-routes.json"' in text


def route_file_for_public_path(repo_root: Path, public_route_path: str) -> Path:
    route_rel = Path(public_route_path.strip("/")) / "index.html"
    return repo_root / "site" / route_rel


def readonly_route_text(title: str, scope_id: str, public_route_path: str) -> str:
    del title, scope_id, public_route_path
    return (default_repo_root() / PUBLIC_ROUTE_TEMPLATE_REL_PATH).read_text(encoding="utf-8")


def public_route_body_class(scope_id: str, public_route_path: str) -> str:
    route_section = public_route_path.strip("/").split("/", 1)[0] or scope_id
    return route_section


def public_route_record(
    scope_id: str,
    public_route_path: str,
    *,
    title: str,
) -> dict[str, Any]:
    search_label = f"search {title.lower()}"
    return {
        "schema_version": "docs_viewer_route_config_v1",
        "route_id": scope_id,
        "route_path": public_route_path,
        "default_scope_id": scope_id,
        "include_scope_param": False,
        "allow_scope_query": False,
        "viewer_base_url": public_route_path,
        "generated_base_url": "",
        "access": {
            "allow_scope_query": False,
            "management_base_url": "",
        },
        "docs_paths": {
            "index_tree_url": f"/assets/data/docs/scopes/{scope_id}/index-tree.json",
            "recently_added_url": f"/assets/data/docs/scopes/{scope_id}/recently-added.json",
            "search_index_url": f"/assets/data/search/{scope_id}/index.json",
        },
        "config_urls": {
            "docs_viewer": "/docs-viewer/config/defaults/docs-viewer-public-config.json",
            "report_registry": "/assets/data/docs/public-reports.json",
        },
        "panels": {
            "index": {"enabled": True, "default_state": "normal"},
            "main": {"enabled": True, "default_view": "rendered-document"},
            "info": {"enabled": True, "default_view": "metadata-info"},
        },
        "ui": {
            "route_shell": {
                "page_title": f"{title} | dotlineform",
                "body_class": public_route_body_class(scope_id, public_route_path),
            },
            "viewer_search": {
                "enabled": True,
                "placeholder": search_label,
                "aria_label": f"Search {title}",
            },
        },
        "hosted_views": {
            "records": [],
        },
    }


def route_registry_path_records(repo_root: Path, *, action: str) -> list[dict[str, Any]]:
    return [
        path_record(repo_root, "route_config", repo_root / ROUTE_CONFIG_REL_PATH, action=action),
        *[
            path_record(repo_root, "public_route_config", repo_root / rel_path, action=action)
            for rel_path in PUBLIC_ROUTE_CONFIG_REL_PATHS
        ],
    ]


def load_route_registry(path: Path, label: str) -> dict[str, Any]:
    payload = load_json_object(path, label)
    if payload.get("schema_version") != "docs_viewer_route_config_registry_v1":
        raise ValueError(f"{label} schema_version must be docs_viewer_route_config_registry_v1")
    routes = payload.get("routes")
    if not isinstance(routes, list):
        raise ValueError(f"{label} routes must be an array")
    return payload


def write_route_registry(path: Path, payload: dict[str, Any]) -> None:
    write_text_atomic(path, render_json(payload))


def append_public_route_record(repo_root: Path, route_record: dict[str, Any]) -> None:
    route_id = str(route_record.get("route_id") or "").strip()
    for rel_path in (ROUTE_CONFIG_REL_PATH, *PUBLIC_ROUTE_CONFIG_REL_PATHS):
        path = repo_root / rel_path
        payload = load_route_registry(path, rel_path.as_posix())
        routes = payload["routes"]
        if any(isinstance(item, dict) and str(item.get("route_id") or "").strip() == route_id for item in routes):
            raise ValueError(f"route_id {route_id!r} already exists in {rel_path.as_posix()}")
        routes.append(route_record)
        write_route_registry(path, payload)


def remove_public_route_record(repo_root: Path, scope_id: str) -> None:
    for rel_path in (ROUTE_CONFIG_REL_PATH, *PUBLIC_ROUTE_CONFIG_REL_PATHS):
        path = repo_root / rel_path
        payload = load_route_registry(path, rel_path.as_posix())
        routes = payload["routes"]
        retained = [
            item
            for item in routes
            if not (
                isinstance(item, dict)
                and (
                    str(item.get("route_id") or "").strip() == scope_id
                    or str(item.get("default_scope_id") or "").strip() == scope_id
                )
            )
        ]
        if len(retained) != len(routes):
            payload["routes"] = retained
            write_route_registry(path, payload)


def manage_default_route_ids_for_scope(repo_root: Path, scope_id: str) -> list[str]:
    payload = load_route_registry(repo_root / ROUTE_CONFIG_REL_PATH, ROUTE_CONFIG_REL_PATH.as_posix())
    route_ids: list[str] = []
    for route in payload["routes"]:
        if not isinstance(route, dict):
            continue
        route_path = route.get("route_path") or route.get("viewer_base_url")
        if normalize_route_path(route_path) != DOCS_MANAGEMENT_ROUTE_PATH:
            continue
        if str(route.get("default_scope_id") or "").strip() != scope_id:
            continue
        route_id = str(route.get("route_id") or "").strip()
        route_ids.append(route_id or "(unnamed manage route)")
    return route_ids
