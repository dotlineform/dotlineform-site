#!/usr/bin/env python3
"""Docs Management source-write follow-through and rebuild helpers."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from docs_scope_config import DOCS_SCOPE_CONFIGS
from docs_source_model import scope_root
from docs_watch_suppression import (
    DEFAULT_COMPLETE_TTL_SECONDS,
    DEFAULT_PENDING_TTL_SECONDS,
    SUPPRESSION_COMPLETE,
    SUPPRESSION_PENDING,
    clear_watch_suppressions,
    set_watch_suppressions,
)


def detect_bundle_bin() -> Optional[str]:
    rbenv_bundle = Path.home() / ".rbenv" / "shims" / "bundle"
    if rbenv_bundle.exists() and os.access(rbenv_bundle, os.X_OK):
        return str(rbenv_bundle)
    return shutil.which("bundle")


def ordered_search_doc_ids(doc_ids: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for raw_doc_id in doc_ids:
        doc_id = str(raw_doc_id or "").strip()
        if not doc_id or doc_id in seen:
            continue
        seen.add(doc_id)
        ordered.append(doc_id)
    return ordered


def rebuild_scope_outputs(
    repo_root: Path,
    scope: str,
    include_search: bool = True,
    search_doc_ids: Optional[list[str]] = None,
) -> Dict[str, Any]:
    bundle_bin = detect_bundle_bin()
    if not bundle_bin:
        raise RuntimeError("bundle executable not found")

    commands = [[bundle_bin, "exec", "ruby", "scripts/build_docs.rb", "--scope", scope, "--write"]]
    search = {"mode": "none", "doc_ids": []}
    if include_search:
        if search_doc_ids is None:
            search = {"mode": "full", "doc_ids": []}
            commands.append([bundle_bin, "exec", "ruby", "scripts/build_search.rb", "--scope", scope, "--write"])
        else:
            target_doc_ids = ordered_search_doc_ids(search_doc_ids)
            search = {"mode": "targeted" if target_doc_ids else "none", "doc_ids": target_doc_ids}
            if target_doc_ids:
                commands.append(
                    [
                        bundle_bin,
                        "exec",
                        "ruby",
                        "scripts/build_search.rb",
                        "--scope",
                        scope,
                        "--write",
                        "--only-doc-ids",
                        ",".join(target_doc_ids),
                        "--remove-missing",
                    ]
                )
    steps = []
    for command in commands:
        completed = subprocess.run(
            command,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
        steps.append(
            {
                "command": " ".join(command),
                "returncode": completed.returncode,
                "stdout": completed.stdout.strip(),
                "stderr": completed.stderr.strip(),
            }
        )
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip() or f"exit {completed.returncode}"
            raise RuntimeError(f"rebuild failed for {scope}: {detail}")
    return {
        "ok": True,
        "steps": steps,
        "search": search,
    }


def perform_source_write_and_rebuild(
    repo_root: Path,
    scope: str,
    changed_paths: list[Path],
    write_operation: Callable[[], Any],
    *,
    suppression_reason: str,
    include_search: bool = True,
    search_doc_ids: Optional[list[str]] = None,
) -> Dict[str, Any]:
    root = scope_root(repo_root, scope)
    filenames = sorted(
        {
            path.resolve().relative_to(root.resolve()).as_posix()
            for path in changed_paths
            if isinstance(path, Path)
        }
    )
    if filenames:
        set_watch_suppressions(
            repo_root,
            scope,
            filenames,
            status=SUPPRESSION_PENDING,
            reason=suppression_reason,
            ttl_seconds=DEFAULT_PENDING_TTL_SECONDS,
        )
    try:
        write_operation()
        rebuild = rebuild_scope_outputs(
            repo_root,
            scope,
            include_search=include_search,
            search_doc_ids=search_doc_ids,
        )
    except Exception:
        if filenames:
            clear_watch_suppressions(repo_root, scope, filenames)
        raise
    if filenames:
        set_watch_suppressions(
            repo_root,
            scope,
            filenames,
            status=SUPPRESSION_COMPLETE,
            reason=suppression_reason,
            ttl_seconds=DEFAULT_COMPLETE_TTL_SECONDS,
        )
    return rebuild


def rebuild_all_docs_outputs(repo_root: Path) -> Dict[str, Any]:
    bundle_bin = detect_bundle_bin()
    if not bundle_bin:
        raise RuntimeError("bundle executable not found")

    commands = [
        [bundle_bin, "exec", "ruby", "scripts/build_docs.rb", "--write"],
    ]
    for scope in DOCS_SCOPE_CONFIGS:
        commands.append([bundle_bin, "exec", "ruby", "scripts/build_search.rb", "--scope", scope, "--write"])
    steps = []
    for command in commands:
        completed = subprocess.run(
            command,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
        steps.append(
            {
                "command": " ".join(command),
                "returncode": completed.returncode,
                "stdout": completed.stdout.strip(),
                "stderr": completed.stderr.strip(),
            }
        )
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip() or f"exit {completed.returncode}"
            raise RuntimeError(f"docs rebuild failed: {detail}")
    return {
        "ok": True,
        "steps": steps,
        "summary_text": f"Docs and docs search rebuilt for {', '.join(DOCS_SCOPE_CONFIGS)}.",
    }
