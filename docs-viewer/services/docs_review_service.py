#!/usr/bin/env python3
"""Dispatcher for the Docs Review returned-package API."""

from __future__ import annotations

from http import HTTPStatus
from pathlib import Path
from typing import Any

import docs_review_packages as packages
import docs_review_routes as routes
from docs_document_packages.workspace import workspace_status


def _query_value(query: dict[str, list[str]], name: str) -> str:
    return str((query.get(name) or [""])[0] or "").strip()


def docs_review_get_payload(
    repo_root: Path,
    path: str,
    query: dict[str, list[str]],
) -> dict[str, Any]:
    package_id = _query_value(query, "package_id")
    if path == routes.CAPABILITIES_PATH:
        workspace = workspace_status(repo_root)
        available = workspace.get("available") is True
        return {
            "ok": True,
            "available": available,
            "workspace": workspace,
            "capabilities": {
                "review_packages_list": available,
                "review_manifest_read": available,
                "review_asset_inventory_read": available,
                "review_generated_read": available,
                "review_build": available,
                "canonical_write": False,
                "management": False,
                "publish": False,
            },
        }
    if path == routes.PACKAGES_PATH:
        return packages.list_packages(repo_root)
    if path == routes.MANIFEST_PATH:
        return packages.read_manifest(repo_root, package_id)
    if path == routes.ASSETS_PATH:
        return packages.read_asset_inventories(repo_root, package_id)
    if path == routes.INDEX_TREE_PATH:
        return packages.read_index_tree(repo_root, package_id)
    if path == routes.PAYLOAD_PATH:
        return packages.read_payload(repo_root, package_id, _query_value(query, "doc_id"))
    raise FileNotFoundError("Not found")


def docs_review_asset_path_from_route(repo_root: Path, request_path: str) -> Path:
    suffix = request_path.removeprefix(routes.ASSET_CONTENT_PREFIX)
    package_id, separator, asset_path = suffix.partition("/")
    if not separator:
        raise ValueError("review asset route requires package and asset path")
    return packages.resolve_asset_file(
        repo_root,
        package_id,
        asset_path,
    )


def docs_review_post_response(
    repo_root: Path,
    path: str,
    body: dict[str, Any],
) -> tuple[HTTPStatus, dict[str, Any]]:
    if path == routes.BUILD_PATH:
        return HTTPStatus.OK, packages.build_package(repo_root, body)
    raise FileNotFoundError("Not found")
