#!/usr/bin/env python3
"""Docs Management source-write follow-through and rebuild helpers."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from docs_scope_config import DOCS_SCOPE_CONFIGS, load_docs_scope_configs
from docs_source_model import scope_root
from docs_watch_suppression import (
    DEFAULT_COMPLETE_TTL_SECONDS,
    DEFAULT_PENDING_TTL_SECONDS,
    SUPPRESSION_COMPLETE,
    SUPPRESSION_PENDING,
    clear_watch_suppressions,
    set_watch_suppressions,
)

DOCS_BUILDER_DIAGNOSTICS_PREFIX = "Docs builder diagnostics: "
FRONT_MATTER_ERROR_PREFIX = "problem with front-matter on doc "
PYTHON_EXECUTABLE = sys.executable
DOCS_BUILDER_SCRIPT = "docs-viewer/build/build_docs.py"
SEARCH_BUILDER_SCRIPT = "docs-viewer/build/build_search.py"


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


def targeted_docs_build_fallback_reason(repo_root: Path, scope: str, target_doc_ids: list[str]) -> str:
    try:
        config = load_docs_scope_configs(repo_root)[scope]
    except (KeyError, FileNotFoundError, ValueError) as exc:
        return f"full-scope fallback: docs scope config unavailable: {exc}"

    output_dir = repo_root / config.output
    index_path = output_dir / "index.json"
    references_index_path = output_dir / "references" / "index.json"
    if not index_path.exists():
        return "full-scope fallback: existing docs index missing"
    if not references_index_path.exists():
        return "full-scope fallback: existing references index missing"

    try:
        index_payload = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return f"full-scope fallback: existing docs index unreadable: {exc}"
    docs = index_payload.get("docs") if isinstance(index_payload, dict) else None
    if not isinstance(docs, list):
        return "full-scope fallback: existing docs index has no docs array"

    target_set = set(target_doc_ids)
    missing_payload_ids: list[str] = []
    for item in docs:
        if not isinstance(item, dict):
            continue
        doc_id = str(item.get("doc_id") or "").strip()
        if doc_id and doc_id not in target_set and not (output_dir / "by-id" / f"{doc_id}.json").exists():
            missing_payload_ids.append(doc_id)
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

    changed_match = re.search(
        r"Changed:\s*(\d+)\.\s*Removed:\s*(\d+)\.\s*Unchanged:\s*(\d+)\.\s*Full fallback:\s*(\d+)",
        stdout,
    )
    if changed_match:
        diagnostics.update(
            {
                "changed": int(changed_match.group(1)),
                "removed": int(changed_match.group(2)),
                "unchanged": int(changed_match.group(3)),
                "full_fallback": bool(int(changed_match.group(4))),
            }
        )

    count_match = re.search(r"\bwith\s+(\d+)\s+\S+\s+search entries\b", stdout)
    if count_match:
        diagnostics["entries"] = int(count_match.group(1))

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
    commands = [("docs", docs_command)]
    search = {"mode": "none", "doc_ids": []}
    if include_search:
        if search_doc_ids is None:
            search = {"mode": "full", "doc_ids": []}
            commands.append(("search", python_builder_command(SEARCH_BUILDER_SCRIPT, "--scope", scope, "--write")))
        else:
            target_doc_ids = ordered_search_doc_ids(search_doc_ids)
            search = {"mode": "targeted" if target_doc_ids else "none", "doc_ids": target_doc_ids}
            if target_doc_ids:
                commands.append(
                    (
                        "search",
                        python_builder_command(
                            SEARCH_BUILDER_SCRIPT,
                            "--scope",
                            scope,
                            "--write",
                            "--only-doc-ids",
                            ",".join(target_doc_ids),
                            "--remove-missing",
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
            docs_doc_ids=docs_doc_ids,
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
        root = scope_root(repo_root, scope)
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
