#!/usr/bin/env python3
"""Docs Data Sharing source-write, backup, and rebuild helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import docs_source_model as source_model


MakeBackupBundle = Callable[[Path, str, str, list[source_model.ScopeDoc], Optional[Dict[str, Any]]], Path]
PerformSourceWriteAndRebuild = Callable[..., Dict[str, Any]]


@dataclass(frozen=True)
class DocsDataSharingWriteDependencies:
    make_backup_bundle: MakeBackupBundle
    perform_source_write_and_rebuild: PerformSourceWriteAndRebuild


def relative_path(repo_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def write_document_updates_with_rebuild(
    repo_root: Path,
    *,
    scope: str,
    operation: str,
    suppression_reason: str,
    docs: list[source_model.ScopeDoc],
    rewritten_sources: dict[str, str],
    metadata: Dict[str, Any],
    doc_ids: list[str],
    dependencies: DocsDataSharingWriteDependencies,
) -> Dict[str, Any]:
    backup_dir = dependencies.make_backup_bundle(
        repo_root,
        scope,
        operation,
        docs,
        metadata,
    )
    rebuild = dependencies.perform_source_write_and_rebuild(
        repo_root,
        scope,
        [doc.path for doc in docs],
        lambda: [source_model.write_text_atomic(doc.path, rewritten_sources[doc.doc_id]) for doc in docs],
        suppression_reason=suppression_reason,
        docs_doc_ids=doc_ids,
        search_doc_ids=doc_ids,
    )
    return {
        "backup_dir": relative_path(repo_root, backup_dir),
        "rebuild": rebuild,
    }

