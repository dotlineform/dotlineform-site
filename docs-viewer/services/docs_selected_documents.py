"""One canonical Working selection list, with stage-independent reader rows."""

from pathlib import Path
from typing import Any, Iterable
import json

from docs_document_identity import is_doc_timestamp, is_immutable_doc_id
from docs_source_model import write_text_atomic
from docs_workspace_config import COLLECTION_ID_PATTERN, document_source_path


SELECTED_FILENAME = "selected.json"
SELECTED_SCHEMA = "docs_selected_v1"


def validate_selected_payload(payload: Any) -> None:
    """Require exact identities and display metadata, without stored routes."""
    if not isinstance(payload, dict) or set(payload) != {"schema", "docs"}:
        raise ValueError("Selected Documents requires schema and docs")
    if payload["schema"] != SELECTED_SCHEMA or not isinstance(payload["docs"], list):
        raise ValueError("Selected Documents has an invalid schema or document list")
    seen = set()
    for row in payload["docs"]:
        if not isinstance(row, dict):
            raise ValueError("Selected Documents rows must be objects")
        fields = {"doc_id", "title", "last_updated"}
        if "collection" in row:
            fields |= {"collection", "report_doc_id"}
            if not isinstance(row["collection"], str) or not COLLECTION_ID_PATTERN.fullmatch(row["collection"]):
                raise ValueError("Selected Documents requires exact collection identity")
        if set(row) != fields:
            raise ValueError("Selected Documents row has invalid fields")
        for key in ("doc_id", "report_doc_id"):
            if key in row and (not isinstance(row[key], str) or row[key] != row[key].strip() or not is_immutable_doc_id(row[key])):
                raise ValueError(f"Selected Documents requires an immutable {key}")
        if (not isinstance(row["title"], str) or not row["title"].strip()
                or not isinstance(row["last_updated"], str) or not is_doc_timestamp(row["last_updated"])):
            raise ValueError("Selected Documents requires a title and last_updated timestamp")
        target = (row.get("collection", ""), row["doc_id"])
        if target in seen:
            raise ValueError("Selected Documents contains a duplicate target")
        seen.add(target)


def selected_path(config: Any) -> Path:
    root = document_source_path(config)
    path = root / SELECTED_FILENAME
    if path.is_symlink() or path.resolve().parent != root.resolve():
        raise ValueError("selected.json must stay in the configured document source directory")
    return path


def read_selected(config: Any) -> dict[str, Any]:
    payload = json.loads(selected_path(config).read_text(encoding="utf-8"))
    validate_selected_payload(payload)
    return payload


def selected_text(payload: dict[str, Any]) -> str:
    validate_selected_payload(payload)
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def selected_row(document: Any, owner: Any) -> dict[str, Any]:
    row = {
        "doc_id": document.doc_id,
        "title": document.title,
        "last_updated": document.front_matter["last_updated"],
    }
    collection = getattr(owner, "collection", "")
    if collection:
        row.update(collection=collection, report_doc_id=owner.report_host_doc_id)
    return row


def refresh_selected_documents(config: Any, owner: Any, documents: Iterable[Any], *, write: bool) -> None:
    """Refresh selected metadata for built documents, preserving other selections."""
    payload = read_selected(config)
    collection = getattr(owner, "collection", "")
    built = {doc.doc_id: doc for doc in documents}
    rows = [
        selected_row(built[row["doc_id"]], owner)
        if row.get("collection", "") == collection and row["doc_id"] in built else row
        for row in payload["docs"]
    ]
    updated = {"schema": SELECTED_SCHEMA, "docs": rows}
    text = selected_text(updated)
    if write and updated != payload:
        write_text_atomic(selected_path(config), text)


def set_selected(repo_root: Path, body: dict[str, Any], *, dry_run: bool = False) -> dict[str, Any]:
    """Set the intended star state without changing the document source or date."""
    from docs_management_document_target import resolve_managed_document_target
    from docs_workspace_config import require_document_authoring

    if set(body) - {"collection"} != {"stage", "doc_id", "selected"} or type(body.get("selected")) is not bool:
        raise ValueError("Set Selected requires stage, doc_id and boolean selected, with optional collection")
    resolved = resolve_managed_document_target(repo_root, {key: value for key, value in body.items() if key != "selected"})
    require_document_authoring(resolved.parent_config)
    payload = read_selected(resolved.parent_config)
    rows = [row for row in payload["docs"] if (row.get("collection", ""), row["doc_id"]) != (resolved.collection, resolved.doc_id)]
    if body["selected"]:
        rows.append(selected_row(resolved.document, resolved.document_config))
    updated = {"schema": SELECTED_SCHEMA, "docs": rows}
    text = selected_text(updated)
    if not dry_run and updated != payload:
        write_text_atomic(selected_path(resolved.parent_config), text)
    return {"ok": True, "target": resolved.request_target(), "selected": body["selected"], "dry_run": dry_run}
