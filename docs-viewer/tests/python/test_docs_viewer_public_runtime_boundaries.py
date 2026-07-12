#!/usr/bin/env python3
"""Docs Viewer public runtime boundary tests."""

from __future__ import annotations

import json

from docs_viewer_service_test_support import REPO_ROOT, public_entry_static_import_graph

def test_public_docs_viewer_entry_static_imports_only_public_runtime_modules() -> None:
    entry = REPO_ROOT / "site/docs-viewer/runtime/js/public/docs-viewer-public.js"
    graph = public_entry_static_import_graph(REPO_ROOT, entry)
    blocked = sorted(
        path.relative_to(REPO_ROOT).as_posix()
        for path in graph
        if "management" in path.name or "manage" in path.name
    )

    assert blocked == []

def test_public_docs_viewer_entry_static_graph_excludes_manage_document_actions() -> None:
    entry = REPO_ROOT / "site/docs-viewer/runtime/js/public/docs-viewer-public.js"
    graph = public_entry_static_import_graph(REPO_ROOT, entry)
    graph_paths = {
        path.relative_to(REPO_ROOT).as_posix()
        for path in graph
    }

    assert "docs-viewer/runtime/js/management/docs-viewer-management-document-actions-renderer.js" not in graph_paths
    assert "docs-viewer/runtime/js/management/docs-viewer-management-document-reports.js" not in graph_paths
    assert "docs-viewer/runtime/js/management/docs-viewer-management-shell-composition.js" not in graph_paths
    assert "docs-viewer/runtime/js/reports/docs-viewer-report-service.js" not in graph_paths
    assert "docs-viewer/runtime/js/reports/docs-viewer-reports.js" not in graph_paths
    assert "site/docs-viewer/runtime/js/public/docs-viewer-public-document-reports.js" in graph_paths
    assert "site/docs-viewer/runtime/js/reports/docs-viewer-public-reports.js" in graph_paths
    assert not [
        path
        for path in graph_paths
        if path.startswith("docs-viewer/runtime/js/reports/")
    ]

def test_public_docs_viewer_entry_static_graph_excludes_manage_owned_modules() -> None:
    entry = REPO_ROOT / "site/docs-viewer/runtime/js/public/docs-viewer-public.js"
    graph = public_entry_static_import_graph(REPO_ROOT, entry)
    graph_paths = {
        path.relative_to(REPO_ROOT).as_posix()
        for path in graph
    }
    blocked_exact = {
        "docs-viewer/runtime/js/import/docs-html-import.js",
        "docs-viewer/runtime/js/import/docs-html-import-modals.js",
        "docs-viewer/runtime/js/import/docs-html-import-render.js",
        "docs-viewer/runtime/js/import/docs-html-import-workflow.js",
        "docs-viewer/runtime/js/management/docs-viewer-manage.js",
        "docs-viewer/runtime/js/management/docs-viewer-management-client.js",
        "docs-viewer/runtime/js/reports/docs-viewer-report-service.js",
        "docs-viewer/runtime/js/reports/docs-viewer-reports.js",
        "docs-viewer/runtime/js/management/docs-viewer-scope-lifecycle.js",
        "docs-viewer/runtime/js/management/source-editor/source-editor.js",
    }
    blocked_prefixes = (
        "docs-viewer/runtime/js/management/docs-viewer-management-",
        "docs-viewer/runtime/js/reports/",
        "docs-viewer/runtime/js/review/",
    )

    assert sorted(graph_paths & blocked_exact) == []
    assert sorted(
        path
        for path in graph_paths
        if path.startswith(blocked_prefixes)
    ) == []

def test_public_route_config_uses_public_report_registry_projection() -> None:
    public_payload = json.loads(
        (REPO_ROOT / "site/docs-viewer/config/routes/docs-viewer-public-routes.json").read_text(encoding="utf-8")
    )
    manage_payload = json.loads(
        (REPO_ROOT / "docs-viewer/config/routes/docs-viewer-routes.json").read_text(encoding="utf-8")
    )

    for payload in (public_payload, manage_payload):
        for route in payload["routes"]:
            if route["route_id"] in {"library", "analysis"}:
                assert route["config_urls"]["report_registry"] == "/assets/data/docs/public-reports.json"

def test_route_configs_separate_app_kind_from_service_presence() -> None:
    public_payload = json.loads(
        (REPO_ROOT / "site/docs-viewer/config/routes/docs-viewer-public-routes.json").read_text(encoding="utf-8")
    )
    manage_payload = json.loads(
        (REPO_ROOT / "docs-viewer/config/routes/docs-viewer-routes.json").read_text(encoding="utf-8")
    )

    for route in public_payload["routes"]:
        assert route["schema_version"] == "docs_viewer_route_config_v4"
        assert route["app_kind"] == "public"
        assert route["features"] == [
            "configured-scope-discovery",
            "search",
            "recently-added",
            "bookmarks",
            "reports",
        ]
        assert route["access"] == {"allow_scope_query": False, "management_ui": False}
        assert all(not surface["base_url"] for surface in route["services"].values())

    manage_route = next(route for route in manage_payload["routes"] if route["route_id"] == "docs-manage")
    review_route = next(route for route in manage_payload["routes"] if route["route_id"] == "docs-review")
    assert review_route["app_kind"] == "review"
    assert review_route["features"] == []
    assert review_route["preserve_query_params"] == ["package"]
    assert review_route["services"]["source"]["base_url"] == ""
    assert not (REPO_ROOT / "docs-viewer/runtime/js/review/docs-viewer-review-document-controls.js").exists()
    assert not (REPO_ROOT / "docs-viewer/runtime/js/review/docs-viewer-review-hosted-views.js").exists()
    assert manage_route["app_kind"] == "manage"
    assert manage_route["schema_version"] == "docs_viewer_route_config_v4"
    assert "hosted_views" not in manage_route
    assert manage_route["features"] == [
        "configured-scope-discovery",
        "scope-selection",
        "search",
        "recently-added",
        "bookmarks",
        "reports",
        "source-editing",
        "management",
    ]
    assert manage_route["access"] == {"allow_scope_query": True, "management_ui": True}
    assert set(manage_route["services"]) == {"generated_data", "source", "management"}

def test_public_browser_config_projects_public_readonly_scope_routes() -> None:
    source_payload = json.loads((REPO_ROOT / "docs-viewer/config/scopes/docs_scopes.json").read_text(encoding="utf-8"))
    public_payload = json.loads((REPO_ROOT / "docs-viewer/config/defaults/docs-viewer-public-config.json").read_text(encoding="utf-8"))

    public_source_scopes = [
        scope
        for scope in source_payload["scopes"]
        if scope.get("include_scope_param") is False and scope.get("viewer_base_url") != "/docs/"
    ]
    public_scope_ids = [scope["scope_id"] for scope in public_source_scopes]

    assert public_payload["schema_version"] == "docs_viewer_config_v1"
    assert public_payload["default_scope_id"] == public_scope_ids[0]
    assert [scope["scope_id"] for scope in public_payload["scopes"]] == public_scope_ids
    assert [scope["viewer_base_url"] for scope in public_payload["scopes"]] == [
        scope["viewer_base_url"] for scope in public_source_scopes
    ]
    assert "studio" not in public_payload["docs_viewer"]["ui_statuses_by_scope"]
