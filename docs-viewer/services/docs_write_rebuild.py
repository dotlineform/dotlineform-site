#!/usr/bin/env python3
"""Docs Management source-write follow-through and rebuild helpers."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional, TYPE_CHECKING

from docs_workspace_config import (
    document_source_path,
    load_docs_workspace_config,
    require_document_authoring,
    DocsWorkspaceConfig,
    select_workspace_stage,
)
from docs_build_manifest import remove_build_manifest
from docs_publication_preparation import PublicationHandoffError
from docs_generation import generate_documents
from docs_source_model import SourceDoc, parse_source, write_bytes_atomic
from docs_document_identity import doc_updated_date
from docs_document_media_ownership import DocumentMediaChange
from docs_index_order import index_order_path

if TYPE_CHECKING:
    from docs_builder.collection import CollectionDocsBuilder
    from docs_builder.source import DocRecord
    from docs_management_document_target import ManagedDocumentCollection, ManagedDocumentTarget


class CollectionWriteRebuildFailure(RuntimeError):
    """Report one failed child write/rebuild after its owned rollback attempt."""

    def __init__(self, message: str, *, rollback: dict[str, Any]):
        super().__init__(message)
        self.rollback = rollback


class DocumentWriteRebuildFailure(RuntimeError):
    """Report one failed top-level write/rebuild after its owned rollback attempt."""

    def __init__(self, message: str, *, rollback: dict[str, Any]):
        super().__init__(message)
        self.rollback = rollback


def ordered_docs_doc_ids(doc_ids: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for raw_doc_id in doc_ids:
        doc_id = str(raw_doc_id or "").strip()
        if not doc_id or doc_id in seen:
            continue
        seen.add(doc_id)
        ordered.append(doc_id)
    return ordered


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


def rebuild_working_outputs(
    repo_root: Path, *, docs_doc_ids: Optional[list[str]] = None,
    skip_media_builds: bool = False, links_doc_ids: Optional[list[str]] = None,
    media_changes: list[tuple[str, Any, DocumentMediaChange]] | None = None,
    prepared_documents: list[SourceDoc] | None = None,
    workspace: DocsWorkspaceConfig | None = None,
    publication: Any = None,
) -> Dict[str, Any]:
    """Await explicit Working generation with carried authoring inputs."""
    return _rebuild_outputs(repo_root, "", docs_doc_ids=docs_doc_ids, links_doc_ids=links_doc_ids,
                            skip_media_builds=skip_media_builds, media_changes=media_changes,
                            prepared_documents=prepared_documents, workspace=workspace, publication=publication)


def rebuild_collection_outputs(
    repo_root: Path, collection: str, links_doc_ids: Optional[list[str]] = None,
    docs_doc_ids: Optional[list[str]] = None, *,
    media_changes: list[tuple[str, Any, DocumentMediaChange]] | None = None,
    prepared_documents: list[SourceDoc] | None = None,
    workspace: DocsWorkspaceConfig | None = None,
    publication: Any = None,
) -> Dict[str, Any]:
    """Await a selected/complete collection and its explicit queue completion."""
    return _rebuild_outputs(repo_root, collection, docs_doc_ids=docs_doc_ids, links_doc_ids=links_doc_ids,
                            skip_media_builds=True, media_changes=media_changes,
                            prepared_documents=prepared_documents, workspace=workspace, publication=publication)


def _rebuild_outputs(
    repo_root: Path, collection: str, *, docs_doc_ids: list[str] | None,
    links_doc_ids: list[str] | None, skip_media_builds: bool,
    media_changes: list[tuple[str, Any, DocumentMediaChange]] | None,
    prepared_documents: list[SourceDoc] | None, workspace: DocsWorkspaceConfig | None,
    publication: Any,
) -> dict[str, Any]:
    build_dir = str(repo_root / "docs-viewer/build")
    if build_dir not in sys.path:
        sys.path.insert(0, build_dir)
    from docs_builder.pipeline import DocsDataBuilder
    from docs_builder.collection import CollectionDocsBuilder, selected_collection

    workspace = load_docs_workspace_config(repo_root) if workspace is None else workspace
    config = select_workspace_stage(workspace, "working")
    targets = None if docs_doc_ids is None else ordered_docs_doc_ids(docs_doc_ids)
    if targets is not None and not targets:
        raise ValueError("Targeted docs build requires at least one document ID")
    arguments = {"repo_root": repo_root, "config": config, "workspace": workspace,
                 "only_doc_ids": targets, "links_doc_ids": links_doc_ids if links_doc_ids is not None else targets,
                 "skip_media_builds": skip_media_builds}
    if collection:
        builder = CollectionDocsBuilder(**arguments, collection=selected_collection(config, collection))
    else:
        remove_build_manifest(repo_root, config)
        builder = DocsDataBuilder(**arguments, skip_recent=True)
    records = None if prepared_documents is None else [prepared_build_record(builder, doc) for doc in prepared_documents]
    result = generate_documents(builder, write=True, documents=records,
                                publication=publication,
                                media_changes={doc_id: change for doc_id, _owner, change in media_changes or []})
    return {
        "ok": True, "steps": [], "search": {"mode": "none", "doc_ids": []},
        "docs": {"mode": "targeted" if targets is not None else "collection" if collection else "full",
                 "doc_ids": targets or [], "reason": "explicit document generation",
                 **({"collection": collection} if collection else {})},
        "diagnostics": {"docs": result["diagnostics"]},
    }


def prepared_build_record(builder: Any, document: SourceDoc) -> Any:
    """Project an already parsed authoring/import record without reading it again."""
    return builder.document_record(
        path=document.path, front_matter=document.front_matter, body_markdown=document.body,
        doc_id=document.doc_id, title=document.title, parent_id=document.parent_id,
        report=document.report, source_text=document.source_text,
    )


def validate_changed_source_paths(root: Path, paths: list[Path], *, index_path: Path | None = None) -> None:
    """Confine writes to Markdown storage and an explicitly resolved hierarchy file."""
    for path in paths:
        if path == index_path:
            continue
        path.resolve().relative_to(root.resolve())


def perform_source_write_and_rebuild(
    repo_root: Path,
    changed_paths: list[Path],
    write_operation: Callable[[], Any],
    *,
    docs_doc_ids: Optional[list[str]] = None,
    skip_media_builds: bool = True,
    media_changes: list[tuple[str, Any, DocumentMediaChange]] | None = None,
    prepared_documents: list[SourceDoc] | None = None,
) -> Dict[str, Any]:
    workspace = load_docs_workspace_config(repo_root)
    config = select_workspace_stage(workspace, "working")
    require_document_authoring(config)
    validate_changed_source_paths(document_source_path(config), changed_paths, index_path=index_order_path(config))
    links_before = changed_source_document_ids(changed_paths) if prepared_documents is None else None
    write_operation()
    rebuild = rebuild_working_outputs(
        repo_root, docs_doc_ids=docs_doc_ids,
        skip_media_builds=skip_media_builds,
        **(links_write_arguments(links_before, changed_paths) if prepared_documents is None else {"links_doc_ids": docs_doc_ids}),
        media_changes=media_changes, prepared_documents=prepared_documents, workspace=workspace,
    )
    return rebuild


def perform_source_write_and_rebuild_atomic(
    repo_root: Path,
    changed_paths: list[Path],
    write_operation: Callable[[], Any],
    *,
    source_snapshots: Mapping[Path, bytes],
    docs_doc_ids: Optional[list[str]] = None,
    media_changes: list[tuple[str, Any, DocumentMediaChange]] | None = None,
    prepared_documents: list[SourceDoc] | None = None,
) -> Dict[str, Any]:
    """Write/rebuild one exact parent stage or restore its source snapshot there."""
    workspace = load_docs_workspace_config(repo_root)
    config = select_workspace_stage(workspace, "working")
    require_document_authoring(config)
    root = document_source_path(config)
    normalized_snapshots = {path.resolve(): source_bytes for path, source_bytes in source_snapshots.items()}
    validate_changed_source_paths(root, list(normalized_snapshots), index_path=index_order_path(config))
    links_before = changed_source_document_ids(changed_paths) if prepared_documents is None else [doc.doc_id for doc in prepared_documents]
    try:
        write_operation()
        rebuild = rebuild_working_outputs(
            repo_root, docs_doc_ids=docs_doc_ids,
            skip_media_builds=True,
            **(links_write_arguments(links_before, changed_paths) if prepared_documents is None else {"links_doc_ids": links_before}),
            media_changes=media_changes, prepared_documents=prepared_documents, workspace=workspace,
        )
    except PublicationHandoffError:
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
                    repo_root, docs_doc_ids=docs_doc_ids,
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


def rebuild_prepared_document_outputs(
    repo_root: Path, owner: ManagedDocumentCollection | ManagedDocumentTarget, document: SourceDoc,
    *, parent_ids: dict[str, str] | None = None,
    media_change: DocumentMediaChange | None = None,
    media_writes: dict[str, list[str]] | None = None,
) -> Dict[str, Any]:
    """Carry one prepared source through the existing exact document/Links builder."""
    build_dir = Path(__file__).resolve().parents[1] / "build"
    if str(build_dir) not in sys.path:
        sys.path.insert(0, str(build_dir))
    from docs_builder.pipeline import DocsDataBuilder
    from docs_builder.collection import CollectionDocsBuilder

    workspace = owner.workspace if owner.workspace is not None else load_docs_workspace_config(repo_root)
    arguments = {
        "repo_root": repo_root, "config": owner.parent_config, "workspace": workspace,
        "only_doc_ids": [document.doc_id], "links_doc_ids": [document.doc_id], "skip_media_builds": True,
    }
    if owner.collection:
        builder = CollectionDocsBuilder(**arguments, collection=owner.document_config)
    else:
        remove_build_manifest(repo_root, owner.parent_config)
        builder = DocsDataBuilder(**arguments, skip_recent=True)
    record = prepared_build_record(builder, document)
    started_at = time.perf_counter()
    result = generate_documents(builder, write=True, documents=[record], media_changes={document.doc_id: media_change} if media_change is not None else None,
                         media_writes={document.doc_id: media_writes} if media_writes is not None else None,
                         **({"parent_ids": parent_ids} if not owner.collection else {}))
    return {
        "ok": True, "steps": [], "search": {"mode": "none", "doc_ids": []},
        "docs": {"mode": "targeted", "doc_ids": [document.doc_id], "reason": "prepared source supplied"},
        "diagnostics": {"docs": result["diagnostics"]},
        "elapsed_seconds": round(time.perf_counter() - started_at, 3),
    }


def create_collection_builder(
    repo_root: Path, collection: ManagedDocumentCollection, workspace: DocsWorkspaceConfig,
    *, doc_ids: list[str] | None,
) -> CollectionDocsBuilder:
    """Create the existing builder once for an in-process collection operation."""
    build_dir = Path(__file__).resolve().parents[1] / "build"
    if str(build_dir) not in sys.path:
        sys.path.insert(0, str(build_dir))
    from docs_builder.collection import CollectionDocsBuilder

    return CollectionDocsBuilder(
        repo_root=repo_root, config=collection.parent_config, collection=collection.document_config,
        workspace=workspace, only_doc_ids=doc_ids, skip_media_builds=True,
    )


def _generated_path(root: Path, name: str) -> Path:
    path = root / name
    if root.is_symlink() or path.is_symlink() or path.resolve().parent != root.resolve():
        raise ValueError("Generated document paths must stay in their configured directory")
    return path


def project_document_position(
    repo_root: Path, owner: ManagedDocumentCollection, doc_id: str, parent_ids: dict[str, str],
    write_position: Callable[[dict[str, Any]], None],
) -> dict[str, Any]:
    """Project reparenting and its document/publication eligibility effects."""
    build_dir = Path(__file__).resolve().parents[1] / "build"
    if str(build_dir) not in sys.path:
        sys.path.insert(0, str(build_dir))
    from docs_builder.pipeline import DocsDataBuilder
    from docs_builder.ordinary_metadata import OrdinaryDocumentSummary, read_saved_navigation
    from docs_builder.common import json_text, write_text

    builder = DocsDataBuilder(
        repo_root=repo_root, config=owner.parent_config, workspace=owner.workspace,
        only_doc_ids=[doc_id], links_doc_ids=[], skip_media_builds=True, skip_recent=True,
    )
    rows, previous, previous_text = read_saved_navigation(builder)
    documents = {
        current_id: OrdinaryDocumentSummary(current_id, rows[current_id]["title"], parent_id, rows[current_id])
        for current_id, parent_id in parent_ids.items()
    }
    navigation = builder.index_tree_payload(documents, previous_payload=previous)
    tree_text = json_text(navigation)
    path = _generated_path(builder.items_dir, f"{doc_id}.json")
    previous_document_text = path.read_text(encoding="utf-8")
    payload = json.loads(previous_document_text)
    if parent_ids[doc_id]:
        payload["parent_id"] = parent_ids[doc_id]
    else:
        payload.pop("parent_id", None)
    document_text = json_text(payload)
    record = {key: value for key, value in payload.items() if key != "content_html"}
    record.update(parent_id=parent_ids[doc_id], has_thumbnail=payload.get("has_thumbnail", False))
    for key in ("added_date", "last_updated"):
        record[key] = doc_updated_date(payload[key])
    committed = {"target": {"doc_id": doc_id}, "record": record}
    write_position(committed)
    if document_text != previous_document_text:
        write_text(path, document_text)
    if tree_text != previous_text:
        write_text(_generated_path(builder.output_dir, "index-tree.json"), tree_text)
    from docs_publication_preparation import load_preparation
    from docs_generation import prepare_restored
    publication = load_preparation(repo_root, builder.workspace, navigation=previous, navigation_text=tree_text)
    publication.metadata.ordinary(navigation)
    publication.documents(builder, {doc_id}, [], changed_ids={doc_id})
    publication.write_metadata()
    prepare_restored(builder, {}, publication)
    publication.save()
    remove_build_manifest(repo_root, owner.parent_config)
    return committed


def complete_document_deletion(
    repo_root: Path, owner: ManagedDocumentCollection, doc_ids: list[str],
    selected_payload: dict[str, Any], *, parent_ids: dict[str, str] | None,
) -> dict[str, Any]:
    """Apply known document/Links removals using carried configuration and selections."""
    build_dir = Path(__file__).resolve().parents[1] / "build"
    if str(build_dir) not in sys.path:
        sys.path.insert(0, str(build_dir))
    from docs_builder.pipeline import DocsDataBuilder
    from docs_builder.collection import CollectionDocsBuilder

    arguments = {
        "repo_root": repo_root, "config": owner.parent_config, "workspace": owner.workspace,
        "only_doc_ids": doc_ids, "links_doc_ids": doc_ids, "skip_media_builds": True,
    }
    if owner.collection:
        builder = CollectionDocsBuilder(**arguments, collection=owner.document_config)
        builder.selected_payload = selected_payload
        _generated_path(builder.output_dir, builder.manifest_filename)
        for doc_id in doc_ids:
            _generated_path(builder.items_dir, f"{doc_id}.json")
        result = generate_documents(builder, write=True, documents=[])
    else:
        builder = DocsDataBuilder(**arguments, skip_recent=True)
        _generated_path(builder.output_dir, "index-tree.json")
        for doc_id in doc_ids:
            _generated_path(builder.items_dir, f"{doc_id}.json")
        remove_build_manifest(repo_root, owner.parent_config)
        result = generate_documents(builder, write=True, documents=[], parent_ids=parent_ids, selected_payload=selected_payload)
    return {"ok": True, "diagnostics": result["diagnostics"]}


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
    builder: CollectionDocsBuilder | None = None,
    documents: list[DocRecord] | None = None,
    catalogue_works: dict[str, dict[str, Any]] | None = None,
    publication: Any = None,
    catalogue_pending: dict[str, Any] | None = None,
    prepared_documents: list[SourceDoc] | None = None,
    media_changes: list[tuple[str, Any, DocumentMediaChange]] | None = None,
) -> Dict[str, Any]:
    """Await a selected or complete collection build and its Links update."""
    if builder is None:
        from docs_management_document_target import resolve_managed_document_collection

        resolved = resolve_managed_document_collection(repo_root, collection=collection)
        require_document_authoring(resolved.parent_config)
        root = resolved.source_root
    else:
        root = builder.source_dir
    validate_changed_source_paths(root, changed_paths)
    normalized_snapshots: dict[Path, bytes] | None = None
    if source_snapshots is not None:
        normalized_snapshots = {path.resolve(): source_bytes for path, source_bytes in source_snapshots.items()}
    if prepared_documents is not None:
        build_doc_ids = [doc.doc_id for doc in prepared_documents]
        links_doc_ids = build_doc_ids
    supplied_ids = build_doc_ids is not None and links_doc_ids is not None
    discover_ids = not supplied_ids and (not complete_build or normalized_snapshots is not None)
    source_doc_ids_before = changed_source_document_ids(changed_paths) if discover_ids else []
    docs_doc_ids = source_doc_ids_before
    try:
        write_operation()
        if supplied_ids:
            docs_doc_ids = build_doc_ids
            links_arguments = {"links_doc_ids": links_doc_ids}
        elif complete_build:
            source_doc_ids_after = changed_source_document_ids(changed_paths) if normalized_snapshots is not None else []
            docs_doc_ids = sorted(set(source_doc_ids_before) | set(source_doc_ids_after))
            links_arguments = {}
        else:
            source_doc_ids_after = changed_source_document_ids(changed_paths)
            docs_doc_ids = sorted(set(source_doc_ids_before) | set(source_doc_ids_after) | set(build_doc_ids or []))
            links_arguments = {"links_doc_ids": sorted(set(source_doc_ids_before) | set(source_doc_ids_after))}
            if links_doc_ids is not None:
                links_arguments["links_doc_ids"] = links_doc_ids
        if complete_build:
            links_arguments.pop("links_doc_ids", None)
        if builder is None:
            rebuild = rebuild_collection_outputs(
                repo_root, collection, docs_doc_ids=None if complete_build else docs_doc_ids,
                **links_arguments, media_changes=media_changes, prepared_documents=prepared_documents, workspace=resolved.workspace,
            )
        else:
            builder.only_doc_ids = None if complete_build else docs_doc_ids
            builder.links_doc_ids = links_arguments.get("links_doc_ids")
            rebuild = generate_documents(builder, write=True, documents=documents, catalogue_works=catalogue_works, publication=publication,
                                         catalogue_pending=catalogue_pending,
                                         media_changes={doc_id: change for doc_id, _owner, change in media_changes or []})
    except PublicationHandoffError:
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
    from docs_publication_preparation import load_preparation

    workspace = load_docs_workspace_config(repo_root)
    config = select_workspace_stage(workspace, "working")
    require_document_authoring(config)
    owners = {"": config, **{owner.collection: owner for owner in config.collections}}
    links_before: dict[str, list[str]] = {}
    for plan in rebuild_plans:
        collection = str(plan.get("collection") or "")
        root = document_source_path(owners[collection])
        changed_paths = plan.get("changed_paths", [])
        validate_changed_source_paths(root, changed_paths)
        links_before[collection] = changed_source_document_ids(changed_paths)
    write_operation()
    publication = load_preparation(repo_root, workspace)
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
                workspace=workspace, publication=publication,
            )
        else:
            rebuilds[owner] = rebuild_working_outputs(
                repo_root, docs_doc_ids=plan.get("docs_doc_ids"),
                **links_arguments, skip_media_builds=True,
                workspace=workspace, publication=publication,
            )
    return {"ok": True, "collections": rebuilds}
