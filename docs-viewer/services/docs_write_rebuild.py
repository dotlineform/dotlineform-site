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

from docs_workspace_config import (
    document_source_path,
    generated_documents_path,
    generated_search_path,
    load_docs_stage,
    load_docs_working_config,
    require_document_authoring,
    resolve_workspace_path,
)
from docs_build_manifest import remove_build_manifest, write_build_manifest
from docs_mermaid_preparation import prepare_stage_mermaid
from docs_workspace_links import write_workspace_links
from docs_source_model import parse_source, write_bytes_atomic

DOCS_BUILDER_DIAGNOSTICS_PREFIX = "Docs builder diagnostics: "
FRONT_MATTER_ERROR_PREFIX = "problem with front-matter on doc "
PYTHON_EXECUTABLE = sys.executable
DOCS_BUILDER_SCRIPT = "docs-viewer/build/build_docs.py"
SEARCH_BUILDER_SCRIPT = "docs-viewer/build/build_search.py"


class CollectionWriteRebuildFailure(RuntimeError):
    """Report one failed child write/rebuild after its owned rollback attempt."""

    def __init__(self, message: str, *, rollback: dict[str, Any]):
        super().__init__(message)
        self.rollback = rollback


class CollectionSourceSnapshotChanged(RuntimeError):
    """Stop one child write boundary before mutation when its snapshot changed."""


class DocumentWriteRebuildFailure(RuntimeError):
    """Report one failed top-level write/rebuild after its owned rollback attempt."""

    def __init__(self, message: str, *, rollback: dict[str, Any]):
        super().__init__(message)
        self.rollback = rollback


class DocumentSourceSnapshotChanged(RuntimeError):
    """Stop one top-level write boundary before mutation when its snapshot changed."""


def current_document_source_root(repo_root: Path) -> Path:
    config = load_docs_working_config(repo_root)
    return resolve_workspace_path(repo_root, document_source_path(config))


def current_collection_source_root(repo_root: Path, collection: str) -> Path:
    config = load_docs_working_config(repo_root)
    matching = [
        candidate
        for candidate in config.collections
        if candidate.collection == collection
    ]
    if not matching:
        raise ValueError(f"collection {collection} is not configured")
    return resolve_workspace_path(repo_root, document_source_path(matching[0]))


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


def changed_source_document_ids(paths: list[Path]) -> list[str]:
    """Read exact changed source identities for authored relationship maintenance.

    Capture before deletion as well as after creation. Paths never stand in for
    document identity, and this helper never inventories a collection.
    """
    identities = set()
    for path in paths:
        if path.suffix == ".md" and path.is_file():
            metadata = parse_source(path)[0]
            identities.add(str(metadata.get("doc_id") or ""))
    return sorted(identities - {""})


def links_write_arguments(before: list[str] | None, paths: list[Path]) -> dict[str, list[str]]:
    """Carry exact changed/deleted identities from one source write."""
    if before is None:
        return {}
    after = set(changed_source_document_ids(paths))
    return {"links_doc_ids": sorted(set(before) | after)}


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


