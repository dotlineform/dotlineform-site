#!/usr/bin/env python3
"""Focused checks for Admin audit, risk, and activity ownership."""

from __future__ import annotations

import json
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

from admin_audit_api import audit_get_payload, audit_post_response  # noqa: E402
from admin_risk_api import append_risk_activity, risk_delete_response, risk_get_payload, risk_post_response  # noqa: E402
from studio.shared.python import studio_activity  # noqa: E402


def test_audit_api_routes_return_registry_and_validate_runs() -> None:
    health_payload = audit_get_payload(REPO_ROOT, "/health")
    audits_payload = audit_get_payload(REPO_ROOT, "/audits")

    assert health_payload["ok"] is True
    assert health_payload["service"] == "admin_audit_runner"
    assert "studio-ready-state" in health_payload["audits"]
    assert audits_payload["ok"] is True
    assert any(audit["audit_id"] == "studio-ready-state" for audit in audits_payload["audits"])

    with pytest.raises(ValueError, match="allowlisted"):
        audit_post_response(REPO_ROOT, "/audits/run", {"audit_id": "not-allowlisted"})


def test_risk_api_lists_producers_runs_and_reads_summary(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    run_dir = repo_root / "var" / "admin" / "risk" / "runs" / "sample-run"
    run_dir.mkdir(parents=True)
    (run_dir / "manifest.json").write_text(
        json.dumps({"run_id": "sample-run", "app": "docs-viewer", "area": "runtime", "created_at_utc": "2026-05-31T12:00:00Z"}),
        encoding="utf-8",
    )
    (run_dir / "summary.json").write_text(
        json.dumps({"run_id": "sample-run", "app": "docs-viewer", "area": "runtime", "status": "passed", "warnings": [], "evidence": [{"artifact": "summary.json"}]}),
        encoding="utf-8",
    )
    (run_dir / "summary.md").write_text("# Summary\n", encoding="utf-8")

    health = risk_get_payload(repo_root, "/health")
    producers = risk_get_payload(repo_root, "/producers")
    runs = risk_get_payload(repo_root, "/runs")
    summary = risk_get_payload(repo_root, "/runs/sample-run/summary")

    assert health["ok"] is True
    assert health["service"] == "admin_risk_evidence"
    assert health["runs_root"] == "var/admin/risk/runs"
    assert any(producer["producer_id"] == "runtime-checks" for producer in producers["producers"])
    assert runs["runs"][0]["run_id"] == "sample-run"
    assert runs["runs"][0]["summary_path"] == "var/admin/risk/runs/sample-run/summary.md"
    assert summary["summary"]["status"] == "passed"
    assert summary["summary_markdown"] == "# Summary\n"


def test_risk_api_validates_run_requests_without_command_passthrough() -> None:
    with pytest.raises(ValueError, match="allowlisted"):
        risk_post_response(REPO_ROOT, "/runs", {"app": "bad", "area": "runtime", "dry_run": True})
    with pytest.raises(ValueError, match="safe slug"):
        risk_post_response(REPO_ROOT, "/runs", {"app": "docs-viewer", "area": "../bad", "dry_run": True})
    with pytest.raises(ValueError, match="runtime profile"):
        risk_post_response(REPO_ROOT, "/runs", {"app": "docs-viewer", "area": "runtime", "runtime_profiles": ["not-allowed"], "dry_run": True})

    status, payload = risk_post_response(
        REPO_ROOT,
        "/runs",
        {"app": "docs-viewer", "area": "runtime", "run_id": "risk-api-dry-run", "dry_run": True},
    )

    assert status == HTTPStatus.OK
    assert payload["ok"] is True
    assert payload["dry_run"] is True
    assert "var/admin/risk/runs/risk-api-dry-run" in payload["stdout"]


def test_risk_api_deletes_run_snapshots_with_path_validation(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    run_dir = repo_root / "var" / "admin" / "risk" / "runs" / "sample-run"
    run_dir.mkdir(parents=True)
    (run_dir / "summary.json").write_text(
        json.dumps({"run_id": "sample-run", "app": "docs-viewer", "area": "runtime", "status": "passed"}),
        encoding="utf-8",
    )
    (run_dir / "summary.md").write_text("# Summary\n", encoding="utf-8")

    status, payload = risk_delete_response(repo_root, "/runs/sample-run")

    assert status == HTTPStatus.OK
    assert payload["ok"] is True
    assert payload["status"] == "deleted"
    assert payload["run_id"] == "sample-run"
    assert payload["deleted_path"] == "var/admin/risk/runs/sample-run"
    assert not run_dir.exists()

    with pytest.raises(FileNotFoundError, match="does not exist"):
        risk_delete_response(repo_root, "/runs/sample-run")
    with pytest.raises(ValueError, match="safe slug"):
        risk_delete_response(repo_root, "/runs/../bad")


def test_admin_activity_append_uses_contract_context(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    contract_target = repo_root / "studio" / "data" / "config" / "runtime" / "activity-contract.json"
    contract_target.parent.mkdir(parents=True)
    contract_target.write_text(
        (REPO_ROOT / "studio" / "data" / "config" / "runtime" / "activity-contract.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    run_id = "risk-api-activity-test"
    response = {
        "ok": True,
        "status": "passed",
        "app": "docs-viewer",
        "area": "runtime",
        "run_id": run_id,
        "summary_path": f"var/admin/risk/runs/{run_id}/summary.md",
    }

    append_risk_activity(
        repo_root,
        {
            "activity_context": {
                "page_id": "admin-risk",
                "action_id": "run-risk-evidence",
                "route": "/admin/risk/",
                "control_id": "studioRiskRun",
                "control_selector": "#studioRiskRun",
                "correlation_id": f"pytest:{run_id}",
                "run_id": run_id,
            },
        },
        response,
        "2026-05-31T12:00:00Z",
    )

    activity_path = repo_root / studio_activity.FEED_REL_PATH
    activity_payload = json.loads(activity_path.read_text(encoding="utf-8"))

    assert response["activity_log"]["written_count"] == 1
    assert activity_path == repo_root / "var" / "admin" / "activity" / "activity_log.json"
    assert activity_payload["header"]["schema"] == "admin_activity_log_v1"
    assert activity_payload["entries"][0]["page_id"] == "admin-risk"
    assert activity_payload["entries"][0]["script_purpose_id"] == "generate-report"
