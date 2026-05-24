"""Local Studio app adapter for allowlisted audit routes."""

from __future__ import annotations

from http import HTTPStatus
from pathlib import Path
import sys
from typing import Any

_BOOTSTRAP_START = Path(__file__).resolve()
for _candidate in (_BOOTSTRAP_START.parent, *_BOOTSTRAP_START.parents):
    if (_candidate / "_config.yml").exists():
        if str(_candidate) not in sys.path:
            sys.path.insert(0, str(_candidate))
        break

from scripts.studio_python_paths import ensure_studio_python_paths


REPO_ROOT = ensure_studio_python_paths(__file__)
SCRIPTS_DIR = REPO_ROOT / "scripts"
STUDIO_DIR = Path(__file__).resolve().parent
for candidate in (SCRIPTS_DIR, STUDIO_DIR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from audit_runner import (
    audits_payload,
    build_audit_registry,
    health_payload,
    run_audit_payload,
)
from script_logging import append_script_log
from studio_activity import (
    append_studio_activity,
    normalize_activity_context_from_contract,
    studio_activity_entry,
)


LOGS_REL_DIR = Path("var/studio/audits/logs")
RUN_AUDIT_API_PATH = "/studio/api/audits/audits/run"


def audit_get_payload(repo_root: Path, api_path: str) -> dict[str, Any]:
    if api_path == "/health":
        return health_payload(repo_root)
    if api_path == "/audits":
        return audits_payload(repo_root)
    raise FileNotFoundError(f"Unknown audit API route: {api_path}")


def audit_post_response(
    repo_root: Path,
    api_path: str,
    body: dict[str, Any],
) -> tuple[HTTPStatus, dict[str, Any]]:
    if api_path != "/audits/run":
        raise FileNotFoundError(f"Unknown audit API route: {api_path}")

    audits = build_audit_registry(repo_root)

    def log_event(event: str, details: dict[str, Any] | None = None) -> None:
        append_script_log(
            Path(__file__),
            event=event,
            details=details,
            repo_root=repo_root,
            log_dir_rel=LOGS_REL_DIR,
        )

    def append_activity(entry: dict[str, Any]) -> None:
        append_studio_activity(repo_root, entry)

    return HTTPStatus.OK, run_audit_payload(
        repo_root,
        body,
        audits,
        activity_endpoint=RUN_AUDIT_API_PATH,
        log_event=log_event,
        append_activity=append_activity,
        normalize_activity_context=normalize_activity_context_from_contract,
        build_activity_entry=studio_activity_entry,
    )
