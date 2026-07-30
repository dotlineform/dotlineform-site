#!/usr/bin/env python3
"""Plan and atomically apply top-level edited Docs Review source folders."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Callable

from docs_import_collection_apply import (
    apply_import_content_collection_scope_atomic,
)
from docs_import_collection_plan import (
    CollectionRecordState,
    DocumentsCollectionPlan,
    collection_issue,
    plan_import_content_collection,
)
from docs_import_content import (
    CONTENT_FORMAT_MARKDOWN,
    CONTENT_INTENT_REPLACE,
    ImportContent,
)
from docs_import_document_package_collection import (
    validate_prepared_source_versions,
)
from docs_import_review_source_folder import (
    EDITED_REVIEW_SOURCE_FORMAT,
    EditedReviewSourceFolder,
)
from docs_management_document_target import ManagedDocumentCollection
from docs_source_model import load_scope_docs, normalize_scope
from docs_document_packages.workspace import marker_path


FIDELITY_WARNING = (
    "Edited review sources are derived Markdown. Rich content, tokens, comments, "
    "raw embeds, source formatting, and package assets may not survive this import."
)


def _record_state(
    folder: EditedReviewSourceFolder,
    record_index: int,
) -> CollectionRecordState:
    source = folder.records[record_index]
    front_matter: dict[str, Any] = {"title": source.title}
    if source.summary_present:
        front_matter["summary"] = source.summary
    if source.parent_id_present:
        front_matter["parent_id"] = source.parent_id
    if source.viewable_present:
        front_matter["viewable"] = source.viewable
    normalized = ImportContent(
        source_kind=EDITED_REVIEW_SOURCE_FORMAT,
        source_identity=folder.staged_filename,
        record_identity=source.filename,
        doc_id=source.doc_id,
        title=source.title,
        content_intent=CONTENT_INTENT_REPLACE,
        content_format=CONTENT_FORMAT_MARKDOWN,
        content=source.body,
        front_matter=front_matter,
        parent_id=source.parent_id if source.parent_id_present else "",
        provenance={
            "review_folder_id": folder.review_folder_id,
            "source_export_id": folder.source_export_id,
        },
    )
    return CollectionRecordState(
        record_index=record_index,
        raw={"doc_id": source.doc_id, "filename": source.filename},
        doc_id=source.doc_id,
        source_doc_id=source.doc_id,
        title=source.title,
        parent_id=normalized.parent_id,
        normalized=normalized,
    )


def _validate_destination(
    folder: EditedReviewSourceFolder,
    collection: ManagedDocumentCollection,
) -> None:
    if collection.sub_scope:
        raise ValueError(
            "Edited review source folders for configured sub-scopes are not "
            "available until ERS-1.4.",
        )
    if folder.source_sub_scope:
        raise ValueError(
            "This edited review source folder belongs to a configured sub-scope; "
            "sub-scope apply is not available until ERS-1.4.",
        )
    if folder.source_scope != collection.scope:
        raise ValueError(
            "Edited review source folder belongs to scope "
            f"{folder.source_scope!r}, not {collection.scope!r}.",
        )


def plan_edited_review_source_collection(
    repo_root: Path,
    *,
    folder: EditedReviewSourceFolder,
    collection: ManagedDocumentCollection,
    staging_root: Path,
    workspace_root: Path,
    planned_identities: list[dict[str, Any]] | None = None,
) -> DocumentsCollectionPlan:
    """Map one trusted edited folder into the shared write-free collection plan."""

    _validate_destination(folder, collection)
    scope = normalize_scope(collection.scope)
    docs = load_scope_docs(repo_root, scope)
    source_versions = dict(folder.source_last_updated)
    blockers = validate_prepared_source_versions(
        {
            "selected_doc_ids": list(folder.doc_ids),
            "source_last_updated": source_versions,
        },
        docs,
    )
    states = [
        _record_state(folder, record_index)
        for record_index in range(len(folder.records))
    ]
    package_projection = {
        "export_id": folder.source_export_id,
        "review_folder_id": folder.review_folder_id,
        "profile_id": folder.profile_id,
        "source_scope": folder.source_scope,
        "source_sub_scope": folder.source_sub_scope,
        "content_format": CONTENT_FORMAT_MARKDOWN,
        "document_count": folder.document_count,
        "staged_path": marker_path(folder.path, workspace_root=workspace_root),
        "source_sha256": folder.source_sha256,
        "trusted_metadata_sha256": folder.trusted_metadata_sha256,
        "source_last_updated": copy.deepcopy(source_versions),
    }
    return plan_import_content_collection(
        repo_root,
        source_format=EDITED_REVIEW_SOURCE_FORMAT,
        scope=scope,
        staged_filename=folder.staged_filename,
        states=states,
        docs=docs,
        staging_root=staging_root,
        workspace_root=workspace_root,
        package_projection=package_projection,
        blockers=blockers,
        planned_identities=planned_identities,
        collection=collection,
        overwrite_only=True,
        warnings=[
            collection_issue(
                "warning",
                "derived_markdown_fidelity",
                FIDELITY_WARNING,
            )
        ],
    )


def apply_edited_review_source_collection(
    repo_root: Path,
    *,
    folder: EditedReviewSourceFolder,
    collection: ManagedDocumentCollection,
    body: dict[str, Any],
    staging_root: Path,
    workspace_root: Path,
    log_event: Callable[[Path, str, dict[str, Any]], None],
    perform_scope_source_write_and_rebuild_atomic: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    """Revalidate and atomically apply one confirmed top-level edited folder."""

    if body.get("preview_only") is not False:
        raise ValueError("collection apply requires preview_only false")
    planned_identities = body.get("planned_identities")
    if not isinstance(planned_identities, list):
        raise ValueError(
            "collection apply requires planned_identities from the confirmed preview",
        )
    plan = plan_edited_review_source_collection(
        repo_root,
        folder=folder,
        collection=collection,
        staging_root=staging_root,
        workspace_root=workspace_root,
        planned_identities=planned_identities,
    )
    return apply_import_content_collection_scope_atomic(
        repo_root,
        plan,
        body,
        workspace_root=workspace_root,
        log_event=log_event,
        collection=collection,
        perform_scope_source_write_and_rebuild_atomic=(
            perform_scope_source_write_and_rebuild_atomic
        ),
    )


__all__ = [
    "FIDELITY_WARNING",
    "apply_edited_review_source_collection",
    "plan_edited_review_source_collection",
]
