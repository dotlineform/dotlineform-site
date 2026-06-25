#!/usr/bin/env python3
"""Docs Viewer static asset route and CSS tests."""

from __future__ import annotations

import tempfile
from pathlib import Path

from docs_viewer_service_test_support import REPO_ROOT, docs_viewer_service

def test_basic_docs_viewer_css_excludes_manage_selectors() -> None:
    source = (REPO_ROOT / "site/docs-viewer/static/css/docs-viewer.css").read_text(encoding="utf-8")
    blocked_fragments = [
        "data-docs-viewer-management-shell-mount",
        "docsViewer__manageToolbarMount",
        "docsViewer__statusPills",
        "docsViewer__statusMenu",
        "docsViewerImport",
        "docsViewerSemanticPicker",
        "docsViewerSourceEditor",
        "docsViewerScopeLifecycle",
        "docsViewerReport",
    ]

    assert [fragment for fragment in blocked_fragments if fragment in source] == []

def test_asset_version_uses_canonical_shared_css() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        shared_css = repo_root / "site/docs-viewer/static/css/docs-viewer.css"
        shared_css.parent.mkdir(parents=True)
        shared_css.write_text("/* shared css */\n", encoding="utf-8")

        assert docs_viewer_service.asset_version(repo_root) != "1"

def test_manage_docs_viewer_css_owns_manage_selectors() -> None:
    source = (REPO_ROOT / "docs-viewer/static/css/docs-viewer-manage.css").read_text(encoding="utf-8")
    required_fragments = [
        "data-docs-viewer-management-shell-mount",
        "docsViewer__manageToolbarMount",
        "docsViewerImport",
        "docsViewerSemanticPicker",
        "docsViewerSourceEditor",
        "docsViewerScopeLifecycle",
    ]

    assert [fragment for fragment in required_fragments if fragment not in source] == []

def test_static_path_policy_is_docs_viewer_scoped() -> None:
    def allowed(path: str) -> bool:
        return docs_viewer_service.DocsViewerRequestHandler.is_allowed_static_path(object(), path)

    assert allowed("/docs-viewer/runtime/js/public/docs-viewer-public.js") is True
    assert allowed("/docs-viewer/runtime/js/shared/docs-viewer-app-boot.js") is True
    assert allowed("/docs-viewer/runtime/js/management/docs-viewer-manage.js") is True
    assert allowed("/docs-viewer/runtime/js/import/docs-html-import.js") is True
    assert allowed("/docs-viewer/runtime/js/reports/docs-viewer-reports.js") is True
    assert allowed("/docs-viewer/runtime/js/docs-viewer-public.js") is False
    assert allowed("/docs-viewer/runtime/js/docs-viewer-manage.js") is False
    assert allowed("/docs-viewer/runtime/js/docs-viewer.js") is False
    assert allowed("/docs-viewer/static/css/docs-viewer.css") is True
    assert allowed("/docs-viewer/static/css/docs-viewer-reports.css") is True
    assert allowed("/docs-viewer/static/css/docs-viewer-manage.css") is True
    assert allowed("/docs-viewer/static/css/docs-viewer-base.css") is False
    assert allowed("/docs-viewer/static/css/docs-viewer-management.css") is False
    assert allowed("/docs-viewer/static/css/docs-viewer-public.css") is False
    assert allowed("/docs-viewer/config/defaults/docs-viewer-config.json") is True
    assert allowed("/docs-viewer/config/routes/docs-viewer-public-routes.json") is True
    assert allowed("/docs-viewer/config/reports/reports.json") is True
    assert allowed("/docs-viewer/generated/docs/studio/index-tree.json") is True
    assert allowed("/assets/docs/library/img/example.png") is True
    assert allowed("/studio/app/assets/css/studio.css") is False
    assert allowed("/studio/docs-viewer/runtime/js/docs-viewer.js") is False
    assert allowed("/docs-viewer/source/studio/docs-viewer.md") is False

def test_runtime_static_route_prefixes_resolve_to_owning_roots() -> None:
    assert docs_viewer_service.runtime_static_relative_path(
        "/docs-viewer/runtime/js/public/docs-viewer-public.js"
    ) == Path("site/docs-viewer/runtime/js/public/docs-viewer-public.js")
    assert docs_viewer_service.runtime_static_relative_path(
        "/docs-viewer/runtime/js/shared/docs-viewer-app-boot.js"
    ) == Path("site/docs-viewer/runtime/js/shared/docs-viewer-app-boot.js")
    assert docs_viewer_service.runtime_static_relative_path(
        "/docs-viewer/runtime/js/management/docs-viewer-manage.js"
    ) == Path("docs-viewer/runtime/js/management/docs-viewer-manage.js")
    assert docs_viewer_service.runtime_static_relative_path(
        "/docs-viewer/runtime/js/import/docs-html-import.js"
    ) == Path("docs-viewer/runtime/js/import/docs-html-import.js")
    assert docs_viewer_service.runtime_static_relative_path(
        "/docs-viewer/runtime/js/reports/docs-viewer-reports.js"
    ) == Path("docs-viewer/runtime/js/reports/docs-viewer-reports.js")
    assert docs_viewer_service.runtime_static_relative_path(
        "/docs-viewer/runtime/js/docs-viewer-public.js"
    ) is None

def test_shared_static_routes_resolve_to_owning_roots() -> None:
    assert docs_viewer_service.shared_static_relative_path(
        "/docs-viewer/static/css/docs-viewer.css"
    ) == Path("site/docs-viewer/static/css/docs-viewer.css")
    assert docs_viewer_service.shared_static_relative_path(
        "/docs-viewer/static/css/docs-viewer-reports.css"
    ) == Path("site/docs-viewer/static/css/docs-viewer-reports.css")
    assert docs_viewer_service.shared_static_relative_path(
        "/docs-viewer/static/css/docs-viewer-manage.css"
    ) is None
    assert docs_viewer_service.shared_static_relative_path(
        "/docs-viewer/config/routes/docs-viewer-public-routes.json"
    ) == Path("site/docs-viewer/config/routes/docs-viewer-public-routes.json")
    assert docs_viewer_service.shared_static_relative_path(
        "/docs-viewer/config/ui-text/public.json"
    ) == Path("site/docs-viewer/config/ui-text/public.json")
