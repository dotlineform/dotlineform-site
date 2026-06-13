"""Local Admin app adapter for Admin checks runs."""

from __future__ import annotations

import datetime as dt
import json
import re
import shutil
import sys
from http import HTTPStatus
from pathlib import Path
from typing import Any, Mapping


_BOOTSTRAP_START = Path(__file__).resolve()
for _candidate in (_BOOTSTRAP_START.parent, *_BOOTSTRAP_START.parents):
    if (_candidate / "site-tools" / "config" / "site-tools.json").exists():
        if str(_candidate) not in sys.path:
            sys.path.insert(0, str(_candidate))
        break

from studio.shared.python.studio_python_paths import ensure_studio_python_paths


REPO_ROOT = ensure_studio_python_paths(__file__)
CHECKS_DIR = REPO_ROOT / "admin-app" / "checks"
if str(CHECKS_DIR) not in sys.path:
    sys.path.insert(0, str(CHECKS_DIR))

from admin_checks_config import DEFAULT_CONFIG_PATH, ChecksConfigError, load_checks_config  # noqa: E402
from run_reports import DEFAULT_RUNS_ROOT, run_request  # noqa: E402


CHECKS_RUNS_REL_DIR = DEFAULT_RUNS_ROOT
VALID_SLUG = re.compile(r"^[A-Za-z0-9_.-]+$")
VALID_BROWSER_RUN_REQUEST_KEYS = {"scope", "families", "areas", "routes", "reports", "write"}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def checks_get_payload(repo_root: Path, api_path: str, query: dict[str, list[str]] | None = None) -> dict[str, Any]:
    query = query or {}
    if api_path == "/health":
        return checks_health_payload(repo_root)
    if api_path == "/reports":
        return checks_reports_payload(repo_root)
    if api_path == "/runs":
        limit = parse_limit(query.get("limit", ["20"])[0])
        return checks_runs_payload(repo_root, limit=limit)
    if api_path.startswith("/runs/") and api_path.endswith("/summary"):
        run_id = api_path.removeprefix("/runs/").removesuffix("/summary").strip("/")
        return checks_run_summary_payload(repo_root, run_id)
    if api_path.startswith("/runs/") and "/reports/" in api_path:
        rest = api_path.removeprefix("/runs/").strip("/")
        run_id, report_id = rest.split("/reports/", 1)
        return checks_report_payload(repo_root, run_id, report_id.strip("/"))
    raise FileNotFoundError(f"Unknown checks API route: {api_path}")


def checks_post_response(repo_root: Path, api_path: str, body: Mapping[str, Any]) -> tuple[HTTPStatus, dict[str, Any]]:
    if api_path != "/runs":
        raise FileNotFoundError(f"Unknown checks API route: {api_path}")
    result = run_request(normalized_browser_run_request(body), config_path=DEFAULT_CONFIG_PATH, repo_root=repo_root, argv=["admin-app/checks/run_reports.py"])
    status = "dry-run" if result["mode"] == "dry-run" else str(result["summary"].get("status"))
    return HTTPStatus.OK, {"ok": True, "status": status, **result, "time_utc": utc_now()}


def normalized_browser_run_request(body: Mapping[str, Any]) -> dict[str, Any]:
    unknown = sorted(set(body).difference(VALID_BROWSER_RUN_REQUEST_KEYS))
    if unknown:
        if "options" in unknown:
            raise ValueError("report options are configured in admin-app/checks/config/admin-checks-reports.json")
        raise ValueError(f"request contains unknown keys: {', '.join(unknown)}")
    return {
        "scope": body.get("scope"),
        "families": body.get("families", []),
        "areas": body.get("areas", []),
        "routes": body.get("routes", []),
        "reports": body.get("reports", []),
        "write": body.get("write", False),
    }


def checks_delete_response(repo_root: Path, api_path: str) -> tuple[HTTPStatus, dict[str, Any]]:
    if not api_path.startswith("/runs/"):
        raise FileNotFoundError(f"Unknown checks API route: {api_path}")
    run_id = api_path.removeprefix("/runs/").strip("/")
    if not run_id:
        raise FileNotFoundError(f"Unknown checks API route: {api_path}")
    return HTTPStatus.OK, delete_checks_run_payload(repo_root, run_id)


