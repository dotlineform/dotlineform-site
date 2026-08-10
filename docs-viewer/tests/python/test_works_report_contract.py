#!/usr/bin/env python3
"""Focused registry, loader, input, and isolation checks for Works."""

from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_manage_registry_declares_local_works_report() -> None:
    payload = read_json(REPO_ROOT / "docs-viewer/config/reports/reports.json")
    records = {
        str(record.get("report_id") or ""): record
        for record in payload["reports"]
        if isinstance(record, dict)
    }

    assert records["works"] == {
        "report_id": "works",
        "title": "Works",
        "description": "Shows documentation coverage for every published Series.",
        "default_access": "local",
        "loader_id": "works",
        "presets": [],
    }


def test_manage_loader_owns_one_focused_works_module() -> None:
    loader_source = (
        REPO_ROOT / "docs-viewer/runtime/js/reports/docs-viewer-reports.js"
    ).read_text(encoding="utf-8")

    assert loader_source.count('import("./works-report.js")') == 1
    assert "return module.mountWorksReport;" in loader_source
    assert (REPO_ROOT / "docs-viewer/runtime/js/reports/works-report.js").is_file()


def test_works_module_uses_only_the_frozen_local_inputs_and_targets() -> None:
    source = (
        REPO_ROOT / "docs-viewer/runtime/js/reports/works-report.js"
    ).read_text(encoding="utf-8")

    assert '"catalogue_lookup_series_search"' in source
    assert '"catalogue_lookup_work_search"' in source
    assert 'const PROJECTS_SCOPE = "dotlineform";' in source
    assert 'const PROJECTS_SUB_SCOPE = "projects";' in source
    assert 'const PROJECTS_REPORT_DOC_ID = "d-20260801-073826-8865a8";' in source
    assert "configuredProjectsManifestUrl(context)" in source
    assert "Promise.all([" in source
    assert "subject-associations" not in source
    assert "analysis/works" not in source
    assert "doc_url" not in source


def test_public_and_server_surfaces_do_not_expose_works() -> None:
    public_registry = read_json(REPO_ROOT / "site/assets/data/docs/public-reports.json")
    public_report_ids = {
        str(record.get("report_id") or "")
        for record in public_registry["reports"]
        if isinstance(record, dict)
    }
    public_loader = (
        REPO_ROOT / "site/docs-viewer/runtime/js/reports/docs-viewer-public-reports.js"
    ).read_text(encoding="utf-8")
    report_service = (
        REPO_ROOT / "docs-viewer/runtime/js/reports/docs-viewer-report-service.js"
    ).read_text(encoding="utf-8")
    management_routes = (
        REPO_ROOT / "docs-viewer/services/docs_management_routes.py"
    ).read_text(encoding="utf-8")
    works_module = (
        REPO_ROOT / "docs-viewer/runtime/js/reports/works-report.js"
    ).read_text(encoding="utf-8")

    assert "works" not in public_report_ids
    assert "works-report.js" not in public_loader
    assert "runWorks" not in report_service
    assert '"/docs/works"' not in report_service
    assert '"/docs/works"' not in management_routes
    assert "/assets/data/catalogue" not in works_module
    assert "site/assets/data" not in works_module


def test_manage_report_context_already_passes_every_works_dependency() -> None:
    source = (
        REPO_ROOT
        / "docs-viewer/runtime/js/management/docs-viewer-management-document-reports.js"
    ).read_text(encoding="utf-8")

    for fragment in (
        "publicPreviewBase: cleanString(routeContext.publicPreviewBase)",
        "studioBaseUrl: cleanString(routeContext.studioBaseUrl)",
        "scopeConfigs: scopeConfigs(settings).slice()",
        "viewerUrlForScope: settings.viewerUrlForScope",
    ):
        assert source.count(fragment) == 2
