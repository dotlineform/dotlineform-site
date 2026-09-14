"""Revision-bound draft readiness writes for exact Working documents."""

from pathlib import Path
from typing import Any

import docs_source_model as source_model
from docs_management_document_target import resolve_managed_document_target
from docs_management_mutations import (
    ManagedDocumentRevisionConflict,
    revision_conflict_payload,
)
from docs_watch_suppression import clear_watch_suppressions, watch_suppression_owner


def set_draft(repo_root: Path, body: dict[str, Any], *, dry_run: bool = False) -> dict[str, Any]:
    """Save one revision-checked boolean; the normal watcher owns its build."""
    required = {"scope", "stage", "doc_id", "draft", "source_revision"}
    if set(body) - {"sub_scope"} != required:
        raise ValueError("Set Draft requires scope, stage, doc_id, draft and source_revision, with optional sub_scope")
    if not isinstance(body["draft"], bool):
        raise ValueError("draft must be true or false")
    target = {key: body[key] for key in ("scope", "stage", "sub_scope", "doc_id") if key in body}
    resolved = resolve_managed_document_target(repo_root, target)
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
    source = source_model.format_source(front_matter, document.body, sub_scope=resolved.sub_scope)
    changed = document.front_matter.get("draft") is not body["draft"]
    if changed and not dry_run:
        # A completed earlier management save must not hide this new watcher write.
        clear_watch_suppressions(repo_root, watch_suppression_owner(
            resolved.scope, resolved.sub_scope, stage=resolved.stage,
        ), [document.path.relative_to(resolved.source_root).as_posix()])
        source_model.write_text_atomic(document.path, source)
    return {
        "ok": True, "operation": "set_draft", **resolved.request_target(),
        "target": resolved.request_target(),
        "record": {"doc_id": document.doc_id, "draft": body["draft"]},
        "source_revision": source_model.source_revision(source.encode("utf-8")) if changed and not dry_run else revision,
    }
