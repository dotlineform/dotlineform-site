#!/usr/bin/env python3
"""Focused tests for the Admin checks report orchestrator."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
RUN_REPORTS_PATH = REPO_ROOT / "admin-app" / "checks" / "run_reports.py"
ADMIN_CHECKS_DIR = REPO_ROOT / "admin-app" / "checks"
sys.path.insert(0, str(ADMIN_CHECKS_DIR))


def load_run_reports_module():
    spec = importlib.util.spec_from_file_location("admin_run_reports", RUN_REPORTS_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load run_reports.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_fake_report(path: Path, *, exit_code: int = 0, write_artifacts: bool = True) -> None:
    artifact_block = """
output_dir.mkdir(parents=True, exist_ok=True)
(output_dir / "report.json").write_text(json.dumps({"ok": True, "report_id": args.report_id}) + "\\n", encoding="utf-8")
(output_dir / "report.md").write_text("# Fake Report\\n", encoding="utf-8")
""" if write_artifacts else ""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--config", required=True)
parser.add_argument("--run-manifest", required=True)
parser.add_argument("--report-id", required=True)
parser.add_argument("--output-dir", required=True)
args = parser.parse_args()
output_dir = Path(args.output_dir)
{artifact_block}
raise SystemExit({exit_code})
""",
        encoding="utf-8",
    )


def make_fake_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "docs-viewer" / "runtime" / "js").mkdir(parents=True)
    (repo / "docs-viewer" / "runtime" / "js" / "docs-viewer-search.js").write_text("const search = true;\n", encoding="utf-8")
    (repo / "docs-viewer" / "services").mkdir(parents=True)
    (repo / "docs-viewer" / "services" / "docs_management_routes.py").write_text("ROUTES = []\n", encoding="utf-8")
    write_fake_report(repo / "admin-app" / "checks" / "reports" / "success.py")
    write_fake_report(repo / "admin-app" / "checks" / "reports" / "failure.py", exit_code=7, write_artifacts=False)
    config = {
        "config_id": "admin-checks",
        "version": 1,
        "source": {"owner": "tests"},
        "scopes": {
            "admin": {"label": "Admin", "include": ["admin-app/"], "exclude": []},
            "analytics": {"label": "Analytics", "include": ["analytics-app/"], "exclude": []},
            "docs-viewer": {"label": "Docs Viewer", "include": ["docs-viewer/"], "exclude": []},
            "public-site": {"label": "Public Site", "include": ["works/"], "exclude": []},
            "studio": {"label": "Studio", "include": ["studio/"], "exclude": []},
            "all": {"label": "All", "include": ["admin-app/", "docs-viewer/", "works/"], "exclude": []},
        },
        "families": {
            "runtime-js": {"label": "Runtime JavaScript", "include": ["docs-viewer/runtime/js/"]},
            "services": {"label": "Services", "include": ["docs-viewer/services/"]},
            "public-route": {"label": "Public Routes", "include": ["works/"]},
        },
        "areas": {
            "search": {
                "label": "Search",
                "include": ["**/*search*"],
                "shared": [],
                "routes": ["/library/"],
            }
        },
        "routes": {
            "/library/": {
                "label": "Library",
                "path": "/library/",
                "status": "mapped",
                "include": ["docs-viewer/runtime/js/docs-viewer-search.js"],
                "shared": [],
                "areas": ["search"],
            },
            "/works/": {
                "label": "Works",
                "path": "/works/",
                "status": "inventory-only",
                "include": ["works/"],
                "shared": [],
                "areas": [],
            },
        },
        "reports": {
            "success": {
                "label": "Success",
                "script": "admin-app/checks/reports/success.py",
                "description": "Successful fake report.",
                "default_options": {"limit": 20},
                "allowed_options": {"limit": {"type": "integer", "minimum": 1, "maximum": 100}},
            },
            "failure": {
                "label": "Failure",
                "script": "admin-app/checks/reports/failure.py",
                "description": "Failing fake report.",
                "default_options": {},
                "allowed_options": {},
            },
        },
    }
    write_json(repo / "admin-app" / "checks" / "config" / "admin-checks.json", config)
    return repo


def valid_request(*, write: bool = False, reports: list[str] | None = None) -> dict[str, object]:
    return {
        "scope": "docs-viewer",
        "families": ["runtime-js"],
        "areas": ["search"],
        "routes": ["/library/"],
        "reports": reports or ["success"],
        "options": {"success": {"limit": 5}},
        "write": write,
    }


def test_run_reports_dry_run_resolves_plan_without_writing(tmp_path: Path) -> None:
    repo = make_fake_repo(tmp_path)
    runner = load_run_reports_module()

    result = runner.run_request(valid_request(), repo_root=repo)

    assert result["mode"] == "dry-run"
    plan = result["plan"]
    assert plan["targets"]["scope"] == "docs-viewer"
    assert plan["reports"][0]["options"] == {"limit": 5}
    assert plan["target_match_counts"]["files"] == 1
    assert not (repo / "var" / "admin" / "checks").exists()


def test_run_reports_write_run_preserves_success_and_failure_status(tmp_path: Path) -> None:
    repo = make_fake_repo(tmp_path)
    runner = load_run_reports_module()
    request = valid_request(write=True, reports=["success", "failure"])
    request["options"] = {"success": {"limit": 3}}

    result = runner.run_request(request, repo_root=repo, run_id="pytest-run", argv=["run_reports.py"])

    assert result["mode"] == "write"
    summary = result["summary"]
    run_dir = repo / "var" / "admin" / "checks" / "pytest-run"
    assert summary["status"] == "failed"
    assert summary["totals"] == {"reports": 2, "passed": 1, "failed": 1}
    assert (run_dir / "success" / "report.json").is_file()
    assert (run_dir / "success" / "report.md").is_file()
    assert (run_dir / "manifest.json").is_file()
    assert (run_dir / "commands.json").is_file()
    assert (run_dir / "run-summary.json").is_file()
    commands = json.loads((run_dir / "commands.json").read_text(encoding="utf-8"))
    failure = next(command for command in commands["commands"] if command.get("report_id") == "failure")
    assert failure["argv"][1] == "admin-app/checks/reports/failure.py"
    assert failure["status"] == "failed"


def test_run_reports_rejects_target_ids_that_do_not_resolve_in_scope(tmp_path: Path) -> None:
    repo = make_fake_repo(tmp_path)
    runner = load_run_reports_module()
    request = valid_request()
    request["families"] = ["public-route"]

    with pytest.raises(runner.ChecksConfigError, match="no files in scope docs-viewer"):
        runner.run_request(request, repo_root=repo)


def test_run_reports_rejects_inventory_only_routes(tmp_path: Path) -> None:
    repo = make_fake_repo(tmp_path)
    runner = load_run_reports_module()
    request = valid_request()
    request["routes"] = ["/works/"]

    with pytest.raises(runner.ChecksConfigError, match="inventory-only routes"):
        runner.run_request(request, repo_root=repo)
