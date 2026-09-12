"""Shared placement decisions for metadata confirmation and document drops.

The selected ordinary document identifies a parent or an exact configured
collection host. Sources remain in their current location when collection entry
would move a hierarchy, a report host or the scope default.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import docs_source_model as source_model
from docs_document_location import sub_scope_report_placement, management_collection_viewer_url, management_document_viewer_url
from docs_management_document_target import ManagedDocumentTarget, ManagedDocumentCollection, resolve_managed_document_collection
from docs_scope_config import require_document_authoring


def supports_collection_placement(target: ManagedDocumentTarget) -> bool:
    return target.scope == "analysis" and target.stage == "working"


@dataclass(frozen=True)
class DocumentPlacement:
    source: ManagedDocumentTarget
    destination: ManagedDocumentCollection
    parent_id: str
    ignored: bool = False

    @property
    def collection_changed(self) -> bool:
        return self.source.sub_scope != self.destination.sub_scope

    @property
    def changed(self) -> bool:
        return self.collection_changed or self.parent_id != self.source.document.parent_id

    def target(self) -> dict[str, str]:
        return {**self.destination.request_target(), "doc_id": self.source.doc_id}

    def response(self, repo_root: Path) -> dict[str, object]:
        result: dict[str, object] = {
            "changed": self.changed,
            "collection_changed": self.collection_changed,
            "ignored": self.ignored,
        }
        if self.collection_changed:
            url = management_collection_viewer_url(
                repo_root, self.destination.scope, self.destination.sub_scope,
                stage=self.destination.stage,
            )
            result["viewer_url"] = management_document_viewer_url(
                url, self.source.doc_id, sub_scope=bool(self.destination.sub_scope),
            )
        return result


def resolve_document_placement(
    repo_root: Path, source: ManagedDocumentTarget, parent_id: str | None,
) -> DocumentPlacement:
    """Resolve a current server-side destination, retaining silent no-op placement.

None means no requested placement edit. Empty text means the ordinary root.
The existing parent_id request carries the selected ordinary document ID; in
Analysis Working an exact collection host selects its collection instead.
"""
    require_document_authoring(source.parent_config)
    current = resolve_managed_document_collection(
        repo_root, scope=source.scope, stage=source.stage or None,
        sub_scope=source.sub_scope or None,
    )
    unchanged = DocumentPlacement(source, current, source.document.parent_id)
    if parent_id is None:
        return unchanged
    if source.sub_scope and not supports_collection_placement(source):
        raise ValueError("parent_id is not editable for a sub-scope document")
    docs = source_model.load_scope_docs_for_config(repo_root, source.parent_config)
    by_id = {doc.doc_id: doc for doc in docs}
    if parent_id == source.doc_id and not source.sub_scope:
        raise ValueError("parent_id cannot be the current doc")
    if parent_id and parent_id not in by_id:
        raise ValueError(f"Unknown parent_id {parent_id!r} for scope {source.scope}")
    if not source.sub_scope and parent_id in source_model.descendant_doc_ids(docs, source.doc_id):
        raise ValueError("parent_id cannot be a child or descendant of the current doc")
    parent = by_id.get(parent_id)
    collection = ""
    if supports_collection_placement(source) and parent and parent.report and parent.report.id == "docs_subscope":
        collection = parent.report.sub_scope
        _, _, host_id = sub_scope_report_placement(repo_root, source.scope, collection, stage=source.stage)
        if host_id != parent_id:
            raise ValueError("Placement destination does not match its configured report host")
        protected = (
            source.doc_id == source.parent_config.default_doc_id
            or (source.document.report is not None and source.document.report.id == "docs_subscope")
            or (not source.sub_scope and bool(source_model.direct_child_doc_ids(docs, source.doc_id)))
        )
        if protected:
            return DocumentPlacement(source, current, source.document.parent_id, ignored=True)
    destination = resolve_managed_document_collection(
        repo_root, scope=source.scope, stage=source.stage or None,
        sub_scope=collection or None,
    )
    return DocumentPlacement(source, destination, "" if collection else parent_id)


def document_location_parent_id(repo_root: Path, source: ManagedDocumentTarget) -> str:
    """Return the exact selected location for the existing metadata picker."""
    if not source.sub_scope:
        return source.document.parent_id
    return sub_scope_report_placement(
        repo_root, source.scope, source.sub_scope, stage=source.stage,
    )[2]
