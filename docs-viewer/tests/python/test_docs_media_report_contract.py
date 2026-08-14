#!/usr/bin/env python3
"""Focused route, registry, loader, and public-boundary checks for Docs Media."""

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


def test_manage_registry_declares_local_docs_media_report() -> None:
    payload = read_json(REPO_ROOT / "docs-viewer/config/reports/reports.json")
    records = {
        str(record.get("report_id") or ""): record
        for record in payload["reports"]
        if isinstance(record, dict)
    }

    assert records["docs_media"] == {
        "report_id": "docs_media",
        "title": "Docs Media",
        "description": (
            "Lists each live ready-media and build-source file with its exact "
            "referencing documents."
        ),
        "default_access": "local",
        "loader_id": "docs_media",
        "presets": [],
    }


def test_public_registry_and_static_runtime_do_not_expose_docs_media() -> None:
    payload = read_json(REPO_ROOT / "site/assets/data/docs/public-reports.json")
    report_ids = {
        str(record.get("report_id") or "")
        for record in payload["reports"]
        if isinstance(record, dict)
    }

    assert "docs_media" not in report_ids
    assert not (
        REPO_ROOT / "site/docs-viewer/runtime/js/reports/docs-media-report.js"
    ).exists()


def test_manage_loader_service_and_css_own_focused_docs_media_paths() -> None:
    loader_source = (
        REPO_ROOT / "docs-viewer/runtime/js/reports/docs-viewer-reports.js"
    ).read_text(encoding="utf-8")
    service_source = (
        REPO_ROOT / "docs-viewer/runtime/js/reports/docs-viewer-report-service.js"
    ).read_text(encoding="utf-8")
    css_source = (
        REPO_ROOT / "site/docs-viewer/static/css/docs-viewer-reports.css"
    ).read_text(encoding="utf-8")

    assert 'import("./docs-media-report.js")' in loader_source
    assert 'fetchReportJson("/docs/media-report"' in service_source
    assert 'fetchReportJson("/docs/open-local-target"' in service_source
    assert '[data-report-id="docs_media"]' in css_source


def test_management_service_returns_selected_scope_docs_media_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    management_service = load_management_service(tmp_path, monkeypatch)
    config = object()
    calls: list[tuple[Path, object]] = []
    report = {
        "schema_version": "docs_media_report_v1",
        "scope": "example",
        "rows": [],
    }

    monkeypatch.setattr(
        management_service,
        "refresh_source_model_scope_configs",
        lambda _root: None,
    )
    monkeypatch.setattr(
        management_service.source_model,
        "normalize_scope",
        lambda value: "example" if value == "example" else (_ for _ in ()).throw(ValueError()),
    )
    monkeypatch.setitem(
        management_service.source_model.DOCS_SCOPE_CONFIGS,
        "example",
        config,
    )
    monkeypatch.setattr(
        management_service.docs_media_report,
        "build_docs_media_report",
        lambda repo_root, selected: calls.append((repo_root, selected)) or report,
    )

    status, payload = management_service.docs_management_post_response(
        tmp_path,
        routes.DOCS_MEDIA_REPORT_PATH,
        {"scope": "example"},
    )

    assert status == HTTPStatus.OK
    assert payload == {
        "ok": True,
        "dry_run": False,
        "summary_text": "Docs Media refreshed.",
        "report": report,
    }
    assert calls == [(tmp_path, config)]


def test_docs_media_route_is_management_owned_and_rejects_extra_options(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert routes.DOCS_MEDIA_REPORT_PATH == "/docs/media-report"
    assert routes.DOCS_MEDIA_REPORT_PATH in routes.POST_PATHS
    assert routes.DOCS_MEDIA_REPORT_PATH not in routes.GET_PATHS

    management_service = load_management_service(tmp_path, monkeypatch)
    monkeypatch.setattr(
        management_service,
        "refresh_source_model_scope_configs",
        lambda _root: None,
    )
    with pytest.raises(ValueError, match="must contain only scope"):
        management_service.docs_management_post_response(
            tmp_path,
            routes.DOCS_MEDIA_REPORT_PATH,
            {"scope": "example", "include_missing": True},
        )
