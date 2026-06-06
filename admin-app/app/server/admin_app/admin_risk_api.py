"""Local Admin app adapter for risk evidence runs."""

from __future__ import annotations

import datetime as dt
import json
import re
import shutil
import subprocess
import sys
import time
from http import HTTPStatus
from pathlib import Path
from typing import Any

from studio.shared.python.studio_activity import (
    append_studio_activity,
    normalize_activity_context_from_contract,
    studio_activity_entry,
)


RISK_RUNS_REL_DIR = Path("var/admin/risk/runs")
RISK_RUN_API_PATH = "/admin/api/risk/runs"
VALID_APPS = ("public-site", "studio", "analytics", "docs-viewer", "all")
VALID_RUNTIME_PROFILES = ("studio-smoke", "ui-catalogue-smoke", "analytics-smoke", "docs-viewer-smoke")
VALID_SLUG = re.compile(r"^[A-Za-z0-9_.-]+$")


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def risk_get_payload(repo_root: Path, api_path: str, query: dict[str, list[str]] | None = None) -> dict[str, Any]:
    query = query or {}
    if api_path == "/health":
        return risk_health_payload(repo_root)
    if api_path == "/producers":
        return risk_producers_payload()
    if api_path == "/runs":
        limit = parse_limit(query.get("limit", ["20"])[0])
        return risk_runs_payload(repo_root, limit=limit)
    if api_path.startswith("/runs/") and api_path.endswith("/summary"):
        run_id = api_path.removeprefix("/runs/").removesuffix("/summary").strip("/")
        return risk_run_summary_payload(repo_root, run_id)
    raise FileNotFoundError(f"Unknown risk API route: {api_path}")


def risk_post_response(repo_root: Path, api_path: str, body: dict[str, Any]) -> tuple[HTTPStatus, dict[str, Any]]:
    if api_path != "/runs":
        raise FileNotFoundError(f"Unknown risk API route: {api_path}")
    return HTTPStatus.OK, run_risk_evidence_payload(repo_root, body)


def risk_delete_response(repo_root: Path, api_path: str) -> tuple[HTTPStatus, dict[str, Any]]:
    if not api_path.startswith("/runs/"):
        raise FileNotFoundError(f"Unknown risk API route: {api_path}")
    run_id = api_path.removeprefix("/runs/").strip("/")
    if not run_id:
        raise FileNotFoundError(f"Unknown risk API route: {api_path}")
    return HTTPStatus.OK, delete_risk_run_payload(repo_root, run_id)


def risk_health_payload(repo_root: Path) -> dict[str, Any]:
    runs_root = repo_root / RISK_RUNS_REL_DIR
    return {
        "ok": True,
        "service": "admin_risk_evidence",
        "runs_root": str(RISK_RUNS_REL_DIR),
        "runs_root_exists": runs_root.exists(),
        "apps": list(VALID_APPS),
        "time_utc": utc_now(),
    }


def risk_producers_payload() -> dict[str, Any]:
    return {
        "ok": True,
        "apps": list(VALID_APPS),
        "runtime_profiles": list(VALID_RUNTIME_PROFILES),
        "producers": [
            {
                "producer_id": "static-metrics",
                "label": "Static metrics",
                "description": "File counts, line counts, import/export scan, and ownership-family totals.",
                "default": True,
            },
            {
                "producer_id": "static-searches",
                "label": "Static searches",
                "description": "Configured risk search patterns for stale paths, local URLs, broad browser state, maintenance fixtures, and related smells.",
                "default": True,
            },
            {
                "producer_id": "generated-payloads",
                "label": "Generated payloads",
                "description": "JSON payload counts, sizes, and schema shape observations.",
                "default": True,
            },
            {
                "producer_id": "script-family-inventory",
                "label": "Script family inventory",
                "description": "Python/Ruby file counts, line counts, family totals, and largest-file observations.",
                "default": True,
            },
            {
                "producer_id": "git-history",
                "label": "Git touch counts",
                "description": "Recent edit concentration grouped by family and file.",
                "default": True,
            },
            {
                "producer_id": "javascript-inventory-guardrail",
                "label": "JavaScript inventory guardrail",
                "description": "Transition evidence from the existing JavaScript inventory guardrail.",
                "default": True,
            },
            {
                "producer_id": "runtime-checks",
                "label": "Runtime checks",
                "description": "Optional allowlisted run-check profiles.",
                "default": False,
            },
        ],
        "time_utc": utc_now(),
    }


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


