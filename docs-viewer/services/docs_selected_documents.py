"""One canonical Working selection list, with stage-independent reader rows."""

from pathlib import Path
from typing import Any, Iterable
import json

from docs_document_identity import doc_updated_date
from docs_document_images import has_document_thumbnail
from docs_document_subjects import project_reader_subject
from docs_source_model import write_text_atomic
from docs_workspace_config import document_source_path


SELECTED_FILENAME = "selected.json"
SELECTED_SCHEMA = "docs_selected_v1"


def selected_path(config: Any) -> Path:
    root = document_source_path(config)
    path = root / SELECTED_FILENAME
    if path.is_symlink() or path.resolve().parent != root.resolve():
        raise ValueError("selected.json must stay in the configured document source directory")
    return path


def read_selected(config: Any) -> dict[str, Any]:
    """Parse the owned saved list without auditing unselected rows."""
    return json.loads(selected_path(config).read_text(encoding="utf-8"))


def selected_text(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def selected_row(document: Any, owner: Any) -> dict[str, Any]:
    """Project one thumbnail choice from source for Working and prepared readers.

    Assigned authored thumbnails take precedence. Context otherwise exposes only
    its exact Work subject; Folder subjects and private authoring data are omitted.
    Catalogue thumbnails derive directly from document identity in the reader.
    """
    row = {
        "doc_id": document.doc_id,
        "title": document.title,
        "last_updated": doc_updated_date(document.front_matter["last_updated"]),
    }
    collection = getattr(owner, "collection", "")
    if collection:
        row.update(collection=collection, report_doc_id=owner.report_host_doc_id)
    if has_document_thumbnail(document.front_matter, collection=collection):
        row["has_thumbnail"] = True
    elif collection == "works":
        subject = project_reader_subject(document.front_matter)
        if subject is not None:
            row["subject"] = subject
    return row


def refresh_selected_documents(
    config: Any, owner: Any, documents: Iterable[Any], *, write: bool,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Refresh selected metadata for built documents, preserving other selections."""
    payload = read_selected(config) if payload is None else payload
    collection = getattr(owner, "collection", "")
    built = {doc.doc_id: doc for doc in documents}
    rows = [
        selected_row(built[row["doc_id"]], owner)
        if row.get("collection", "") == collection and row["doc_id"] in built else row
        for row in payload["docs"]
    ]
    updated = {"schema": SELECTED_SCHEMA, "docs": rows}
    if write and updated != payload:
        write_text_atomic(selected_path(config), selected_text(updated))
    return updated


def refresh_workspace_selected(
    config: Any, documents_by_owner: Iterable[tuple[Any, Iterable[Any]]], *, payload: dict[str, Any],
) -> dict[str, Any]:
    """Refresh complete Build metadata with one saved-list read and one write.

    Selection membership is independent: absent targets retain their saved rows.
    """
    built = {
        (getattr(owner, "collection", ""), doc.doc_id): (owner, doc)
        for owner, documents in documents_by_owner for doc in documents
    }
    rows = []
    for row in payload["docs"]:
        known = built.get((row.get("collection", ""), row["doc_id"]))
        rows.append(selected_row(known[1], known[0]) if known is not None else row)
    updated = {"schema": SELECTED_SCHEMA, "docs": rows}
    if updated != payload:
        write_text_atomic(selected_path(config), selected_text(updated))
    return updated


def set_selected(repo_root: Path, body: dict[str, Any], *, dry_run: bool = False) -> dict[str, Any]:
    """Set the intended star state without changing the document source or date."""
    from docs_management_document_target import normalize_managed_document_target, resolve_managed_document_collection, resolve_managed_document_target
    from docs_workspace_config import require_document_authoring

    if set(body) - {"collection"} != { "doc_id", "selected"} or type(body.get("selected")) is not bool:
        raise ValueError("Set Selected requires doc_id and boolean selected, with optional collection")
    target = normalize_managed_document_target({key: value for key, value in body.items() if key != "selected"})
    resolved = resolve_managed_document_target(repo_root, target) if body["selected"] else resolve_managed_document_collection(repo_root, collection=target.get("collection"))
    require_document_authoring(resolved.parent_config)
    payload = read_selected(resolved.parent_config)
    rows = [row for row in payload["docs"] if (row.get("collection", ""), row["doc_id"]) != (target.get("collection", ""), target["doc_id"])]
    if body["selected"]:
        rows.append(selected_row(resolved.document, resolved.document_config))
    updated = {"schema": SELECTED_SCHEMA, "docs": rows}
    text = selected_text(updated)
    if not dry_run and updated != payload:
        write_text_atomic(selected_path(resolved.parent_config), text)
    return {"ok": True, "target": target, "selected": body["selected"], "dry_run": dry_run}
