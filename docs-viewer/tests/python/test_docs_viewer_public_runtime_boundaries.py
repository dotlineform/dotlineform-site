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

def test_public_readonly_route_page_uses_public_entrypoint_contract() -> None:
    html = (REPO_ROOT / "site/library/index.html").read_text(encoding="utf-8")

    assert 'data-route-config-url="/docs-viewer/config/routes/docs-viewer-public-routes.json"' in html
    assert 'data-route-id="library"' in html
    assert "data-docs-viewer-header-controls-mount" in html
    assert 'data-enable-search="true"' in html
    assert 'data-search-placeholder="search library"' in html
    assert 'data-search-aria-label="Search library"' in html
    assert 'data-allow-management="false"' not in html
    assert "docs-viewer/static/css/docs-viewer.css" in html
    assert "docs-viewer/static/css/docs-viewer-management.css" not in html
    assert "docs-viewer/static/css/docs-viewer-reports.css" in html
    assert 'src="/docs-viewer/runtime/js/public/docs-viewer-public.js' in html

def test_public_route_shell_attributes_have_runtime_readers() -> None:
    route_config = (REPO_ROOT / "site/docs-viewer/runtime/js/shared/docs-viewer-route-config.js").read_text(encoding="utf-8")
    app_shell = (REPO_ROOT / "site/docs-viewer/runtime/js/shared/docs-viewer-app-shell.js").read_text(encoding="utf-8")
    toolbar = (REPO_ROOT / "site/docs-viewer/runtime/js/shared/docs-viewer-viewer-toolbar-renderer.js").read_text(encoding="utf-8")

    assert "dataset.routeConfigUrl" in route_config
    assert "dataset.routeId" in route_config
    assert "[data-docs-viewer-header-controls-mount]" in app_shell
    assert "dataset.enableSearch" in toolbar
    assert "dataset.searchPlaceholder" in toolbar
    assert "dataset.searchAriaLabel" in toolbar

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

def test_public_docs_viewer_entry_static_graph_excludes_manage_runtime_specifiers() -> None:
    entry = REPO_ROOT / "site/docs-viewer/runtime/js/public/docs-viewer-public.js"
    graph = public_entry_static_import_graph(REPO_ROOT, entry)
    blocked_fragments = [
        "../import/docs-html-import.js",
        "../management/docs-viewer-scope-lifecycle.js",
        "../management/docs-viewer-management-actions-renderer.js",
        "../management/docs-viewer-management-document-actions-renderer.js",
        "../management/docs-viewer-management-document-reports.js",
        "../management/docs-viewer-management-shell-composition.js",
        "../management/docs-viewer-management-shell-renderer.js",
        "../reports/docs-viewer-report-service.js",
        "../reports/docs-viewer-reports.js",
        "./source-editor/source-editor.js",
        "/assets/data/docs/reports.json",
        "docsHtmlImportRoot",
        "docsViewerSemanticPicker",
        "docsViewerSettingsModal",
        "docsViewerSourceEditor",
        "openCreateScopeFlow",
        "openDeleteScopeFlow",
        "scopeCreateSupported",
        "scopeDeleteSupported",
    ]
    matches: dict[str, list[str]] = {}

    for path in graph:
        relative_path = path.relative_to(REPO_ROOT).as_posix()
        source = path.read_text(encoding="utf-8")
        found = [fragment for fragment in blocked_fragments if fragment in source]
        if found:
            matches[relative_path] = found

    assert matches == {}

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
