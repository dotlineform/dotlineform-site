"""Shared context and plumbing for Docs management service routes."""

from __future__ import annotations

import datetime as dt
import json
import shutil
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from script_logging import append_script_log
import docs_scope_manifest
import docs_source_model as source_model
from docs_scope_config import DOCS_SCOPE_CONFIGS


MAX_BODY_BYTES = 64 * 1024
BACKUPS_REL_DIR = Path("var/docs/backups")
LOGS_REL_DIR = Path("var/docs/logs")
DEFAULT_MARKDOWN_APP_ENV = "DOCS_MANAGEMENT_DEFAULT_MARKDOWN_APP"


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def backup_stamp_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%S-%f")


def find_repo_root(start: Path) -> Optional[Path]:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "_config.yml").exists():
            return candidate
    return None


def detect_repo_root(explicit_root: str) -> Path:
    if explicit_root:
        repo_root = Path(explicit_root).expanduser().resolve()
        if not (repo_root / "_config.yml").exists():
            raise SystemExit(f"--repo-root does not look like repo root (missing _config.yml): {repo_root}")
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


def make_backup_bundle(
    repo_root: Path,
    scope: str,
    operation: str,
    docs: list[source_model.ScopeDoc],
    metadata: Optional[Dict[str, Any]] = None,
) -> Path:
    bundle_dir = repo_root / BACKUPS_REL_DIR / f"{backup_stamp_now()}-{scope}-{operation}"
    bundle_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "time_utc": utc_now(),
        "scope": scope,
        "operation": operation,
        "count": len(docs),
        "files": [
            {
                "doc_id": doc.doc_id,
                "title": doc.title,
                "path": relative_path(repo_root, doc.path),
                "filename": doc.path.name,
            }
            for doc in docs
        ],
    }
    if metadata:
        manifest["metadata"] = metadata
    source_model.write_text_atomic(bundle_dir / "manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    for doc in docs:
        shutil.copy2(doc.path, bundle_dir / doc.path.name)
    return bundle_dir


def make_import_overwrite_backup(
    repo_root: Path,
    scope: str,
    target: source_model.ScopeDoc,
    metadata: Optional[Dict[str, Any]] = None,
) -> Path:
    bundle_name = f"{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%d')}-{scope}-import-overwrite-{source_model.slugify(target.doc_id)}"
    bundle_dir = repo_root / BACKUPS_REL_DIR / bundle_name
    if bundle_dir.exists():
        shutil.rmtree(bundle_dir)
    bundle_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "time_utc": utc_now(),
        "scope": scope,
        "operation": "import-overwrite",
        "count": 1,
        "files": [
            {
                "doc_id": target.doc_id,
                "title": target.title,
                "path": relative_path(repo_root, target.path),
                "filename": target.path.name,
            }
        ],
    }
    if metadata:
        manifest["metadata"] = metadata
    source_model.write_text_atomic(bundle_dir / "manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    shutil.copy2(target.path, bundle_dir / target.path.name)
    return bundle_dir


def make_scope_lifecycle_backup(repo_root: Path, scope: str, operation: str) -> Path:
    bundle_dir = repo_root / BACKUPS_REL_DIR / f"{backup_stamp_now()}-{scope}-scope-{operation}"
    bundle_dir.mkdir(parents=True, exist_ok=True)
    candidates = [
        repo_root / docs_scope_manifest.MANIFEST_REL_PATH,
        repo_root / docs_scope_manifest.CONFIG_REL_PATH,
    ]
    files = []
    for path in candidates:
        record = {
            "path": relative_path(repo_root, path),
            "exists": path.exists(),
        }
        if path.exists() and path.is_file():
            shutil.copy2(path, bundle_dir / path.name)
            record["backup_name"] = path.name
        files.append(record)
    manifest = {
        "time_utc": utc_now(),
        "scope": scope,
        "operation": f"scope-{operation}",
        "files": files,
    }
    source_model.write_text_atomic(bundle_dir / "manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return bundle_dir


def relative_path(repo_root: Path, path: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def viewer_url_for(scope: str, doc_id: str) -> str:
    normalized_scope = scope if scope in DOCS_SCOPE_CONFIGS else next(iter(DOCS_SCOPE_CONFIGS))
    return f"/docs/?scope={normalized_scope}&doc={doc_id}&mode=manage"


def log_event(repo_root: Path, event: str, details: Dict[str, Any]) -> None:
    append_script_log(
        repo_root / "studio" / "docs-viewer" / "services" / "docs_management_service.py",
        event,
        details=details,
        repo_root=repo_root,
        log_dir_rel=LOGS_REL_DIR,
    )