def rebuild_stage_outputs(
    repo_root: Path,
    include_search: bool = False,
    search_doc_ids: Optional[list[str]] = None,
    docs_doc_ids: Optional[list[str]] = None,
    skip_media_builds: bool = False,
    stage: str | None = None,
    links_doc_ids: Optional[list[str]] = None,
    docs_base_dir: Path | None = None,
    assets_base_dir: Path | None = None,
    copied_search_index: bytes | None = None,
    copied_recent_payload: bytes | None = None,
    related_links_dir: Path | None = None,
) -> Dict[str, Any]:
    """Await document work and built/copied discovery data before completion.

    Full Working docs-and-Search rebuilds also combine prepared Links records.
    Individual document operations omit Search and leave that aggregate alone.
    """
    if stage == "preview" and docs_base_dir is None:
        raise ValueError("Preview builds require an explicit temporary workspace")
    if include_search and stage != "working":
        raise ValueError("Search rebuilds require Working; Preview copies the existing index")
    if (copied_search_index is None) != (copied_recent_payload is None):
        raise ValueError("Preview requires both captured Working Search and freshly prepared Recents")
    docs_target_doc_ids = ordered_docs_doc_ids(docs_doc_ids or [])
    if docs_doc_ids is not None and not docs_target_doc_ids:
        raise ValueError("Targeted docs build requires at least one document ID")
    if copied_search_index is not None:
        if stage != "preview":
            raise ValueError("Only Preview copies an existing Search index")
        from docs_preview_snapshot import _validate_prepared_index

        _validate_prepared_index(Path("search/index.json"), copied_search_index)
        _validate_prepared_index(Path("documents/recent.json"), copied_recent_payload)
    try:
        stage_config = load_docs_stage(repo_root, stage)
    except KeyError as exc:
        raise ValueError(f"stage {stage!r} is not configured") from exc
    remove_build_manifest(repo_root, stage_config)
    docs_mode = "full"
    docs_reason = "full document build requested"
    docs_command = python_builder_command(DOCS_BUILDER_SCRIPT, "--write", "--diagnostics")
    if not include_search:
        docs_command.append("--skip-recent")
    if stage:
        docs_command.extend(["--stage", stage])
    if stage == "working":
        selected_links = links_doc_ids if links_doc_ids is not None else docs_doc_ids
        if selected_links is not None:
            docs_command.extend(["--links-doc-ids", ",".join(ordered_docs_doc_ids(selected_links))])
    if docs_doc_ids is not None:
        docs_mode = "targeted"
        docs_reason = "targeted docs payload ids provided"
        docs_command.extend(["--only-doc-ids", ",".join(docs_target_doc_ids)])
    if skip_media_builds:
        docs_command.append("--skip-media-builds")
    commands = [("docs", docs_command)]
    search = {"mode": "copy" if copied_search_index is not None else "none", "doc_ids": []}
    if include_search or copied_search_index is not None:
        collection_commands = [
            (collection, (
                "collection_docs",
                python_builder_command(
                    DOCS_BUILDER_SCRIPT,
                    "--collection",
                    collection.collection,
                    "--write",
                    "--diagnostics",
                    "--skip-browser-config",
                    *(["--stage", stage_config.stage] if stage_config.stage else []),
                    *(["--skip-media-builds"] if skip_media_builds else []),
                ),
            ))
            for collection in stage_config.collections
        ]
        if stage_config.stage == "working":
            # Recents consumes current collection metadata inside the ordinary build.
            commands = [
                *(command for collection, command in collection_commands if collection.include_in_site_search),
                *commands,
                *(command for collection, command in collection_commands if not collection.include_in_site_search),
            ]
        else:
            commands.extend(command for _collection, command in collection_commands)
    if include_search:
        if search_doc_ids is None:
            search = {"mode": "full", "doc_ids": []}
            commands.append(("search", python_builder_command(
                SEARCH_BUILDER_SCRIPT, "--write",
                *(["--stage", stage_config.stage] if stage_config.stage else []),
            )))
        else:
            target_doc_ids = ordered_search_doc_ids(search_doc_ids)
            search = {"mode": "full" if target_doc_ids else "none", "doc_ids": target_doc_ids}
            if target_doc_ids:
                commands.append(
                    (
                        "search",
                        python_builder_command(
                            SEARCH_BUILDER_SCRIPT,
                            "--write",
                            *(["--stage", stage_config.stage] if stage_config.stage else []),
                        ),
                    )
                )
    steps = []
    docs_diagnostics: Optional[Dict[str, Any]] = None
    search_diagnostics = extract_search_step_diagnostics("", search)
    for label, command in commands:
        if docs_base_dir is not None:
            command.extend(["--docs-base-dir", str(docs_base_dir)])
        if assets_base_dir is not None:
            command.extend(["--assets-base-dir", str(assets_base_dir)])
        if related_links_dir is not None and command[1] == DOCS_BUILDER_SCRIPT:
            command.extend(["--related-links-dir", str(related_links_dir)])
        if stage == "preview" and command[1] == DOCS_BUILDER_SCRIPT and "--skip-browser-config" not in command:
            command.append("--skip-browser-config")
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
            raise RuntimeError(rebuild_failure_message(f"rebuild failed for {stage}", detail))
    if copied_search_index is not None:
        output_path = resolve_workspace_path(repo_root, generated_search_path(stage_config))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(copied_search_index)
        recent_path = resolve_workspace_path(repo_root, generated_documents_path(stage_config)) / "recent.json"
        recent_path.write_bytes(copied_recent_payload)
    complete_build = search["mode"] in {"full", "copy"}
    links = (
        write_workspace_links(repo_root, stage_config)
        if complete_build
        and stage_config.stage == "working"
        else None
    )
    mermaid = (
        prepare_stage_mermaid(repo_root, stage_config)
        if complete_build
        else None
    )
    build_manifest = (
        write_build_manifest(repo_root, stage_config)
        if complete_build
        else None
    )
    return {
        "ok": True,
        "steps": steps,
        "search": search,
        "docs": {"mode": docs_mode, "doc_ids": docs_target_doc_ids, "reason": docs_reason},
        "diagnostics": {
            "docs": docs_diagnostics,
            "search": search_diagnostics,
        },
        "build_manifest": build_manifest,
        **({"mermaid": mermaid} if mermaid is not None else {}),
        **({"links": links} if links is not None else {}),
    }


