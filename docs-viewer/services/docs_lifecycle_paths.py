#!/usr/bin/env python3
"""Shared path and JSON helpers for Docs Viewer lifecycle services."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from docs_scope_config import path_label, safe_relative_path, safe_scope_data_path


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


def path_record(repo_root: Path, kind: str, path: Path, *, action: str = "track") -> dict[str, Any]:
    location = path_location(repo_root, path)
    return {
        "kind": kind,
        "path": path_label(repo_root, path),
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
    if Path(text).is_absolute():
        path = safe_scope_data_path(text, field=field, allow_external=True).resolve()
        if external_data_root is None or not path_is_relative_to_path(path, external_data_root):
            raise ValueError(f"{field} external path must stay under external_data_root")
        return path
    return repo_root / safe_relative_path(text, field=field)


def resolve_lifecycle_record_path(repo_root: Path, value: Any, *, field: str) -> Path:
    text = str(value or "").strip()
    if Path(text).is_absolute():
        return safe_scope_data_path(text, field=field, allow_external=True)
    return repo_root / safe_relative_path(text, field=field)


def delete_path_sort_key(repo_root: Path, record: dict[str, Any]) -> tuple[int, str]:
    path_text = str(record.get("path") or "")
    path = Path(path_text) if Path(path_text).is_absolute() else repo_root / safe_relative_path(path_text, field="delete file path")
    return (-len(path.parts), path.as_posix())


def delete_manifest_paths(repo_root: Path, delete_files: list[dict[str, Any]]) -> None:
    for record in sorted(delete_files, key=lambda item: delete_path_sort_key(repo_root, item)):
        path_text = str(record.get("path") or "")
        path = Path(path_text) if Path(path_text).is_absolute() else repo_root / safe_relative_path(path_text, field="delete file path")
        if not path.exists():
            continue
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
