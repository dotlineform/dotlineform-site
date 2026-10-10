"""Revision-bound draft readiness writes for exact Working documents."""

from pathlib import Path
from typing import Any

import docs_source_model as source_model
from docs_management_document_target import committed_document_record, resolve_managed_document_target
from docs_management_mutations import (
    ManagedDocumentRevisionConflict,
    revision_conflict_payload,
)
from docs_document_rebuild import rebuild_resolved_document
from docs_document_actions import require_document_action
from docs_workspace_config import require_document_authoring


def set_draft(repo_root: Path, body: dict[str, Any], *, dry_run: bool = False) -> dict[str, Any]:
    """Save one revision-checked boolean and await its exact document generation."""
    required = { "doc_id", "draft", "source_revision"}
    if set(body) - {"collection"} != required:
        raise ValueError("Set Draft requires doc_id, draft and source_revision, with optional collection")
    if not isinstance(body["draft"], bool):
        raise ValueError("draft must be true or false")
    target = {key: body[key] for key in ( "collection", "doc_id") if key in body}
    resolved = resolve_managed_document_target(repo_root, target)
    require_document_authoring(resolved.parent_config)
    require_document_action(repo_root, resolved.parent_config, "set-draft", resolved.request_target())
    if not source_model.collection_supports_draft(resolved.document_config):
        raise ValueError("Set Draft is available only in Working")
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
    source = source_model.format_source(front_matter, document.body, collection=resolved.collection)
    changed = document.front_matter["draft"] is not body["draft"]
    record = committed_document_record(front_matter, document.doc_id, resolved.document_config, collection=resolved.collection, parent_id=document.parent_id)
    if changed and not dry_run:
        source_model.write_text_atomic(document.path, source)
    payload = {
        "ok": True, "operation": "set_draft", **resolved.request_target(),
        "target": resolved.request_target(),
        "record": record,
        "source_revision": source_model.source_revision(source.encode("utf-8")) if changed and not dry_run else revision,
    }
    if not dry_run:
        payload["source_saved"] = True
        payload["generation_complete"] = False
        try:
            payload["rebuild"] = rebuild_resolved_document(repo_root, resolved)["rebuild"]
        except Exception as error:
            payload.update(ok=False, error=f"Draft readiness saved, but document generation failed: {error}")
            return payload
        payload["generation_complete"] = True
    return payload
