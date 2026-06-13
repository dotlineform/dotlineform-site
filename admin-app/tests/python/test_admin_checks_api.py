#!/usr/bin/env python3
"""Focused tests for the Admin checks API adapter."""

from __future__ import annotations

import json
import shutil
import sys
from http import HTTPStatus
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
ADMIN_SERVER_DIR = REPO_ROOT / "admin-app" / "app" / "server"
ADMIN_PACKAGE_DIR = ADMIN_SERVER_DIR / "admin_app"
for path in (REPO_ROOT, ADMIN_SERVER_DIR, ADMIN_PACKAGE_DIR):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

from admin_checks_api import checks_delete_response, checks_get_payload, checks_post_response  # noqa: E402


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_minimal_config(repo_root: Path) -> None:
    config = {
        "config_id": "admin-checks",
        "version": 1,
        "source": {"owner": "tests"},
        "scopes": {
            "admin": {"label": "Admin", "include": ["admin-app/"], "exclude": []},
            "analytics": {"label": "Analytics", "include": ["analytics-app/"], "exclude": []},
            "docs-viewer": {"label": "Docs Viewer", "include": ["docs-viewer/", "site/docs-viewer/"], "exclude": []},
            "public-site": {"label": "Public Site", "include": ["works/"], "exclude": []},
            "studio": {"label": "Studio", "include": ["studio/"], "exclude": []},
            "all": {"label": "All", "include": ["admin-app/", "docs-viewer/", "works/"], "exclude": []},
        },
        "families": {
            "runtime-js": {"label": "Runtime JavaScript", "include": ["site/docs-viewer/runtime/js/"]},
            "source-docs": {"label": "Source Docs", "include": ["docs-viewer/source/"]},
        },
        "areas": {
            "search": {"label": "Search", "include": ["site/docs-viewer/runtime/js/**/*search*"], "shared": [], "routes": ["/library/"]}
        },
        "routes": {
            "/library/": {
                "label": "Library",
                "path": "/library/",
                "status": "mapped",
                "include": ["site/docs-viewer/runtime/js/shared/docs-viewer-search.js"],
                "shared": [],
                "areas": ["search"],
            }
        },
        "reports": {
            "files": {
                "label": "Files",
                "script": "admin-app/checks/reports/files.py",
                "description": "File count, line count, and byte size evidence.",
                "default_options": {"limit": 20, "sort": "lines_desc"},
                "allowed_options": {
                    "limit": {"type": "integer", "minimum": 1, "maximum": 500},
                    "sort": {"type": "string", "enum": ["lines_desc", "bytes_desc", "path_asc"]},
                },
            }
        },
    }
    write_json(repo_root / "admin-app" / "checks" / "config" / "admin-checks.json", config)


def write_sample_run(repo_root: Path, run_id: str = "sample-run") -> Path:
    run_dir = repo_root / "var" / "admin" / "checks" / run_id
    report_dir = run_dir / "files"
    report_dir.mkdir(parents=True)
    write_json(
        run_dir / "manifest.json",
        {
            "run_id": run_id,
            "created_at": "2026-06-09T12:00:00+00:00",
            "status": "passed",
            "targets": {"scope": "docs-viewer", "families": [], "areas": [], "routes": []},
            "reports": [{"report_id": "files"}],
        },
    )
    write_json(
        run_dir / "run-summary.json",
        {
            "run_id": run_id,
            "created_at": "2026-06-09T12:00:00+00:00",
            "finished_at": "2026-06-09T12:00:01+00:00",
            "status": "passed",
            "targets": {"scope": "docs-viewer", "families": [], "areas": [], "routes": []},
            "reports": [
                {
                    "report_id": "files",
                    "status": "passed",
                    "artifacts": {
                        "report_json": f"var/admin/checks/{run_id}/files/report.json",
                        "report_markdown": f"var/admin/checks/{run_id}/files/report.md",
                        "report_csv": f"var/admin/checks/{run_id}/files/report.csv",
                    },
                }
            ],
        },
    )
    (run_dir / "run-summary.md").write_text("# Run Summary\n", encoding="utf-8")
    write_json(report_dir / "report.json", {"report_id": "files", "totals": {"files": 1, "lines": 2, "bytes": 3}})
    (report_dir / "report.md").write_text("# Files Report\n", encoding="utf-8")
    (report_dir / "report.csv").write_text("path,lines\nsample.py,2\n", encoding="utf-8")
    return run_dir


def write_source_file_for_files_report(repo_root: Path) -> None:
    source_path = repo_root / "site" / "docs-viewer" / "runtime" / "js" / "shared" / "docs-viewer-search.js"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text("const search = true;\n", encoding="utf-8")


def copy_checks_package(repo_root: Path) -> None:
    source = REPO_ROOT / "admin-app" / "checks"
    destination = repo_root / "admin-app" / "checks"
    shutil.copytree(source, destination, dirs_exist_ok=True)


