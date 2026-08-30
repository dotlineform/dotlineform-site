#!/usr/bin/env python3
"""Completion evidence for one full external Docs Viewer scope Build."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from docs_lifecycle_paths import render_json, write_text_atomic
from docs_scope_config import DocsScopeConfig, resolve_location_path


BUILD_MANIFEST_FILENAME = "build-manifest.json"
BUILD_MANIFEST_SCHEMA_VERSION = "docs_scope_build_manifest_v1"
IGNORED_FILENAMES = frozenset({".DS_Store", ".gitkeep"})


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _safe_root(repo_root: Path, config: DocsScopeConfig, *, role: str) -> Path:
    location = config.scope_root
    scope_root = resolve_location_path(repo_root, location)
    root = scope_root / role
    if scope_root.is_symlink() or root.is_symlink():
        raise ValueError(f"Docs scope {config.scope_id!r} {role} root must not be a symlink")
    if not scope_root.is_dir() or not root.is_dir():
        raise FileNotFoundError(f"Docs scope {config.scope_id!r} {role} root is unavailable")
    return root.resolve()


def _managed_files(root: Path, *, excluded: Iterable[str] = ()) -> list[Path]:
    excluded_set = set(excluded)
    paths: list[Path] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"Docs lifecycle output must not contain symlinks: {path.relative_to(root)}")
        if not path.is_file() or path.name in IGNORED_FILENAMES:
            continue
        relative = path.relative_to(root).as_posix()
        if relative in excluded_set:
            continue
        paths.append(path)
    return paths


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_revision(root: Path, paths: Iterable[Path]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(bytes.fromhex(_sha256(path)))
        digest.update(b"\0")
    return f"sha256:{digest.hexdigest()}"


def build_manifest_path(repo_root: Path, config: DocsScopeConfig) -> Path:
    return _safe_root(repo_root, config, role="generated") / BUILD_MANIFEST_FILENAME


def remove_build_manifest(repo_root: Path, config: DocsScopeConfig) -> bool:
    path = build_manifest_path(repo_root, config)
    if not path.exists():
        return False
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Docs scope {config.scope_id!r} build manifest must be a regular file")
    path.unlink()
    return True


def write_build_manifest(repo_root: Path, config: DocsScopeConfig) -> dict[str, Any]:
    source_root = _safe_root(repo_root, config, role="source")
    generated_root = _safe_root(repo_root, config, role="generated")
    source_files = _managed_files(source_root)
    generated_files = _managed_files(generated_root, excluded=(BUILD_MANIFEST_FILENAME,))
    records = [
        {
            "path": path.relative_to(generated_root).as_posix(),
            "size": path.stat().st_size,
            "sha256": _sha256(path),
        }
        for path in generated_files
    ]
    payload: dict[str, Any] = {
        "schema_version": BUILD_MANIFEST_SCHEMA_VERSION,
        "scope": config.scope_id,
        "completed_at": utc_now(),
        "source_revision": tree_revision(source_root, source_files),
        "generated_revision": tree_revision(generated_root, generated_files),
        "file_count": len(records),
        "files": records,
    }
    path = generated_root / BUILD_MANIFEST_FILENAME
    write_text_atomic(path, render_json(payload))
    persisted = json.loads(path.read_text(encoding="utf-8"))
    if persisted != payload:
        raise RuntimeError(f"Docs scope {config.scope_id!r} build manifest did not verify")
    return payload


__all__ = [
    "BUILD_MANIFEST_FILENAME",
    "BUILD_MANIFEST_SCHEMA_VERSION",
    "build_manifest_path",
    "remove_build_manifest",
    "tree_revision",
    "write_build_manifest",
]
