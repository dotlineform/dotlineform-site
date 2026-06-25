#!/usr/bin/env python3
"""Docs Viewer management runtime boundary tests."""

from __future__ import annotations

import json

from docs_viewer_service_test_support import REPO_ROOT, public_entry_static_import_graph

def test_manage_docs_viewer_entry_static_graph_includes_manage_owned_modules() -> None:
    entry = REPO_ROOT / "docs-viewer/runtime/js/management/docs-viewer-manage.js"
    graph = public_entry_static_import_graph(REPO_ROOT, entry)
    graph_paths = {
        path.relative_to(REPO_ROOT).as_posix()
        for path in graph
    }
    required_paths = {
        "docs-viewer/runtime/js/management/docs-viewer-management-actions-renderer.js",
        "docs-viewer/runtime/js/management/docs-viewer-management-document-actions-renderer.js",
        "docs-viewer/runtime/js/management/docs-viewer-management-document-reports.js",
        "docs-viewer/runtime/js/management/docs-viewer-management-hosted-views.js",
        "docs-viewer/runtime/js/management/docs-viewer-management-shell-composition.js",
        "docs-viewer/runtime/js/management/docs-viewer-management-shell-renderer.js",
        "docs-viewer/runtime/js/reports/docs-viewer-report-service.js",
        "docs-viewer/runtime/js/reports/docs-viewer-reports.js",
    }

    assert sorted(required_paths - graph_paths) == []

def test_shared_app_shell_excludes_manage_shell_modal_refs() -> None:
    source = (REPO_ROOT / "site/docs-viewer/runtime/js/shared/docs-viewer-app-shell.js").read_text(encoding="utf-8")
    blocked_fragments = [
        "./docs-viewer-management-actions-renderer.js",
        "./docs-viewer-management-document-actions-renderer.js",
        "./docs-viewer-management-shell-renderer.js",
        "docsViewerContextMenu",
        "docsViewerMetadataModal",
        "docsViewerImportModal",
        "docsHtmlImportRoot",
        "docsViewerSettingsModal",
        "docsViewerSettingsBooleanInput",
    ]

    assert [fragment for fragment in blocked_fragments if fragment in source] == []

def test_manage_shell_composition_owns_manage_shell_renderer_imports() -> None:
    source = (
        REPO_ROOT / "docs-viewer/runtime/js/management/docs-viewer-management-shell-composition.js"
    ).read_text(encoding="utf-8")
    manage_entry = (REPO_ROOT / "docs-viewer/runtime/js/management/docs-viewer-manage.js").read_text(encoding="utf-8")

    assert "./docs-viewer-management-actions-renderer.js" in source
    assert "./docs-viewer-management-document-actions-renderer.js" in source
    assert "./docs-viewer-management-shell-renderer.js" in source
    assert "createDocsViewerManagementShellRenderers" in manage_entry

def test_manage_hosted_views_module_owns_document_display_mode_import() -> None:
    source = (
        REPO_ROOT / "docs-viewer/runtime/js/management/docs-viewer-management-hosted-views.js"
    ).read_text(encoding="utf-8")
    manage_entry = (REPO_ROOT / "docs-viewer/runtime/js/management/docs-viewer-manage.js").read_text(encoding="utf-8")
    source_editor = (
        REPO_ROOT / "docs-viewer/runtime/js/management/source-editor/source-editor.js"
    ).read_text(encoding="utf-8")

    assert "./source-editor/source-editor.js" in source
    assert "createDocsViewerSourceEditorMode" in source
    assert "markdown-source" in source
    assert "createDocsViewerManagementHostedViews" in manage_entry
    assert "createDocsViewerManagementDocumentDisplayModes" in manage_entry
    assert "documentDisplayModes" in manage_entry
    assert "createDocsViewerSourceEditorMode" in source_editor

def test_shared_main_view_renderer_excludes_manage_document_actions() -> None:
    source = (REPO_ROOT / "site/docs-viewer/runtime/js/shared/docs-viewer-main-view-renderer.js").read_text(encoding="utf-8")
    blocked_fragments = [
        "createDocsViewerReportService",
        "docs-viewer-reports.js",
        "docsViewerManageEditButton",
        "docsViewerManageSourceButton",
        "docsViewerStatusPills",
        "Markdown source",
        "markdown-source",
        "reportRegistryUrl",
        "dataset.docsViewerAction",
        "viewer_report",
    ]

    assert [fragment for fragment in blocked_fragments if fragment in source] == []

def test_manage_document_reports_module_owns_report_runtime_imports() -> None:
    source = (
        REPO_ROOT / "docs-viewer/runtime/js/management/docs-viewer-management-document-reports.js"
    ).read_text(encoding="utf-8")

    assert "createDocsViewerReportService" in source
    assert "mountDocsViewerReport" in source
    assert "viewer_report" in source
    assert "reportRegistryUrl" in source

