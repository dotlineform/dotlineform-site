#!/usr/bin/env python3
"""Shared path and JSON helpers for Docs Viewer lifecycle services."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from docs_workspace_config import (
    EXTERNAL_DATA_ROOT_MARKER,
    path_label,
    resolve_external_data_root,
    resolve_external_data_marker_path,
    safe_relative_path,
)


def resolve_workspace_data_path(value: str, *, field: str) -> Path:
    """Confine external lifecycle records to descendants of the explicit root."""
    root = resolve_external_data_root()
    if value == EXTERNAL_DATA_ROOT_MARKER or value.startswith(f"{EXTERNAL_DATA_ROOT_MARKER}/"):
        path = resolve_external_data_marker_path(value, field=field)
    else:
        path = Path(value)
        if not path.is_absolute() or ".." in path.parts:
            raise ValueError(f"{field} must identify a configured external path")
        path = path.resolve()
    if path == root or not path.is_relative_to(root):
        raise ValueError(f"{field} must stay beneath the Docs workspace root")
    return path


def repo_relative(repo_root: Path, path: Path) -> str:
    resolved_root = repo_root.resolve()
    resolved_path = path.resolve()
    try:
        return resolved_path.relative_to(resolved_root).as_posix()
    except ValueError as exc:
        raise ValueError(f"path escapes repo root: {path}") from exc


def path_location(repo_root: Path, path: Path) -> str:
    try:
        path.resolve().relative_to(repo_root.resolve())
        return "repo"
    except ValueError:
        return "external"


def lifecycle_path_label(repo_root: Path, path: Path) -> str:
    label = path_label(repo_root, path)
    if path_location(repo_root, path) != "external":
        return label
    try:
        relative = path.resolve().relative_to(resolve_external_data_root().resolve())
    except (ValueError, OSError):
        return label
    if relative == Path("."):
        return EXTERNAL_DATA_ROOT_MARKER
    return f"{EXTERNAL_DATA_ROOT_MARKER}/{relative.as_posix()}"


def path_record(repo_root: Path, kind: str, path: Path, *, action: str = "track") -> dict[str, Any]:
    location = path_location(repo_root, path)
    return {
        "kind": kind,
        "path": lifecycle_path_label(repo_root, path),
        "location": location,
        "action": action,
        "exists": path.exists(),
    }


def write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.tmp")
    temp_path.write_text(text, encoding="utf-8")
    temp_path.replace(path)


def render_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} is invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be a JSON object")
    return payload


def path_is_relative_to_path(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def resolve_manifest_path(
    repo_root: Path,
    value: Any,
    *,
    field: str,
    external_data_root: Path | None = None,
) -> Path:
    text = str(value or "").strip()
    if text == EXTERNAL_DATA_ROOT_MARKER or text.startswith(f"{EXTERNAL_DATA_ROOT_MARKER}/"):
        path = resolve_workspace_data_path(text, field=field)
        if external_data_root is None or not path_is_relative_to_path(path, external_data_root):
            raise ValueError(f"{field} external path must stay under external_data_root")
        return path
    if Path(text).is_absolute():
        path = resolve_workspace_data_path(text, field=field)
        if external_data_root is None or not path_is_relative_to_path(path, external_data_root):
            raise ValueError(f"{field} external path must stay under external_data_root")
        return path
    return repo_root / safe_relative_path(text, field=field)


def resolve_lifecycle_record_path(repo_root: Path, value: Any, *, field: str) -> Path:
    text = str(value or "").strip()
    if (
        text == EXTERNAL_DATA_ROOT_MARKER
        or text.startswith(f"{EXTERNAL_DATA_ROOT_MARKER}/")
        or Path(text).is_absolute()
    ):
        return resolve_workspace_data_path(text, field=field)
    return repo_root / safe_relative_path(text, field=field)


def delete_path_sort_key(repo_root: Path, record: dict[str, Any]) -> tuple[int, str]:
    path_text = str(record.get("path") or "")
    path = resolve_lifecycle_record_path(repo_root, path_text, field="delete file path")
    return (-len(path.parts), path.as_posix())


def delete_manifest_paths(repo_root: Path, delete_files: list[dict[str, Any]]) -> None:
    for record in sorted(delete_files, key=lambda item: delete_path_sort_key(repo_root, item)):
        path_text = str(record.get("path") or "")
        path = resolve_lifecycle_record_path(repo_root, path_text, field="delete file path")
        if not path.exists():
            continue
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
