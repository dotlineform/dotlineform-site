#!/usr/bin/env python3
"""Docs Management source-write follow-through and rebuild helpers."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional

from docs_scope_config import (
    DOCS_SCOPE_CONFIGS,
    document_source_path,
    load_docs_scope_configs,
    published_documents_path,
    resolve_scope_path,
)
from docs_source_model import load_scope_docs_for_config, scope_root, write_bytes_atomic
from docs_watch_suppression import (
    DEFAULT_COMPLETE_TTL_SECONDS,
    DEFAULT_PENDING_TTL_SECONDS,
    SUPPRESSION_COMPLETE,
    SUPPRESSION_PENDING,
    clear_watch_suppressions,
    set_watch_suppressions,
    watch_suppression_owner,
)

DOCS_BUILDER_DIAGNOSTICS_PREFIX = "Docs builder diagnostics: "
FRONT_MATTER_ERROR_PREFIX = "problem with front-matter on doc "
PYTHON_EXECUTABLE = sys.executable
DOCS_BUILDER_SCRIPT = "docs-viewer/build/build_docs.py"
SEARCH_BUILDER_SCRIPT = "docs-viewer/build/build_search.py"


class SubScopeWriteRebuildFailure(RuntimeError):
    """Report one failed child write/rebuild after its owned rollback attempt."""

    def __init__(self, message: str, *, rollback: dict[str, Any]):
        super().__init__(message)
        self.rollback = rollback


class SubScopeSourceSnapshotChanged(RuntimeError):
    """Stop one child write boundary before mutation when its snapshot changed."""


class ScopeWriteRebuildFailure(RuntimeError):
    """Report one failed top-level write/rebuild after its owned rollback attempt."""

    def __init__(self, message: str, *, rollback: dict[str, Any]):
        super().__init__(message)
        self.rollback = rollback


class ScopeSourceSnapshotChanged(RuntimeError):
    """Stop one top-level write boundary before mutation when its snapshot changed."""


def current_scope_source_root(repo_root: Path, scope: str) -> Path:
    try:
        configs = load_docs_scope_configs(repo_root)
    except FileNotFoundError:
        return scope_root(repo_root, scope)
    config = configs.get(scope)
    if config is None:
        raise ValueError(f"scope {scope!r} is not configured")
    return resolve_scope_path(repo_root, document_source_path(config))


def current_sub_scope_source_root(repo_root: Path, scope: str, sub_scope: str) -> Path:
    configs = load_docs_scope_configs(repo_root, scope_ids=[scope])
    try:
        config = configs[scope]
    except KeyError as exc:
        raise ValueError(f"scope {scope!r} is not configured") from exc
    matching = [
        candidate
        for candidate in config.sub_scopes
        if candidate.sub_scope == sub_scope
    ]
    if not matching:
        raise ValueError(f"sub-scope {scope}/{sub_scope} is not configured")
    return resolve_scope_path(repo_root, document_source_path(matching[0]))


def python_builder_command(script: str, *args: str) -> list[str]:
    return [PYTHON_EXECUTABLE, script, *args]


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


def ordered_docs_doc_ids(doc_ids: list[str]) -> list[str]:
    return ordered_search_doc_ids(doc_ids)


def iter_docs_tree_records(docs: Any) -> list[Dict[str, Any]]:
    if not isinstance(docs, list):
        return []
    records: list[Dict[str, Any]] = []
    stack = [doc for doc in docs if isinstance(doc, dict)]
    while stack:
        record = stack.pop(0)
        records.append(record)
        children = record.get("children")
        if isinstance(children, list):
            stack.extend(child for child in children if isinstance(child, dict))
    return records


def targeted_docs_build_fallback_reason(repo_root: Path, scope: str, target_doc_ids: list[str]) -> str:
    try:
        config = load_docs_scope_configs(repo_root)[scope]
    except (KeyError, FileNotFoundError, ValueError) as exc:
        return f"full-scope fallback: docs scope config unavailable: {exc}"

    output_dir = resolve_scope_path(repo_root, published_documents_path(config))
    index_tree_path = output_dir / "index-tree.json"
    semantic_token_index_path = output_dir / "semantic-tokens" / "index.json"
    if not index_tree_path.exists():
        return "full-scope fallback: existing docs index tree missing"
    if not semantic_token_index_path.exists():
        return "full-scope fallback: existing semantic-token index missing"

    try:
        index_payload = json.loads(index_tree_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return f"full-scope fallback: existing docs index tree unreadable: {exc}"
    docs = index_payload.get("docs") if isinstance(index_payload, dict) else None
    if not iter_docs_tree_records(docs):
        return "full-scope fallback: existing docs index tree has no docs array"

    try:
        current_docs = load_scope_docs_for_config(repo_root, config)
    except (OSError, ValueError) as exc:
        return f"full-scope fallback: current source docs unavailable: {exc}"

    target_set = set(target_doc_ids)
    missing_payload_ids = [
        doc.doc_id
        for doc in current_docs
        if doc.doc_id not in target_set and not (output_dir / "by-id" / f"{doc.doc_id}.json").exists()
    ]
    if missing_payload_ids:
        return "full-scope fallback: existing payloads missing for unselected docs"
    return ""


def extract_docs_builder_diagnostics(stdout: str) -> list[Dict[str, Any]]:
    diagnostics: list[Dict[str, Any]] = []
    for line in stdout.splitlines():
        text = line.strip()
        if not text.startswith(DOCS_BUILDER_DIAGNOSTICS_PREFIX):
            continue
        raw_payload = text[len(DOCS_BUILDER_DIAGNOSTICS_PREFIX) :].strip()
        try:
            payload = json.loads(raw_payload)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            diagnostics.append(payload)
    return diagnostics


def extract_search_step_diagnostics(stdout: str, search: Dict[str, Any]) -> Dict[str, Any]:
    diagnostics: Dict[str, Any] = {
        "mode": search.get("mode", "none"),
        "doc_ids": list(search.get("doc_ids", [])),
    }
    if diagnostics["mode"] == "none":
        return diagnostics

    count_match = re.search(r"\bwith\s+(\d+)\s+\S+\s+search docs\b", stdout)
    if count_match:
        diagnostics["docs"] = int(count_match.group(1))

    skipped_match = re.search(r"\bSkipped:\s*(\d+)\b", stdout)
    if skipped_match:
        diagnostics["skipped"] = int(skipped_match.group(1))

    wrote_match = re.search(r"\bWrote:\s*(\d+)\b", stdout)
    if wrote_match:
        diagnostics["wrote"] = int(wrote_match.group(1))

    return diagnostics


def run_rebuild_command(command: list[str], repo_root: Path) -> Dict[str, Any]:
    started_at = time.perf_counter()
    completed = subprocess.run(
        command,
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "command": " ".join(command),
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
        "elapsed_seconds": round(time.perf_counter() - started_at, 3),
    }


def rebuild_failure_message(prefix: str, detail: str) -> str:
    clean_detail = str(detail or "").strip()
    if clean_detail.startswith(FRONT_MATTER_ERROR_PREFIX):
        return clean_detail
    return f"{prefix}: {clean_detail}"


def rebuild_scope_outputs(
    repo_root: Path,
    scope: str,
    include_search: bool = True,
    search_doc_ids: Optional[list[str]] = None,
    docs_doc_ids: Optional[list[str]] = None,
    skip_media_builds: bool = False,
) -> Dict[str, Any]:
    docs_mode = "full"
    docs_target_doc_ids: list[str] = []
    docs_reason = "full-scope fallback: no targeted docs payload ids provided"
    docs_command = python_builder_command(DOCS_BUILDER_SCRIPT, "--scope", scope, "--write", "--diagnostics")
    if docs_doc_ids is not None:
        docs_target_doc_ids = ordered_docs_doc_ids(docs_doc_ids)
        if docs_target_doc_ids:
            fallback_reason = targeted_docs_build_fallback_reason(repo_root, scope, docs_target_doc_ids)
            if fallback_reason:
                docs_reason = fallback_reason
            else:
                docs_mode = "targeted"
                docs_reason = "targeted docs payload ids provided"
                docs_command.extend(["--only-doc-ids", ",".join(docs_target_doc_ids)])
        else:
            docs_reason = "full-scope fallback: targeted docs payload ids normalized empty"
    if skip_media_builds:
        docs_command.append("--skip-media-builds")
    commands = [("docs", docs_command)]
    search = {"mode": "none", "doc_ids": []}
    if include_search:
        if search_doc_ids is None:
            search = {"mode": "full", "doc_ids": []}
            commands.append(("search", python_builder_command(SEARCH_BUILDER_SCRIPT, "--scope", scope, "--write")))
        else:
            target_doc_ids = ordered_search_doc_ids(search_doc_ids)
            search = {"mode": "full" if target_doc_ids else "none", "doc_ids": target_doc_ids}
            if target_doc_ids:
                commands.append(
                    (
                        "search",
                        python_builder_command(
                            SEARCH_BUILDER_SCRIPT,
                            "--scope",
                            scope,
                            "--write",
                        ),
                    )
                )
    steps = []
    docs_diagnostics: Optional[Dict[str, Any]] = None
    search_diagnostics = extract_search_step_diagnostics("", search)
    for label, command in commands:
        step = run_rebuild_command(command, repo_root)
        steps.append(step)
        if label == "docs":
            docs_payloads = extract_docs_builder_diagnostics(step["stdout"])
            docs_diagnostics = docs_payloads[-1] if docs_payloads else None
        elif label == "search":
            search_diagnostics = extract_search_step_diagnostics(step["stdout"], search)
            search_diagnostics["elapsed_seconds"] = step["elapsed_seconds"]
        if step["returncode"] != 0:
            detail = step["stderr"] or step["stdout"] or f"exit {step['returncode']}"
            raise RuntimeError(rebuild_failure_message(f"rebuild failed for {scope}", detail))
    return {
        "ok": True,
        "steps": steps,
        "search": search,
        "docs": {"mode": docs_mode, "doc_ids": docs_target_doc_ids, "reason": docs_reason},
        "diagnostics": {
            "docs": docs_diagnostics,
            "search": search_diagnostics,
        },
    }


def rebuild_sub_scope_outputs(
    repo_root: Path,
    scope: str,
    sub_scope: str,
) -> Dict[str, Any]:
    docs_command = python_builder_command(
        DOCS_BUILDER_SCRIPT,
        "--scope",
        scope,
        "--sub-scope",
        sub_scope,
        "--write",
        "--diagnostics",
        "--skip-browser-config",
    )
    steps = []
    docs_diagnostics: Optional[Dict[str, Any]] = None
    step = run_rebuild_command(docs_command, repo_root)
    steps.append(step)
    docs_payloads = extract_docs_builder_diagnostics(step["stdout"])
    docs_diagnostics = docs_payloads[-1] if docs_payloads else None
    if step["returncode"] != 0:
        detail = step["stderr"] or step["stdout"] or f"exit {step['returncode']}"
        raise RuntimeError(
            rebuild_failure_message(
                f"rebuild failed for {scope}/{sub_scope}",
                detail,
            )
        )
    return {
        "ok": True,
        "steps": steps,
        "search": {"mode": "none", "doc_ids": []},
        "docs": {
            "mode": "sub_scope",
            "doc_ids": [],
            "sub_scope": sub_scope,
            "reason": "configured sub-scope rebuild",
        },
        "diagnostics": {
            "docs": docs_diagnostics,
            "search": {"mode": "none", "doc_ids": []},
        },
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
    docs_doc_ids: Optional[list[str]] = None,
    written_paths: Optional[list[Path]] = None,
    skip_media_builds: bool = False,
) -> Dict[str, Any]:
    root = current_scope_source_root(repo_root, scope)
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
            docs_doc_ids=docs_doc_ids,
            skip_media_builds=skip_media_builds,
        )
    except Exception:
        if filenames:
            clear_watch_suppressions(repo_root, scope, filenames)
        raise
    completion_filenames = filenames
    if written_paths is not None:
        completion_filenames = sorted(
            {
                path.resolve().relative_to(root.resolve()).as_posix()
                for path in written_paths
                if isinstance(path, Path)
            }
        )
        if filenames:
            clear_watch_suppressions(repo_root, scope, filenames)
    if completion_filenames:
        set_watch_suppressions(
            repo_root,
            scope,
            completion_filenames,
            status=SUPPRESSION_COMPLETE,
            reason=suppression_reason,
            ttl_seconds=DEFAULT_COMPLETE_TTL_SECONDS,
        )
    return rebuild


def perform_scope_source_write_and_rebuild_atomic(
    repo_root: Path,
    scope: str,
    changed_paths: list[Path],
    write_operation: Callable[[], Any],
    *,
    suppression_reason: str,
    source_snapshots: Mapping[Path, bytes],
    search_doc_ids: Optional[list[str]] = None,
    docs_doc_ids: Optional[list[str]] = None,
) -> Dict[str, Any]:
    """Write/rebuild one parent scope or restore its complete source snapshot."""

    root = current_scope_source_root(repo_root, scope)
    resolved_changed_paths = {
        path.resolve()
        for path in changed_paths
        if isinstance(path, Path)
    }
    normalized_snapshots = {
        path.resolve(): source_bytes
        for path, source_bytes in source_snapshots.items()
    }
    if set(normalized_snapshots) != resolved_changed_paths:
        raise ValueError(
            "scope rollback snapshot must cover every changed source exactly",
        )
    if any(
        not isinstance(source_bytes, bytes)
        for source_bytes in normalized_snapshots.values()
    ):
        raise ValueError("scope rollback snapshot values must be bytes")
    for path in normalized_snapshots:
        try:
            path.relative_to(root.resolve())
        except ValueError as exc:
            raise ValueError(
                "scope rollback snapshot escapes configured source root",
            ) from exc
    filenames = sorted(
        path.relative_to(root.resolve()).as_posix()
        for path in resolved_changed_paths
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
        changed_before_write = [
            path.name
            for path, source_bytes in normalized_snapshots.items()
            if path.read_bytes() != source_bytes
        ]
        if changed_before_write:
            raise ScopeSourceSnapshotChanged(
                "scope sources changed immediately before apply: "
                + ", ".join(sorted(changed_before_write)),
            )
        write_operation()
        rebuild = rebuild_scope_outputs(
            repo_root,
            scope,
            include_search=True,
            search_doc_ids=search_doc_ids,
            docs_doc_ids=docs_doc_ids,
            skip_media_builds=True,
        )
    except ScopeSourceSnapshotChanged:
        if filenames:
            clear_watch_suppressions(repo_root, scope, filenames)
        raise
    except Exception as exc:
        restoration_errors: list[str] = []
        for path, source_bytes in normalized_snapshots.items():
            try:
                write_bytes_atomic(path, source_bytes)
            except Exception as restore_exc:
                restoration_errors.append(
                    str(restore_exc).strip() or restore_exc.__class__.__name__,
                )
        recovery_rebuild: dict[str, Any] | None = None
        recovery_error = ""
        if not restoration_errors:
            try:
                recovery_rebuild = rebuild_scope_outputs(
                    repo_root,
                    scope,
                    include_search=True,
                    search_doc_ids=search_doc_ids,
                    docs_doc_ids=docs_doc_ids,
                    skip_media_builds=True,
                )
            except Exception as recovery_exc:
                recovery_error = (
                    str(recovery_exc).strip()
                    or recovery_exc.__class__.__name__
                )
        rollback_status = (
            "failed"
            if restoration_errors or recovery_error
            else "completed"
        )
        if filenames:
            if rollback_status == "completed":
                set_watch_suppressions(
                    repo_root,
                    scope,
                    filenames,
                    status=SUPPRESSION_COMPLETE,
                    reason=f"{suppression_reason}-rollback",
                    ttl_seconds=DEFAULT_COMPLETE_TTL_SECONDS,
                )
            else:
                clear_watch_suppressions(repo_root, scope, filenames)
        raise ScopeWriteRebuildFailure(
            str(exc).strip() or exc.__class__.__name__,
            rollback={
                "status": rollback_status,
                "sources_restored": not restoration_errors,
                "rebuild": recovery_rebuild,
                "error": "; ".join(
                    [*restoration_errors, recovery_error],
                ).strip("; "),
            },
        ) from exc
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


def perform_sub_scope_source_write_and_rebuild(
    repo_root: Path,
    scope: str,
    sub_scope: str,
    changed_paths: list[Path],
    write_operation: Callable[[], Any],
    *,
    suppression_reason: str,
    source_snapshots: Mapping[Path, bytes] | None = None,
) -> Dict[str, Any]:
    root = current_sub_scope_source_root(repo_root, scope, sub_scope)
    resolved_changed_paths = {
        path.resolve()
        for path in changed_paths
        if isinstance(path, Path)
    }
    normalized_snapshots: dict[Path, bytes] | None = None
    if source_snapshots is not None:
        normalized_snapshots = {
            path.resolve(): source_bytes
            for path, source_bytes in source_snapshots.items()
        }
        if set(normalized_snapshots) != resolved_changed_paths:
            raise ValueError(
                "sub-scope rollback snapshot must cover every changed source exactly"
            )
        if any(not isinstance(source_bytes, bytes) for source_bytes in normalized_snapshots.values()):
            raise ValueError("sub-scope rollback snapshot values must be bytes")
        for path in normalized_snapshots:
            try:
                path.relative_to(root.resolve())
            except ValueError as exc:
                raise ValueError(
                    "sub-scope rollback snapshot escapes configured source root"
                ) from exc
    filenames = sorted(
        {
            path.resolve().relative_to(root.resolve()).as_posix()
            for path in changed_paths
            if isinstance(path, Path)
        }
    )
    suppression_owner = watch_suppression_owner(scope, sub_scope)
    if filenames:
        set_watch_suppressions(
            repo_root,
            suppression_owner,
            filenames,
            status=SUPPRESSION_PENDING,
            reason=suppression_reason,
            ttl_seconds=DEFAULT_PENDING_TTL_SECONDS,
        )
    try:
        if normalized_snapshots is not None:
            changed_before_write = [
                path.name
                for path, source_bytes in normalized_snapshots.items()
                if path.read_bytes() != source_bytes
            ]
            if changed_before_write:
                raise SubScopeSourceSnapshotChanged(
                    "sub-scope sources changed immediately before apply: "
                    + ", ".join(sorted(changed_before_write))
                )
        write_operation()
        rebuild = rebuild_sub_scope_outputs(repo_root, scope, sub_scope)
    except SubScopeSourceSnapshotChanged:
        if filenames:
            clear_watch_suppressions(repo_root, suppression_owner, filenames)
        raise
    except Exception as exc:
        if normalized_snapshots is None:
            if filenames:
                clear_watch_suppressions(repo_root, suppression_owner, filenames)
            raise
        restoration_errors: list[str] = []
        for path, source_bytes in normalized_snapshots.items():
            try:
                write_bytes_atomic(path, source_bytes)
            except Exception as restore_exc:
                restoration_errors.append(str(restore_exc).strip() or restore_exc.__class__.__name__)
        recovery_rebuild: dict[str, Any] | None = None
        recovery_error = ""
        if not restoration_errors:
            try:
                recovery_rebuild = rebuild_sub_scope_outputs(repo_root, scope, sub_scope)
            except Exception as recovery_exc:
                recovery_error = str(recovery_exc).strip() or recovery_exc.__class__.__name__
        rollback_status = "failed" if restoration_errors or recovery_error else "completed"
        if filenames:
            if rollback_status == "completed":
                set_watch_suppressions(
                    repo_root,
                    suppression_owner,
                    filenames,
                    status=SUPPRESSION_COMPLETE,
                    reason=f"{suppression_reason}-rollback",
                    ttl_seconds=DEFAULT_COMPLETE_TTL_SECONDS,
                )
            else:
                clear_watch_suppressions(repo_root, suppression_owner, filenames)
        raise SubScopeWriteRebuildFailure(
            str(exc).strip() or exc.__class__.__name__,
            rollback={
                "status": rollback_status,
                "sources_restored": not restoration_errors,
                "rebuild": recovery_rebuild,
                "error": "; ".join([*restoration_errors, recovery_error]).strip("; "),
            },
        ) from exc
    if filenames:
        set_watch_suppressions(
            repo_root,
            suppression_owner,
            filenames,
            status=SUPPRESSION_COMPLETE,
            reason=suppression_reason,
            ttl_seconds=DEFAULT_COMPLETE_TTL_SECONDS,
        )
    return rebuild


def perform_multi_scope_source_write_and_rebuild(
    repo_root: Path,
    rebuild_plans: list[Dict[str, Any]],
    write_operation: Callable[[], Any],
    *,
    suppression_reason: str,
) -> Dict[str, Any]:
    suppressions: list[tuple[str, list[str]]] = []
    for plan in rebuild_plans:
        scope = str(plan.get("scope") or "").strip()
        root = current_scope_source_root(repo_root, scope)
        filenames = sorted(
            {
                path.resolve().relative_to(root.resolve()).as_posix()
                for path in plan.get("changed_paths", [])
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
            suppressions.append((scope, filenames))
    try:
        write_operation()
        rebuilds: Dict[str, Any] = {}
        for plan in rebuild_plans:
            scope = str(plan.get("scope") or "").strip()
            rebuilds[scope] = rebuild_scope_outputs(
                repo_root,
                scope,
                include_search=plan.get("include_search") is not False,
                search_doc_ids=plan.get("search_doc_ids"),
                docs_doc_ids=plan.get("docs_doc_ids"),
            )
    except Exception:
        for scope, filenames in suppressions:
            clear_watch_suppressions(repo_root, scope, filenames)
        raise
    for scope, filenames in suppressions:
        set_watch_suppressions(
            repo_root,
            scope,
            filenames,
            status=SUPPRESSION_COMPLETE,
            reason=suppression_reason,
            ttl_seconds=DEFAULT_COMPLETE_TTL_SECONDS,
        )
    return {
        "ok": True,
        "scopes": rebuilds,
    }


def rebuild_all_docs_outputs(repo_root: Path) -> Dict[str, Any]:
    try:
        scope_ids = list(load_docs_scope_configs(repo_root).keys())
    except FileNotFoundError:
        scope_ids = list(DOCS_SCOPE_CONFIGS.keys())

    commands = [
        ("docs", python_builder_command(DOCS_BUILDER_SCRIPT, "--write", "--diagnostics")),
    ]
    for scope in scope_ids:
        commands.append(("search", python_builder_command(SEARCH_BUILDER_SCRIPT, "--scope", scope, "--write")))
    steps = []
    docs_diagnostics: list[Dict[str, Any]] = []
    search_diagnostics: list[Dict[str, Any]] = []
    for label, command in commands:
        step = run_rebuild_command(command, repo_root)
        steps.append(step)
        if label == "docs":
            docs_diagnostics.extend(extract_docs_builder_diagnostics(step["stdout"]))
        elif label == "search":
            scope_index = len(search_diagnostics)
            scope_id = scope_ids[scope_index] if scope_index < len(scope_ids) else ""
            diagnostics = extract_search_step_diagnostics(step["stdout"], {"mode": "full", "doc_ids": []})
            diagnostics["scope"] = scope_id
            diagnostics["elapsed_seconds"] = step["elapsed_seconds"]
            search_diagnostics.append(diagnostics)
        if step["returncode"] != 0:
            detail = step["stderr"] or step["stdout"] or f"exit {step['returncode']}"
            raise RuntimeError(rebuild_failure_message("docs rebuild failed", detail))
    return {
        "ok": True,
        "steps": steps,
        "diagnostics": {
            "docs": docs_diagnostics,
            "search": search_diagnostics,
        },
        "summary_text": f"Docs and docs search rebuilt for {', '.join(DOCS_SCOPE_CONFIGS)}.",
    }
