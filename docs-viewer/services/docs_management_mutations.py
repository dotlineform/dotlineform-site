"""Create-only source construction for Docs Management."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

import docs_source_model as source_model
from docs_document_subjects import subject_key_is_canonical
from docs_index_order import index_order_path, index_order_text, insert_node, read_index_order, tree_parent_ids
from docs_management_document_target import committed_document_record, ManagedDocumentCollection, resolve_managed_document_collection
from docs_workspace_config import require_document_authoring, resolve_external_data_root


def relative_path(repo_root: Path, path: Path) -> str:
    resolved = path.resolve()
    if resolved.is_relative_to(repo_root.resolve()):
        return resolved.relative_to(repo_root.resolve()).as_posix()
    return resolved.relative_to(resolve_external_data_root().resolve()).as_posix()


def normalize_metadata_text(value: Any) -> str:
    return str(value or "").strip()


@dataclass(frozen=True)
class SourceWrite:
    path: Path
    text: str
    create_only: bool = False


@dataclass(frozen=True)
class ManagementMutationPlan:
    """Carry prepared writes, exact hierarchy authority and the document build handoff."""

    response: Dict[str, Any]
    source_writes: tuple[SourceWrite, ...]
    index_order_path: Path | None
    prepared_owner: ManagedDocumentCollection
    prepared_document: source_model.SourceDoc
    parent_ids: dict[str, str] | None = None
    log_event_name: str | None = None
    log_details: Dict[str, Any] = field(default_factory=dict)

    @property
    def changed_paths(self) -> list[Path]:
        return [write.path for write in self.source_writes]


def plan_create(
    repo_root: Path, body: Dict[str, Any], *, body_markdown: str | None = None,
) -> ManagementMutationPlan:
    """Plan one create-only write without reading existing named-collection docs.

    Ordinary documents add their ID to the authored tree.
    Catalogue records have no draft field; other documents start as drafts. Catalogue
    fields are present before the creation build. Internal generators may supply
    body_markdown; the HTTP create request does not expose it.
    """
    if "scope" in body:
        raise ValueError("scope is retired; use optional collection")
    if "viewable" in body:
        raise ValueError("legacy viewable is not accepted")
    if "publishable" in body or "draft" in body:
        raise ValueError("publishable is retired and draft is assigned by Create")
    collection_requested = "collection" in body
    resolved_collection = resolve_managed_document_collection(
        repo_root,
        collection=body.get("collection") if collection_requested else None,
        require_existing_source_root=False,
    )
    require_document_authoring(resolved_collection.parent_config)
    collection = resolved_collection.collection
    if not isinstance(body.get("title"), str):
        raise ValueError("New title must be a string")
    title = body["title"].strip()
    if collection == "catalogue":
        work_id = body.get("work_id")
        if not isinstance(work_id, str) or not work_id.isascii() or not subject_key_is_canonical("work", work_id):
            raise ValueError("Catalogue New requires work_id as an exact five-digit string")
        title = body["title"]
    elif "work_id" in body:
        raise ValueError("work_id is only accepted when creating a Catalogue collection document")
    target_root = resolved_collection.source_root
    if "parent_id" in body:
        raise ValueError("Create uses target_doc_id and placement, not parent_id")
    order_path = index_order_path(resolved_collection.parent_config) if not collection else None
    tree = read_index_order(order_path) if order_path is not None else []

    timestamp = source_model.current_doc_timestamp()
    doc_id = work_id if collection == "catalogue" else source_model.allocate_doc_id(
        timestamp, set(tree_parent_ids(tree)),
    )
    parent_id = ""
    if not collection:
        parent_id = insert_node(
            tree, {"doc_id": doc_id},
            str(body.get("target_doc_id") or ""), str(body.get("placement") or "inside"),
        )
    target_path = target_root / f"{doc_id}.md"
    document = source_model.new_document_source(
        target_path, doc_id, title, f"# {title}\n" if body_markdown is None else body_markdown,
        config=resolved_collection.document_config, timestamp=timestamp,
    )
    front_matter = document.front_matter
    source_text = document.source_text
    document.parent_id = parent_id
    document.report = source_model.parse_collection_document_report(
        repo_root, resolved_collection.parent_config, resolved_collection.document_config,
        source_text, front_matter=front_matter, body=document.body, source_name=target_path.name,
    )
    path = relative_path(repo_root, target_path)
    target = {**resolved_collection.request_target(), "doc_id": doc_id}
    if collection:
        target["collection"] = collection
    record = committed_document_record(front_matter, doc_id, resolved_collection.document_config, collection=collection, parent_id=parent_id)
    response: Dict[str, Any] = {
        "ok": True,
        "doc_id": doc_id,
        "path": path,
        "target": target,
        "record": record,
        "summary_text": f"Created {doc_id}.",
    }
    if collection:
        response["collection"] = collection
    log_details = {
        "doc_id": doc_id,
        "path": path,
    }
    if collection:
        log_details["collection"] = collection

    return ManagementMutationPlan(
        response=response,
        index_order_path=order_path,
        source_writes=(
            SourceWrite(
                target_path,
                source_text,
                create_only=True,
            ),
            *((SourceWrite(order_path, index_order_text(tree)),) if order_path is not None else ()),
        ),
        prepared_owner=resolved_collection,
        prepared_document=document,
        parent_ids=tree_parent_ids(tree) if not collection else None,
        log_event_name="docs-create",
        log_details=log_details,
    )