def risk_runs_payload(repo_root: Path, *, limit: int = 20) -> dict[str, Any]:
    runs_root = repo_root / RISK_RUNS_REL_DIR
    runs: list[dict[str, Any]] = []
    if runs_root.exists():
        for run_dir in sorted((path for path in runs_root.iterdir() if path.is_dir()), key=lambda path: path.stat().st_mtime, reverse=True)[:limit]:
            runs.append(compact_run_payload(repo_root, run_dir))
    return {
        "ok": True,
        "runs_root": str(RISK_RUNS_REL_DIR),
        "runs": runs,
        "time_utc": utc_now(),
    }


def compact_run_payload(repo_root: Path, run_dir: Path) -> dict[str, Any]:
    manifest = read_json_object(run_dir / "manifest.json")
    summary = read_json_object(run_dir / "summary.json")
    run_id = str(summary.get("run_id") or manifest.get("run_id") or run_dir.name)
    return {
        "run_id": run_id,
        "app": summary.get("app") or manifest.get("app"),
        "area": summary.get("area") or manifest.get("area"),
        "status": summary.get("status"),
        "created_at_utc": manifest.get("created_at_utc"),
        "run_dir": repo_relative(run_dir, repo_root),
        "summary_path": repo_relative(run_dir / "summary.md", repo_root) if (run_dir / "summary.md").exists() else None,
        "warning_count": len(summary.get("warnings") or []) if isinstance(summary.get("warnings"), list) else 0,
        "evidence_count": len(summary.get("evidence") or []) if isinstance(summary.get("evidence"), list) else 0,
    }


def risk_run_summary_payload(repo_root: Path, run_id: str) -> dict[str, Any]:
    safe_run_id, run_dir = validated_run_dir(repo_root, run_id)
    if not run_dir.is_dir():
        raise FileNotFoundError(f"Risk evidence run does not exist: {safe_run_id}")

    summary_json_path = run_dir / "summary.json"
    summary_md_path = run_dir / "summary.md"
    if not summary_json_path.exists() and not summary_md_path.exists():
        raise FileNotFoundError(f"Risk evidence run has no summary: {safe_run_id}")
    return {
        "ok": True,
        "run": compact_run_payload(repo_root, run_dir),
        "summary": read_json_object(summary_json_path) if summary_json_path.exists() else None,
        "summary_markdown": summary_md_path.read_text(encoding="utf-8") if summary_md_path.exists() else "",
        "summary_path": repo_relative(summary_md_path, repo_root) if summary_md_path.exists() else None,
        "time_utc": utc_now(),
    }


def delete_risk_run_payload(repo_root: Path, run_id: str) -> dict[str, Any]:
    safe_run_id, run_dir = validated_run_dir(repo_root, run_id)
    if run_dir.is_symlink() or not run_dir.is_dir():
        raise FileNotFoundError(f"Risk evidence run does not exist: {safe_run_id}")
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


