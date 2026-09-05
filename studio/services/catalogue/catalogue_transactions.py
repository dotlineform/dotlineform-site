#!/usr/bin/env python3
"""Canonical Catalogue JSON transactions; generated output is completed separately."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

from catalogue.catalogue_source import SOURCE_FILES, work_detail_payloads_for_maps


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
        expanded_payloads, delete_paths = expand_source_payloads(payloads)
        written_paths = atomic_write_many(expanded_payloads, delete_paths=delete_paths)
    return SourceJsonWriteResult(written_paths=written_paths)


def expand_source_payloads(payloads_by_path: Mapping[Path, Dict[str, Any]]) -> tuple[Dict[Path, Dict[str, Any]], list[Path]]:
    expanded: Dict[Path, Dict[str, Any]] = {}
    delete_paths: list[Path] = []
    for path, payload in payloads_by_path.items():
        if path.name == SOURCE_FILES["work_details"] and isinstance(payload.get("work_details"), Mapping):
            detail_dir = path
            source_dir = detail_dir.parent
            details_payloads = work_detail_payloads_for_maps(
                source_dir,
                payload.get("work_detail_sections") if isinstance(payload.get("work_detail_sections"), Mapping) else {},
                payload.get("work_details") if isinstance(payload.get("work_details"), Mapping) else {},
            )
            expanded.update(details_payloads)
            expected_paths = {target.resolve() for target in details_payloads}
            if detail_dir.exists():
                for current_path in sorted(detail_dir.glob("*.json")):
                    if current_path.name == "index.json":
                        continue
                    if current_path.resolve() not in expected_paths:
                        delete_paths.append(current_path.resolve())
            continue
        expanded[path] = payload
    return expanded, delete_paths


def unique_paths(paths: Iterable[Path]) -> list[Path]:
    seen: set[Path] = set()
    out: list[Path] = []
    for path in paths:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        out.append(path)
    return out


def atomic_write_many(payloads_by_path: Dict[Path, Dict[str, Any]], *, delete_paths: Iterable[Path] = ()) -> list[Path]:
    temp_paths: Dict[Path, Path] = {}
    replaced_paths: list[Path] = []
    originals: Dict[Path, bytes | None] = {}
    deleted_originals: Dict[Path, bytes] = {}

    try:
        for path, payload in payloads_by_path.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            originals[path] = path.read_bytes() if path.exists() else None

            fd, temp_name = tempfile.mkstemp(prefix=f"{path.name}.", suffix=".tmp", dir=str(path.parent))
            temp_path = Path(temp_name)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=False)
                handle.write("\n")
            temp_paths[path] = temp_path

        for path, temp_path in temp_paths.items():
            os.replace(temp_path, path)
            replaced_paths.append(path)
        for delete_path in unique_paths(delete_paths):
            if delete_path.exists() and delete_path.is_file():
                deleted_originals[delete_path] = delete_path.read_bytes()
                delete_path.unlink()
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
        for path, original in deleted_originals.items():
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(original)
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

    return [*payloads_by_path.keys()]
