#!/usr/bin/env python3
"""Docs Viewer public runtime boundary tests."""

from __future__ import annotations

import json
import re

from docs_subscope_customisations import registered_sub_scope_customisation_access
from docs_viewer_service_test_support import REPO_ROOT, public_entry_static_import_graph


def _public_runtime_manifest() -> list[str]:
    payload = json.loads(
        (REPO_ROOT / "site-tools/config/site-code-update.json").read_text(
            encoding="utf-8"
        )
    )
    runtime_prefix = "site/docs-viewer/runtime/js/"
    return sorted(
        f"{projection['destination_root'].removeprefix(runtime_prefix)}/{filename}"
        for projection in payload["projections"]
        if projection["destination_root"].startswith(runtime_prefix)
        for filename in projection["files"]
    )


def test_inline_mermaid_module_is_manage_owned_and_absent_from_public_runtime() -> None:
    runtime_manifest = _public_runtime_manifest()
    entry = REPO_ROOT / "docs-viewer/runtime/js/public/docs-viewer-public.js"
    graph_paths = {
        path.relative_to(REPO_ROOT).as_posix()
        for path in public_entry_static_import_graph(REPO_ROOT, entry)
    }

    assert "shared/docs-viewer-inline-mermaid.js" not in runtime_manifest
    assert (REPO_ROOT / "docs-viewer/runtime/js/management/docs-viewer-inline-mermaid.js").is_file()
    assert not (REPO_ROOT / "site/docs-viewer/runtime/js/shared/docs-viewer-inline-mermaid.js").exists()
    assert "docs-viewer/runtime/js/management/docs-viewer-inline-mermaid.js" not in graph_paths


def test_public_docs_viewer_entry_static_imports_only_public_runtime_modules() -> None:
    entry = REPO_ROOT / "docs-viewer/runtime/js/public/docs-viewer-public.js"
    graph = public_entry_static_import_graph(REPO_ROOT, entry)
    blocked = sorted(
        path.relative_to(REPO_ROOT).as_posix()
        for path in graph
        if "management" in path.name or "manage" in path.name
    )

    assert blocked == []


def test_persistent_diagram_detail_is_shared_by_public_and_manage_but_not_review() -> None:
    public_entry = REPO_ROOT / "docs-viewer/runtime/js/public/docs-viewer-public.js"
    public_graph = {
        path.relative_to(REPO_ROOT).as_posix()
        for path in public_entry_static_import_graph(REPO_ROOT, public_entry)
    }
    manage_entry = (REPO_ROOT / "docs-viewer/runtime/js/management/docs-viewer-manage.js").read_text(
        encoding="utf-8"
    )
    review_entry = (REPO_ROOT / "docs-viewer/runtime/js/review/docs-viewer-review.js").read_text(
        encoding="utf-8"
    )

    assert "docs-viewer/runtime/js/shared/docs-viewer-diagram-detail.js" in public_graph
    assert "docs-viewer-diagram-detail.js" in manage_entry
    assert "docs-viewer-diagram-detail.js" not in review_entry


def test_expanded_report_adapter_is_local_owned_and_only_manage_composed() -> None:
    runtime_manifest = _public_runtime_manifest()
    public_entry = REPO_ROOT / "docs-viewer/runtime/js/public/docs-viewer-public.js"
    public_graph = {
        path.relative_to(REPO_ROOT).as_posix()
        for path in public_entry_static_import_graph(REPO_ROOT, public_entry)
    }
    manage_entry = (REPO_ROOT / "docs-viewer/runtime/js/management/docs-viewer-manage.js").read_text(
        encoding="utf-8"
    )
    review_entry = (REPO_ROOT / "docs-viewer/runtime/js/review/docs-viewer-review.js").read_text(
        encoding="utf-8"
    )

    assert "shared/docs-viewer-report-presentation.js" not in runtime_manifest
    assert (
        REPO_ROOT / "docs-viewer/runtime/js/reports/docs-viewer-report-presentation.js"
    ).is_file()
    assert not (
        REPO_ROOT / "site/docs-viewer/runtime/js/shared/docs-viewer-report-presentation.js"
    ).exists()
    assert "docs-viewer/runtime/js/shared/docs-viewer-report-presentation.js" not in public_graph
    assert "docs-viewer/runtime/js/reports/docs-viewer-report-presentation.js" not in public_graph
    assert '../reports/docs-viewer-report-presentation.js' in manage_entry
    assert "docs-viewer-report-presentation.js" not in review_entry


