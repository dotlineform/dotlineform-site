#!/usr/bin/env python3
"""Focused registry, target, rendering, adoption, and public-boundary checks."""

from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_manage_registry_and_loader_own_one_local_backlinks_report() -> None:
    registry = read_json(REPO_ROOT / "docs-viewer/config/reports/reports.json")
    records = {
        str(record.get("report_id") or ""): record
        for record in registry["reports"]
        if isinstance(record, dict)
    }
    assert records["docs_backlinks"] == {
        "report_id": "docs_backlinks",
        "title": "Documents Linking Here",
        "description": (
            "Lists current same-scope documents linking to the exact report "
            "host document."
        ),
        "default_access": "local",
        "loader_id": "docs_backlinks",
        "presets": [],
    }

    loader = (
        REPO_ROOT / "docs-viewer/runtime/js/reports/docs-viewer-reports.js"
    ).read_text(encoding="utf-8")
    assert loader.count('import("./docs-backlinks-report.js")') == 1
    assert loader.count("return module.mountDocsBacklinksReport;") == 1


def test_directives_menu_owns_the_exact_local_backlinks_insertion() -> None:
    source = (
        REPO_ROOT
        / "docs-viewer/runtime/js/management/source-editor/directive-actions.js"
    ).read_text(encoding="utf-8")
    assert source.count('id: "docs-backlinks"') == 1
    assert source.count('label: "Documents linking here"') == 1
    assert source.count(
        'source: ":::report\\nid: docs_backlinks\\naccess: local\\n:::"'
    ) == 1
    assert "createDirectiveInsertionPlan" in source
    assert 'if (/^\\n+$/.test(source.slice(insertionPoint))) return "";' in source


def test_report_binds_only_the_exact_loaded_host_target_and_scope_owned_url() -> None:
    source = (
        REPO_ROOT / "docs-viewer/runtime/js/reports/docs-backlinks-report.js"
    ).read_text(encoding="utf-8")
    config_controller = (
        REPO_ROOT
        / "docs-viewer/runtime/js/shared/docs-viewer-config-controller.js"
    ).read_text(encoding="utf-8")
    browser_config_builder = (
        REPO_ROOT / "docs-viewer/build/docs_builder/browser_config.py"
    ).read_text(encoding="utf-8")
    backlinks_builder = (
        REPO_ROOT / "docs-viewer/build/docs_builder/backlinks.py"
    ).read_text(encoding="utf-8")

    for required in (
        "context && context.viewerScope",
        "context && context.payload && context.payload.doc_id",
        "config && config.backlinksUrl",
        'payload.schema !== "docs_backlinks_v1"',
        'cache: "no-store"',
        '"No documents link here."',
        'document.createElement("a")',
    ):
        assert required in source
    for forbidden in (
        "window.location",
        "context.doc",
        "report_scope",
        "selectedRow",
        "managementService",
        "reportService",
    ):
        assert forbidden not in source
    assert 'backlinksUrl: String(rawScope.backlinks_url || "").trim()' in (
        config_controller
    )
    assert "if published:" in browser_config_builder
    assert 'return f"/docs/backlinks?scope={quote(config.scope_id)}"' in (
        browser_config_builder
    )
    assert "scope_uses_external_data" not in backlinks_builder


def test_backlinks_report_and_payload_are_absent_from_public_owners() -> None:
    public_registry = read_json(
        REPO_ROOT / "site/assets/data/docs/public-reports.json"
    )
    public_report_ids = {
        str(record.get("report_id") or "")
        for record in public_registry["reports"]
        if isinstance(record, dict)
    }
    public_loader = (
        REPO_ROOT
        / "docs-viewer/runtime/js/reports/docs-viewer-public-reports.js"
    ).read_text(encoding="utf-8")
    public_browser_config = read_json(
        REPO_ROOT / "docs-viewer/config/defaults/docs-viewer-public-config.json"
    )
    publish_gate = (
        REPO_ROOT / "docs-viewer/services/docs_publish_gate.py"
    ).read_text(encoding="utf-8")

    assert "docs_backlinks" not in public_report_ids
    assert "docs-backlinks-report.js" not in public_loader
    assert all(
        "backlinks_url" not in scope
        for scope in public_browser_config["scopes"]
        if isinstance(scope, dict)
    )
    assert 'relative_path == Path("backlinks.json")' in publish_gate
