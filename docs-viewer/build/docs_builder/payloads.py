from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any
from .common import (
    DOCS_INDEX_TREE_SCHEMA_VERSION,
    read_json,
    utc_timestamp,
)
from .rendering import add_missing_image_titles
from .source import DocRecord, DocumentIdentity
from .ordinary_metadata import OrdinaryDocumentSummary
from .related_links import render_related_links
from docs_document_identity import doc_updated_date
from docs_discovery_selection import select_collection_documents, select_ordinary_documents
from docs_publication_ignore import read_publication_ignore_ids
from docs_recent_exclusions import read_recent_exclusions
from docs_recent_payload import build_recent_payload
from docs_report_source import project_report_markdown


class PayloadBuilderMixin:
    def item_entry(
        self,
        doc: DocRecord,
        docs_by_id: Mapping[str, DocumentIdentity],
    ) -> dict[str, Any]:
        projected_markdown = project_report_markdown(
            doc.body_markdown,
            doc.report,
            include_host=True,
        )
        resolved = self.resolve_content_tokens(
            projected_markdown,
            document_id=doc.doc_id,
        )
        try:
            rendered = self.inline_icons.render_markdown(
                resolved, related_links=lambda heading: render_related_links(self, doc, heading), summary=doc.summary,
            )
        except ValueError as exc:
            raise ValueError(f"Document {doc.doc_id}: {exc}") from exc
        content_html = add_missing_image_titles(
            self.rewrite_doc_links(
                self.restore_semantic_media_html(rendered),
                current_doc=doc, docs_by_id=docs_by_id,
            )
        )
        entry = self.by_id_metadata_entry(doc, docs_by_id)
        entry["content_html"] = content_html
        return entry

    def doc_sort_key(self, doc: DocRecord) -> tuple[str, str]:
        return (doc.title.lower(), doc.doc_id)

    def ordered_docs_for_index(self, docs: list[DocRecord]) -> list[DocRecord]:
        """Preserve authored ordinary order and the separate flat collection sort."""
        if getattr(self, "collection_config", None) is not None:
            return sorted(docs, key=self.doc_sort_key)
        return docs

    def effective_generated_at_for_payload(
        self, path: Path, comparable_payload: dict[str, Any], *, existing_payload: dict[str, Any] | None = None,
    ) -> str:
        existing = read_json(path) if existing_payload is None else existing_payload
        if not isinstance(existing, dict):
            return utc_timestamp()
        generated_at = str(existing.get("generated_at") or "").strip()
        comparable_existing = {key: value for key, value in existing.items() if key != "generated_at"}
        if comparable_existing == comparable_payload and generated_at:
            return generated_at
        return utc_timestamp()

    def tree_entry(self, doc: DocRecord | OrdinaryDocumentSummary) -> dict[str, Any]:
        if isinstance(doc, OrdinaryDocumentSummary):
            return dict(doc.navigation_entry)
        entry: dict[str, Any] = {
            "doc_id": doc.doc_id,
            "title": doc.title,
            "content_url": doc.content_url,
        }
        if self.config.stage == "working":
            entry["draft"] = doc.front_matter["draft"]
        if doc.ui_status:
            entry["ui_status"] = doc.ui_status
        if doc.report is not None:
            entry["report_id"] = doc.report.id
        return entry

    def index_tree_payload(
        self, docs_by_id: Mapping[str, DocRecord | OrdinaryDocumentSummary], viewer_options: dict[str, Any],
        *, previous_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        included_docs = list(docs_by_id.values())
        included_by_parent: dict[str, list[DocRecord | OrdinaryDocumentSummary]] = {}
        for doc in included_docs:
            parent_id = self.effective_parent_id(doc.parent_id, docs_by_id)
            if parent_id not in docs_by_id:
                parent_id = ""
            included_by_parent.setdefault(parent_id, []).append(doc)

        emitted_ids: set[str] = set()

        def node_for(doc: DocRecord | OrdinaryDocumentSummary, active_ids: set[str] | None = None) -> dict[str, Any]:
            active = active_ids or set()
            active.add(doc.doc_id)
            emitted_ids.add(doc.doc_id)
            node = self.tree_entry(doc)
            children = [
                node_for(child, set(active))
                for child in included_by_parent.get(doc.doc_id, [])
                if child.doc_id not in active and child.doc_id not in emitted_ids
            ]
            if children:
                node["children"] = children
            return node

        tree = [node_for(doc) for doc in included_by_parent.get("", [])]
        for doc in included_docs:
            if doc.doc_id not in emitted_ids:
                tree.append(node_for(doc))
        comparable = {
            "schema": DOCS_INDEX_TREE_SCHEMA_VERSION,
            "viewer_options": viewer_options,
            "docs": tree,
        }
        return {
            **comparable,
            "generated_at": self.effective_generated_at_for_payload(
                self.output_dir / "index-tree.json", comparable, existing_payload=previous_payload,
            ),
        }

    def recent_limit(self) -> int:
        return self.workspace.recent_limit

    def recent_entry(
        self,
        doc: DocRecord,
        title_by_id: dict[str, str],
    ) -> dict[str, Any]:
        entry: dict[str, Any] = {
            "doc_id": doc.doc_id,
            "title": doc.title,
            "last_updated": doc_updated_date(doc.last_updated),
        }
        parent_id = self.effective_parent_id(doc.parent_id, title_by_id)
        if parent_id and parent_id in title_by_id:
            entry["parent_id"] = parent_id
            entry["parent_title"] = title_by_id[parent_id]
        return entry

    def recent_candidates(self, docs: list[DocRecord], tree: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Use current in-memory ordinary metadata and saved flat collection metadata.

        Only full Working builds call this. Collection bodies and the Search
        index are never opened; missing metadata must be rebuilt by its owner.
        """
        if self.config.stage != "working":
            raise ValueError("Recents generation requires Working; Preview copies the prepared payload")
        selected = select_ordinary_documents(
            tree, read_publication_ignore_ids(self.repo_root), field="Working Recents tree",
        )
        eligible_docs = [doc for doc in docs if doc.doc_id in selected]
        title_by_id = {doc.doc_id: doc.title for doc in eligible_docs}
        rows = [self.recent_entry(doc, title_by_id) for doc in eligible_docs]
        for collection, children in select_collection_documents(self.repo_root, self.config, set(selected)):
            for doc_id, child in children.items():
                rows.append({
                    "doc_id": doc_id,
                    "title": child["title"].strip(),
                    "last_updated": child["last_updated"].strip(),
                    "collection": collection.collection,
                    "report_doc_id": collection.report_host_doc_id,
                    "collection_title": collection.title,
                })
        return rows

    def recent_payload(
        self,
        candidates: list[dict[str, Any]],
        *,
        output_path: Path,
    ) -> dict[str, Any]:
        """Sort the complete candidate set before limiting a reader projection."""
        payload = build_recent_payload(
            candidates, limit=self.recent_limit(), generated_at=utc_timestamp(),
            exclusions=read_recent_exclusions(self.config),
        )
        comparable = {key: value for key, value in payload.items() if key != "generated_at"}
        payload["generated_at"] = self.effective_generated_at_for_payload(output_path, comparable)
        return payload