def test_public_docs_viewer_entry_static_graph_excludes_manage_document_actions() -> None:
    entry = REPO_ROOT / "docs-viewer/runtime/js/public/docs-viewer-public.js"
    graph = public_entry_static_import_graph(REPO_ROOT, entry)
    graph_paths = {
        path.relative_to(REPO_ROOT).as_posix()
        for path in graph
    }

    assert "docs-viewer/runtime/js/management/docs-viewer-management-control-renderers.js" not in graph_paths
    assert "docs-viewer/runtime/js/management/docs-viewer-management-document-reports.js" not in graph_paths
    assert "docs-viewer/runtime/js/management/docs-viewer-management-subscope-default-contribution.js" not in graph_paths
    assert "docs-viewer/runtime/js/management/docs-viewer-management-subscope-composition.js" not in graph_paths
    assert "docs-viewer/runtime/js/management/docs-viewer-management-subscope-analysis-tags.js" not in graph_paths
    assert "docs-viewer/runtime/js/management/docs-viewer-management-subscope-dotlineform-projects.js" not in graph_paths
    assert (
        "docs-viewer/runtime/js/management/"
        "docs-viewer-management-subscope-delete-workflow.js"
    ) not in graph_paths
    assert "docs-viewer/runtime/js/management/docs-viewer-management-shell-composition.js" not in graph_paths
    assert "docs-viewer/runtime/js/management/docs-viewer-inline-mermaid.js" not in graph_paths
    assert "docs-viewer/runtime/js/reports/docs-viewer-report-service.js" not in graph_paths
    assert "docs-viewer/runtime/js/reports/docs-viewer-reports.js" not in graph_paths
    assert "docs-viewer/runtime/js/public/docs-viewer-public-document-reports.js" in graph_paths
    assert "docs-viewer/runtime/js/reports/docs-viewer-public-reports.js" in graph_paths
    assert sorted(
        path
        for path in graph_paths
        if path.startswith("docs-viewer/runtime/js/reports/")
    ) == ["docs-viewer/runtime/js/reports/docs-viewer-public-reports.js"]


def test_subscope_manage_customisations_are_publicly_isolated() -> None:
    public_reports = json.loads(
        (REPO_ROOT / "site/assets/data/docs/public-reports.json").read_text(
            encoding="utf-8"
        )
    )
    public_loader = (
        REPO_ROOT / "docs-viewer/runtime/js/reports/docs-viewer-public-reports.js"
    ).read_text(encoding="utf-8")
    canonical_report = (
        REPO_ROOT / "docs-viewer/runtime/js/shared/docs-subscope-report.js"
    ).read_text(encoding="utf-8")
    entry = REPO_ROOT / "docs-viewer/runtime/js/public/docs-viewer-public.js"
    graph_paths = {
        path.relative_to(REPO_ROOT).as_posix()
        for path in public_entry_static_import_graph(REPO_ROOT, entry)
    }

    assert "docs_subscope_candidate" not in {
        report["report_id"] for report in public_reports["reports"]
    }
    assert "docs_subscope_candidate" not in public_loader
    assert "docs-viewer/runtime/js/reports/docs-subscope-candidate-report.js" not in graph_paths
    assert 'from "./docs-subscope-customisation-registry.js"' in canonical_report
    assert not [
        path
        for path in graph_paths
        if path.startswith("docs-viewer/runtime/js/management/")
        and ("subscope-customisation" in path or "subscope-composition" in path)
    ]


