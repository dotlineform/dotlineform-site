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
    assert resolver.path_matches("site/docs-viewer/runtime/js/", "site/docs-viewer/runtime/js/shared/docs-viewer-search.js")
    assert resolver.path_matches("site/docs-viewer/runtime/js/shared/docs-viewer-search*", "site/docs-viewer/runtime/js/shared/docs-viewer-search.js")
    assert resolver.path_matches("**/*search*", "docs-viewer/build/build_search.py")
    assert not resolver.path_matches("docs-viewer/services/", "site/docs-viewer/runtime/js/shared/docs-viewer-search.js")


def test_source_file_discovery_excludes_markdown_documents(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "docs-viewer" / "source" / "studio").mkdir(parents=True)
    (repo / "docs-viewer" / "source" / "studio" / "notes.md").write_text("# Notes\n", encoding="utf-8")
    (repo / "docs-viewer" / "config").mkdir(parents=True)
    (repo / "docs-viewer" / "config" / "docs-viewer.json").write_text("{}\n", encoding="utf-8")
    (repo / "assets" / "css").mkdir(parents=True)
    (repo / "assets" / "css" / "site.css").write_text(":root {}\n", encoding="utf-8")

    assert resolver.iter_repo_source_files(repo) == [
        "assets/css/site.css",
        "docs-viewer/config/docs-viewer.json",
    ]


def test_resolve_scope_reports_families_routes_shared_and_exclusions() -> None:
    config = checks_config.load_checks_config(repo_root=REPO_ROOT)
    source_files = [
        "docs-viewer/static/css/docs-viewer.css",
        "site/docs-viewer/runtime/js/shared/docs-viewer-search.js",
        "site/docs-viewer/runtime/js/public/docs-viewer-public.js",
        "docs-viewer/services/docs_management_routes.py",
        "docs-viewer/generated/docs/studio/index.json",
    ]

    scope = resolver.resolve_scope(config, "docs-viewer", source_files=source_files, global_source_files=source_files)
    by_path = {row["path"]: row for row in scope["files"]}

    assert "docs-viewer/generated/docs/studio/index.json" not in by_path
    assert by_path["docs-viewer/static/css/docs-viewer.css"]["families"] == ["runtime-assets"]
    assert by_path["site/docs-viewer/runtime/js/shared/docs-viewer-search.js"]["families"] == ["runtime-js"]
    assert "search" in by_path["site/docs-viewer/runtime/js/shared/docs-viewer-search.js"]["areas"]
    assert "/library/" in by_path["site/docs-viewer/runtime/js/shared/docs-viewer-search.js"]["shared_routes"]
    assert "/docs/" in by_path["docs-viewer/services/docs_management_routes.py"]["shared_routes"]
    assert scope["totals"]["excluded_files"] == 1


def test_resolve_run_files_intersects_selected_targets_and_keeps_shared_dependencies() -> None:
    config = checks_config.load_checks_config(repo_root=REPO_ROOT)
    source_files = [
        "site/docs-viewer/runtime/js/shared/docs-viewer-search.js",
        "site/docs-viewer/runtime/js/public/docs-viewer-public.js",
        "site/docs-viewer/runtime/js/shared/docs-viewer-route-config.js",
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
    assert [row["path"] for row in search_library] == ["site/docs-viewer/runtime/js/shared/docs-viewer-search.js"]

    docs_route = resolver.resolve_run_files(
        config,
        scope_id="docs-viewer",
        routes=["/docs/"],
        source_files=source_files,
    )
    assert {row["path"] for row in docs_route} == {
        "site/docs-viewer/runtime/js/shared/docs-viewer-route-config.js",
        "docs-viewer/services/docs_management_routes.py",
    }


def test_resolve_target_map_reports_unclassified_and_stale_patterns() -> None:
    config = checks_config.load_checks_config(repo_root=REPO_ROOT)
    source_files = [
        "analytics-app/unmapped.txt",
        "docs-viewer/unmapped.txt",
    ]

    target_map = resolver.resolve_target_map(config, source_files=source_files, repo_root=REPO_ROOT)
    analytics = next(scope for scope in target_map["scopes"] if scope["scope_id"] == "analytics")
    docs_viewer = next(scope for scope in target_map["scopes"] if scope["scope_id"] == "docs-viewer")

    assert analytics["totals"]["unclassified_files"] == 1
    assert docs_viewer["totals"]["unclassified_files"] == 1
    assert any(pattern["status"] == "stale" for pattern in docs_viewer["patterns"])


def test_resolve_scope_excludes_retired_prior_art() -> None:
    config = checks_config.load_checks_config(repo_root=REPO_ROOT)
    source_files = [
        "studio/app/assets/css/studio.css",
        "studio/retired/thumbnail-quality/thumbnail-quality.css",
    ]

    scope = resolver.resolve_scope(config, "studio", source_files=source_files, global_source_files=source_files)
    by_path = {row["path"]: row for row in scope["files"]}

    assert by_path["studio/app/assets/css/studio.css"]["families"] == ["runtime-assets"]
    assert "studio/retired/thumbnail-quality/thumbnail-quality.css" not in by_path
    assert scope["totals"]["excluded_files"] == 1
