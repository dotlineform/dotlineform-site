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
from typing import Any, Callable, Dict, Iterable, Mapping

from catalogue import catalogue_cleanup


@dataclass(frozen=True)
class SourceJsonWriteResult:
    backup_paths: list[Path]
    backups: list[str]


@dataclass(frozen=True)
class CleanupTransactionResult:
    payload: Dict[str, Any]
    backup_paths: list[Path]


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


def ensure_catalogue_delete_payload_scope(
    repo_root: Path,
    allowed_write_paths: Iterable[Path],
    payloads: Mapping[Path, Dict[str, Any]],
) -> None:
    generated_roots = [
        repo_root / "assets" / "works" / "index",
        repo_root / "assets" / "series" / "index",
    ]
    generated_paths = {
        (repo_root / "assets" / "data" / "works_index.json").resolve(),
        (repo_root / "assets" / "data" / "series_index.json").resolve(),
        (repo_root / "assets" / "data" / "recent_index.json").resolve(),
        (repo_root / "assets" / "studio" / "data" / "work_storage_index.json").resolve(),
        (repo_root / "assets" / "studio" / "data" / "tag_assignments.json").resolve(),
    }
    allowed = {path.resolve() for path in allowed_write_paths}
    for target_path in payloads:
        resolved = target_path.resolve()
        if resolved in allowed:
            continue
        if resolved in generated_paths:
            continue
        if any(catalogue_cleanup.path_is_under(resolved, root) for root in generated_roots):
            continue
        raise ValueError("write target not allowlisted")


def execute_catalogue_cleanup_transaction(
    *,
    repo_root: Path,
    backups_dir: Path,
    dry_run: bool,
    allowed_write_paths: Iterable[Path],
    backup_label: str,
    payloads: Dict[Path, Dict[str, Any]],
    cleanup: Mapping[str, Any],
    rebuild_catalogue_search: Callable[[Path], Dict[str, Any]],
    refresh_lookup_payloads: Callable[[], Any] | None = None,
) -> CleanupTransactionResult:
    catalogue_cleanup.ensure_catalogue_delete_cleanup_scope(repo_root, cleanup)
    ensure_catalogue_delete_payload_scope(repo_root, allowed_write_paths, payloads)
    search_index_path = (repo_root / "assets" / "data" / "search" / "catalogue" / "index.json").resolve()
    rebuild_search = bool(cleanup.get("catalogue_search"))
    transaction_backup_root: Path | None = None
    deleted_file_count = 0
    search_rebuild: Dict[str, Any] = {"ok": True, "exit_code": 0}
    backup_paths: list[Path] = []

    if not dry_run:
        transaction_backup_root = backups_dir / f"{backup_label}-{backup_stamp_now()}"
        touched_paths = unique_paths(
            [
                *payloads.keys(),
                *(cleanup.get("delete_paths") or []),
                *([search_index_path] if rebuild_search else []),
            ]
        )
        transaction_backups = backup_transaction_paths(touched_paths, transaction_backup_root, repo_root)
        try:
            backup_paths = atomic_write_many(payloads, backups_dir)
            backup_paths.extend(transaction_backups.values())
            deleted_file_count = catalogue_cleanup.delete_existing_files(cleanup.get("delete_paths") or [])
            if rebuild_search:
                search_rebuild = rebuild_catalogue_search(repo_root)
            if refresh_lookup_payloads is not None:
                refresh_lookup_payloads()
        except Exception:
            restore_transaction_paths(touched_paths, transaction_backups)
            raise

    return CleanupTransactionResult(
        payload={
            "deleted_files": deleted_file_count,
            "would_delete_files": len(cleanup.get("delete_paths") or []),
            "updated_json_files": 0 if dry_run else len(payloads),
            "would_update_json_files": len(payloads),
            "catalogue_search_rebuilt": bool(not dry_run and rebuild_search and search_rebuild.get("ok")),
            "would_rebuild_catalogue_search": rebuild_search,
            "search_exit_code": search_rebuild.get("exit_code"),
            "backup_root": rel_response_path(transaction_backup_root, repo_root) if transaction_backup_root else "",
        },
        backup_paths=backup_paths,
    )


def execute_moment_cleanup_transaction(
    *,
    repo_root: Path,
    backups_dir: Path,
    dry_run: bool,
    allowed_write_paths: Iterable[Path],
    backup_label: str,
    metadata_path: Path,
    metadata_payload: Dict[str, Any],
    cleanup: Mapping[str, Any],
    moment_id: str,
    rebuild_catalogue_search: Callable[[Path], Dict[str, Any]],
) -> CleanupTransactionResult:
    catalogue_cleanup.ensure_moment_delete_cleanup_scope(repo_root, cleanup)
    metadata_path = metadata_path.resolve()
    moments_index_path = (repo_root / "assets" / "data" / "moments_index.json").resolve()
    search_index_path = (repo_root / "assets" / "data" / "search" / "catalogue" / "index.json").resolve()
    allowed = {path.resolve() for path in allowed_write_paths}
    if metadata_path not in allowed:
        raise ValueError("write target not allowlisted")

    allowed_generated_paths = {moments_index_path, search_index_path}
    generated_payloads: Dict[Path, Dict[str, Any]] = {}
    if not dry_run:
        generated_payloads = catalogue_cleanup.build_moment_delete_generated_payloads(repo_root, moment_id)
        for target_path in generated_payloads:
            if target_path.resolve() not in allowed_generated_paths:
                raise ValueError("generated write target not allowlisted")

    payloads: Dict[Path, Dict[str, Any]] = {
        metadata_path: metadata_payload,
        **generated_payloads,
    }
    deleted_file_count = 0
    search_rebuild: Dict[str, Any] = {"ok": True, "exit_code": 0}
    transaction_backup_root: Path | None = None
    backup_paths: list[Path] = []

    if not dry_run:
        transaction_backup_root = backups_dir / f"{backup_label}-{backup_stamp_now()}"
        touched_paths = unique_paths(
            [
                *payloads.keys(),
                search_index_path,
                *(cleanup.get("delete_paths") or []),
            ]
        )
        transaction_backups = backup_transaction_paths(touched_paths, transaction_backup_root, repo_root)
        try:
            backup_paths = atomic_write_many(payloads, backups_dir)
            backup_paths.extend(transaction_backups.values())
            deleted_file_count = catalogue_cleanup.delete_existing_files(cleanup.get("delete_paths") or [])
            search_rebuild = rebuild_catalogue_search(repo_root)
        except Exception:
            restore_transaction_paths(touched_paths, transaction_backups)
            raise

    moments_index_will_update = moments_index_path.exists()
    return CleanupTransactionResult(
        payload={
            "deleted_files": deleted_file_count,
            "would_delete_files": len(cleanup.get("delete_paths") or []),
            "moments_index_updated": bool(not dry_run and moments_index_will_update),
            "would_update_moments_index": moments_index_will_update,
            "catalogue_search_rebuilt": bool(not dry_run and search_rebuild.get("ok")),
            "would_rebuild_catalogue_search": True,
            "search_exit_code": search_rebuild.get("exit_code"),
            "backup_root": rel_response_path(transaction_backup_root, repo_root) if transaction_backup_root else "",
        },
        backup_paths=backup_paths,
    )


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
