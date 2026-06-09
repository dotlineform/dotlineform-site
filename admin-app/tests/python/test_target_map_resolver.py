#!/usr/bin/env python3
"""Focused tests for Admin checks target-map resolution."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
ADMIN_CHECKS_DIR = REPO_ROOT / "admin-app" / "checks"
sys.path.insert(0, str(ADMIN_CHECKS_DIR))

import admin_checks_config as checks_config  # noqa: E402
import target_map_resolver as resolver  # noqa: E402


def test_path_matching_supports_prefixes_and_globs() -> None:
    assert resolver.path_matches("docs-viewer/runtime/js/", "docs-viewer/runtime/js/docs-viewer-search.js")
    assert resolver.path_matches("docs-viewer/runtime/js/docs-viewer-search*", "docs-viewer/runtime/js/docs-viewer-search.js")
    assert resolver.path_matches("**/*search*", "docs-viewer/build/build_search.py")
    assert not resolver.path_matches("docs-viewer/services/", "docs-viewer/runtime/js/docs-viewer-search.js")


def test_resolve_scope_reports_families_routes_shared_and_exclusions() -> None:
    config = checks_config.load_checks_config(repo_root=REPO_ROOT)
    source_files = [
        "docs-viewer/runtime/js/docs-viewer-search.js",
        "docs-viewer/runtime/js/docs-viewer-public.js",
        "docs-viewer/services/docs_management_routes.py",
        "docs-viewer/generated/docs/studio/index.json",
    ]

    scope = resolver.resolve_scope(config, "docs-viewer", source_files=source_files, global_source_files=source_files)
    by_path = {row["path"]: row for row in scope["files"]}

    assert "docs-viewer/generated/docs/studio/index.json" not in by_path
    assert by_path["docs-viewer/runtime/js/docs-viewer-search.js"]["families"] == ["runtime-js"]
    assert "search" in by_path["docs-viewer/runtime/js/docs-viewer-search.js"]["areas"]
    assert "/library/" in by_path["docs-viewer/runtime/js/docs-viewer-search.js"]["shared_routes"]
    assert "/docs/" in by_path["docs-viewer/services/docs_management_routes.py"]["shared_routes"]
    assert scope["totals"]["excluded_files"] == 1


def test_resolve_run_files_intersects_selected_targets_and_keeps_shared_dependencies() -> None:
    config = checks_config.load_checks_config(repo_root=REPO_ROOT)
    source_files = [
        "docs-viewer/runtime/js/docs-viewer-search.js",
        "docs-viewer/runtime/js/docs-viewer-public.js",
        "docs-viewer/runtime/js/docs-viewer-route-config.js",
        "docs-viewer/services/docs_management_routes.py",
    ]

    search_library = resolver.resolve_run_files(
        config,
        scope_id="docs-viewer",
        families=["runtime-js"],
        areas=["search"],
        routes=["/library/"],
        source_files=source_files,
    )
    assert [row["path"] for row in search_library] == ["docs-viewer/runtime/js/docs-viewer-search.js"]

    docs_route = resolver.resolve_run_files(
        config,
        scope_id="docs-viewer",
        routes=["/docs/"],
        source_files=source_files,
    )
    assert {row["path"] for row in docs_route} == {
        "docs-viewer/runtime/js/docs-viewer-route-config.js",
        "docs-viewer/services/docs_management_routes.py",
    }


def test_resolve_target_map_reports_unclassified_and_stale_patterns() -> None:
    config = checks_config.load_checks_config(repo_root=REPO_ROOT)
    source_files = [
        "analytics-app/app/assets/css/analytics.css",
        "docs-viewer/shell/docs-viewer-shell.html",
    ]

    target_map = resolver.resolve_target_map(config, source_files=source_files, repo_root=REPO_ROOT)
    analytics = next(scope for scope in target_map["scopes"] if scope["scope_id"] == "analytics")
    docs_viewer = next(scope for scope in target_map["scopes"] if scope["scope_id"] == "docs-viewer")

    assert analytics["totals"]["unclassified_files"] == 1
    assert docs_viewer["totals"]["unclassified_files"] == 1
    assert any(pattern["status"] == "stale" for pattern in docs_viewer["patterns"])
