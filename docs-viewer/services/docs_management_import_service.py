"""Docs import source service adapters for Local Studio."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import docs_import_source_service as import_source_service
import docs_write_rebuild as write_rebuild
from docs_management_context import log_event
from docs_management_document_target import (
    ManagedDocumentCollection,
    resolve_managed_document_collection_target,
)
from docs_document_packages.workspace import configured_workspace_paths, workspace_status


def import_source_dependencies() -> import_source_service.ImportSourceDependencies:
    return import_source_service.ImportSourceDependencies(
        log_event=log_event,
        perform_source_write_and_rebuild=write_rebuild.perform_source_write_and_rebuild,
        perform_scope_source_write_and_rebuild_atomic=(
            write_rebuild.perform_scope_source_write_and_rebuild_atomic
        ),
        perform_sub_scope_source_write_and_rebuild=(
            write_rebuild.perform_sub_scope_source_write_and_rebuild
        ),
    )


def ordinary_import_target_request(body: Dict[str, Any]) -> Dict[str, Any]:
    target = {"scope": body.get("scope")}
    if "sub_scope" in body:
        target["sub_scope"] = body.get("sub_scope")
    return target


def resolve_ordinary_import_target(
    repo_root: Path,
    target: Dict[str, Any],
) -> ManagedDocumentCollection:
    return resolve_managed_document_collection_target(repo_root, target)


def handle_import_source(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    target = resolve_ordinary_import_target(
        repo_root,
        ordinary_import_target_request(body),
    )
    source_directory = str(body.get("source_directory") or "")
    if not source_directory.strip():
        raise ValueError("source_directory is required")
    source = import_source_service.resolve_import_source_directory(source_directory)
    status = workspace_status(repo_root)
    if not status["available"]:
        raise ValueError(status["message"])
    workspace_paths = configured_workspace_paths(repo_root)
    source_body = dict(body)
    source_body.pop("source_directory", None)
    return import_source_service.handle_import_source(
        repo_root,
        {**source_body, "scope": target.scope},
        dry_run,
        import_source_dependencies(),
        staging_root=source.path,
        workspace_root=workspace_paths.root,
        metadata_root=workspace_paths.meta,
        destination=target,
        projects_base=source.projects_base,
        source_directory=source.marker,
        trusted_sources_allowed=(
            source.path == workspace_paths.import_staging.resolve()
        ),
    )
