#!/usr/bin/env python3
"""Focused registry, loader, service, and public-boundary checks for Project State."""

from __future__ import annotations

from http import HTTPStatus
import importlib
import json
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
SERVICES_DIR = REPO_ROOT / "docs-viewer/services"
if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))

import docs_management_routes as routes  # noqa: E402


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_management_service(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(tmp_path))
    return importlib.import_module("docs_management_service")


def test_manage_registry_declares_local_project_state_report() -> None:
    payload = read_json(REPO_ROOT / "docs-viewer/config/reports/reports.json")
    records = {
        str(record.get("report_id") or ""): record
        for record in payload["reports"]
        if isinstance(record, dict)
    }

    assert records["project_state"] == {
        "report_id": "project_state",
        "title": "Project State",
        "description": (
            "Reconciles immediate project folders with canonical Works, Series, "
            "and Project documents."
        ),
        "default_access": "local",
        "loader_id": "project_state",
        "presets": [],
    }


def test_public_registry_does_not_expose_project_state_report() -> None:
    payload = read_json(REPO_ROOT / "site/assets/data/docs/public-reports.json")
    report_ids = {
        str(record.get("report_id") or "")
        for record in payload["reports"]
        if isinstance(record, dict)
    }

    assert "project_state" not in report_ids


def test_manage_loader_owns_project_state_module() -> None:
    loader_source = (
        REPO_ROOT / "docs-viewer/runtime/js/reports/docs-viewer-reports.js"
    ).read_text(encoding="utf-8")

    assert 'import("./project-state-report.js")' in loader_source
    assert (
        REPO_ROOT / "docs-viewer/runtime/js/reports/project-state-report.js"
    ).is_file()


def test_manage_report_context_passes_public_preview_base() -> None:
    source = (
        REPO_ROOT
        / "docs-viewer/runtime/js/management/docs-viewer-management-document-reports.js"
    ).read_text(encoding="utf-8")

    assert source.count("publicPreviewBase: cleanString(routeContext.publicPreviewBase)") == 2


def test_management_service_runs_producer_and_returns_live_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    management_service = load_management_service(tmp_path, monkeypatch)
    calls: list[dict[str, object]] = []
    report = {
        "schema_version": "docs_project_state_report_v2",
        "generation": "sha256:" + "a" * 64,
        "generated_at": "2026-08-05T15:10:00Z",
        "rows": [],
    }

    class FakeProducer:
        def __init__(self, *, repo_root: Path) -> None:
            calls.append({"repo_root": repo_root})

        def run(self) -> dict[str, object]:
            return {
                "report": report,
                "diagnostics": {},
            }

    monkeypatch.setattr(management_service, "refresh_source_model_scope_configs", lambda _root: None)
    monkeypatch.setattr(management_service.docs_project_state, "ProjectStateProducer", FakeProducer)

    status, payload = management_service.docs_management_post_response(
        tmp_path,
        routes.PROJECT_STATE_PATH,
        {},
    )

    assert status == HTTPStatus.OK
    assert payload["ok"] is True
    assert payload["dry_run"] is False
    assert payload["report"] is report
    assert "lookup" not in payload
    assert calls == [{"repo_root": tmp_path}]


def test_management_service_dry_run_uses_the_same_read_only_operation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    management_service = load_management_service(tmp_path, monkeypatch)
    runs: list[bool] = []

    class FakeProducer:
        def __init__(self, *, repo_root: Path) -> None:
            assert repo_root == tmp_path

        def run(self) -> dict[str, object]:
            runs.append(True)
            return {"report": {}, "diagnostics": {}}

    monkeypatch.setattr(management_service, "refresh_source_model_scope_configs", lambda _root: None)
    monkeypatch.setattr(management_service.docs_project_state, "ProjectStateProducer", FakeProducer)

    status, payload = management_service.docs_management_post_response(
        tmp_path,
        routes.PROJECT_STATE_PATH,
        {},
        dry_run=True,
    )

    assert status == HTTPStatus.OK
    assert payload["dry_run"] is True
    assert runs == [True]
    assert "lookup" not in payload
