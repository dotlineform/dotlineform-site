#!/usr/bin/env python3
"""Focused checks for the standalone Docs Viewer service shell."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import tempfile

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_SERVICE_DIR = REPO_ROOT / "docs-viewer" / "services"
if str(DOCS_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(DOCS_SERVICE_DIR))

import docs_viewer_service  # noqa: E402


STATIC_IMPORT_PATTERN = re.compile(
    r"(?:import|export)\s+(?:(?:[^'\"]+?)\s+from\s+)?[\"']([^\"']+)[\"']",
    re.DOTALL,
)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def jekyll_excludes(repo_root: Path) -> set[str]:
    excludes: set[str] = set()
    in_exclude = False
    for line in (repo_root / "_config.yml").read_text(encoding="utf-8").splitlines():
        if line == "exclude:":
            in_exclude = True
            continue
        if in_exclude and line and not line.startswith("  "):
            break
        if in_exclude and line.startswith("  - "):
            excludes.add(line.removeprefix("  - ").strip())
    return excludes


def static_module_imports(path: Path) -> list[str]:
    return [match.group(1) for match in STATIC_IMPORT_PATTERN.finditer(path.read_text(encoding="utf-8"))]


def public_entry_static_import_graph(repo_root: Path, entry: Path) -> set[Path]:
    visited: set[Path] = set()
    pending = [entry]
    while pending:
        current = pending.pop()
        if current in visited:
            continue
        visited.add(current)
        for specifier in static_module_imports(current):
            if not specifier.startswith("."):
                continue
            target = (current.parent / specifier).resolve()
            if target.suffix:
                module_path = target
            else:
                module_path = target.with_suffix(".js")
            try:
                module_path.relative_to(repo_root)
            except ValueError:
                continue
            if module_path.exists() and module_path not in visited:
                pending.append(module_path)
    return visited


def test_load_service_config_reads_static_site_env() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        (repo_root / "_config.yml").write_text("title: fixture\n", encoding="utf-8")
        write_json(
            repo_root / "docs-viewer/config/defaults/docs-viewer-service.json",
            {
                "capabilities": {
                    "management_enabled_default": False,
                    "generated_reads_enabled_default": True,
                    "watch_enabled_default": True,
                },
            },
        )
        site_env = repo_root / "var/local/site.env"
        site_env.parent.mkdir(parents=True)
        site_env.write_text(
            "\n".join(
                [
                    'export DOCS_VIEWER_HOST="127.0.0.1"',
                    'export DOCS_VIEWER_PORT="8899"',
                    'export DOCS_VIEWER_BASE_URL="http://127.0.0.1:8899"',
                    'export DOCS_VIEWER_MANAGEMENT_ENABLED="1"',
                    'export DOCS_VIEWER_GENERATED_READS_ENABLED="0"',
                    'export DOCS_VIEWER_WATCH_ENABLED="0"',
                ]
            ),
            encoding="utf-8",
        )

        config = docs_viewer_service.load_service_config(repo_root, environ={})

    assert config.host == "127.0.0.1"
    assert config.port == 8899
    assert config.base_url == "http://127.0.0.1:8899"
    assert config.management_enabled is True
    assert config.generated_reads_enabled is False
    assert config.watch_enabled is False


def test_public_docs_viewer_entry_static_imports_only_public_runtime_modules() -> None:
    entry = REPO_ROOT / "docs-viewer/runtime/js/docs-viewer-public.js"
    graph = public_entry_static_import_graph(REPO_ROOT, entry)
    excluded = jekyll_excludes(REPO_ROOT)
    blocked = sorted(
        path.relative_to(REPO_ROOT).as_posix()
        for path in graph
        if path.relative_to(REPO_ROOT).as_posix() in excluded
    )

    assert blocked == []


def test_public_readonly_route_include_uses_public_entrypoint_contract() -> None:
    readonly_include = (REPO_ROOT / "_includes/docs_viewer_readonly_route.html").read_text(encoding="utf-8")
    shell_include = (REPO_ROOT / "_includes/docs_viewer_shell.html").read_text(encoding="utf-8")

    assert "route_config_url='/docs-viewer/config/routes/docs-viewer-public-routes.json'" in readonly_include
    assert "allow_management=false" in readonly_include
    assert "docs_viewer_management_route.html" not in readonly_include
    assert "docs-viewer/static/css/docs-viewer.css" in shell_include
    assert "docs-viewer/static/css/docs-viewer-manage.css" not in shell_include
    assert "docs-viewer/static/css/docs-viewer-reports.css" not in shell_include
    assert "default: '/docs-viewer/runtime/js/docs-viewer-public.js'" in shell_include


def test_public_docs_viewer_entry_static_graph_excludes_manage_document_actions() -> None:
    entry = REPO_ROOT / "docs-viewer/runtime/js/docs-viewer-public.js"
    graph = public_entry_static_import_graph(REPO_ROOT, entry)
    graph_paths = {
        path.relative_to(REPO_ROOT).as_posix()
        for path in graph
    }

    assert "docs-viewer/runtime/js/docs-viewer-management-document-actions-renderer.js" not in graph_paths
    assert "docs-viewer/runtime/js/docs-viewer-management-document-reports.js" not in graph_paths
    assert "docs-viewer/runtime/js/docs-viewer-management-shell-composition.js" not in graph_paths
    assert "docs-viewer/runtime/js/docs-viewer-report-service.js" not in graph_paths
    assert "docs-viewer/runtime/js/docs-viewer-reports.js" not in graph_paths
    assert not [
        path
        for path in graph_paths
        if path.startswith("docs-viewer/runtime/js/reports/")
    ]


def test_public_docs_viewer_entry_static_graph_excludes_manage_runtime_specifiers() -> None:
    entry = REPO_ROOT / "docs-viewer/runtime/js/docs-viewer-public.js"
    graph = public_entry_static_import_graph(REPO_ROOT, entry)
    blocked_fragments = [
        "./docs-html-import.js",
        "./docs-viewer-scope-lifecycle.js",
        "./docs-viewer-management-actions-renderer.js",
        "./docs-viewer-management-document-actions-renderer.js",
        "./docs-viewer-management-document-reports.js",
        "./docs-viewer-management-shell-composition.js",
        "./docs-viewer-management-shell-renderer.js",
        "./docs-viewer-report-service.js",
        "./docs-viewer-reports.js",
        "./modules/source-editor/source-editor.js",
        "/assets/data/docs/reports.json",
        "docsHtmlImportRoot",
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
    entry = REPO_ROOT / "docs-viewer/runtime/js/docs-viewer-public.js"
    graph = public_entry_static_import_graph(REPO_ROOT, entry)
    graph_paths = {
        path.relative_to(REPO_ROOT).as_posix()
        for path in graph
    }
    blocked_exact = {
        "docs-viewer/runtime/js/docs-html-import.js",
        "docs-viewer/runtime/js/docs-html-import-modals.js",
        "docs-viewer/runtime/js/docs-html-import-render.js",
        "docs-viewer/runtime/js/docs-html-import-workflow.js",
        "docs-viewer/runtime/js/docs-viewer-manage.js",
        "docs-viewer/runtime/js/docs-viewer-management-client.js",
        "docs-viewer/runtime/js/docs-viewer-report-service.js",
        "docs-viewer/runtime/js/docs-viewer-reports.js",
        "docs-viewer/runtime/js/docs-viewer-scope-lifecycle.js",
        "docs-viewer/runtime/js/modules/source-editor/source-editor.js",
    }
    blocked_prefixes = (
        "docs-viewer/runtime/js/docs-viewer-management-",
        "docs-viewer/runtime/js/reports/",
    )

    assert sorted(graph_paths & blocked_exact) == []
    assert sorted(
        path
        for path in graph_paths
        if path.startswith(blocked_prefixes)
    ) == []


def test_manage_docs_viewer_entry_static_graph_includes_manage_owned_modules() -> None:
    entry = REPO_ROOT / "docs-viewer/runtime/js/docs-viewer-manage.js"
    graph = public_entry_static_import_graph(REPO_ROOT, entry)
    graph_paths = {
        path.relative_to(REPO_ROOT).as_posix()
        for path in graph
    }
    required_paths = {
        "docs-viewer/runtime/js/docs-viewer-management-actions-renderer.js",
        "docs-viewer/runtime/js/docs-viewer-management-document-actions-renderer.js",
        "docs-viewer/runtime/js/docs-viewer-management-document-reports.js",
        "docs-viewer/runtime/js/docs-viewer-management-hosted-views.js",
        "docs-viewer/runtime/js/docs-viewer-management-shell-composition.js",
        "docs-viewer/runtime/js/docs-viewer-management-shell-renderer.js",
        "docs-viewer/runtime/js/docs-viewer-report-service.js",
        "docs-viewer/runtime/js/docs-viewer-reports.js",
    }

    assert sorted(required_paths - graph_paths) == []


def test_shared_app_shell_excludes_manage_shell_modal_refs() -> None:
    source = (REPO_ROOT / "docs-viewer/runtime/js/docs-viewer-app-shell.js").read_text(encoding="utf-8")
    blocked_fragments = [
        "./docs-viewer-management-actions-renderer.js",
        "./docs-viewer-management-document-actions-renderer.js",
        "./docs-viewer-management-shell-renderer.js",
        "docsViewerContextMenu",
        "docsViewerMetadataModal",
        "docsViewerImportModal",
        "docsHtmlImportRoot",
        "docsViewerSettingsModal",
        "docsViewerSettingsUpdatedInput",
    ]

    assert [fragment for fragment in blocked_fragments if fragment in source] == []


def test_manage_shell_composition_owns_manage_shell_renderer_imports() -> None:
    source = (
        REPO_ROOT / "docs-viewer/runtime/js/docs-viewer-management-shell-composition.js"
    ).read_text(encoding="utf-8")
    manage_entry = (REPO_ROOT / "docs-viewer/runtime/js/docs-viewer-manage.js").read_text(encoding="utf-8")

    assert "./docs-viewer-management-actions-renderer.js" in source
    assert "./docs-viewer-management-document-actions-renderer.js" in source
    assert "./docs-viewer-management-shell-renderer.js" in source
    assert "createDocsViewerManagementShellRenderers" in manage_entry


def test_manage_hosted_views_module_owns_source_editor_view_import() -> None:
    source = (
        REPO_ROOT / "docs-viewer/runtime/js/docs-viewer-management-hosted-views.js"
    ).read_text(encoding="utf-8")
    manage_entry = (REPO_ROOT / "docs-viewer/runtime/js/docs-viewer-manage.js").read_text(encoding="utf-8")

    assert "./modules/source-editor/source-editor.js" in source
    assert "markdown-source" in source
    assert "createDocsViewerManagementHostedViews" in manage_entry


def test_shared_main_view_renderer_excludes_manage_document_actions() -> None:
    source = (REPO_ROOT / "docs-viewer/runtime/js/docs-viewer-main-view-renderer.js").read_text(encoding="utf-8")
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
        REPO_ROOT / "docs-viewer/runtime/js/docs-viewer-management-document-reports.js"
    ).read_text(encoding="utf-8")

    assert "createDocsViewerReportService" in source
    assert "mountDocsViewerReport" in source
    assert "viewer_report" in source
    assert "reportRegistryUrl" in source


def test_report_runtime_has_no_fallback_registry() -> None:
    source = (REPO_ROOT / "docs-viewer/runtime/js/docs-viewer-reports.js").read_text(encoding="utf-8")

    assert "FALLBACK_REPORT_REGISTRY" not in source
    assert '"/assets/data/docs/reports.json"' not in source
    assert "Report registry is not configured." in source


def test_public_route_config_excludes_report_registry() -> None:
    public_payload = json.loads(
        (REPO_ROOT / "docs-viewer/config/routes/docs-viewer-public-routes.json").read_text(encoding="utf-8")
    )
    manage_payload = json.loads(
        (REPO_ROOT / "docs-viewer/config/routes/docs-viewer-routes.json").read_text(encoding="utf-8")
    )

    for payload in (public_payload, manage_payload):
        for route in payload["routes"]:
            if route["route_id"] in {"library", "analysis"}:
                assert "report_registry" not in route["config_urls"]


def test_basic_docs_viewer_css_excludes_manage_selectors() -> None:
    source = (REPO_ROOT / "docs-viewer/static/css/docs-viewer.css").read_text(encoding="utf-8")
    blocked_fragments = [
        "data-docs-viewer-management-shell-mount",
        "docsViewer__manageToolbarMount",
        "docsViewer__statusPills",
        "docsViewer__statusMenu",
        "docsViewerImport",
        "docsViewerSourceEditor",
        "docsViewerScopeLifecycle",
        "docsViewerReport",
    ]

    assert [fragment for fragment in blocked_fragments if fragment in source] == []


def test_manage_docs_viewer_css_owns_manage_selectors() -> None:
    source = (REPO_ROOT / "docs-viewer/static/css/docs-viewer-manage.css").read_text(encoding="utf-8")
    required_fragments = [
        "data-docs-viewer-management-shell-mount",
        "docsViewer__manageToolbarMount",
        "docsViewer__statusPills",
        "docsViewer__statusMenu",
        "docsViewerImport",
        "docsViewerSourceEditor",
        "docsViewerScopeLifecycle",
    ]

    assert [fragment for fragment in required_fragments if fragment not in source] == []


def test_manage_document_actions_renderer_owns_selected_document_controls() -> None:
    source = (
        REPO_ROOT / "docs-viewer/runtime/js/docs-viewer-management-document-actions-renderer.js"
    ).read_text(encoding="utf-8")

    assert "docsViewerManageEditButton" in source
    assert "docsViewerManageSourceButton" in source
    assert "docsViewerStatusPills" in source
    assert "Markdown source" in source
    assert "markdown-source" in source


@pytest.mark.parametrize(
    ("host", "base_url", "message"),
    [
        ("0.0.0.0", "http://0.0.0.0:8776", "loopback"),
        ("127.0.0.1", "http://127.0.0.1:8777", "DOCS_VIEWER_PORT"),
        ("127.0.0.1", "https://127.0.0.1:8776", "http loopback"),
    ],
)
def test_load_service_config_rejects_non_local_or_mismatched_service_location(
    host: str,
    base_url: str,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        docs_viewer_service.load_service_config(
            REPO_ROOT,
            environ={
                "DOCS_VIEWER_HOST": host,
                "DOCS_VIEWER_PORT": "8776",
                "DOCS_VIEWER_BASE_URL": base_url,
            },
        )


def test_manage_shell_uses_docs_viewer_service_api_base() -> None:
    config = docs_viewer_service.DocsViewerServiceConfig(
        host="127.0.0.1",
        port=8776,
        base_url="http://127.0.0.1:8776",
        management_enabled=True,
        generated_reads_enabled=True,
        watch_enabled=True,
    )

    rendered = docs_viewer_service.render_manage_page(REPO_ROOT, config, "test-version")
    route_registry = docs_viewer_service.render_route_config_registry(REPO_ROOT, config)
    manage_route = next(route for route in route_registry["routes"] if route["route_id"] == "docs-manage")

    assert "<title>Docs Viewer</title>" in rendered
    assert 'data-allow-management="true"' in rendered
    assert 'data-route-id="docs-manage"' in rendered
    assert 'data-route-config-url="/docs-viewer/config/routes/docs-viewer-routes.json"' in rendered
    assert manage_route["viewer_base_url"] == "/docs/"
    assert manage_route["include_scope_param"] is True
    assert manage_route["access"]["allow_management"] is True
    assert manage_route["access"]["allow_scope_query"] is True
    assert manage_route["generated_base_url"] == "http://127.0.0.1:8776"
    assert manage_route["access"]["management_base_url"] == "http://127.0.0.1:8776"
    assert "/docs-viewer/runtime/js/docs-viewer-manage.js?v=test-version" in rendered
    assert "/docs-viewer/static/css/docs-viewer.css?v=test-version" in rendered
    assert "/docs-viewer/static/css/docs-viewer-reports.css?v=test-version" in rendered
    assert "/docs-viewer/static/css/docs-viewer-manage.css?v=test-version" in rendered
    assert "/docs-viewer/static/css/docs-viewer-base.css" not in rendered
    assert "/docs-viewer/static/css/docs-viewer-public.css" not in rendered
    assert "/studio/api/docs" not in rendered
    assert "/studio/app/assets/css/studio.css" not in rendered
    assert "{%" not in rendered
    assert "{{" not in rendered
    assert "__DOCS_VIEWER_" not in rendered


def test_manage_shell_template_is_service_template_not_liquid() -> None:
    template = (REPO_ROOT / "docs-viewer/shell/docs-viewer-shell.html").read_text(encoding="utf-8")

    assert "{%" not in template
    assert "{{" not in template


def test_manage_shell_can_disable_management_markup_by_capability_flag() -> None:
    config = docs_viewer_service.DocsViewerServiceConfig(
        host="127.0.0.1",
        port=8776,
        base_url="http://127.0.0.1:8776",
        management_enabled=False,
        generated_reads_enabled=True,
        watch_enabled=True,
    )

    rendered = docs_viewer_service.render_manage_page(REPO_ROOT, config, "test-version")
    route_registry = docs_viewer_service.render_route_config_registry(REPO_ROOT, config)
    manage_route = next(route for route in route_registry["routes"] if route["route_id"] == "docs-manage")

    assert manage_route["access"]["allow_management"] is False
    assert manage_route["access"]["management_base_url"] == ""
    assert 'data-allow-management="false"' in rendered
    assert "docs-viewer-manage.css" not in rendered
    assert "docsViewerManagementShellMount" not in rendered
    assert "docsViewerManageActionsButton" not in rendered


def test_apply_capability_flags_respects_local_service_flags() -> None:
    payload = {
        "ok": True,
        "capabilities": {
            "docs_management": True,
            "generated_data_reads": True,
            "source_config_settings_writes": True,
            "html_import": True,
            "docs_export": True,
            "library_import": True,
            "scope_lifecycle": {"create_apply": True, "delete_apply": True},
            "scopes": {
                "studio": {
                    "generated_data_reads": True,
                    "generated_search_reads": True,
                },
            },
        },
    }
    config = docs_viewer_service.DocsViewerServiceConfig(
        host="127.0.0.1",
        port=8776,
        base_url="http://127.0.0.1:8776",
        management_enabled=False,
        generated_reads_enabled=False,
        watch_enabled=True,
    )

    result = docs_viewer_service.apply_capability_flags(payload, config)
    capabilities = result["capabilities"]

    assert capabilities["docs_management"] is False
    assert capabilities["generated_data_reads"] is False
    assert capabilities["source_config_settings_writes"] is False
    assert capabilities["html_import"] is False
    assert capabilities["scope_lifecycle"]["create_apply"] is False
    assert capabilities["scopes"]["studio"]["generated_data_reads"] is False
    assert capabilities["scopes"]["studio"]["generated_search_reads"] is False


def test_static_path_policy_is_docs_viewer_scoped() -> None:
    def allowed(path: str) -> bool:
        return docs_viewer_service.DocsViewerRequestHandler.is_allowed_static_path(object(), path)

    assert allowed("/docs-viewer/runtime/js/docs-viewer-public.js") is True
    assert allowed("/docs-viewer/runtime/js/docs-viewer-manage.js") is True
    assert allowed("/docs-viewer/runtime/js/docs-viewer.js") is False
    assert allowed("/docs-viewer/static/css/docs-viewer.css") is True
    assert allowed("/docs-viewer/static/css/docs-viewer-manage.css") is True
    assert allowed("/docs-viewer/static/css/docs-viewer-base.css") is False
    assert allowed("/docs-viewer/static/css/docs-viewer-management.css") is False
    assert allowed("/docs-viewer/static/css/docs-viewer-public.css") is False
    assert allowed("/docs-viewer/config/defaults/docs-viewer-config.json") is True
    assert allowed("/docs-viewer/generated/docs/studio/index-tree.json") is True
    assert allowed("/assets/docs/library/img/example.png") is True
    assert allowed("/studio/app/assets/css/studio.css") is False
    assert allowed("/studio/docs-viewer/runtime/js/docs-viewer.js") is False
    assert allowed("/docs-viewer/source/studio/docs-viewer.md") is False


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