def checks_health_payload(repo_root: Path) -> dict[str, Any]:
    runs_root = repo_root / CHECKS_RUNS_REL_DIR
    config = load_checks_config(repo_root=repo_root)
    return {
        "ok": True,
        "service": "admin_checks",
        "config_id": config["config_id"],
        "config_version": config["version"],
        "runs_root": CHECKS_RUNS_REL_DIR.as_posix(),
        "runs_root_exists": runs_root.exists(),
        "reports": sorted(config["reports"]),
        "time_utc": utc_now(),
    }


def checks_reports_payload(repo_root: Path) -> dict[str, Any]:
    config = load_checks_config(repo_root=repo_root)
    return {
        "ok": True,
        "config_id": config["config_id"],
        "version": config["version"],
        "scopes": project_targets(config["scopes"]),
        "families": project_targets(config["families"]),
        "areas": project_targets(config["areas"], include_fields=("label", "routes")),
        "routes": project_targets(config["routes"], include_fields=("label", "path", "status", "areas")),
        "reports": project_reports(config["reports"]),
        "time_utc": utc_now(),
    }


def project_targets(targets: Mapping[str, Any], include_fields: tuple[str, ...] = ("label",)) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for target_id, target in sorted(targets.items()):
        row: dict[str, Any] = {"id": target_id}
        if isinstance(target, dict):
            for field in include_fields:
                if field in target:
                    row[field] = target[field]
        out.append(row)
    return out


