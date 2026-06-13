#!/usr/bin/env python3
"""Focused tests for the Admin checks target-map report producer."""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TARGET_MAP_REPORT_PATH = REPO_ROOT / "admin-app" / "checks" / "reports" / "target_map.py"
RUN_REPORTS_PATH = REPO_ROOT / "admin-app" / "checks" / "run_reports.py"
ADMIN_CHECKS_DIR = REPO_ROOT / "admin-app" / "checks"
sys.path.insert(0, str(ADMIN_CHECKS_DIR))


def load_target_map_report_module():
    spec = importlib.util.spec_from_file_location("admin_target_map_report", TARGET_MAP_REPORT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load target_map.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_run_reports_module():
    spec = importlib.util.spec_from_file_location("admin_run_reports_for_target_map", RUN_REPORTS_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load run_reports.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_file(path: Path, text: str = "x\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fake_config() -> dict[str, object]:
    return {
        "config_id": "admin-checks",
        "version": 1,
        "source": {"owner": "tests"},
        "scopes": {
            "admin": {"label": "Admin", "include": ["admin-app/"], "exclude": []},
            "analytics": {"label": "Analytics", "include": ["analytics-app/"], "exclude": []},
            "docs-viewer": {"label": "Docs Viewer", "include": ["docs-viewer/", "site/docs-viewer/"], "exclude": ["docs-viewer/generated/"]},
            "public-site": {"label": "Public Site", "include": ["works/"], "exclude": []},
            "studio": {"label": "Studio", "include": ["studio/"], "exclude": []},
            "all": {"label": "All", "include": ["admin-app/", "docs-viewer/", "works/"], "exclude": []},
        },
        "families": {
            "runtime-js": {
                "label": "Runtime JavaScript",
                "include": ["site/docs-viewer/runtime/js/", "docs-viewer/runtime/js/", "docs-viewer/shared/"],
            },
            "services": {"label": "Services", "include": ["docs-viewer/services/", "docs-viewer/shared/"]},
            "config": {"label": "Config", "include": ["docs-viewer/config/"]},
        },
        "areas": {
            "search": {
                "label": "Search",
                "include": ["site/docs-viewer/runtime/js/shared/docs-viewer-search.js", "docs-viewer/services/docs_management_search.py"],
                "shared": ["site/docs-viewer/runtime/js/shared/docs-viewer-shared.js"],
                "routes": ["/library/"],
            },
            "management": {
                "label": "Management",
                "include": [
                    "docs-viewer/runtime/js/management/docs-viewer-management.js",
                    "docs-viewer/runtime/js/management/docs-viewer-management-search.js",
                    "docs-viewer/services/docs_management_search.py",
                    "docs-viewer/services/orphan_docs_management.py",
                ],
                "shared": ["site/docs-viewer/runtime/js/shared/docs-viewer-shared.js"],
                "routes": ["/docs/"],
            },
            "docs-build": {
                "label": "Docs build",
                "include": ["docs-viewer/build/", "docs-viewer/missing-build.py"],
                "shared": [],
            },
        },
        "routes": {
            "/library/": {
                "label": "Library",
                "path": "/library/",
                "status": "mapped",
                "include": ["site/docs-viewer/runtime/js/shared/docs-viewer-search.js", "docs-viewer/services/docs_management_search.py"],
                "shared": ["site/docs-viewer/runtime/js/shared/docs-viewer-shared.js"],
                "areas": ["search"],
            },
            "/docs/": {
                "label": "Docs",
                "path": "/docs/",
                "status": "mapped",
                "include": [
                    "docs-viewer/runtime/js/management/docs-viewer-management.js",
                    "docs-viewer/runtime/js/management/docs-viewer-management-search.js",
                    "docs-viewer/services/docs_management_search.py",
                ],
                "shared": ["site/docs-viewer/runtime/js/shared/docs-viewer-shared.js"],
                "areas": ["management"],
            },
        },
        "reports": {
            "target-map": {
                "label": "Target Map",
                "script": "admin-app/checks/reports/target_map.py",
                "description": "Target ownership, shared dependency, and boundary-crossing evidence.",
                "default_options": {"limit": 20, "pattern_limit": 20},
                "allowed_options": {
                    "limit": {"type": "integer", "minimum": 1, "maximum": 500},
                    "pattern_limit": {"type": "integer", "minimum": 1, "maximum": 500},
                },
            }
        },
    }


def fake_manifest(*, limit: int = 20, pattern_limit: int = 20, families: list[str] | None = None) -> dict[str, object]:
    return {
        "run_id": "pytest-run",
        "targets": {
            "scope": "docs-viewer",
            "families": families or [],
            "areas": [],
            "routes": [],
        },
        "reports": [
            {
                "report_id": "target-map",
                "options": {
                    "limit": limit,
                    "pattern_limit": pattern_limit,
                },
            }
        ],
    }


def make_fake_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    write_file(repo / "site" / "docs-viewer" / "runtime" / "js" / "shared" / "docs-viewer-search.js")
    write_file(repo / "docs-viewer" / "runtime" / "js" / "management" / "docs-viewer-management.js")
    write_file(repo / "docs-viewer" / "runtime" / "js" / "management" / "docs-viewer-management-search.js")
    write_file(repo / "site" / "docs-viewer" / "runtime" / "js" / "shared" / "docs-viewer-shared.js")
    write_file(repo / "docs-viewer" / "shared" / "bridge.js")
    write_file(repo / "docs-viewer" / "services" / "docs_management_search.py")
    write_file(repo / "docs-viewer" / "services" / "orphan_docs_management.py")
    write_file(repo / "docs-viewer" / "config" / "docs-viewer-config.json", "{}\n")
    write_file(repo / "docs-viewer" / "unmapped.txt")
    write_file(repo / "docs-viewer" / "generated" / "index.json", "{}\n")
    for index in range(100):
        write_file(repo / "site" / "docs-viewer" / "runtime" / "js" / "shared" / f"module-{index:03}.js")
    return repo


def test_target_map_report_metrics_boundary_flags_and_patterns(tmp_path: Path) -> None:
    repo = make_fake_repo(tmp_path)
    report_module = load_target_map_report_module()

    report = report_module.build_report(
        config=fake_config(),
        manifest=fake_manifest(),
        report_id="target-map",
        repo_root=repo,
    )

    by_path = {row["path"]: row for row in report["files"]}
    assert report["schema_version"] == "admin_checks_target_map_report_v1"
    assert report["totals"]["files"] == 109
    assert report["totals"]["unclassified_files"] == 1
    assert report["totals"]["multi_family_files"] == 1
    assert report["totals"]["cross_area_files"] == 2
    assert report["totals"]["cross_route_files"] == 2
    assert report["totals"]["shared_dependency_files"] == 1
    assert report["totals"]["stale_patterns"] >= 1
    assert report["totals"]["broad_patterns"] >= 1
    assert "unclassified-family" in by_path["docs-viewer/unmapped.txt"]["boundary_flags"]
    assert "multi-family" in by_path["docs-viewer/shared/bridge.js"]["boundary_flags"]
    assert "cross-area" in by_path["docs-viewer/services/docs_management_search.py"]["boundary_flags"]
    assert "cross-route" in by_path["docs-viewer/services/docs_management_search.py"]["boundary_flags"]
    assert "route-service" in by_path["docs-viewer/services/docs_management_search.py"]["boundary_flags"]
    assert "shared-dependency" in by_path["site/docs-viewer/runtime/js/shared/docs-viewer-shared.js"]["boundary_flags"]
    assert "likely-unmapped-route" in by_path["docs-viewer/services/orphan_docs_management.py"]["boundary_flags"]
    assert report["shared_dependencies"][0]["path"] == "site/docs-viewer/runtime/js/shared/docs-viewer-shared.js"
    assert report["shared_dependencies"][0]["target_count"] == 4
    assert any(pattern["status"] == "stale" for pattern in report["patterns"])
    assert any(pattern["status"] == "broad" for pattern in report["patterns"])


def test_target_map_report_respects_family_filters(tmp_path: Path) -> None:
    repo = make_fake_repo(tmp_path)
    report_module = load_target_map_report_module()

    report = report_module.build_report(
        config=fake_config(),
        manifest=fake_manifest(families=["services"]),
        report_id="target-map",
        repo_root=repo,
    )

    paths = {row["path"] for row in report["files"]}
    assert paths == {
        "docs-viewer/services/docs_management_search.py",
        "docs-viewer/services/orphan_docs_management.py",
        "docs-viewer/shared/bridge.js",
    }
    assert report["target_counts"]["families"]["services"] == 3


def test_target_map_report_markdown_and_artifact_shape(tmp_path: Path) -> None:
    repo = make_fake_repo(tmp_path)
    report_module = load_target_map_report_module()
    report = report_module.build_report(
        config=fake_config(),
        manifest=fake_manifest(limit=1, pattern_limit=1),
        report_id="target-map",
        repo_root=repo,
    )

    markdown = report_module.render_markdown(report)
    output_dir = repo / "var" / "admin" / "checks" / "pytest-run" / "target-map"
    json_path, md_path = report_module.write_outputs(report, markdown, output_dir)

    assert "# Target Map Report" in markdown
    assert "## Review Questions" in markdown
    assert "## Shared Dependencies" in markdown
    assert "## Boundary Findings" in markdown
    assert "## Pattern Findings" in markdown
    assert "```text" in markdown
    assert "| path |" not in markdown
    assert "| status |" not in markdown
    assert "Showing 1 of" in markdown
    assert json_path.name == "report.json"
    assert md_path.name == "report.md"
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["report_id"] == "target-map"
    assert "files" in payload
    assert "patterns" in payload
    assert md_path.read_text(encoding="utf-8").startswith("# Target Map Report\n")


def test_target_map_report_runs_through_orchestrator(tmp_path: Path) -> None:
    repo = make_fake_repo(tmp_path)
    shutil.copytree(REPO_ROOT / "admin-app" / "checks", repo / "admin-app" / "checks", dirs_exist_ok=True)
    write_json(repo / "admin-app" / "checks" / "config" / "admin-checks.json", fake_config())
    runner = load_run_reports_module()

    result = runner.run_request(
        {
            "scope": "docs-viewer",
            "reports": ["target-map"],
            "options": {"target-map": {"limit": 5, "pattern_limit": 5}},
            "write": True,
        },
        repo_root=repo,
        run_id="pytest-run",
        argv=["run_reports.py"],
    )

    assert result["mode"] == "write"
    assert result["summary"]["status"] == "passed"
    assert "report_csv" not in result["summary"]["reports"][0]["artifacts"]
    run_dir = repo / "var" / "admin" / "checks" / "pytest-run"
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert "report_csv" not in manifest["reports"][0]["artifacts"]
    assert (run_dir / "target-map" / "report.json").is_file()
    assert (run_dir / "target-map" / "report.md").is_file()
    assert not (run_dir / "target-map" / "report.csv").exists()
