"""Operation completion for a full Working Build; no publication inventory."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

from docs_json_files import render_json, write_text_atomic
from docs_workspace_config import DocsStageConfig, generated_documents_path


BUILD_MANIFEST_FILENAME = "build-manifest.json"


def build_manifest_path(repo_root: Path, config: DocsStageConfig) -> Path:
    path = generated_documents_path(config).parent / BUILD_MANIFEST_FILENAME
    if path.resolve() != path:
        raise ValueError("Working build receipt must stay in its configured directory")
    return path


def remove_build_manifest(repo_root: Path, config: DocsStageConfig) -> bool:
    path = build_manifest_path(repo_root, config)
    existed = path.exists()
    path.unlink(missing_ok=True)
    return existed


def write_working_build_completion(repo_root: Path, config: DocsStageConfig) -> dict[str, Any]:
    """Record completion without reopening sources or generated artifacts."""
    completed = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    payload = {"schema_version": "docs_working_build_v1", "stage": "working", "completed_at": completed}
    write_text_atomic(build_manifest_path(repo_root, config), render_json(payload))
    return payload
