"""Draft readiness writes for exact Working documents."""

from dataclasses import replace
from pathlib import Path
from typing import Any

import docs_source_model as source_model
from docs_management_document_target import committed_document_record, resolve_managed_document_target
from docs_front_matter import rewrite_front_matter_fields
from docs_document_rebuild import rebuild_prepared_document
from docs_workspace_config import require_document_authoring


def set_draft(repo_root: Path, body: dict[str, Any], *, dry_run: bool = False) -> dict[str, Any]:
    """Write only the intended boolean and carry its prepared source into generation."""
    required = {"doc_id", "draft"}
    if set(body) - {"collection"} != required:
        raise ValueError("Set Draft requires doc_id and draft, with optional collection")
    if not isinstance(body["draft"], bool):
        raise ValueError("draft must be true or false")
    target = {key: body[key] for key in ( "collection", "doc_id") if key in body}
    resolved = resolve_managed_document_target(repo_root, target)
    require_document_authoring(resolved.parent_config)
    if not source_model.collection_supports_draft(resolved.document_config):
        raise ValueError("Set Draft is available only in Working")
    document = resolved.document
    parts = document.parts
    front_matter = {**document.front_matter, "draft": body["draft"]}
    source_model.validate_document_status_front_matter(front_matter, collection_config=resolved.document_config, source_name=document.path.name)
    changed = document.front_matter.get("draft") is not body["draft"]
    source = (
        rewrite_front_matter_fields(parts.prefix, {"draft": body["draft"]}, fields=parts.fields) + parts.body
        if changed else document.source_text
    )
    report = source_model.parse_collection_document_report(
        repo_root, resolved.parent_config, resolved.document_config, source,
        front_matter=front_matter, body=document.body, source_name=document.path.name,
    )
    prepared = replace(document, source_text=source, front_matter=front_matter, report=report, parts=None)
    record = committed_document_record(front_matter, document.doc_id, resolved.document_config, collection=resolved.collection, parent_id=document.parent_id)
    if changed and not dry_run:
        source_model.write_text_atomic(document.path, source)
    payload = {
        "ok": True, "operation": "set_draft", **resolved.request_target(),
        "target": resolved.request_target(),
        "record": record,
    }
    if not dry_run:
        payload["source_saved"] = True
        payload["generation_complete"] = False
        try:
            payload["rebuild"] = rebuild_prepared_document(repo_root, resolved, prepared)["rebuild"]
        except Exception as error:
            payload.update(ok=False, error=f"Draft readiness saved, but document generation failed: {error}")
            return payload
        payload["generation_complete"] = True
    return payload
