"""Revision-bound draft readiness writes for exact Analysis Working documents."""

from pathlib import Path
from typing import Any

import docs_source_model as source_model
from docs_management_document_target import resolve_managed_document_target
from docs_management_mutations import (
    ManagedDocumentRevisionConflict,
    ManagementMutationPlan,
    SourceWrite,
    revision_conflict_payload,
)


def plan_set_draft(repo_root: Path, body: dict[str, Any]) -> ManagementMutationPlan:
    """Set one boolean without changing visual status or publication intent."""
    required = {"scope", "stage", "doc_id", "draft", "source_revision"}
    if set(body) - {"sub_scope"} != required:
        raise ValueError("Set Draft requires scope, stage, doc_id, draft and source_revision, with optional sub_scope")
    if not isinstance(body["draft"], bool):
        raise ValueError("draft must be true or false")
    target = {key: body[key] for key in ("scope", "stage", "sub_scope", "doc_id") if key in body}
    resolved = resolve_managed_document_target(repo_root, target)
    if not source_model.collection_supports_draft(resolved.document_config):
        raise ValueError("Set Draft is available only in Analysis Working")
    document = resolved.document
    original = document.source_text.encode("utf-8")
    revision = source_model.source_revision(original)
    if body["source_revision"] != revision:
        raise ManagedDocumentRevisionConflict(revision_conflict_payload(
            target=resolved.request_target(), requested_revision=str(body["source_revision"]),
            current_revision=revision, operation="set_draft",
            error="Document source changed before draft readiness was saved",
        ))
    front_matter = {**document.front_matter, "draft": body["draft"]}
    source = source_model.format_source(front_matter, document.body, sub_scope=resolved.sub_scope)
    changed = document.front_matter.get("draft") is not body["draft"]
    return ManagementMutationPlan(
        scope=resolved.scope, stage=resolved.stage, sub_scope=resolved.sub_scope,
        response={
            "ok": True, "operation": "set_draft", **resolved.request_target(),
            "target": resolved.request_target(),
            "record": {"doc_id": document.doc_id, "draft": body["draft"]},
            "source_revision": source_model.source_revision(source.encode("utf-8")) if changed else revision,
        },
        source_writes=(SourceWrite(document.path, source, original_bytes=original),) if changed else (),
        suppression_reason="docs-set-draft",
        build_doc_ids=[] if resolved.sub_scope else [document.doc_id],
        log_event_name="docs-set-draft", log_details={**target, "draft": body["draft"]},
        include_write_result_keys=True,
        revision_conflict_operation="set_draft",
        revision_conflict_error="Document source changed before draft readiness was saved",
    )
