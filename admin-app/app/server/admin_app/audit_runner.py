#!/usr/bin/env python3
"""Allowlisted Admin audit registry and direct runner."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

_BOOTSTRAP_START = Path(__file__).resolve()
for _candidate in (_BOOTSTRAP_START.parent, *_BOOTSTRAP_START.parents):
    if (_candidate / "public-site" / "config" / "public-site.json").exists():
        if str(_candidate) not in sys.path:
            sys.path.insert(0, str(_candidate))
        break

from studio.shared.python.studio_python_paths import ensure_studio_python_paths

REPO_ROOT = ensure_studio_python_paths(__file__)
SCRIPTS_DIR = REPO_ROOT / "scripts"

from script_logging import append_script_log  # noqa: E402


LOGS_REL_DIR = Path("var/admin/audits/logs")
RUN_AUDIT_PATH = "/admin/api/audits/audits/run"


@dataclass(frozen=True)
class AuditDefinition:
    audit_id: str
    label: str
    description: str
    argv: tuple[str, ...]

    def public_payload(self) -> dict[str, str]:
        return {
            "audit_id": self.audit_id,
            "label": self.label,
            "description": self.description,
        }


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def find_repo_root(start: Path) -> Path | None:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "public-site" / "config" / "public-site.json").exists():
            return candidate
    return None


def detect_repo_root(explicit_root: str) -> Path:
    if explicit_root:
        repo_root = Path(explicit_root).expanduser().resolve()
        if not (repo_root / "public-site" / "config" / "public-site.json").exists():
            raise SystemExit(f"--repo-root does not look like repo root (missing public-site/config/public-site.json): {repo_root}")
        return repo_root

    for start in [Path.cwd(), Path(__file__).resolve().parent]:
        found = find_repo_root(start)
        if found is not None:
            return found

    raise SystemExit("Could not auto-detect repo root. Pass --repo-root.")


def build_audit_registry(repo_root: Path) -> dict[str, AuditDefinition]:
    return {
        "studio-ready-state": AuditDefinition(
            audit_id="studio-ready-state",
            label="Studio ready state",
            description="Checks Studio route-ready template contracts and static-route drift.",
            argv=(
                sys.executable,
                str(repo_root / "admin-app" / "checks" / "audit_studio_ready_state.py"),
                "--strict",
                "--json",
            ),
        )
    }


def health_payload(repo_root: Path, audits: dict[str, AuditDefinition] | None = None) -> dict[str, Any]:
    audit_registry = audits or build_audit_registry(repo_root)
    return {
        "ok": True,
        "service": "admin_audit_runner",
        "audits": sorted(audit_registry.keys()),
        "time_utc": utc_now(),
    }


def audits_payload(repo_root: Path, audits: dict[str, AuditDefinition] | None = None) -> dict[str, Any]:
    audit_registry = audits or build_audit_registry(repo_root)
    return {
        "ok": True,
        "audits": [audit.public_payload() for audit in audit_registry.values()],
        "time_utc": utc_now(),
    }


def run_audit_payload(
    repo_root: Path,
    body: dict[str, Any],
    audits: dict[str, AuditDefinition] | None = None,
    *,
    activity_endpoint: str = RUN_AUDIT_PATH,
    log_event: Callable[[str, dict[str, Any] | None], None] | None = None,
    append_activity: Callable[[dict[str, Any]], None] | None = None,
    normalize_activity_context: Callable[..., dict[str, Any] | None] | None = None,
    build_activity_entry: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    audit_registry = audits or build_audit_registry(repo_root)
    audit_id = str(body.get("audit_id") or "").strip()
    if not audit_id:
        raise ValueError("audit_id is required")
    audit = audit_registry.get(audit_id)
    if audit is None:
        raise ValueError("audit_id is not allowlisted")

    started_at = utc_now()
    started = time.monotonic()
    result = subprocess.run(
        audit.argv,
        cwd=repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    finished_at = utc_now()
    duration = time.monotonic() - started

    try:
        parsed = json.loads(result.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"audit returned invalid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise RuntimeError("audit returned invalid JSON payload")

    summary = parsed.get("summary") if isinstance(parsed.get("summary"), dict) else {}
    response_payload: dict[str, Any] = {
        "ok": True,
        "audit_id": audit.audit_id,
        "label": audit.label,
        "status": str(parsed.get("status") or ("passed" if result.returncode == 0 else "failed")),
        "exit_code": result.returncode,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_seconds": round(duration, 3),
        "summary": {
            "errors": int(summary.get("errors") or 0),
            "warnings": int(summary.get("warnings") or 0),
        },
        "totals": parsed.get("totals") if isinstance(parsed.get("totals"), dict) else {},
        "findings": parsed.get("findings") if isinstance(parsed.get("findings"), list) else [],
        "stdout": result.stdout,
        "stderr": result.stderr,
    }

    if append_activity and normalize_activity_context and build_activity_entry:
        try:
            activity_context = normalize_activity_context(
                repo_root,
                body.get("activity_context"),
                endpoint=activity_endpoint,
                record_id=audit.audit_id,
            )
            if activity_context:
                errors = response_payload["summary"]["errors"]
                warnings = response_payload["summary"]["warnings"]
                status = "failed" if response_payload["status"] == "failed" or errors else ("warning" if warnings else "completed")
                response_payload["activity_context"] = activity_context
                append_activity(
                    build_activity_entry(
                        activity_context,
                        script_purpose_id="run-audit",
                        now_utc=finished_at,
                        status=status,
                        record_groups={"docs": [audit.audit_id]},
                        detail_items=[
                            f"Ran Admin audit: {audit.label}.",
                            f"Status: {response_payload['status']}; errors: {errors}; warnings: {warnings}.",
                            f"Duration: {response_payload['duration_seconds']} seconds.",
                        ],
                        source_refs=[{"kind": "log", "path": str(LOGS_REL_DIR / "admin_audit_runner.log")}],
                    )
                )
                response_payload["activity_log"] = {"written_count": 1}
        except Exception as exc:  # noqa: BLE001
            response_payload["activity_log"] = {"written_count": 0, "error": str(exc)}

    if log_event:
        log_event(
            "audit_run",
            {
                "audit_id": audit.audit_id,
                "status": response_payload["status"],
                "exit_code": result.returncode,
                "errors": response_payload["summary"]["errors"],
                "warnings": response_payload["summary"]["warnings"],
                "duration_seconds": response_payload["duration_seconds"],
            },
        )
    return response_payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run an allowlisted Admin audit directly.")
    parser.add_argument("--repo-root", default="", help="Repo root path (auto-detected if omitted)")
    parser.add_argument("--audit-id", default="studio-ready-state", help="Allowlisted audit id to run")
    parser.add_argument("--list", action="store_true", help="Print the allowlisted audit registry and exit")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = detect_repo_root(args.repo_root)
    audits = build_audit_registry(repo_root)

    if args.list:
        print(json.dumps(audits_payload(repo_root, audits), indent=2, sort_keys=True))
        return

    def log_event(event: str, details: dict[str, Any] | None = None) -> None:
        append_script_log(
            Path(__file__),
            event=event,
            details=details,
            repo_root=repo_root,
            log_dir_rel=LOGS_REL_DIR,
        )

    try:
        payload = run_audit_payload(
            repo_root,
            {"audit_id": args.audit_id},
            audits,
            log_event=log_event,
        )
    except ValueError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2, sort_keys=True), file=sys.stderr)
        raise SystemExit(2) from exc
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2, sort_keys=True), file=sys.stderr)
        raise SystemExit(1) from exc

    print(json.dumps(payload, indent=2, sort_keys=True))
    raise SystemExit(int(payload.get("exit_code") or 0))


if __name__ == "__main__":
    main()
