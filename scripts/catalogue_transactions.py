#!/usr/bin/env python3
"""Catalogue write backup, restore, and atomic JSON write helpers."""

from __future__ import annotations

import datetime as dt
import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

import catalogue_cleanup


@dataclass(frozen=True)
class SourceJsonWriteResult:
    backup_paths: list[Path]
    backups: list[str]


def backup_stamp_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%S-%f")


def rel_response_path(path: Path, repo_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return path.name


def response_backup_paths(paths: Iterable[Path], repo_root: Path) -> list[str]:
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
    backups_dir: Path,
    *,
    dry_run: bool,
    repo_root: Path,
) -> SourceJsonWriteResult:
    payloads = validate_json_payloads_by_path(payloads_by_path)
    backup_paths: list[Path] = []
    if not dry_run:
        backup_paths = atomic_write_many(payloads, backups_dir)
    return SourceJsonWriteResult(
        backup_paths=backup_paths,
        backups=response_backup_paths(backup_paths, repo_root),
    )


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


def backup_transaction_paths(paths: Iterable[Path], backup_root: Path, repo_root: Path) -> Dict[Path, Path]:
    backups: Dict[Path, Path] = {}
    for path in catalogue_cleanup.unique_existing_paths(paths):
        resolved = path.resolve()
        if resolved in backups:
            continue
        try:
            rel_path = Path("repo") / resolved.relative_to(repo_root.resolve())
        except ValueError:
            rel_path = Path("external") / path.name
        backup_path = backup_root / rel_path
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup_path)
        backups[resolved] = backup_path
    return backups


def restore_transaction_paths(touched_paths: Iterable[Path], backups: Mapping[Path, Path]) -> None:
    for path in unique_paths(touched_paths):
        resolved = path.resolve()
        backup_path = backups.get(resolved)
        try:
            if backup_path and backup_path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup_path, path)
            elif path.exists() and path.is_file():
                path.unlink()
        except OSError:
            pass


def atomic_write_many(payloads_by_path: Dict[Path, Dict[str, Any]], backups_dir: Path) -> list[Path]:
    backups_dir.mkdir(parents=True, exist_ok=True)
    stamp = backup_stamp_now()
    bundle_dir = backups_dir / f"catalogue-save-{stamp}"
    bundle_dir.mkdir(parents=True, exist_ok=False)
    backups: Dict[Path, Path] = {}
    temp_paths: Dict[Path, Path] = {}
    replaced_paths: list[Path] = []

    try:
        for path, payload in payloads_by_path.items():
            if path.exists():
                backup_path = bundle_dir / path.name
                shutil.copy2(path, backup_path)
                backups[path] = backup_path

            fd, temp_name = tempfile.mkstemp(prefix=f"{path.name}.", suffix=".tmp", dir=str(path.parent))
            temp_path = Path(temp_name)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=False)
                handle.write("\n")
            temp_paths[path] = temp_path

        for path, temp_path in temp_paths.items():
            os.replace(temp_path, path)
            replaced_paths.append(path)
    except Exception:
        for path in reversed(replaced_paths):
            backup_path = backups.get(path)
            try:
                if backup_path and backup_path.exists():
                    shutil.copy2(backup_path, path)
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

    return list(backups.values())


def atomic_write_text_no_backup(target_path: Path, text: str) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{target_path.name}.",
        suffix=".tmp",
        dir=str(target_path.parent),
        text=True,
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        os.replace(temp_path, target_path)
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass
