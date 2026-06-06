"""Read-only Admin testing run summary API."""

from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path
from typing import Any


TEST_RUNS_REL_DIR = Path("var/admin/test-runs")
VALID_SLUG = re.compile(r"^[A-Za-z0-9_.-]+$")


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def testing_get_payload(repo_root: Path, api_path: str, query: dict[str, list[str]] | None = None) -> dict[str, Any]:
    query = query or {}
    if api_path == "/health":
        runs_root = repo_root / TEST_RUNS_REL_DIR
        return {
            "ok": True,
            "service": "admin_testing",
            "runs_root": str(TEST_RUNS_REL_DIR),
            "runs_root_exists": runs_root.exists(),
            "time_utc": utc_now(),
        }
    if api_path == "/runs":
        limit = parse_limit(query.get("limit", ["20"])[0])
        return testing_runs_payload(repo_root, limit=limit)
    if api_path.startswith("/runs/") and api_path.endswith("/summary"):
        run_id = api_path.removeprefix("/runs/").removesuffix("/summary").strip("/")
        return testing_run_summary_payload(repo_root, run_id)
    raise FileNotFoundError(f"Unknown testing API route: {api_path}")


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


def testing_runs_payload(repo_root: Path, *, limit: int = 20) -> dict[str, Any]:
    runs_root = repo_root / TEST_RUNS_REL_DIR
    runs: list[dict[str, Any]] = []
    if runs_root.exists():
        run_dirs = [path for path in runs_root.iterdir() if path.is_dir()]
        for run_dir in sorted(run_dirs, key=lambda path: path.stat().st_mtime, reverse=True)[:limit]:
            runs.append(compact_run_payload(repo_root, run_dir))
    return {
        "ok": True,
        "runs_root": str(TEST_RUNS_REL_DIR),
        "runs": runs,
        "time_utc": utc_now(),
    }


def testing_run_summary_payload(repo_root: Path, run_id: str) -> dict[str, Any]:
    safe_run_id = validate_slug(run_id, "run_id")
    run_dir = repo_root / TEST_RUNS_REL_DIR / safe_run_id
    if not run_dir.is_dir():
        raise FileNotFoundError(f"Test run does not exist: {safe_run_id}")

    summary_json_path = run_dir / "summary.json"
    summary_md_path = run_dir / "summary.md"
    if not summary_json_path.exists() and not summary_md_path.exists():
        raise FileNotFoundError(f"Test run has no summary: {safe_run_id}")
    return {
        "ok": True,
        "run": compact_run_payload(repo_root, run_dir),
        "summary": read_json_object(summary_json_path) if summary_json_path.exists() else None,
        "summary_markdown": summary_md_path.read_text(encoding="utf-8") if summary_md_path.exists() else "",
        "summary_path": repo_relative(summary_md_path, repo_root) if summary_md_path.exists() else None,
        "time_utc": utc_now(),
    }


def compact_run_payload(repo_root: Path, run_dir: Path) -> dict[str, Any]:
    summary_json_path = run_dir / "summary.json"
    summary = read_json_object(summary_json_path) if summary_json_path.exists() else {}
    results = summary.get("results")
    failed = []
    if isinstance(results, list):
        failed = [result for result in results if isinstance(result, dict) and result.get("exit_code") != 0]
    return {
        "run_id": str(summary.get("run_id") or run_dir.name),
        "profiles": summary.get("profiles") if isinstance(summary.get("profiles"), list) else [],
        "status": summary.get("status"),
        "run_dir": repo_relative(run_dir, repo_root),
        "summary_path": repo_relative(run_dir / "summary.md", repo_root) if (run_dir / "summary.md").exists() else None,
        "result_count": len(results) if isinstance(results, list) else 0,
        "failed_count": len(failed),
        "updated_at_utc": dt.datetime.fromtimestamp(run_dir.stat().st_mtime, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def repo_relative(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()