def rebuild_working_outputs(
    repo_root: Path,
    *,
    include_search: bool = False,
    docs_doc_ids: Optional[list[str]] = None,
    skip_media_builds: bool = False,
    links_doc_ids: Optional[list[str]] = None,
) -> Dict[str, Any]:
    """Resolve the authoring owner once before invoking the internal build pipeline."""
    config = load_docs_working_config(repo_root)
    return rebuild_stage_outputs(
        repo_root, stage=config.stage, include_search=include_search,
        docs_doc_ids=docs_doc_ids, skip_media_builds=skip_media_builds,
        links_doc_ids=links_doc_ids,
    )


def rebuild_collection_outputs(
    repo_root: Path,
    collection: str,
    links_doc_ids: Optional[list[str]] = None,
    docs_doc_ids: Optional[list[str]] = None,
) -> Dict[str, Any]:
    """Build a complete collection or render only its exact changed/deleted IDs."""
    docs_command = python_builder_command(
        DOCS_BUILDER_SCRIPT,
        "--collection",
        collection,
        "--write",
        "--diagnostics",
        "--skip-browser-config",
        "--skip-media-builds",
    )
    config = load_docs_working_config(repo_root)
    docs_command.extend(["--stage", config.stage])
    target_doc_ids = None if docs_doc_ids is None else ordered_docs_doc_ids(docs_doc_ids)
    if target_doc_ids is not None:
        docs_command.extend(["--only-doc-ids", ",".join(target_doc_ids)])
    if links_doc_ids is not None:
        docs_command.extend(["--links-doc-ids", ",".join(ordered_docs_doc_ids(links_doc_ids))])
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
                f"rebuild failed for {collection}",
                detail,
            )
        )
    return {
        "ok": True,
        "steps": steps,
        "search": {"mode": "none", "doc_ids": []},
        "docs": {
            "mode": "targeted" if target_doc_ids is not None else "collection",
            "doc_ids": target_doc_ids or [],
            "collection": collection,
            "reason": "targeted collection document ids provided" if target_doc_ids is not None else "configured collection rebuild",
        },
        "diagnostics": {
            "docs": docs_diagnostics,
            "search": {"mode": "none", "doc_ids": []},
        },
    }


def validate_changed_source_paths(root: Path, paths: list[Path]) -> None:
    """Keep write follow-through confined to its configured source owner."""
    for path in paths:
        path.resolve().relative_to(root.resolve())


def perform_source_write_and_rebuild(
    repo_root: Path,
    changed_paths: list[Path],
    write_operation: Callable[[], Any],
    *,
    docs_doc_ids: Optional[list[str]] = None,
    skip_media_builds: bool = True,
) -> Dict[str, Any]:
    require_document_authoring(load_docs_working_config(repo_root))
    validate_changed_source_paths(current_document_source_root(repo_root), changed_paths)
    links_before = changed_source_document_ids(changed_paths)
    write_operation()
    return rebuild_working_outputs(
        repo_root, include_search=False, docs_doc_ids=docs_doc_ids,
        skip_media_builds=skip_media_builds,
        **links_write_arguments(links_before, changed_paths),
    )


