#!/usr/bin/env python3
"""Docs Management source-write follow-through and rebuild helpers."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
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


def rebuild_scope_outputs(
    repo_root: Path,
    scope: str,
    include_search: bool = True,
    search_doc_ids: Optional[list[str]] = None,
) -> Dict[str, Any]:
    bundle_bin = detect_bundle_bin()
    if not bundle_bin:
        raise RuntimeError("bundle executable not found")

    commands = [("docs", [bundle_bin, "exec", "ruby", "scripts/build_docs.rb", "--scope", scope, "--write"])]
    search = {"mode": "none", "doc_ids": []}
    if include_search:
        if search_doc_ids is None:
            search = {"mode": "full", "doc_ids": []}
            commands.append(("search", [bundle_bin, "exec", "ruby", "scripts/build_search.rb", "--scope", scope, "--write"]))
        else:
            target_doc_ids = ordered_search_doc_ids(search_doc_ids)
            search = {"mode": "targeted" if target_doc_ids else "none", "doc_ids": target_doc_ids}
            if target_doc_ids:
                commands.append(
                    (
                        "search",
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
                        ],
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
            raise RuntimeError(f"rebuild failed for {scope}: {detail}")
    return {
        "ok": True,
        "steps": steps,
        "search": search,
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

    try:
        scope_ids = list(load_docs_scope_configs(repo_root).keys())
    except (FileNotFoundError, ValueError):
        scope_ids = list(DOCS_SCOPE_CONFIGS.keys())

    commands = [
        ("docs", [bundle_bin, "exec", "ruby", "scripts/build_docs.rb", "--write"]),
    ]
    for scope in scope_ids:
        commands.append(("search", [bundle_bin, "exec", "ruby", "scripts/build_search.rb", "--scope", scope, "--write"]))
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
            raise RuntimeError(f"docs rebuild failed: {detail}")
    return {
        "ok": True,
        "steps": steps,
        "diagnostics": {
            "docs": docs_diagnostics,
            "search": search_diagnostics,
        },
        "summary_text": f"Docs and docs search rebuilt for {', '.join(DOCS_SCOPE_CONFIGS)}.",
    }