def test_checks_api_health_and_metadata(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    write_minimal_config(repo_root)

    health = checks_get_payload(repo_root, "/health")
    reports = checks_get_payload(repo_root, "/reports")

    assert health["ok"] is True
    assert health["service"] == "admin_checks"
    assert health["runs_root"] == "var/admin/checks"
    assert health["reports"] == ["files"]
    assert reports["reports"][0]["id"] == "files"
    assert "default_options" not in reports["reports"][0]
    assert "allowed_options" not in reports["reports"][0]
    assert reports["scopes"][0]["id"] == "admin"


def test_checks_api_lists_runs_and_reads_summary_and_report(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    write_minimal_config(repo_root)
    write_sample_run(repo_root)

    runs = checks_get_payload(repo_root, "/runs")
    summary = checks_get_payload(repo_root, "/runs/sample-run/summary")
    report = checks_get_payload(repo_root, "/runs/sample-run/reports/files")

    assert runs["runs"][0]["run_id"] == "sample-run"
    assert runs["runs"][0]["summary_path"] == "var/admin/checks/sample-run/run-summary.md"
    assert runs["runs"][0]["report_ids"] == ["files"]
    assert summary["summary"]["status"] == "passed"
    assert summary["summary_markdown"] == "# Run Summary\n"
    assert report["report"]["totals"]["files"] == 1
    assert report["report_markdown"] == "# Files Report\n"
    assert report["report_csv_exists"] is True
    assert report["report_csv_path"] == "var/admin/checks/sample-run/files/report.csv"


def test_checks_api_validates_run_requests_without_command_passthrough(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    write_minimal_config(repo_root)

    with pytest.raises(ValueError, match="unknown keys"):
        checks_post_response(
            repo_root,
            "/runs",
            {"scope": "docs-viewer", "reports": ["files"], "command": "rm -rf var", "write": False},
        )
    with pytest.raises(ValueError, match="report options are configured"):
        checks_post_response(
            repo_root,
            "/runs",
            {"scope": "docs-viewer", "reports": ["files"], "options": {}, "write": False},
        )

    status, payload = checks_post_response(
        repo_root,
        "/runs",
        {"scope": "docs-viewer", "reports": ["files"], "write": False},
    )

    assert status == HTTPStatus.OK
    assert payload["ok"] is True
    assert payload["status"] == "dry-run"
    assert payload["mode"] == "dry-run"
    assert payload["plan"]["reports"][0]["options"]["limit"] == 20
    assert not (repo_root / "var" / "admin" / "checks").exists()


def test_checks_api_creates_write_run_with_files_report_artifacts(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    copy_checks_package(repo_root)
    write_minimal_config(repo_root)
    write_source_file_for_files_report(repo_root)

    status, payload = checks_post_response(
        repo_root,
        "/runs",
        {
            "scope": "docs-viewer",
            "families": ["runtime-js"],
            "areas": ["search"],
            "routes": ["/library/"],
            "reports": ["files"],
            "write": True,
        },
    )

    assert status == HTTPStatus.OK
    assert payload["ok"] is True
    assert payload["status"] == "passed"
    assert payload["mode"] == "write"
    run_dir = repo_root / payload["summary"]["run_dir"]
    assert (run_dir / "manifest.json").is_file()
    assert (run_dir / "run-summary.json").is_file()
    assert (run_dir / "files" / "report.json").is_file()
    assert (run_dir / "files" / "report.md").is_file()
    assert payload["summary"]["reports"][0]["artifacts"]["report_json"].endswith("/files/report.json")


def test_checks_api_deletes_run_snapshots_with_path_validation(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    write_minimal_config(repo_root)
    run_dir = write_sample_run(repo_root)

    status, payload = checks_delete_response(repo_root, "/runs/sample-run")

    assert status == HTTPStatus.OK
    assert payload["ok"] is True
    assert payload["status"] == "deleted"
    assert payload["run_id"] == "sample-run"
    assert payload["deleted_path"] == "var/admin/checks/sample-run"
    assert not run_dir.exists()

    with pytest.raises(FileNotFoundError, match="does not exist"):
        checks_delete_response(repo_root, "/runs/sample-run")
    with pytest.raises(ValueError, match="safe slug"):
        checks_delete_response(repo_root, "/runs/../bad")


def test_checks_api_rejects_unsafe_or_unknown_report_reads(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    write_minimal_config(repo_root)
    write_sample_run(repo_root)

    with pytest.raises(ValueError, match="safe slug"):
        checks_get_payload(repo_root, "/runs/../sample-run/summary")
    with pytest.raises(ValueError, match="safe slug"):
        checks_get_payload(repo_root, "/runs/sample-run/reports/../files")
    with pytest.raises(ValueError, match="allowlisted"):
        checks_get_payload(repo_root, "/runs/sample-run/reports/missing")
