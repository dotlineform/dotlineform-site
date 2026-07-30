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
    if target.sub_scope:
        raise ValueError(
            "Ordinary Docs Import preview and create are not yet available "
            "for configured sub-scope destinations."
        )
    status = workspace_status(repo_root, required_paths=("import_staging",))
    if not status["available"]:
        raise ValueError(status["message"])
    workspace_paths = configured_workspace_paths(repo_root)
    return import_source_service.handle_import_source(
        repo_root,
        {**body, "scope": target.scope},
        dry_run,
        import_source_dependencies(),
        staging_root=workspace_paths.import_staging,
        workspace_root=workspace_paths.root,
        metadata_root=workspace_paths.meta,
    )
