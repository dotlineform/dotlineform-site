#!/usr/bin/env python3
"""Focused registry, service, and public-boundary checks for Uncataloged Files."""

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
    (tmp_path / "docs-viewer").mkdir(exist_ok=True)
    monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(tmp_path))
    return importlib.import_module("docs_management_service")


def test_manage_registry_declares_local_uncataloged_files_report() -> None:
    payload = read_json(REPO_ROOT / "docs-viewer/config/reports/reports.json")
    records = {
        str(record.get("report_id") or ""): record
        for record in payload["reports"]
        if isinstance(record, dict)
    }

    assert records["uncataloged_files"] == {
        "report_id": "uncataloged_files",
        "title": "Uncataloged Files",
        "description": (
            "Lists ordinary files in represented Work source folders that are "
            "not canonical Work primary sources."
        ),
        "default_access": "local",
        "loader_id": "uncataloged_files",
        "presets": [],
    }


def test_public_registry_does_not_expose_uncataloged_files_report() -> None:
    payload = read_json(REPO_ROOT / "site/assets/data/docs/public-reports.json")
    report_ids = {
        str(record.get("report_id") or "")
        for record in payload["reports"]
        if isinstance(record, dict)
    }

    assert "uncataloged_files" not in report_ids


def test_manage_loader_and_service_own_explicit_uncataloged_files_paths() -> None:
    loader_source = (
        REPO_ROOT / "docs-viewer/runtime/js/reports/docs-viewer-reports.js"
    ).read_text(encoding="utf-8")
    service_source = (
        REPO_ROOT / "docs-viewer/runtime/js/reports/docs-viewer-report-service.js"
    ).read_text(encoding="utf-8")

    assert 'import("./uncataloged-files-report.js")' in loader_source
    assert 'fetchReportJson("/docs/uncataloged-files"' in service_source
    assert 'fetchReportJson("/docs/open-local-target"' in service_source


def test_management_service_returns_table_only_live_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    management_service = load_management_service(tmp_path, monkeypatch)
    calls: list[Path] = []
    report = {
        "schema_version": "docs_uncataloged_files_report_v1",
        "rows": [
            {
                "folder": "alpha",
                "file_name": "notes.pdf",
                "local_target": "projects/alpha/notes.pdf",
            }
        ],
    }

    class FakeProducer:
        def __init__(self, *, repo_root: Path) -> None:
            calls.append(repo_root)

        def run(self) -> dict[str, object]:
            return {"report": report}

    monkeypatch.setattr(management_service, "refresh_source_model_scope_configs", lambda _root: None)
    monkeypatch.setattr(
        management_service.docs_uncataloged_files,
        "UncatalogedFilesProducer",
        FakeProducer,
    )

    status, payload = management_service.docs_management_post_response(
        tmp_path,
        routes.UNCATALOGED_FILES_PATH,
        {},
    )

    assert status == HTTPStatus.OK
    assert payload == {
        "ok": True,
        "dry_run": False,
        "summary_text": "Uncataloged Files refreshed.",
        "report": report,
    }
    assert calls == [tmp_path]


def test_management_service_rejects_report_options(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    management_service = load_management_service(tmp_path, monkeypatch)
    monkeypatch.setattr(management_service, "refresh_source_model_scope_configs", lambda _root: None)

    with pytest.raises(ValueError, match="request must be empty"):
        management_service.docs_management_post_response(
            tmp_path,
            routes.UNCATALOGED_FILES_PATH,
            {"include_subfolders": True},
        )
