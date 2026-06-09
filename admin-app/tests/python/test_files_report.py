#!/usr/bin/env python3
"""Focused tests for the Admin checks files report producer."""

from __future__ import annotations

import importlib.util
import csv
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
FILES_REPORT_PATH = REPO_ROOT / "admin-app" / "checks" / "reports" / "files.py"
ADMIN_CHECKS_DIR = REPO_ROOT / "admin-app" / "checks"
sys.path.insert(0, str(ADMIN_CHECKS_DIR))


def load_files_report_module():
    spec = importlib.util.spec_from_file_location("admin_files_report", FILES_REPORT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load files.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def fake_config() -> dict[str, object]:
    return {
        "config_id": "admin-checks",
        "version": 1,
        "source": {"owner": "tests"},
        "scopes": {
            "admin": {"label": "Admin", "include": ["admin-app/"], "exclude": []},
            "analytics": {"label": "Analytics", "include": ["analytics-app/"], "exclude": []},
            "docs-viewer": {"label": "Docs Viewer", "include": ["docs-viewer/"], "exclude": ["docs-viewer/generated/"]},
            "public-site": {"label": "Public Site", "include": ["works/"], "exclude": []},
            "studio": {"label": "Studio", "include": ["studio/"], "exclude": []},
            "all": {"label": "All", "include": ["admin-app/", "docs-viewer/", "works/"], "exclude": []},
        },
        "families": {
            "runtime-js": {"label": "Runtime JavaScript", "include": ["docs-viewer/runtime/js/"]},
            "services": {"label": "Services", "include": ["docs-viewer/services/"]},
            "source-docs": {"label": "Source Docs", "include": ["docs-viewer/source/"]},
        },
        "areas": {
            "search": {
                "label": "Search",
                "include": ["docs-viewer/runtime/js/docs-viewer-search.js"],
                "shared": ["docs-viewer/runtime/js/docs-viewer-shared.js"],
                "routes": ["/library/"],
            }
        },
        "routes": {
            "/library/": {
                "label": "Library",
                "path": "/library/",
                "status": "mapped",
                "include": ["docs-viewer/runtime/js/docs-viewer-search.js"],
                "shared": ["docs-viewer/runtime/js/docs-viewer-shared.js"],
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


def fake_manifest(*, limit: int = 20, sort: str = "lines_desc") -> dict[str, object]:
    return {
        "run_id": "pytest-run",
        "targets": {
            "scope": "docs-viewer",
            "families": ["runtime-js"],
            "areas": ["search"],
            "routes": ["/library/"],
        },
        "reports": [
            {
                "report_id": "files",
                "options": {
                    "limit": limit,
                    "sort": sort,
                },
            }
        ],
    }


def make_fake_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    write_file(repo / "docs-viewer" / "runtime" / "js" / "docs-viewer-search.js", "alpha\nbeta\ngamma\n")
    write_file(repo / "docs-viewer" / "runtime" / "js" / "docs-viewer-shared.js", "shared\n")
    write_file(repo / "docs-viewer" / "runtime" / "js" / "docs-viewer-other.js", "ignored\nignored\nignored\nignored\n")
    write_file(repo / "docs-viewer" / "generated" / "index.json", "{}\n")
    return repo


def test_files_report_counts_lines_bytes_and_target_metadata(tmp_path: Path) -> None:
    repo = make_fake_repo(tmp_path)
    report_module = load_files_report_module()

    report = report_module.build_report(
        config=fake_config(),
        manifest=fake_manifest(),
        report_id="files",
        repo_root=repo,
    )

    assert report["totals"]["files"] == 2
    assert report["totals"]["lines"] == 4
    assert report["totals"]["bytes"] == len("alpha\nbeta\ngamma\n".encode("utf-8")) + len("shared\n".encode("utf-8"))
    by_path = {row["path"]: row for row in report["files"]}
    assert by_path["docs-viewer/runtime/js/docs-viewer-search.js"]["target_match"] == "direct"
    assert by_path["docs-viewer/runtime/js/docs-viewer-shared.js"]["target_match"] == "shared"
    assert "docs-viewer/runtime/js/docs-viewer-other.js" not in by_path
    assert "docs-viewer/generated/index.json" not in by_path


def test_files_report_sorts_and_limits_markdown(tmp_path: Path) -> None:
    repo = make_fake_repo(tmp_path)
    report_module = load_files_report_module()

    report = report_module.build_report(
        config=fake_config(),
        manifest=fake_manifest(limit=1, sort="path_asc"),
        report_id="files",
        repo_root=repo,
    )
    markdown = report_module.render_markdown(report)

    assert [row["path"] for row in report["files"]] == [
        "docs-viewer/runtime/js/docs-viewer-search.js",
        "docs-viewer/runtime/js/docs-viewer-shared.js",
    ]
    assert "Showing 1 of 2 files" in markdown
    assert "docs-viewer/runtime/js/docs-viewer-search.js" in markdown
    assert "docs-viewer/runtime/js/docs-viewer-shared.js" not in markdown
    assert "| lines | size | family | path |" in markdown
    assert "target_match" not in markdown
    assert "direct" not in markdown
    assert " KB" in markdown


def test_files_report_bytes_sort(tmp_path: Path) -> None:
    repo = make_fake_repo(tmp_path)
    report_module = load_files_report_module()

    report = report_module.build_report(
        config=fake_config(),
        manifest=fake_manifest(sort="bytes_desc"),
        report_id="files",
        repo_root=repo,
    )

    assert report["files"][0]["path"] == "docs-viewer/runtime/js/docs-viewer-search.js"


def test_files_report_writes_required_artifacts(tmp_path: Path) -> None:
    repo = make_fake_repo(tmp_path)
    report_module = load_files_report_module()
    report = report_module.build_report(
        config=fake_config(),
        manifest=fake_manifest(),
        report_id="files",
        repo_root=repo,
    )
    output_dir = repo / "var" / "admin" / "checks" / "pytest-run" / "files"

    json_path, md_path, csv_path = report_module.write_outputs(report, report_module.render_markdown(report), output_dir)

    assert json_path.name == "report.json"
    assert md_path.name == "report.md"
    assert csv_path.name == "report.csv"
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "admin_checks_files_report_v1"
    assert md_path.read_text(encoding="utf-8").startswith("# Files Report\n")
    csv_rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
    assert csv_rows[0]["target_match"] == "direct"
    assert csv_rows[0]["size_kb"] == "0"