def run_risk_evidence_payload(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    app = str(body.get("app") or "").strip()
    if app not in VALID_APPS:
        raise ValueError("app is not allowlisted")
    area = validate_slug(str(body.get("area") or ""), "area")
    run_id = str(body.get("run_id") or "").strip()
    if run_id:
        run_id = validate_slug(run_id, "run_id")

    dry_run = bool(body.get("dry_run"))
    include_runtime = bool(body.get("include_runtime"))
    include_lighthouse = bool(body.get("include_lighthouse"))
    runtime_profiles = normalize_runtime_profiles(body.get("runtime_profiles"))

    script_path = repo_root / "studio" / "checks" / "risk_evidence_pack.py"
    argv = [
        sys.executable,
        str(script_path),
        "--app",
        app,
        "--area",
        area,
        "--runs-root",
        str(repo_root / RISK_RUNS_REL_DIR),
    ]
    if run_id:
        argv.extend(["--run-id", run_id])
    if include_runtime:
        argv.append("--include-runtime")
    if include_lighthouse:
        argv.append("--include-lighthouse")
    for profile in runtime_profiles:
        argv.extend(["--runtime-profile", profile])
    if not dry_run:
        argv.append("--write")

    started_at = utc_now()
    started = time.monotonic()
    result = subprocess.run(
        argv,
        cwd=repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    finished_at = utc_now()
    duration = round(time.monotonic() - started, 3)

    response: dict[str, Any] = {
        "ok": result.returncode == 0,
        "status": "passed" if result.returncode == 0 else "failed",
        "exit_code": result.returncode,
        "app": app,
        "area": area,
        "dry_run": dry_run,
        "include_runtime": include_runtime,
        "include_lighthouse": include_lighthouse,
        "runtime_profiles": runtime_profiles,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_seconds": duration,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
    summary_path = extract_summary_path(result.stdout)
    if summary_path:
        response["summary_path"] = summary_path
        run_id_from_path = Path(summary_path).parent.name
        if run_id_from_path:
            response["run_id"] = run_id_from_path
    elif run_id:
        response["run_id"] = run_id
    if response["ok"] and not dry_run:
        append_risk_activity(repo_root, body, response, finished_at)
    return response


def append_risk_activity(repo_root: Path, body: dict[str, Any], response: dict[str, Any], finished_at: str) -> None:
    run_id = str(response.get("run_id") or "").strip()
    if not run_id:
        return
    try:
        activity_context = normalize_activity_context_from_contract(
            repo_root,
            body.get("activity_context"),
            endpoint=RISK_RUN_API_PATH,
            record_id=run_id,
            record_id_field="run_id",
        )
        if not activity_context:
            return
        summary_path = str(response.get("summary_path") or "").strip()
        status = "warning" if response.get("status") not in {"passed", "completed"} else "completed"
        append_studio_activity(
            repo_root,
            studio_activity_entry(
                activity_context,
                script_purpose_id="generate-report",
                now_utc=finished_at,
                status=status,
                record_groups={"files": [summary_path] if summary_path else [], "docs": [run_id]},
                detail_items=[
                    f"Ran risk evidence pack for {response.get('app')} / {response.get('area')}.",
                    f"Status: {response.get('status')}; run id: {run_id}.",
                    f"Summary: {summary_path or 'not available'}.",
                ],
                source_refs=[{"kind": "report", "path": summary_path}] if summary_path else [],
            ),
        )
        response["activity_log"] = {"written_count": 1}
    except Exception as exc:  # noqa: BLE001
        response["activity_log"] = {"written_count": 0, "error": str(exc)}


def normalize_runtime_profiles(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        profiles = [value]
    elif isinstance(value, list):
        profiles = [str(item) for item in value]
    else:
        raise ValueError("runtime_profiles must be a string or list")
    normalized: list[str] = []
    for profile in profiles:
        profile = profile.strip()
        if not profile:
            continue
        if profile not in VALID_RUNTIME_PROFILES:
            raise ValueError("runtime profile is not allowlisted")
        if profile not in normalized:
            normalized.append(profile)
    return normalized


def validated_run_dir(repo_root: Path, run_id: str) -> tuple[str, Path]:
    safe_run_id = validate_slug(run_id, "run_id")
    runs_root = repo_root / RISK_RUNS_REL_DIR
    resolved_runs_root = runs_root.resolve()
    run_dir = runs_root / safe_run_id
    resolved_run_dir = run_dir.resolve()
    try:
        resolved_run_dir.relative_to(resolved_runs_root)
    except ValueError as error:
        raise ValueError("run_id resolved outside the risk runs directory") from error
    return safe_run_id, run_dir


def extract_summary_path(stdout: str) -> str | None:
    for line in stdout.splitlines():
        text = line.strip()
        if text.startswith("summary: "):
            return text.removeprefix("summary: ").strip()
    return None


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
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)
