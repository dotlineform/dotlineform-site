"""Allocate a document-owned identity in its exact configured Working collection."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import docs_source_model as source_model
from docs_document_identities import IDENTITY_FIELDS, next_document_identity, normalize_document_identity, validate_unique_document_identities
from docs_management_document_target import managed_document_target_request, resolve_managed_document_target
from docs_management_mutations import ManagementMutationPlan, ManagedDocumentRevisionConflict, SOURCE_REVISION_PATTERN, SourceWrite, revision_conflict_payload, source_revision
from docs_scope_config import require_document_authoring
from docs_subscope_customisations import sub_scope_customisation_identity_kind


def plan_allocate_document_identity(repo_root: Path, body: dict[str, Any]) -> ManagementMutationPlan:
    """Plan one revision-bound allocation; an existing identity is an idempotent read."""
    if set(body) != {"scope", "stage", "sub_scope", "doc_id", "source_revision", "confirm"}:
        raise ValueError("allocate identity requires scope, stage, sub_scope, doc_id, source_revision and confirm")
    if body["confirm"] is not True:
        raise ValueError("allocate identity requires confirm=true")
    resolved = resolve_managed_document_target(repo_root, managed_document_target_request(body))
    require_document_authoring(resolved.parent_config)
    if resolved.stage != "working" or not resolved.sub_scope:
        raise ValueError("document identity allocation requires a Working sub-scope")
    kind = sub_scope_customisation_identity_kind(resolved.document_config.sub_scope_customisation)
    if not kind:
        raise ValueError("document identity allocation is not configured for this collection")
    identity_field = IDENTITY_FIELDS[kind]
    target = resolved.document
    source_bytes = target.source_text.encode("utf-8")
    current_revision = source_revision(source_bytes)
    requested_revision = body["source_revision"]
    if not isinstance(requested_revision, str) or not SOURCE_REVISION_PATTERN.fullmatch(requested_revision):
        raise ValueError("source_revision is required for identity allocation")
    if requested_revision != current_revision:
        raise ManagedDocumentRevisionConflict(revision_conflict_payload(
            target=resolved.request_target(), requested_revision=requested_revision,
            current_revision=current_revision, operation="allocate_identity",
            error="managed document source changed before identity allocation",
        ))
    documents = source_model.load_document_collection_docs_for_config(repo_root, resolved.parent_config, resolved.document_config)
    declarations = {doc.doc_id: normalize_document_identity(doc.front_matter, identity_field) for doc in documents}
    validate_unique_document_identities(declarations, identity_field)
    current = declarations[target.doc_id]
    changed = current["state"] == "none"
    value = next_document_identity(declarations, identity_field) if changed else current[identity_field]
    response = {
        "ok": True, "operation": "allocate_identity", "target": resolved.request_target(),
        "scope": resolved.scope, "sub_scope": resolved.sub_scope, "doc_id": target.doc_id,
        "kind": kind, "field": identity_field, "value": value, "changed": changed,
        "source_revision": current_revision,
        "summary_text": f"{kind.title()} {value}",
    }
    if not changed:
        return ManagementMutationPlan(scope=resolved.scope, sub_scope=resolved.sub_scope, stage=resolved.stage, response=response)
    front_matter = dict(target.front_matter)
    front_matter[identity_field] = value
    front_matter = source_model.advance_front_matter_for_recent_edit(target.front_matter, target.body, front_matter, target.body)
    updated_source = source_model.format_source(front_matter, target.body)
    source_model.parse_collection_document_report(repo_root, resolved.parent_config, resolved.document_config, updated_source, source_name=target.path.as_posix())
    response["source_revision"] = source_revision(updated_source.encode("utf-8"))
    return ManagementMutationPlan(
        scope=resolved.scope, sub_scope=resolved.sub_scope, stage=resolved.stage, response=response,
        source_writes=(SourceWrite(target.path, updated_source, original_bytes=source_bytes),),
        suppression_reason="docs-allocate-identity", log_event_name="docs-allocate-identity",
        log_details={"scope": resolved.scope, "sub_scope": resolved.sub_scope, "doc_id": target.doc_id, "kind": kind, "value": value},
        include_write_result_keys=True, revision_conflict_operation="allocate_identity",
        revision_conflict_error="managed document source changed before identity allocation",
    )