def test_report_runtime_has_no_fallback_registry() -> None:
    source = (REPO_ROOT / "docs-viewer/runtime/js/reports/docs-viewer-reports.js").read_text(encoding="utf-8")

    assert "FALLBACK_REPORT_REGISTRY" not in source
    assert '"/assets/data/docs/reports.json"' not in source
    assert "Report registry is not configured." in source

def test_manage_route_config_uses_source_report_registry() -> None:
    payload = json.loads(
        (REPO_ROOT / "docs-viewer/config/routes/docs-viewer-routes.json").read_text(encoding="utf-8")
    )
    manage_route = next(route for route in payload["routes"] if route["route_id"] == "docs-manage")

    assert manage_route["config_urls"]["report_registry"] == "/docs-viewer/config/reports/reports.json"

def test_semantic_picker_default_is_management_owned() -> None:
    shared_runtime = (
        REPO_ROOT / "site/docs-viewer/runtime/js/shared/docs-viewer-app-runtime.js"
    ).read_text(encoding="utf-8")
    manage_entry = (
        REPO_ROOT / "docs-viewer/runtime/js/management/docs-viewer-manage.js"
    ).read_text(encoding="utf-8")
    hosted_views = (
        REPO_ROOT / "docs-viewer/runtime/js/management/docs-viewer-management-hosted-views.js"
    ).read_text(encoding="utf-8")

    assert "semantic-token-picker" not in shared_runtime
    assert "activeSemanticTokenAdapter" not in shared_runtime
    assert "setActiveSemanticTokenAdapter" not in shared_runtime
    assert "infoPanelDefaultViewByDocumentMode" in shared_runtime
    assert '"markdown-source": "semantic-token-picker"' in manage_entry
    assert 'id: "semantic-token-picker"' in hosted_views

def test_open_info_panel_follows_document_mode_default_generically() -> None:
    shared_runtime = (
        REPO_ROOT / "site/docs-viewer/runtime/js/shared/docs-viewer-app-runtime.js"
    ).read_text(encoding="utf-8")

    assert "function syncInfoPanelDefaultForDocumentMode(modeId)" in shared_runtime
    assert "infoPanelDefaultViewIdForMode(settings, modeId)" in shared_runtime
    assert "infoPanelController.openView(defaultViewId)" in shared_runtime
    assert "requestSettings.onAccepted = function (mode)" in shared_runtime
    assert 'infoPanelController.openView("semantic-token-picker")' not in shared_runtime

def test_info_panel_has_no_internal_view_switcher() -> None:
    renderer = (
        REPO_ROOT / "site/docs-viewer/runtime/js/shared/docs-viewer-info-panel-renderer.js"
    ).read_text(encoding="utf-8")
    controller = (
        REPO_ROOT / "site/docs-viewer/runtime/js/shared/docs-viewer-info-panel-controller.js"
    ).read_text(encoding="utf-8")
    css = (REPO_ROOT / "site/docs-viewer/static/css/docs-viewer.css").read_text(encoding="utf-8")

    blocked_fragments = [
        "docsViewerInfoPanelLabel",
        "docsViewerInfoPanelToolbar",
        "docsViewer__infoPanelLabel",
        "docsViewer__infoPanelToolbar",
        "docsViewer__infoPanelToolbarButton",
        "data-info-panel-view",
        "Info views",
        "Document metadata",
    ]

    assert [fragment for fragment in blocked_fragments if fragment in renderer] == []
    assert [fragment for fragment in blocked_fragments if fragment in controller] == []
    assert [fragment for fragment in blocked_fragments if fragment in css] == []

def test_source_editor_uses_wrapping_textarea_without_line_gutter() -> None:
    source_editor = (
        REPO_ROOT / "docs-viewer/runtime/js/management/source-editor/source-editor.js"
    ).read_text(encoding="utf-8")
    css = (
        REPO_ROOT / "docs-viewer/static/css/docs-viewer-manage.css"
    ).read_text(encoding="utf-8")

    assert 'textarea.wrap = "soft"' in source_editor
    assert "renderLineNumbers" not in source_editor
    assert "docsViewerSourceEditor__gutter" not in source_editor
    assert "docsViewerSourceEditor__gutter" not in css
    assert "white-space: pre-wrap" in css
    assert 'data-document-display-mode="markdown-source"' in css
    assert "--docs-viewer-measure: 100%" in css
    assert "flex: 1 1 auto" in css
    assert "width: 100%" in css
    assert "min-height: max(32rem, calc(100dvh - 8rem))" in css
    assert "max-height: none" in css

def test_manage_document_actions_renderer_owns_selected_document_controls() -> None:
    source = (
        REPO_ROOT / "docs-viewer/runtime/js/management/docs-viewer-management-document-actions-renderer.js"
    ).read_text(encoding="utf-8")
    management = (
        REPO_ROOT / "docs-viewer/runtime/js/management/docs-viewer-management.js"
    ).read_text(encoding="utf-8")

    assert "docsViewerManageEditButton" in source
    assert "docsViewerManageSourceButton" in source
    assert "Markdown source" in source
    assert "markdown-source" in source
    assert 'manageSourceButton.textContent = markdownMode ? "📄" : "☰";' in management
