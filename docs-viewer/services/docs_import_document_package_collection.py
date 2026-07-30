#!/usr/bin/env python3
"""Returned document-package collection orchestration for managed Docs Import."""

from __future__ import annotations

import copy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
from typing import Any, Callable

from docs_import_collection_apply import (
    apply_import_content_collection,
    apply_import_content_collection_atomic,
)
from docs_import_collection_plan import (
    DocumentsCollectionPlan,
    blocked_collection_plan,
    collection_issue,
    plan_import_content_collection,
)
from docs_import_document_package import (
    COLLECTION_SOURCE_FORMAT,
    document_package_record_states,
    load_document_package,
    normalize_document_package_record_states,
)
from docs_management_document_target import (
    ManagedDocumentCollection,
)
from docs_source_model import (
    ScopeDoc,
    load_document_collection_docs_for_config,
    load_scope_docs,
    normalize_scope,
)
from docs_document_packages.workspace import marker_path


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, (list, tuple, dict, set)):
        return bool(value)
    return bool(_clean_text(value))


def _returned_hierarchy_fields(raw_row: Any) -> list[str]:
    if not isinstance(raw_row, dict):
        return []
    sources = [raw_row]
    if isinstance(raw_row.get("document"), dict):
        sources.append(raw_row["document"])
    return sorted(
        {
            field
            for source in sources
            for field in ("parent_id", "parent_title", "ancestors", "children")
            if _has_value(source.get(field))
        }
    )