def perform_source_write_and_rebuild_atomic(
    repo_root: Path,
    changed_paths: list[Path],
    write_operation: Callable[[], Any],
    *,
    source_snapshots: Mapping[Path, bytes],
    docs_doc_ids: Optional[list[str]] = None,
) -> Dict[str, Any]:
    """Write/rebuild one exact parent stage or restore its source snapshot there."""
    require_document_authoring(load_docs_working_config(repo_root))
    root = current_document_source_root(repo_root)
    resolved_changed_paths = {path.resolve() for path in changed_paths}
    normalized_snapshots = {path.resolve(): source_bytes for path, source_bytes in source_snapshots.items()}
    if set(normalized_snapshots) != resolved_changed_paths:
        raise ValueError("document rollback snapshot must cover every changed source exactly")
    if any(not isinstance(source_bytes, bytes) for source_bytes in normalized_snapshots.values()):
        raise ValueError("document rollback snapshot values must be bytes")
    validate_changed_source_paths(root, list(normalized_snapshots))
    links_before = changed_source_document_ids(changed_paths)
    try:
        changed_before_write = [
            path.name for path, source_bytes in normalized_snapshots.items()
            if path.read_bytes() != source_bytes
        ]
        if changed_before_write:
            raise DocumentSourceSnapshotChanged(
                "document sources changed immediately before apply: "
                + ", ".join(sorted(changed_before_write)),
            )
        write_operation()
        rebuild = rebuild_working_outputs(
            repo_root, include_search=False, docs_doc_ids=docs_doc_ids,
            skip_media_builds=True, **links_write_arguments(links_before, changed_paths),
        )
    except DocumentSourceSnapshotChanged:
        raise
    except Exception as exc:
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
                recovery_rebuild = rebuild_working_outputs(
                    repo_root, include_search=False, docs_doc_ids=docs_doc_ids,
                    skip_media_builds=True, links_doc_ids=links_before,
                )
            except Exception as recovery_exc:
                recovery_error = str(recovery_exc).strip() or recovery_exc.__class__.__name__
        rollback_status = "failed" if restoration_errors or recovery_error else "completed"
        raise DocumentWriteRebuildFailure(
            str(exc).strip() or exc.__class__.__name__,
            rollback={
                "status": rollback_status, "sources_restored": not restoration_errors,
                "rebuild": recovery_rebuild,
                "error": "; ".join([*restoration_errors, recovery_error]).strip("; "),
            },
        ) from exc
    return rebuild


