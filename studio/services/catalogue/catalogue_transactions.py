#!/usr/bin/env python3
"""Catalogue atomic JSON write and cleanup transaction helpers."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Mapping

from catalogue import catalogue_cleanup
from catalogue import catalogue_public_paths as public_paths


@dataclass(frozen=True)
class SourceJsonWriteResult:
    written_paths: list[Path]


@dataclass(frozen=True)
class CleanupTransactionResult:
    payload: Dict[str, Any]
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


def snapshot_transaction_paths(paths: Iterable[Path]) -> Dict[Path, bytes]:
    snapshots: Dict[Path, bytes] = {}
    for path in catalogue_cleanup.unique_existing_paths(paths):
        resolved = path.resolve()
        if resolved in snapshots:
            continue
        snapshots[resolved] = path.read_bytes()
    return snapshots


def restore_transaction_paths(touched_paths: Iterable[Path], snapshots: Mapping[Path, bytes]) -> None:
    for path in unique_paths(touched_paths):
        resolved = path.resolve()
        try:
            if resolved in snapshots:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(snapshots[resolved])
            elif path.exists() and path.is_file():
                path.unlink()
        except OSError:
            pass


def atomic_write_many(payloads_by_path: Dict[Path, Dict[str, Any]]) -> list[Path]:
    temp_paths: Dict[Path, Path] = {}
    replaced_paths: list[Path] = []
    originals: Dict[Path, bytes | None] = {}

    try:
        for path, payload in payloads_by_path.items():
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

    return list(payloads_by_path.keys())


def ensure_catalogue_delete_payload_scope(
    repo_root: Path,
    allowed_write_paths: Iterable[Path],
    payloads: Mapping[Path, Dict[str, Any]],
) -> None:
    generated_roots = [
        repo_root / public_paths.WORKS_JSON_DIR,
        repo_root / public_paths.SERIES_JSON_DIR,
    ]
    generated_paths = {
        (repo_root / public_paths.WORKS_INDEX_JSON_PATH).resolve(),
        (repo_root / public_paths.SERIES_INDEX_JSON_PATH).resolve(),
        (repo_root / public_paths.RECENT_INDEX_JSON_PATH).resolve(),
        (repo_root / catalogue_cleanup.tag_source_paths.TAG_ASSIGNMENTS_REL_PATH).resolve(),
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
    dry_run: bool,
    allowed_write_paths: Iterable[Path],
    payloads: Dict[Path, Dict[str, Any]],
    cleanup: Mapping[str, Any],
    rebuild_catalogue_search: Callable[[Path], Dict[str, Any]],
    refresh_lookup_payloads: Callable[[], Any] | None = None,
) -> CleanupTransactionResult:
    catalogue_cleanup.ensure_catalogue_delete_cleanup_scope(repo_root, cleanup)
    ensure_catalogue_delete_payload_scope(repo_root, allowed_write_paths, payloads)
    search_index_path = (repo_root / public_paths.CATALOGUE_SEARCH_INDEX_JSON_PATH).resolve()
    rebuild_search = bool(cleanup.get("catalogue_search"))
    deleted_file_count = 0
    search_rebuild: Dict[str, Any] = {"ok": True, "exit_code": 0}
    written_paths: list[Path] = []

    if not dry_run:
        touched_paths = unique_paths(
            [
                *payloads.keys(),
                *(cleanup.get("delete_paths") or []),
                *([search_index_path] if rebuild_search else []),
            ]
        )
        transaction_snapshots = snapshot_transaction_paths(touched_paths)
        try:
            written_paths = atomic_write_many(payloads)
            deleted_file_count = catalogue_cleanup.delete_existing_files(cleanup.get("delete_paths") or [])
            if rebuild_search:
                search_rebuild = rebuild_catalogue_search(repo_root)
            if refresh_lookup_payloads is not None:
                refresh_lookup_payloads()
        except Exception:
            restore_transaction_paths(touched_paths, transaction_snapshots)
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
        },
        written_paths=written_paths,
    )


def execute_moment_cleanup_transaction(
    *,
    repo_root: Path,
    dry_run: bool,
    allowed_write_paths: Iterable[Path],
    metadata_path: Path,
    metadata_payload: Dict[str, Any],
    cleanup: Mapping[str, Any],
    moment_id: str,
    rebuild_catalogue_search: Callable[[Path], Dict[str, Any]],
) -> CleanupTransactionResult:
    catalogue_cleanup.ensure_moment_delete_cleanup_scope(repo_root, cleanup)
    metadata_path = metadata_path.resolve()
    moments_index_path = (repo_root / public_paths.MOMENTS_INDEX_JSON_PATH).resolve()
    search_index_path = (repo_root / public_paths.CATALOGUE_SEARCH_INDEX_JSON_PATH).resolve()
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
    written_paths: list[Path] = []

    if not dry_run:
        touched_paths = unique_paths(
            [
                *payloads.keys(),
                search_index_path,
                *(cleanup.get("delete_paths") or []),
            ]
        )
        transaction_snapshots = snapshot_transaction_paths(touched_paths)
        try:
            written_paths = atomic_write_many(payloads)
            deleted_file_count = catalogue_cleanup.delete_existing_files(cleanup.get("delete_paths") or [])
            search_rebuild = rebuild_catalogue_search(repo_root)
        except Exception:
            restore_transaction_paths(touched_paths, transaction_snapshots)
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
        },
        written_paths=written_paths,
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
