"""Shared context and plumbing for Docs management service routes."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from script_logging import append_script_log
from docs_scope_config import DOCS_SCOPE_CONFIGS


MAX_BODY_BYTES = 64 * 1024
LOGS_REL_DIR = Path("var/docs/logs")
DEFAULT_MARKDOWN_APP_ENV = "DOCS_MANAGEMENT_DEFAULT_MARKDOWN_APP"


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def find_repo_root(start: Path) -> Optional[Path]:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "site-tools" / "config" / "site-tools.json").exists():
            return candidate
    return None


def detect_repo_root(explicit_root: str) -> Path:
    if explicit_root:
        repo_root = Path(explicit_root).expanduser().resolve()
        if not (repo_root / "site-tools" / "config" / "site-tools.json").exists():
            raise SystemExit(f"--repo-root does not look like repo root (missing site-tools/config/site-tools.json): {repo_root}")
        return repo_root

    for start in [Path.cwd(), Path(__file__).resolve().parent]:
        found = find_repo_root(start)
        if found is not None:
            return found

    raise SystemExit("Could not auto-detect repo root. Pass --repo-root.")


def allowed_origin(origin: str) -> Optional[str]:
    if not origin:
        return None

    try:
        parsed = urlparse(origin)
    except Exception:
        return None

    if parsed.scheme != "http":
        return None
    if parsed.hostname not in {"localhost", "127.0.0.1"}:
        return None
    if parsed.path not in {"", "/"}:
        return None
    if parsed.params or parsed.query or parsed.fragment:
        return None
    if parsed.port is None:
        return f"{parsed.scheme}://{parsed.hostname}"
    return f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"


def relative_path(repo_root: Path, path: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def viewer_url_for(scope: str, doc_id: str) -> str:
    normalized_scope = scope if scope in DOCS_SCOPE_CONFIGS else next(iter(DOCS_SCOPE_CONFIGS))
    return f"/docs/?scope={normalized_scope}&doc={doc_id}"


def log_event(repo_root: Path, event: str, details: Dict[str, Any]) -> None:
    append_script_log(
        repo_root / "docs-viewer" / "services" / "docs_management_service.py",
        event,
        details=details,
        repo_root=repo_root,
        log_dir_rel=LOGS_REL_DIR,
    )