def perform_collection_source_write_and_rebuild(
    repo_root: Path,
    collection: str,
    changed_paths: list[Path],
    write_operation: Callable[[], Any],
    *,
    source_snapshots: Mapping[Path, bytes] | None = None,
    links_doc_ids: list[str] | None = None,
    build_doc_ids: list[str] | None = None,
    complete_build: bool = False,
) -> Dict[str, Any]:
    """Await a selected or complete collection build and its Links update."""
    require_document_authoring(load_docs_working_config(repo_root))
    root = current_collection_source_root(repo_root, collection)
    resolved_changed_paths = {path.resolve() for path in changed_paths}
    validate_changed_source_paths(root, changed_paths)
    normalized_snapshots: dict[Path, bytes] | None = None
    if source_snapshots is not None:
        normalized_snapshots = {path.resolve(): source_bytes for path, source_bytes in source_snapshots.items()}
        if set(normalized_snapshots) != resolved_changed_paths:
            raise ValueError("collection rollback snapshot must cover every changed source exactly")
        if any(not isinstance(source_bytes, bytes) for source_bytes in normalized_snapshots.values()):
            raise ValueError("collection rollback snapshot values must be bytes")
    source_doc_ids_before = changed_source_document_ids(changed_paths)
    docs_doc_ids = source_doc_ids_before
    try:
        if normalized_snapshots is not None:
            changed_before_write = [
                path.name for path, source_bytes in normalized_snapshots.items()
                if path.read_bytes() != source_bytes
            ]
            if changed_before_write:
                raise CollectionSourceSnapshotChanged(
                    "collection sources changed immediately before apply: "
                    + ", ".join(sorted(changed_before_write))
                )
        write_operation()
        docs_doc_ids = sorted(set(source_doc_ids_before) | set(changed_source_document_ids(changed_paths))
                              | set(build_doc_ids or []))
        links_arguments = links_write_arguments(source_doc_ids_before, changed_paths)
        if links_doc_ids is not None:
            links_arguments["links_doc_ids"] = links_doc_ids
        if complete_build:
            links_arguments.pop("links_doc_ids", None)
        rebuild = rebuild_collection_outputs(
            repo_root, collection, docs_doc_ids=None if complete_build else docs_doc_ids,
            **links_arguments,
        )
    except CollectionSourceSnapshotChanged:
        raise
    except Exception as exc:
        if normalized_snapshots is None:
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
                recovery_rebuild = rebuild_collection_outputs(
                    repo_root, collection, docs_doc_ids=docs_doc_ids,
                    links_doc_ids=source_doc_ids_before if links_doc_ids is None else links_doc_ids,
                )
            except Exception as recovery_exc:
                recovery_error = str(recovery_exc).strip() or recovery_exc.__class__.__name__
        rollback_status = "failed" if restoration_errors or recovery_error else "completed"
        raise CollectionWriteRebuildFailure(
            str(exc).strip() or exc.__class__.__name__,
            rollback={
                "status": rollback_status, "sources_restored": not restoration_errors,
                "rebuild": recovery_rebuild,
                "error": "; ".join([*restoration_errors, recovery_error]).strip("; "),
            },
        ) from exc
    return rebuild


def perform_multi_collection_source_write_and_rebuild(
    repo_root: Path,
    rebuild_plans: list[Dict[str, Any]],
    write_operation: Callable[[], Any],
) -> Dict[str, Any]:
    """Write once and await each exact collection's document/Links rebuild."""
    require_document_authoring(load_docs_working_config(repo_root))
    links_before: dict[str, list[str]] = {}
    for plan in rebuild_plans:
        collection = str(plan.get("collection") or "")
        root = current_collection_source_root(repo_root, collection) if collection else current_document_source_root(repo_root)
        changed_paths = plan.get("changed_paths", [])
        validate_changed_source_paths(root, changed_paths)
        links_before[collection] = changed_source_document_ids(changed_paths)
    write_operation()
    rebuilds: Dict[str, Any] = {}
    prepared_rebuilds = []
    for plan in rebuild_plans:
        collection = str(plan.get("collection") or "")
        changed_paths = plan.get("changed_paths", [])
        docs_doc_ids = ordered_docs_doc_ids([
            *(plan.get("docs_doc_ids") or []), *links_before[collection],
            *changed_source_document_ids(changed_paths),
        ])
        links_arguments = links_write_arguments(links_before[collection], changed_paths)
        has_destination = bool(set(links_arguments.get("links_doc_ids", [])) - set(links_before[collection]))
        prepared_rebuilds.append((plan, links_arguments, docs_doc_ids, has_destination))
    # Transfer a moved document's prior Links record to its destination before deletion.
    prepared_rebuilds.sort(key=lambda item: not item[3])
    for plan, links_arguments, docs_doc_ids, _has_destination in prepared_rebuilds:
        collection = str(plan.get("collection") or "")
        owner = f"documents__collection__{collection}" if collection else "documents"
        if collection:
            rebuilds[owner] = rebuild_collection_outputs(
                repo_root, collection, docs_doc_ids=docs_doc_ids, **links_arguments,
            )
        else:
            rebuilds[owner] = rebuild_working_outputs(
                repo_root, include_search=False, docs_doc_ids=plan.get("docs_doc_ids"),
                **links_arguments, skip_media_builds=True,
            )
    return {"ok": True, "collections": rebuilds}
