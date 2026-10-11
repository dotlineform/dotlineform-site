#!/usr/bin/env python3
"""Canonical Catalogue JSON transactions; generated output is completed separately."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping


@dataclass(frozen=True)
class SourceJsonWriteResult:
    written_paths: list[Path]


def rel_response_path(path: Path, repo_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return path.name


def response_written_paths(paths: Iterable[Path], repo_root: Path) -> list[str]:
    return [rel_response_path(path, repo_root) for path in paths]


def validate_json_payloads_by_path(payloads_by_path: Mapping[Path, Mapping[str, Any]]) -> Dict[Path, Dict[str, Any]]:
    if not payloads_by_path:
        raise ValueError("source write payloads are required")

    payloads: Dict[Path, Dict[str, Any]] = {}
    for raw_path, raw_payload in payloads_by_path.items():
        if not isinstance(raw_path, Path):
            raise TypeError("source write target paths must be pathlib.Path values")
        path = raw_path.resolve()
        if path in payloads:
            raise ValueError(f"duplicate source write target: {path}")
        if not isinstance(raw_payload, Mapping):
            raise TypeError("source write payloads must be mappings")
        payloads[path] = dict(raw_payload)
    return payloads


def execute_source_json_write(
    payloads_by_path: Mapping[Path, Mapping[str, Any]],
    *,
    dry_run: bool,
    repo_root: Path,
) -> SourceJsonWriteResult:
    payloads = validate_json_payloads_by_path(payloads_by_path)
    written_paths: list[Path] = []
    if not dry_run:
        written_paths = atomic_write_many(payloads)
    return SourceJsonWriteResult(written_paths=written_paths)


def atomic_write_many(
    payloads_by_path: Dict[Path, Dict[str, Any]], *,
    media_files: Mapping[Path, bytes] | None = None,
) -> list[Path]:
    """Commit Catalogue JSON and any prepared current media through the same rollback owner."""
    temp_paths: Dict[Path, Path] = {}
    replaced_paths: list[Path] = []
    originals: Dict[Path, bytes | None] = {}

    try:
        data_by_path = {
            path: (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n").encode("utf-8")
            for path, payload in payloads_by_path.items()
        }
        if set(data_by_path).intersection(media_files or {}):
            raise ValueError("Catalogue JSON and media write destinations must be distinct")
        data_by_path.update(media_files or {})
        for path, data in data_by_path.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            originals[path] = path.read_bytes() if path.exists() else None

            fd, temp_name = tempfile.mkstemp(prefix=f"{path.name}.", suffix=".tmp", dir=str(path.parent))
            temp_path = Path(temp_name)
            temp_paths[path] = temp_path
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)

        for path, temp_path in temp_paths.items():
            os.replace(temp_path, path)
            replaced_paths.append(path)
    except Exception:
        for path in reversed(replaced_paths):
            try:
                original = originals.get(path)
                if original is not None:
                    path.write_bytes(original)
                elif path.exists():
                    path.unlink()
            except Exception:
                pass
        raise
    finally:
        for temp_path in temp_paths.values():
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass

    return list(data_by_path)