def test_subscope_customisation_registry_access_agrees_across_runtimes() -> None:
    manage_source = (
        REPO_ROOT
        / "docs-viewer/runtime/js/management/"
        "docs-viewer-management-subscope-customisation-registry.js"
    ).read_text(encoding="utf-8")
    public_source = (
        REPO_ROOT
        / "docs-viewer/runtime/js/shared/"
        "docs-subscope-customisation-registry.js"
    ).read_text(encoding="utf-8")
    manage_ids = set(re.findall(r"^  ([a-z][a-z0-9_]*): function", manage_source, re.MULTILINE))
    public_ids = set(re.findall(r"^  ([a-z][a-z0-9_]*): function", public_source, re.MULTILINE))
    python_access = registered_sub_scope_customisation_access()

    assert manage_ids == {
        customisation_id
        for customisation_id, access in python_access.items()
        if "manage" in access
    }
    assert public_ids == {
        customisation_id
        for customisation_id, access in python_access.items()
        if "public" in access
    }


def test_projects_metadata_contribution_does_not_intercept_native_paste_or_undo() -> None:
    source = (
        REPO_ROOT
        / "docs-viewer/runtime/js/management/"
        "docs-viewer-management-subscope-dotlineform-projects.js"
    ).read_text(encoding="utf-8")

    assert "execCommand" not in source
    assert "clipboard" not in source.lower()
    assert "onpaste" not in source
    assert 'addEventListener("paste"' not in source
    assert 'addEventListener("beforeinput"' not in source

def test_public_docs_viewer_entry_static_graph_excludes_manage_owned_modules() -> None:
    entry = REPO_ROOT / "docs-viewer/runtime/js/public/docs-viewer-public.js"
    graph = public_entry_static_import_graph(REPO_ROOT, entry)
    graph_paths = {
        path.relative_to(REPO_ROOT).as_posix()
        for path in graph
    }
    blocked_exact = {
        "docs-viewer/runtime/js/import/docs-html-import.js",
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
        "docs-viewer/runtime/js/review/",
    )

    assert sorted(graph_paths & blocked_exact) == []
    assert sorted(
        path
        for path in graph_paths
        if path.startswith(blocked_prefixes)
    ) == []
    assert sorted(
        path
        for path in graph_paths
        if path.startswith("docs-viewer/runtime/js/reports/")
    ) == ["docs-viewer/runtime/js/reports/docs-viewer-public-reports.js"]

def test_public_route_config_uses_public_report_registry_projection() -> None:
    public_payload = json.loads(
        (REPO_ROOT / "site/docs-viewer/config/routes/docs-viewer-public-routes.json").read_text(encoding="utf-8")
    )
    manage_payload = json.loads(
        (REPO_ROOT / "docs-viewer/config/routes/docs-viewer-routes.json").read_text(encoding="utf-8")
    )

    for payload in (public_payload, manage_payload):
        for route in payload["routes"]:
            if route["route_id"] in {"example", "analysis"}:
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
            "recent",
            "bookmarks",
            "reports",
        ]
        assert route["access"] == {"allow_scope_query": False, "management_ui": False}
        assert all(not surface["base_url"] for surface in route["services"].values())
        assert route["recent_basis"] == "edited"

    manage_route = next(route for route in manage_payload["routes"] if route["route_id"] == "docs-manage")
    review_route = next(route for route in manage_payload["routes"] if route["route_id"] == "docs-review")
    assert review_route["app_kind"] == "review"
    assert review_route["features"] == []
    assert review_route["preserve_query_params"] == ["package"]
    assert review_route["services"]["source"]["base_url"] == ""
    assert not (REPO_ROOT / "docs-viewer/runtime/js/review/docs-viewer-review-document-controls.js").exists()
    assert not (REPO_ROOT / "docs-viewer/runtime/js/review/docs-viewer-review-hosted-views.js").exists()
    assert manage_route["app_kind"] == "manage"
    assert manage_route["recent_basis"] == "edited"
    assert manage_route["schema_version"] == "docs_viewer_route_config_v4"
    assert "hosted_views" not in manage_route
    assert manage_route["features"] == [
        "configured-scope-discovery",
        "scope-selection",
        "search",
        "recent",
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
    assert "ui_statuses_by_scope" not in public_payload["docs_viewer"]
    assert "scope_type_badges" not in public_payload["docs_viewer"]
