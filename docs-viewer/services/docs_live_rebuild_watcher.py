#!/usr/bin/env python3
"""
Watch docs source roots and rebuild same-scope docs payloads plus docs search.

Run:
  ./docs-viewer/services/docs_live_rebuild_watcher.py
  ./docs-viewer/services/docs_live_rebuild_watcher.py --poll-seconds 0.5 --debounce-seconds 1.5
  ./docs-viewer/services/docs_live_rebuild_watcher.py --repo-root /path/to/dotlineform-site
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, Optional

_BOOTSTRAP_START = Path(__file__).resolve()
for _candidate in (_BOOTSTRAP_START.parent, *_BOOTSTRAP_START.parents):
    if (_candidate / "site-tools" / "config" / "site-tools.json").exists():
        if str(_candidate) not in sys.path:
            sys.path.insert(0, str(_candidate))
        break

from studio.shared.python.studio_python_paths import ensure_studio_python_paths

REPO_ROOT = ensure_studio_python_paths(__file__)
SCRIPTS_DOCS_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
for path in (SCRIPTS_DIR, SCRIPTS_DOCS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from docs_source_model import (
    current_doc_timestamp,
    is_doc_timestamp,
    load_scope_docs,
    recent_edit_content,
    rewrite_front_matter_source_timestamp,
    scope_doc_sort_key,
    source_revision,
    split_source_text,
    strictly_later_doc_timestamp,
    write_text_atomic,
)
from docs_artifact_locations import (
    ArtifactLocation,
    artifact_location_adapter,
    authenticated_remote_client_for_locations,
)
from docs_mermaid_media import produce_mermaid_svg
from docs_scope_config import (
    CONFIG_REL_PATH,
    DOCS_SCOPE_CONFIGS,
    DOCUMENT_SOURCE_ROOTS,
    document_source_path,
    load_docs_scope_configs,
    resolve_scope_path,
)
from docs_write_rebuild import targeted_docs_build_fallback_reason
from docs_watch_suppression import (
    SUPPRESSION_COMPLETE,
    clear_watch_suppressions,
    load_active_watch_suppressions,
    watch_suppression_owner,
)
from local_env import runtime_env

DOCS_BUILDER_DIAGNOSTICS_PREFIX = "Docs builder diagnostics: "
PYTHON_EXECUTABLE = sys.executable
DOCS_BUILDER_SCRIPT = "docs-viewer/build/build_docs.py"
SEARCH_BUILDER_SCRIPT = "docs-viewer/build/build_search.py"


def log(message: str) -> None:
    print(f"[docs-watch] {message}", flush=True)


def find_repo_root(start: Path) -> Optional[Path]:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "site-tools" / "config" / "site-tools.json").exists():
            return candidate
    return None


def detect_repo_root(explicit_root: str) -> Path:
    if explicit_root:
        repo_root = Path(explicit_root).expanduser().resolve()
        if not (repo_root / "site-tools" / "config" / "site-tools.json").exists():
            raise SystemExit(f"--repo-root does not look like repo root (missing site-tools/config/site-tools.json): {repo_root}")
        return repo_root

    for start in [Path.cwd(), Path(__file__).resolve().parent]:
        found = find_repo_root(start)
        if found is not None:
            return found

    raise SystemExit("Could not auto-detect repo root. Pass --repo-root.")


def python_builder_command(script: str, *args: str) -> list[str]:
    return [PYTHON_EXECUTABLE, script, *args]


def snapshot_scope(root: Path, scope: str) -> Dict[str, tuple[int, int]]:
    if not root.exists():
        raise FileNotFoundError(f"Source root not found: {root}")

    snapshot: Dict[str, tuple[int, int]] = {}
    for path in sorted(root.glob("**/*.md")):
        try:
            stat = path.stat()
        except FileNotFoundError:
            continue
        snapshot[path.relative_to(root).as_posix()] = (stat.st_mtime_ns, stat.st_size)
    return snapshot


def snapshot_markdown_root(root: Path) -> Dict[str, tuple[int, int]]:
    if not root.exists():
        raise FileNotFoundError(f"Source root not found: {root}")

    snapshot: Dict[str, tuple[int, int]] = {}
    for path in sorted(root.glob("**/*.md")):
        try:
            stat = path.stat()
        except FileNotFoundError:
            continue
        snapshot[path.relative_to(root).as_posix()] = (stat.st_mtime_ns, stat.st_size)
    return snapshot


def snapshot_mermaid_root(root: Path) -> Dict[str, tuple[int, int]]:
    if not root.exists():
        raise FileNotFoundError(f"Source root not found: {root}")

    snapshot: Dict[str, tuple[int, int]] = {}
    for path in sorted(root.glob("**/*.mmd")):
        try:
            stat = path.stat()
        except FileNotFoundError:
            continue
        snapshot[path.relative_to(root).as_posix()] = (stat.st_mtime_ns, stat.st_size)
    return snapshot


def state_snapshot(state: dict[str, Any]) -> Dict[str, tuple[int, int]]:
    root = state["root"]
    if state.get("watch_kind") == "build_media":
        return snapshot_mermaid_root(root)
    if state.get("sub_scope"):
        return snapshot_markdown_root(root)
    return snapshot_scope(root, state["scope"])


def try_state_snapshot(state: dict[str, Any]) -> tuple[Optional[Dict[str, tuple[int, int]]], str]:
    try:
        return state_snapshot(state), ""
    except FileNotFoundError as exc:
        return None, str(exc)


def pause_state_for_missing_source(state: dict[str, Any]) -> bool:
    newly_missing = state.get("source_missing") is not True
    state["source_missing"] = True
    state["snapshot"] = {}
    state["doc_snapshot"] = None
    state["dirty_at"] = None
    state["changed_files"] = []
    return newly_missing


def config_file_signature(path: Path) -> tuple[int, int]:
    try:
        stat = path.stat()
    except FileNotFoundError:
        return (0, 0)
    return (stat.st_mtime_ns, stat.st_size)


def sync_scope_config_globals(configs: dict[str, Any]) -> None:
    DOCS_SCOPE_CONFIGS.clear()
    DOCS_SCOPE_CONFIGS.update(configs)
    DOCUMENT_SOURCE_ROOTS.clear()
    DOCUMENT_SOURCE_ROOTS.update({scope: document_source_path(config) for scope, config in configs.items()})


def desired_watch_state_specs(repo_root: Path, configs: dict[str, Any]) -> dict[str, dict[str, Any]]:
    specs: dict[str, dict[str, Any]] = {}

    def add_build_media_specs(
        scope: str,
        sub_scope: str,
        source_config: Any,
        published_config: Any,
    ) -> None:
        for build_type, build in sorted(getattr(source_config, "build_media", {}).items()):
            label_prefix = f"{scope}/{sub_scope}" if sub_scope else scope
            label = f"{label_prefix}/media/{build_type}"
            specs[label] = {
                "scope": scope,
                "sub_scope": sub_scope,
                "label": label,
                "root": resolve_scope_path(repo_root, source_config.location.path / build.path),
                "config": configs[scope],
                "watch_kind": "build_media",
                "build_type": build_type,
                "source_config": source_config,
                "published_config": published_config,
            }

    for scope, config in sorted(configs.items()):
        specs[scope] = {
            "scope": scope,
            "sub_scope": "",
            "label": scope,
            "root": resolve_scope_path(repo_root, document_source_path(config)),
            "config": config,
            "watch_kind": "documents",
        }
        add_build_media_specs(scope, "", config.source, getattr(config, "published", None))
        for sub_scope in config.sub_scopes:
            label = f"{scope}/{sub_scope.sub_scope}"
            specs[label] = {
                "scope": scope,
                "sub_scope": sub_scope.sub_scope,
                "label": label,
                "root": resolve_scope_path(repo_root, document_source_path(sub_scope)),
                "config": config,
                "watch_kind": "documents",
            }
            add_build_media_specs(
                scope,
                sub_scope.sub_scope,
                sub_scope.source,
                getattr(sub_scope, "published", None),
            )
    return specs


def new_watch_state(repo_root: Path, spec: dict[str, Any], *, baseline: bool) -> dict[str, Any]:
    state = {
        **spec,
        "snapshot": {},
        "doc_snapshot": None,
        "dirty_at": None,
        "changed_files": [],
        "source_missing": False,
        "startup_doc_error": "",
        "startup_source_error": "",
    }
    if not baseline:
        return state
    if state.get("watch_kind") == "documents" and not state.get("sub_scope"):
        doc_snapshot, snapshot_error = try_parsed_doc_snapshot(repo_root, state["scope"])
        state["doc_snapshot"] = doc_snapshot
        state["startup_doc_error"] = snapshot_error
    initial_snapshot, source_error = try_state_snapshot(state)
    if initial_snapshot is None:
        pause_state_for_missing_source(state)
        state["startup_source_error"] = source_error
    else:
        state["snapshot"] = initial_snapshot
    return state


def reconcile_watch_states(
    repo_root: Path,
    states: dict[str, dict[str, Any]],
    configs: dict[str, Any],
    *,
    baseline: bool,
) -> dict[str, list[str]]:
    sync_scope_config_globals(configs)
    desired = desired_watch_state_specs(repo_root, configs)
    changes = {"added": [], "removed": [], "reloaded": []}

    for key in sorted(set(states) - set(desired)):
        del states[key]
        changes["removed"].append(key)

    for key, spec in desired.items():
        existing = states.get(key)
        if existing is None:
            states[key] = new_watch_state(repo_root, spec, baseline=baseline)
            changes["added"].append(key)
            continue
        if existing.get("root") != spec["root"] or existing.get("config") != spec["config"]:
            states[key] = new_watch_state(repo_root, spec, baseline=baseline)
            changes["reloaded"].append(key)
    return changes


def watch_roots_log_text(states: dict[str, dict[str, Any]]) -> str:
    return ", ".join(f"{state['root']} -> {state['label']}" for _, state in sorted(states.items()))


def summarize_output(output: str, fallback: str) -> str:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    return lines[-1] if lines else fallback


def extract_docs_builder_diagnostics(stdout: str) -> Optional[Dict[str, Any]]:
    for line in stdout.splitlines():
        text = line.strip()
        if not text.startswith(DOCS_BUILDER_DIAGNOSTICS_PREFIX):
            continue
        raw_payload = text[len(DOCS_BUILDER_DIAGNOSTICS_PREFIX) :].strip()
        try:
            payload = json.loads(raw_payload)
        except json.JSONDecodeError:
            return None
        return payload if isinstance(payload, dict) else None
    return None


def formatted_docs_builder_diagnostics(stdout: str) -> list[str]:
    payload = extract_docs_builder_diagnostics(stdout)
    if not payload:
        return []
    return [f"{key}: {json.dumps(value) if isinstance(value, (list, dict)) else value}" for key, value in payload.items()]


def changed_filenames(previous: Dict[str, tuple[int, int]], current: Dict[str, tuple[int, int]]) -> list[str]:
    filenames = set(previous.keys()) | set(current.keys())
    return sorted(name for name in filenames if previous.get(name) != current.get(name))


def merge_changed_filenames(existing: list[str], detected: list[str]) -> list[str]:
    return ordered_unique([*existing, *detected])


def ordered_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        item = str(value or "").strip()
        if not item or item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def affected_doc_ids_log_text(doc_ids: Optional[list[str]]) -> str:
    if doc_ids is None:
        return "full-search fallback"
    if not doc_ids:
        return "none"
    return ", ".join(doc_ids)


def parsed_doc_snapshot(repo_root: Path, scope: str) -> Dict[str, Dict[str, Any]]:
    docs = load_scope_docs(repo_root, scope)
    root = resolve_scope_path(repo_root, DOCUMENT_SOURCE_ROOTS[scope])
    return {
        doc.path.relative_to(root).as_posix(): {
            "filename": doc.path.relative_to(root).as_posix(),
            "doc_id": doc.doc_id,
            "title": doc.title,
            "parent_id": doc.parent_id,
            "viewable": doc.viewable,
            "added_date": str(doc.front_matter.get("added_date") or "").strip(),
            "last_updated": str(doc.front_matter.get("last_updated") or "").strip(),
            "recent_edit_content": recent_edit_content(doc.front_matter, doc.body),
            "source_revision": source_revision(doc.source_text.encode("utf-8")),
            "sort_key": scope_doc_sort_key(doc),
        }
        for doc in docs
    }


def try_parsed_doc_snapshot(repo_root: Path, scope: str) -> tuple[Optional[Dict[str, Dict[str, Any]]], str]:
    try:
        return parsed_doc_snapshot(repo_root, scope), ""
    except Exception as exc:  # noqa: BLE001 - watcher must fall back rather than stop on bad source state.
        return None, str(exc)


def direct_child_doc_ids(snapshot: Dict[str, Dict[str, Any]], parent_doc_id: str) -> list[str]:
    children = [row for row in snapshot.values() if row.get("parent_id") == parent_doc_id]
    children.sort(key=lambda row: row.get("sort_key") or (True, 0, str(row.get("title") or "").lower(), row.get("doc_id")))
    return [str(row.get("doc_id") or "").strip() for row in children]


def affected_search_doc_ids(
    previous_docs: Optional[Dict[str, Dict[str, Any]]],
    current_docs: Dict[str, Dict[str, Any]],
    changed_files: list[str],
    threshold: int,
) -> tuple[Optional[list[str]], str]:
    if previous_docs is None:
        return None, "missing previous parsed docs snapshot"
    if threshold >= 0 and len(changed_files) > threshold:
        return None, f"changed file count {len(changed_files)} exceeds targeted threshold {threshold}"

    affected: list[str] = []
    for filename in changed_files:
        previous = previous_docs.get(filename)
        current = current_docs.get(filename)

        if previous is None and current is None:
            return None, f"could not resolve changed file {filename}"
        if previous is None:
            affected.append(str(current.get("doc_id") or ""))
            continue
        if current is None:
            affected.append(str(previous.get("doc_id") or ""))
            continue

        current_doc_id = str(current.get("doc_id") or "")
        previous_doc_id = str(previous.get("doc_id") or "")
        affected.append(current_doc_id)
        if previous_doc_id != current_doc_id:
            affected.append(previous_doc_id)
        if str(previous.get("title") or "") != str(current.get("title") or ""):
            affected.extend(direct_child_doc_ids(current_docs, current_doc_id))

    return ordered_unique(affected), ""


def direct_edit_timestamp_plan(
    previous_docs: Optional[Dict[str, Dict[str, Any]]],
    current_docs: Dict[str, Dict[str, Any]],
    changed_files: list[str],
    *,
    captured_timestamp: str,
) -> list[Dict[str, Any]]:
    """Plan timestamp evidence for changed current docs without writing source."""

    if not is_doc_timestamp(captured_timestamp):
        raise ValueError("captured timestamp must use YYYY-MM-DD HH:MM:SS")

    plans: list[Dict[str, Any]] = []
    for filename in changed_files:
        current = current_docs.get(filename)
        if current is None:
            continue

        doc_id = str(current.get("doc_id") or "").strip()
        current_last_updated = str(current.get("last_updated") or "").strip()
        previous_filename = ""
        previous: Optional[Dict[str, Any]] = None
        unmatched_reason = ""
        if previous_docs is None:
            unmatched_reason = "missing_previous_snapshot"
        elif not doc_id:
            unmatched_reason = "invalid_current_identity"
        else:
            same_filename = previous_docs.get(filename)
            if (
                same_filename is not None
                and str(same_filename.get("doc_id") or "").strip() == doc_id
            ):
                previous_filename = filename
                previous = same_filename
            else:
                same_doc_id = [
                    (candidate_filename, row)
                    for candidate_filename, row in previous_docs.items()
                    if str(row.get("doc_id") or "").strip() == doc_id
                ]
                if len(same_doc_id) == 1:
                    previous_filename, previous = same_doc_id[0]
                elif len(same_doc_id) > 1:
                    unmatched_reason = "ambiguous_previous_identity"
                elif same_filename is not None:
                    unmatched_reason = "document_identity_changed"
                else:
                    unmatched_reason = "no_previous_document"

        plan: Dict[str, Any] = {
            "filename": filename,
            "previous_filename": previous_filename,
            "doc_id": doc_id,
            "matched": previous is not None,
            "qualifying_content_changed": None,
            "manual_timestamp_evidence": False,
            "requires_rewrite": False,
            "previous_last_updated": "",
            "current_last_updated": current_last_updated,
            "previous_source_revision": "",
            "current_source_revision": str(
                current.get("source_revision") or ""
            ).strip(),
            "replacement_last_updated": "",
            "reason": unmatched_reason,
        }
        if previous is None:
            plans.append(plan)
            continue

        previous_last_updated = str(previous.get("last_updated") or "").strip()
        plan["previous_last_updated"] = previous_last_updated
        plan["previous_source_revision"] = str(
            previous.get("source_revision") or ""
        ).strip()
        previous_content = previous.get("recent_edit_content")
        current_content = current.get("recent_edit_content")
        if not (
            isinstance(previous_content, tuple)
            and len(previous_content) == 3
            and isinstance(current_content, tuple)
            and len(current_content) == 3
        ):
            plan["reason"] = "invalid_recent_edit_content"
            plans.append(plan)
            continue

        content_changed = previous_content != current_content
        plan["qualifying_content_changed"] = content_changed
        if not content_changed:
            plan["reason"] = "recent_edit_content_unchanged"
        elif (
            is_doc_timestamp(current_last_updated)
            and current_last_updated != previous_last_updated
        ):
            plan["manual_timestamp_evidence"] = True
            plan["reason"] = "manual_full_timestamp"
        else:
            plan["requires_rewrite"] = True
            plan["reason"] = (
                "last_updated_not_advanced"
                if current_last_updated == previous_last_updated
                else "invalid_last_updated"
            )
        plans.append(plan)

    replacement_timestamp = captured_timestamp
    for plan in plans:
        if plan["requires_rewrite"]:
            replacement_timestamp = strictly_later_doc_timestamp(
                plan["previous_last_updated"],
                replacement_timestamp,
            )
    for plan in plans:
        if plan["requires_rewrite"]:
            plan["replacement_last_updated"] = replacement_timestamp
    return plans


def timestamp_issues_from_plan(
    plans: list[Dict[str, Any]],
) -> list[Dict[str, str]]:
    """Render warning records for plan entries that still lack timestamp evidence."""

    issues: list[Dict[str, str]] = []
    for plan in plans:
        reason = ""
        if plan["requires_rewrite"]:
            reason = (
                "last_updated did not advance"
                if plan["reason"] == "last_updated_not_advanced"
                else "last_updated is not a full timestamp"
            )
        elif not plan["matched"] and not is_doc_timestamp(
            plan["current_last_updated"]
        ):
            reason = "new source lacks a full last_updated timestamp"
        if not reason:
            continue
        issues.append(
            {
                "filename": str(plan["filename"]),
                "doc_id": str(plan["doc_id"]),
                "reason": reason,
            }
        )
    return issues


def direct_edit_timestamp_issues(
    previous_docs: Optional[Dict[str, Dict[str, Any]]],
    current_docs: Dict[str, Dict[str, Any]],
    changed_files: list[str],
) -> list[Dict[str, str]]:
    """Describe changed source whose explicit write timestamp evidence is missing."""

    if previous_docs is None:
        return []
    plans = direct_edit_timestamp_plan(
        previous_docs,
        current_docs,
        changed_files,
        captured_timestamp=current_doc_timestamp(),
    )
    return timestamp_issues_from_plan(plans)


def apply_parent_scope_timestamp_rewrites(
    source_root: Path,
    plans: list[Dict[str, Any]],
) -> Dict[str, list[Dict[str, Any]]]:
    """Apply planned parent-scope timestamp-only writes with revision checks."""

    resolved_root = source_root.resolve()
    result: Dict[str, list[Dict[str, Any]]] = {
        "rewritten": [],
        "conflicts": [],
        "failures": [],
    }
    for plan in plans:
        if not plan["requires_rewrite"]:
            continue

        filename = str(plan["filename"])
        doc_id = str(plan["doc_id"])
        path = source_root / filename
        record = {
            "filename": filename,
            "doc_id": doc_id,
        }
        try:
            if path.is_symlink() or path.resolve().parent != resolved_root:
                raise ValueError("planned timestamp source path is not confined")
            expected_revision = str(plan["current_source_revision"])
            if not expected_revision:
                raise ValueError("planned timestamp source revision is missing")
            current_bytes = path.read_bytes()
            current_revision = source_revision(current_bytes)
            if current_revision != expected_revision:
                result["conflicts"].append(
                    {
                        **record,
                        "reason": "source changed after timestamp planning",
                    }
                )
                continue

            current_text = current_bytes.decode("utf-8")
            front_matter_source, front_matter, body = split_source_text(
                current_text,
                source_name=filename,
            )
            current_doc_id = str(front_matter.get("doc_id") or "").strip()
            if current_doc_id != doc_id:
                raise ValueError("planned timestamp doc_id no longer matches source")
            next_front_matter_source = rewrite_front_matter_source_timestamp(
                front_matter_source,
                front_matter,
                timestamp=str(plan["replacement_last_updated"]),
            )
            next_text = next_front_matter_source + body
            write_text_atomic(path, next_text)

            before_read = path.stat()
            verified_bytes = path.read_bytes()
            after_read = path.stat()
            signature = (after_read.st_mtime_ns, after_read.st_size)
            if (
                (before_read.st_mtime_ns, before_read.st_size) != signature
                or verified_bytes != next_text.encode("utf-8")
            ):
                result["conflicts"].append(
                    {
                        **record,
                        "reason": "source changed after timestamp write",
                    }
                )
                continue

            _next_source, next_front_matter, _next_body = split_source_text(
                next_text,
                source_name=filename,
            )
            result["rewritten"].append(
                {
                    **record,
                    "signature": signature,
                    "source_revision": source_revision(verified_bytes),
                    "added_date": str(
                        next_front_matter.get("added_date") or ""
                    ).strip(),
                    "last_updated": str(
                        next_front_matter.get("last_updated") or ""
                    ).strip(),
                }
            )
        except Exception as exc:  # noqa: BLE001 - watcher reports one failed source and continues the batch.
            result["failures"].append(
                {
                    **record,
                    "reason": str(exc),
                }
            )
    return result


def adopt_parent_scope_timestamp_rewrites(
    state: Dict[str, Any],
    current_docs: Dict[str, Dict[str, Any]],
    rewrite_result: Dict[str, list[Dict[str, Any]]],
) -> list[str]:
    """Adopt verified watcher writes into physical and parsed snapshots."""

    adopted: list[str] = []
    for record in rewrite_result["rewritten"]:
        filename = str(record["filename"])
        current = current_docs.get(filename)
        if current is None:
            continue
        state["snapshot"][filename] = tuple(record["signature"])
        current["source_revision"] = str(record["source_revision"])
        current["added_date"] = str(record["added_date"])
        current["last_updated"] = str(record["last_updated"])
        adopted.append(filename)
    return adopted


def rebuild_scope(
    repo_root: Path,
    scope: str,
    docs_doc_ids: Optional[list[str]] = None,
    search_doc_ids: Optional[list[str]] = None,
) -> bool:
    docs_command = python_builder_command(DOCS_BUILDER_SCRIPT, "--scope", scope, "--write", "--diagnostics")
    docs_target_doc_ids = ordered_unique(docs_doc_ids or [])
    if docs_doc_ids is not None and docs_target_doc_ids:
        fallback_reason = targeted_docs_build_fallback_reason(repo_root, scope, docs_target_doc_ids)
        if fallback_reason:
            log(f"{scope} targeted docs fallback: {fallback_reason}")
        else:
            docs_command.extend(["--only-doc-ids", ",".join(docs_target_doc_ids)])
    commands = [("docs", docs_command)]
    if search_doc_ids is None:
        commands.append(("search", python_builder_command(SEARCH_BUILDER_SCRIPT, "--scope", scope, "--write")))
        log(f"Rebuilding {scope} docs and full docs search.")
    else:
        target_doc_ids = ordered_unique(search_doc_ids)
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
            log(f"Rebuilding {scope} docs and targeted docs search: {', '.join(target_doc_ids)}.")
        else:
            log(f"Rebuilding {scope} docs; no docs-search ids were affected.")

    for label, command in commands:
        completed = subprocess.run(
            command,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
        stdout = completed.stdout.strip()
        stderr = completed.stderr.strip()
        if completed.returncode != 0:
            detail = stderr or stdout or f"exit {completed.returncode}"
            log(f"{scope} {label} rebuild failed: {detail}")
            return False
        if label == "docs":
            diagnostics = formatted_docs_builder_diagnostics(stdout)
            if diagnostics:
                log(f"{scope} docs diagnostics:")
                for line in diagnostics:
                    log(f"  {line}")
                continue
        log(f"{scope} {label}: {summarize_output(stdout, 'done')}")
    return True


def process_parent_scope_changes(
    repo_root: Path,
    state: Dict[str, Any],
    changed_files: list[str],
    *,
    targeted_search_threshold: int,
) -> tuple[bool, Optional[Dict[str, Dict[str, Any]]]]:
    """Capture eligible timestamps, then run one existing parent-scope rebuild."""

    scope = str(state["scope"])
    current_docs, snapshot_error = try_parsed_doc_snapshot(repo_root, scope)
    if snapshot_error or current_docs is None:
        log(
            f"{scope} targeted search fallback; affected ids unavailable: "
            f"{snapshot_error or 'parsed docs snapshot unavailable'}"
        )
        return rebuild_scope(repo_root, scope), None

    search_doc_ids, fallback_reason = affected_search_doc_ids(
        state["doc_snapshot"],
        current_docs,
        changed_files,
        targeted_search_threshold,
    )
    docs_doc_ids = None
    if fallback_reason:
        log(f"{scope} targeted search fallback; affected ids unavailable: {fallback_reason}")
    else:
        docs_doc_ids = search_doc_ids
        log(
            f"{scope} affected docs for targeted search: "
            f"{affected_doc_ids_log_text(search_doc_ids)}."
        )

    timestamp_plans = direct_edit_timestamp_plan(
        state["doc_snapshot"],
        current_docs,
        changed_files,
        captured_timestamp=current_doc_timestamp(),
    )
    rewrite_result = apply_parent_scope_timestamp_rewrites(
        state["root"],
        timestamp_plans,
    )
    adopted_files = adopt_parent_scope_timestamp_rewrites(
        state,
        current_docs,
        rewrite_result,
    )
    adopted_set = set(adopted_files)
    if adopted_files:
        captured = [
            f"{record['filename']} ({record['doc_id']})"
            for record in rewrite_result["rewritten"]
            if record["filename"] in adopted_set
        ]
        log(
            f"{scope} captured last_updated for direct source edits: "
            f"{', '.join(captured)}."
        )
    for record in rewrite_result["conflicts"]:
        log(
            f"{scope} timestamp capture deferred for "
            f"{record['filename']} ({record['doc_id']}): "
            f"{record['reason']}."
        )
    for record in rewrite_result["failures"]:
        log(
            f"{scope} timestamp capture failed for "
            f"{record['filename']} ({record['doc_id']}): "
            f"{record['reason']}."
        )
    handled_files = {
        str(record["filename"])
        for result_key in ("rewritten", "conflicts", "failures")
        for record in rewrite_result[result_key]
    }
    for issue in timestamp_issues_from_plan(
        [
            plan
            for plan in timestamp_plans
            if str(plan["filename"]) not in handled_files
        ]
    ):
        log(
            f"{scope} timestamp evidence warning for "
            f"{issue['filename']} ({issue['doc_id']}): "
            f"{issue['reason']}; this source is not eligible "
            "for automatic timestamp capture."
        )

    return (
        rebuild_scope(
            repo_root,
            scope,
            docs_doc_ids=docs_doc_ids,
            search_doc_ids=search_doc_ids,
        ),
        current_docs,
    )


def rebuild_sub_scope(repo_root: Path, scope: str, sub_scope: str) -> bool:
    command = python_builder_command(
        DOCS_BUILDER_SCRIPT,
        "--scope",
        scope,
        "--sub-scope",
        sub_scope,
        "--write",
        "--diagnostics",
    )
    label = f"{scope}/{sub_scope}"
    log(f"Rebuilding {label} sub-scope docs.")
    completed = subprocess.run(
        command,
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    stdout = completed.stdout.strip()
    stderr = completed.stderr.strip()
    if completed.returncode != 0:
        detail = stderr or stdout or f"exit {completed.returncode}"
        log(f"{label} sub-scope rebuild failed: {detail}")
        return False
    diagnostics = formatted_docs_builder_diagnostics(stdout)
    if diagnostics:
        log(f"{label} sub-scope diagnostics:")
        for line in diagnostics:
            log(f"  {line}")
    else:
        log(f"{label} sub-scope docs: {summarize_output(stdout, 'done')}")
    return True


def rebuild_build_media(
    repo_root: Path,
    state: dict[str, Any],
    changed_files: list[str],
) -> bool:
    build_type = str(state.get("build_type") or "").strip()
    if build_type != "mermaid":
        log(f"{state['label']} rebuild failed: unsupported build-media producer {build_type!r}")
        return False

    source_config = state["source_config"]
    published_config = state["published_config"]
    build = source_config.build_media[build_type]
    published_media = published_config.media[build.publishes_to]
    requested_outputs = tuple(
        Path(filename).with_suffix(".svg").as_posix()
        for filename in ordered_unique(changed_files)
        if Path(filename).suffix.lower() == ".mmd"
    )
    if not requested_outputs:
        return True

    try:
        remote_client = authenticated_remote_client_for_locations(
            repo_root,
            [published_media.location],
        )
        source = artifact_location_adapter(
            repo_root,
            ArtifactLocation(
                provider=source_config.location.provider,
                path=source_config.location.path / build.path,
            ),
        )
        published = artifact_location_adapter(
            repo_root,
            published_media.location,
            served_path_prefix=published_media.served_path_prefix,
            remote_client=remote_client,
        )
        outputs = produce_mermaid_svg(
            SimpleNamespace(
                source=source,
                published=published,
                write=True,
                requested_published_identities=requested_outputs,
            )
        )
    except Exception as exc:  # noqa: BLE001 - watcher reports and retries on the next source change.
        log(f"{state['label']} rebuild failed: {exc}")
        return False

    log(f"{state['label']} rendered: {', '.join(outputs) if outputs else 'no matching sources'}.")
    return True


def parse_args() -> argparse.Namespace:
    env = runtime_env()
    parser = argparse.ArgumentParser(description="Watch docs source roots and rebuild same-scope outputs.")
    parser.add_argument("--repo-root", default="", help="Override repo root auto-detection.")
    parser.add_argument(
        "--poll-seconds",
        type=float,
        default=float(env.get("DOCS_WATCH_POLL_SECONDS", "1.0")),
        help="Polling interval in seconds.",
    )
    parser.add_argument(
        "--debounce-seconds",
        type=float,
        default=float(env.get("DOCS_WATCH_DEBOUNCE_SECONDS", "1.0")),
        help="Debounce window in seconds before rebuild.",
    )
    parser.add_argument(
        "--targeted-search-threshold",
        type=int,
        default=int(env.get("DOCS_WATCH_TARGETED_SEARCH_THRESHOLD", "5")),
        help="Maximum changed file count for targeted docs-search updates; use -1 to always target when safe.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.poll_seconds <= 0:
        raise SystemExit("--poll-seconds must be greater than zero")
    if args.debounce_seconds < 0:
        raise SystemExit("--debounce-seconds must be zero or greater")

    repo_root = detect_repo_root(args.repo_root)
    config_path = repo_root / CONFIG_REL_PATH
    config_signature = config_file_signature(config_path)
    states: dict[str, dict[str, Any]] = {}
    reconcile_watch_states(
        repo_root,
        states,
        load_docs_scope_configs(repo_root),
        baseline=True,
    )
    for state in states.values():
        if state.get("startup_doc_error"):
            log(
                f"{state['label']} parsed docs snapshot unavailable at startup; "
                f"watcher search will use full rebuilds: {state['startup_doc_error']}"
            )
        if state.get("startup_source_error"):
            log(f"{state['label']} source root unavailable at startup; watcher is waiting: {state['startup_source_error']}")

    log(
        f"Watching {watch_roots_log_text(states)} "
        f"(poll={args.poll_seconds:.2f}s, debounce={args.debounce_seconds:.2f}s)."
    )
    log(f"Watching scope config {config_path}; scope and sub-scope state will reconcile after config changes.")

    try:
        while True:
            now = time.monotonic()
            current_config_signature = config_file_signature(config_path)
            if current_config_signature != config_signature:
                config_signature = current_config_signature
                try:
                    changes = reconcile_watch_states(
                        repo_root,
                        states,
                        load_docs_scope_configs(repo_root),
                        baseline=False,
                    )
                except (FileNotFoundError, ValueError) as exc:
                    log(f"Scope config reload failed; keeping current watch state: {exc}")
                else:
                    for change_kind, labels in changes.items():
                        if labels:
                            log(f"Scope config {change_kind}: {', '.join(labels)}.")

            for key in list(states):
                state = states[key]
                previous_snapshot = state["snapshot"]
                current_snapshot, source_error = try_state_snapshot(state)
                if current_snapshot is None:
                    if pause_state_for_missing_source(state):
                        log(f"{state['label']} source root unavailable; watcher is waiting: {source_error}")
                    continue
                if state.get("source_missing"):
                    state["source_missing"] = False
                    log(f"{state['label']} source root is available again; resuming change detection.")
                if current_snapshot != previous_snapshot:
                    state["snapshot"] = current_snapshot
                    state["changed_files"] = merge_changed_filenames(
                        state["changed_files"],
                        changed_filenames(previous_snapshot, current_snapshot),
                    )
                    state["dirty_at"] = now
                    changed_text = ", ".join(state["changed_files"]) or "unknown files"
                    log(f"Detected source changes for {state['label']}: {changed_text}.")

            ready_key = None
            for key in list(states):
                dirty_at = states[key]["dirty_at"]
                if dirty_at is not None and (now - dirty_at) >= args.debounce_seconds:
                    ready_key = key
                    break

            if ready_key:
                state = states[ready_key]
                ready_scope = state["scope"]
                ready_label = state["label"]
                changed_files = list(state["changed_files"])
                suppression_owner = watch_suppression_owner(
                    ready_scope,
                    str(state.get("sub_scope") or ""),
                )
                active_suppressions = load_active_watch_suppressions(
                    repo_root,
                    suppression_owner,
                )
                if changed_files:
                    matching = [active_suppressions.get(filename) for filename in changed_files]
                    if (
                        state.get("watch_kind") == "documents"
                        and all(record is not None for record in matching)
                    ):
                        if all(str(record.get("status") or "").strip() == SUPPRESSION_COMPLETE for record in matching):
                            clear_watch_suppressions(
                                repo_root,
                                suppression_owner,
                                changed_files,
                            )
                            if not state.get("sub_scope"):
                                current_doc_snapshot, snapshot_error = try_parsed_doc_snapshot(repo_root, ready_scope)
                                if snapshot_error:
                                    log(f"{ready_scope} parsed docs snapshot not refreshed after suppressed write: {snapshot_error}")
                                else:
                                    state["doc_snapshot"] = current_doc_snapshot
                            state["dirty_at"] = None
                            state["changed_files"] = []
                            log(
                                f"Skipped duplicate {ready_label} rebuild for docs-management write: "
                                f"{', '.join(changed_files)}."
                            )
                            continue
                        continue

                if state.get("watch_kind") == "build_media":
                    rebuild_succeeded = rebuild_build_media(repo_root, state, changed_files)
                    current_doc_snapshot = None
                elif state.get("sub_scope"):
                    rebuild_succeeded = rebuild_sub_scope(repo_root, ready_scope, state["sub_scope"])
                    current_doc_snapshot = None
                else:
                    rebuild_succeeded, current_doc_snapshot = (
                        process_parent_scope_changes(
                            repo_root,
                            state,
                            changed_files,
                            targeted_search_threshold=(
                                args.targeted_search_threshold
                            ),
                        )
                    )

                post_rebuild_snapshot, source_error = try_state_snapshot(state)
                if post_rebuild_snapshot is None:
                    if pause_state_for_missing_source(state):
                        log(f"{ready_label} source root unavailable after rebuild; watcher is waiting: {source_error}")
                    continue
                if post_rebuild_snapshot != state["snapshot"]:
                    previous_snapshot = state["snapshot"]
                    state["snapshot"] = post_rebuild_snapshot
                    state["changed_files"] = changed_filenames(previous_snapshot, post_rebuild_snapshot)
                    state["dirty_at"] = time.monotonic()
                    log(f"Additional source changes arrived during the {ready_label} rebuild; scheduling another pass.")
                else:
                    if rebuild_succeeded and current_doc_snapshot is not None:
                        state["doc_snapshot"] = current_doc_snapshot
                    state["dirty_at"] = None
                    state["changed_files"] = []
                continue

            time.sleep(args.poll_seconds)
    except KeyboardInterrupt:
        log("Stopping watcher.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