def project_reports(reports: Mapping[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for report_id, report in sorted(reports.items()):
        if not isinstance(report, dict):
            continue
        out.append(
            {
                "id": report_id,
                "label": report.get("label"),
                "description": report.get("description"),
            }
        )
    return out


def parse_limit(value: str) -> int:
    try:
        limit = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError("limit must be an integer") from error
    return max(1, min(limit, 100))


def validate_slug(value: str, field: str) -> str:
    slug = value.strip()
    if not slug:
        raise ValueError(f"{field} is required")
    if "/" in slug or "\\" in slug or ".." in slug or not VALID_SLUG.match(slug):
        raise ValueError(f"{field} must be a safe slug")
    return slug


def validated_run_dir(repo_root: Path, run_id: str) -> tuple[str, Path]:
    safe_run_id = validate_slug(run_id, "run_id")
    runs_root = repo_root / CHECKS_RUNS_REL_DIR
    resolved_runs_root = runs_root.resolve()
    run_dir = runs_root / safe_run_id
    resolved_run_dir = run_dir.resolve()
    try:
        resolved_run_dir.relative_to(resolved_runs_root)
    except ValueError as error:
        raise ValueError("run_id resolved outside the checks runs directory") from error
    return safe_run_id, run_dir


def validated_report_dir(repo_root: Path, run_id: str, report_id: str) -> tuple[str, str, Path]:
    safe_run_id, run_dir = validated_run_dir(repo_root, run_id)
    safe_report_id = validate_slug(report_id, "report_id")
    config = load_checks_config(repo_root=repo_root)
    if safe_report_id not in config["reports"]:
        raise ValueError("report_id is not allowlisted")
    report_dir = run_dir / safe_report_id
    resolved_run_dir = run_dir.resolve()
    resolved_report_dir = report_dir.resolve()
    try:
        resolved_report_dir.relative_to(resolved_run_dir)
    except ValueError as error:
        raise ValueError("report_id resolved outside the checks run directory") from error
    return safe_run_id, safe_report_id, report_dir


def checks_runs_payload(repo_root: Path, *, limit: int = 20) -> dict[str, Any]:
    runs_root = repo_root / CHECKS_RUNS_REL_DIR
    runs: list[dict[str, Any]] = []
    if runs_root.exists():
        candidates = [path for path in runs_root.iterdir() if path.is_dir() and (path / "run-summary.json").exists()]
        for run_dir in sorted(candidates, key=lambda path: path.stat().st_mtime, reverse=True)[:limit]:
            runs.append(compact_run_payload(repo_root, run_dir))
    return {
        "ok": True,
        "runs_root": CHECKS_RUNS_REL_DIR.as_posix(),
        "runs": runs,
        "time_utc": utc_now(),
    }


def compact_run_payload(repo_root: Path, run_dir: Path) -> dict[str, Any]:
    manifest = read_json_object(run_dir / "manifest.json")
    summary = read_json_object(run_dir / "run-summary.json")
    run_id = str(summary.get("run_id") or manifest.get("run_id") or run_dir.name)
    reports = summary.get("reports") if isinstance(summary.get("reports"), list) else []
    report_ids = [
        str(report["report_id"])
        for report in reports
        if isinstance(report, dict) and isinstance(report.get("report_id"), str) and report["report_id"]
    ]
    targets = summary.get("targets") or manifest.get("targets") or {}
    if not isinstance(targets, dict):
        targets = {}
    return {
        "run_id": run_id,
        "status": summary.get("status") or manifest.get("status"),
        "created_at": summary.get("created_at") or manifest.get("created_at"),
        "finished_at": summary.get("finished_at") or manifest.get("finished_at"),
        "scope": targets.get("scope"),
        "run_dir": repo_relative(run_dir, repo_root),
        "summary_path": repo_relative(run_dir / "run-summary.md", repo_root) if (run_dir / "run-summary.md").exists() else None,
        "report_ids": report_ids,
        "report_count": len(reports),
        "failed_report_count": sum(1 for report in reports if isinstance(report, dict) and report.get("status") != "passed"),
    }


def checks_run_summary_payload(repo_root: Path, run_id: str) -> dict[str, Any]:
    safe_run_id, run_dir = validated_run_dir(repo_root, run_id)
    if not run_dir.is_dir():
        raise FileNotFoundError(f"Checks run does not exist: {safe_run_id}")

    summary_json_path = run_dir / "run-summary.json"
    summary_md_path = run_dir / "run-summary.md"
    if not summary_json_path.exists() and not summary_md_path.exists():
        raise FileNotFoundError(f"Checks run has no summary: {safe_run_id}")
    return {
        "ok": True,
        "run": compact_run_payload(repo_root, run_dir),
        "summary": read_json_object(summary_json_path) if summary_json_path.exists() else None,
        "summary_markdown": summary_md_path.read_text(encoding="utf-8") if summary_md_path.exists() else "",
        "summary_path": repo_relative(summary_md_path, repo_root) if summary_md_path.exists() else None,
        "time_utc": utc_now(),
    }


def checks_report_payload(repo_root: Path, run_id: str, report_id: str) -> dict[str, Any]:
    safe_run_id, safe_report_id, report_dir = validated_report_dir(repo_root, run_id, report_id)
    if not report_dir.is_dir():
        raise FileNotFoundError(f"Checks report does not exist: {safe_run_id}/{safe_report_id}")

    report_json_path = report_dir / "report.json"
    report_md_path = report_dir / "report.md"
    report_csv_path = report_dir / "report.csv"
    if not report_json_path.exists() and not report_md_path.exists():
        raise FileNotFoundError(f"Checks report has no artifacts: {safe_run_id}/{safe_report_id}")
    return {
        "ok": True,
        "run_id": safe_run_id,
        "report_id": safe_report_id,
        "report": read_json_object(report_json_path) if report_json_path.exists() else None,
        "report_markdown": report_md_path.read_text(encoding="utf-8") if report_md_path.exists() else "",
        "report_path": repo_relative(report_json_path, repo_root) if report_json_path.exists() else None,
        "report_markdown_path": repo_relative(report_md_path, repo_root) if report_md_path.exists() else None,
        "report_csv_path": repo_relative(report_csv_path, repo_root) if report_csv_path.exists() else None,
        "report_csv_exists": report_csv_path.exists(),
        "time_utc": utc_now(),
    }


def delete_checks_run_payload(repo_root: Path, run_id: str) -> dict[str, Any]:
    safe_run_id, run_dir = validated_run_dir(repo_root, run_id)
    if run_dir.is_symlink() or not run_dir.is_dir():
        raise FileNotFoundError(f"Checks run does not exist: {safe_run_id}")
    deleted_run = compact_run_payload(repo_root, run_dir)
    deleted_path = repo_relative(run_dir, repo_root)
    shutil.rmtree(run_dir)
    return {
        "ok": True,
        "status": "deleted",
        "run_id": safe_run_id,
        "deleted_path": deleted_path,
        "run": deleted_run,
        "time_utc": utc_now(),
    }


def read_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def repo_relative(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()