def _validate_prepared_source_versions(
    package_metadata: dict[str, Any],
    docs: list[ScopeDoc],
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    selected = package_metadata.get("selected_doc_ids")
    selected_ids = {
        _clean_text(doc_id)
        for doc_id in selected
        if isinstance(doc_id, str) and _clean_text(doc_id)
    } if isinstance(selected, list) else set()
    raw_versions = package_metadata.get("source_last_updated")
    if not isinstance(raw_versions, dict):
        return [
            collection_issue(
                "error",
                "missing_prepared_source_versions",
                "trusted package metadata must contain source_last_updated for every prepared document",
            )
        ]
    normalized_versions = {
        _clean_text(doc_id): _clean_text(value)
        for doc_id, value in raw_versions.items()
        if isinstance(doc_id, str)
    }
    invalid_value_ids = sorted(
        _clean_text(doc_id)
        for doc_id, value in raw_versions.items()
        if isinstance(doc_id, str) and not isinstance(value, str)
    )
    if invalid_value_ids:
        issues.append(
            collection_issue(
                "error",
                "invalid_prepared_source_versions",
                "trusted source_last_updated values must be strings for: "
                + ", ".join(invalid_value_ids),
            )
        )
    version_ids = {doc_id for doc_id in normalized_versions if doc_id}
    if version_ids != selected_ids:
        missing = sorted(selected_ids - version_ids)
        extra = sorted(version_ids - selected_ids)
        message_parts = []
        if missing:
            message_parts.append("missing " + ", ".join(missing))
        if extra:
            message_parts.append("unexpected " + ", ".join(extra))
        issues.append(
            collection_issue(
                "error",
                "prepared_source_version_membership_mismatch",
                "trusted source_last_updated membership does not match selected_doc_ids: "
                + "; ".join(message_parts),
            )
        )
    blank_versions = sorted(
        doc_id
        for doc_id in selected_ids
        if not normalized_versions.get(doc_id)
    )
    if blank_versions:
        issues.append(
            collection_issue(
                "error",
                "invalid_prepared_source_versions",
                "trusted source_last_updated values must be non-blank for: "
                + ", ".join(blank_versions),
            )
        )
    docs_by_id = {doc.doc_id: doc for doc in docs}
    stale = sorted(
        doc_id
        for doc_id in selected_ids
        if doc_id in docs_by_id
        and normalized_versions.get(doc_id)
        != _clean_text(docs_by_id[doc_id].front_matter.get("last_updated"))
    )
    if stale:
        issue = collection_issue(
            "error",
            "stale_prepared_sources",
            "canonical documents changed after package preparation: " + ", ".join(stale),
        )
        issue["stale_doc_ids"] = stale
        issues.append(issue)
    return issues


def _confine_sub_scope_records(
    states: list[Any],
) -> None:
    for state in states:
        hierarchy_fields = _returned_hierarchy_fields(state.raw)
        record = state.normalized
        if record is not None and record.parent_id:
            hierarchy_fields = sorted({*hierarchy_fields, "parent_id"})
        if hierarchy_fields:
            state.blocked = True
            problem = collection_issue(
                "error",
                "sub_scope_hierarchy_not_allowed",
                "returned sub-scope document has non-empty hierarchy fields: "
                + ", ".join(hierarchy_fields),
                record_index=state.record_index,
                doc_id=state.doc_id,
            )
            state.errors.append(problem)
            continue
        if record is None:
            continue
        if record.assets:
            state.blocked = True
            problem = collection_issue(
                "error",
                "sub_scope_assets_not_supported",
                "returned sub-scope documents cannot materialize package assets",
                record_index=state.record_index,
                doc_id=state.doc_id,
            )
            state.errors.append(problem)
            continue
        front_matter = {
            field: copy.deepcopy(record.front_matter[field])
            for field in ("title", "summary")
            if field in record.front_matter
        }
        state.normalized = replace(
            record,
            parent_id="",
            front_matter=front_matter,
        )
        state.parent_id = ""


def plan_document_package_collection(
    repo_root: Path,
    *,
    scope: str,
    staged_filename: str,
    staging_root: Path,
    workspace_root: Path,
    metadata_root: Path,
    planned_identities: list[dict[str, Any]] | None = None,
    collection: ManagedDocumentCollection | None = None,
) -> DocumentsCollectionPlan:
    """Read and completely plan one trusted package without applying any writes."""

    normalized_scope = normalize_scope(scope)
    if collection is not None and collection.scope != normalized_scope:
        raise ValueError("managed collection does not match requested package scope")
    sub_scope = collection.sub_scope if collection is not None else ""
    package, blockers = load_document_package(
        repo_root,
        scope=normalized_scope,
        staged_filename=staged_filename,
        staging_root=staging_root,
        metadata_root=metadata_root,
        sub_scope=sub_scope or None,
    )
    if package is None:
        return blocked_collection_plan(
            source_format=COLLECTION_SOURCE_FORMAT,
            scope=normalized_scope,
            staged_filename=staged_filename,
            blockers=blockers,
            workspace_root=workspace_root,
            sub_scope=sub_scope,
        )

    docs = (
        load_document_collection_docs_for_config(
            repo_root,
            collection.parent_config,
            collection.document_config,
        )
        if collection is not None and collection.sub_scope
        else load_scope_docs(repo_root, normalized_scope)
    )
    if sub_scope:
        non_flat_targets = sorted(doc.doc_id for doc in docs if doc.parent_id)
        if non_flat_targets:
            blockers.append(
                collection_issue(
                    "error",
                    "non_flat_sub_scope_target",
                    "configured sub-scope contains canonical hierarchy metadata: "
                    + ", ".join(non_flat_targets),
                )
            )
        blockers.extend(
            _validate_prepared_source_versions(
                package.package_metadata,
                docs,
            )
        )
    states, identity_blockers = document_package_record_states(package.raw_rows)
    blockers.extend(identity_blockers)
    blockers.extend(
        normalize_document_package_record_states(
            package,
            states,
            current_doc_ids={doc.doc_id for doc in docs},
            staged_filename=staged_filename,
        )
    )
    if sub_scope:
        _confine_sub_scope_records(states)
    package_projection = {
        "export_id": package.export_id,
        "profile_id": _clean_text(
            package.package_metadata.get("profile_id")
            or package.package_metadata.get("config_id")
        ),
        "schema_version": _clean_text(package.package_metadata.get("schema_version")),
        "source_scope": _clean_text(package.package_metadata.get("scope")),
        "content_format": _clean_text(package.package_metadata.get("content_format")),
        "staged_path": marker_path(package.path, workspace_root=workspace_root),
        "source_sha256": package.source_sha256,
    }
    if sub_scope:
        package_projection["source_sub_scope"] = _clean_text(
            package.package_metadata.get("sub_scope")
        )
        package_projection["source_last_updated"] = copy.deepcopy(
            package.package_metadata.get("source_last_updated")
        )
        package_projection["trusted_metadata_sha256"] = hashlib.sha256(
            json.dumps(
                package.package_metadata,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
    return plan_import_content_collection(
        repo_root,
        source_format=COLLECTION_SOURCE_FORMAT,
        scope=normalized_scope,
        staged_filename=staged_filename,
        states=states,
        docs=docs,
        staging_root=staging_root,
        workspace_root=workspace_root,
        package_projection=package_projection,
        blockers=blockers,
        planned_identities=planned_identities,
        collection=collection,
        overwrite_only=bool(sub_scope),
    )


def apply_document_package_collection(
    repo_root: Path,
    *,
    scope: str,
    staged_filename: str,
    body: dict[str, Any],
    staging_root: Path,
    workspace_root: Path,
    metadata_root: Path,
    log_event: Callable[[Path, str, dict[str, Any]], None],
    perform_source_write_and_rebuild: Callable[..., dict[str, Any]],
    collection: ManagedDocumentCollection | None = None,
    perform_sub_scope_source_write_and_rebuild: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Recompute and synchronously apply one confirmed whole-package plan."""

    if body.get("preview_only") is not False:
        raise ValueError("collection apply requires preview_only false")
    planned_identities = body.get("planned_identities")
    if not isinstance(planned_identities, list):
        raise ValueError("collection apply requires planned_identities from the confirmed preview")
    plan = plan_document_package_collection(
        repo_root,
        scope=scope,
        staged_filename=staged_filename,
        staging_root=staging_root,
        workspace_root=workspace_root,
        metadata_root=metadata_root,
        planned_identities=planned_identities,
        collection=collection,
    )
    if collection is not None and collection.sub_scope:
        if perform_sub_scope_source_write_and_rebuild is None:
            raise ValueError("sub-scope collection apply requires its confined rebuild owner")
        return apply_import_content_collection_atomic(
            repo_root,
            plan,
            body,
            workspace_root=workspace_root,
            log_event=log_event,
            collection=collection,
            perform_sub_scope_source_write_and_rebuild=(
                perform_sub_scope_source_write_and_rebuild
            ),
        )
    return apply_import_content_collection(
        repo_root,
        plan,
        body,
        staging_root=staging_root,
        workspace_root=workspace_root,
        source_path=staging_root / staged_filename,
        log_event=log_event,
        perform_source_write_and_rebuild=perform_source_write_and_rebuild,
    )


__all__ = [
    "COLLECTION_SOURCE_FORMAT",
    "DocumentsCollectionPlan",
    "apply_document_package_collection",
    "plan_document_package_collection",
]
