from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any
from urllib.parse import quote

from .browser_config import browser_collection_output_url_base
from .common import (
    DOCS_INDEX_TREE_SCHEMA_VERSION,
    DOCS_RECENT_SCHEMA_VERSION,
    humanize,
    read_json,
    render_markdown_to_html,
    utc_timestamp,
)
from .rendering import add_missing_image_titles
from .source import DocRecord, DocumentIdentity, extract_title
from docs_document_identity import is_doc_timestamp, is_immutable_doc_id
from docs_document_subjects import project_reader_subject
from docs_report_source import project_report_markdown
from docs_source_model import load_document_collection_docs_for_config


class PayloadBuilderMixin:
    def item_entry(
        self,
        doc: DocRecord,
        docs: Sequence[DocumentIdentity],
        semantic_tokens_by_doc: dict[str, list[dict[str, Any]]],
    ) -> dict[str, Any]:
        projected_markdown = project_report_markdown(
            doc.body_markdown,
            doc.report,
            include_host=True,
        )
        resolved = self.resolve_content_tokens(
            projected_markdown,
            doc=doc,
            semantic_tokens_by_doc=semantic_tokens_by_doc,
        )
        content_html = add_missing_image_titles(
            self.rewrite_doc_links(
                self.restore_catalogue_media_html(render_markdown_to_html(resolved)),
                current_doc=doc, docs=docs,
            )
        )
        entry = self.by_id_metadata_entry(doc, docs)
        entry["subject"] = project_reader_subject(doc.front_matter)
        entry["content_html"] = content_html
        return entry

    def doc_sort_key(self, doc: DocRecord) -> tuple[str, str]:
        return (doc.title.lower(), doc.doc_id)

    def ordered_docs_for_index(self, docs: list[DocRecord]) -> list[DocRecord]:
        children_by_parent: dict[str, list[DocRecord]] = {}
        for doc in docs:
            children_by_parent.setdefault(self.effective_parent_id(doc, docs), []).append(doc)
        for children in children_by_parent.values():
            children.sort(key=self.doc_sort_key)
        ordered: list[DocRecord] = []
        seen: set[str] = set()

        def append_children(parent_id: str) -> None:
            for child in children_by_parent.get(parent_id, []):
                if child.doc_id in seen:
                    continue
                seen.add(child.doc_id)
                ordered.append(child)
                append_children(child.doc_id)

        append_children("")
        for doc in sorted(docs, key=self.doc_sort_key):
            if doc.doc_id not in seen:
                seen.add(doc.doc_id)
                ordered.append(doc)
        return ordered

    def effective_generated_at_for_payload(self, path: Path, comparable_payload: dict[str, Any]) -> str:
        existing = read_json(path)
        if not isinstance(existing, dict):
            return utc_timestamp()
        generated_at = str(existing.get("generated_at") or "").strip()
        comparable_existing = {key: value for key, value in existing.items() if key != "generated_at"}
        if comparable_existing == comparable_payload and generated_at:
            return generated_at
        return utc_timestamp()

    def tree_entry(self, doc: DocRecord) -> dict[str, Any]:
        entry: dict[str, Any] = {
            "doc_id": doc.doc_id,
            "title": doc.title,
            "content_url": doc.content_url,
        }
        if self.config.stage == "working":
            entry["draft"] = doc.front_matter.get("draft", True)
        if doc.ui_status:
            entry["ui_status"] = doc.ui_status
        if doc.report is not None:
            entry["report_id"] = doc.report.id
        return entry

    def index_tree_payload(self, docs: list[DocRecord], viewer_options: dict[str, Any]) -> dict[str, Any]:
        included_docs = self.ordered_docs_for_index(docs)
        included_ids = {doc.doc_id for doc in included_docs}
        included_by_parent: dict[str, list[DocRecord]] = {}
        for doc in included_docs:
            parent_id = self.effective_parent_id(doc, docs)
            if parent_id not in included_ids:
                parent_id = ""
            included_by_parent.setdefault(parent_id, []).append(doc)

        emitted_ids: set[str] = set()

        def node_for(doc: DocRecord, active_ids: set[str] | None = None) -> dict[str, Any]:
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
            "generated_at": self.effective_generated_at_for_payload(self.output_dir / "index-tree.json", comparable),
        }

    def recent_limit(self) -> int:
        return self.workspace.recent_limit

    def recent_entry(
        self,
        doc: DocRecord,
        docs: list[DocRecord],
        title_by_id: dict[str, str],
    ) -> dict[str, Any]:
        entry: dict[str, Any] = {
            "doc_id": doc.doc_id,
            "title": doc.title,
            "content_url": doc.content_url,
            "added_date": doc.added_date,
            "last_updated": doc.last_updated,
        }
        parent_id = self.effective_parent_id(doc, docs)
        if parent_id and parent_id in title_by_id:
            entry["parent_id"] = parent_id
            entry["parent_title"] = title_by_id[parent_id]
        return entry

    def recent_candidates(self, docs: list[DocRecord]) -> list[dict[str, Any]]:
        """Read all stage-local Recent metadata once, without rendering children.

        Full stage builds own this scan. Preparation already selected the stage's
        documents; collection configuration supplies their report host IDs.
        """
        title_by_id = {doc.doc_id: doc.title for doc in docs}
        rows = [self.recent_entry(doc, docs, title_by_id) for doc in docs]
        for collection in self.config.collections:
            children = load_document_collection_docs_for_config(self.repo_root, self.config, collection)
            if not children:
                continue
            output_base = browser_collection_output_url_base(self.config, collection)
            for child in children:
                if not is_immutable_doc_id(child.doc_id):
                    raise ValueError(f"Recent child has invalid doc_id: {child.path}")
                last_updated = str(child.front_matter.get("last_updated") or "").strip()
                rows.append({
                    "doc_id": child.doc_id,
                    "title": str(child.front_matter.get("title") or extract_title(child.body) or humanize(child.path.stem)).strip(),
                    "content_url": f"{output_base}/by-id/{quote(child.doc_id)}.json",
                    "added_date": str(child.front_matter.get("added_date") or last_updated).strip(),
                    "last_updated": last_updated,
                    "collection": collection.collection,
                    "report_doc_id": collection.report_host_doc_id,
                    "collection_title": collection.title,
                })
        return rows

    def recent_payload(
        self,
        candidates: list[dict[str, Any]],
        *,
        basis: str,
        output_path: Path,
        published: bool = False,
    ) -> dict[str, Any]:
        """Sort the complete candidate set before limiting a reader projection."""
        if basis not in {"added", "edited"}:
            raise ValueError(f"unsupported Recent basis {basis!r}")
        limit = self.recent_limit()
        timestamp_key = "added_date" if basis == "added" else "last_updated"
        ordered = sorted(
            candidates,
            key=lambda row: (row["title"].lower(), row["doc_id"], row.get("collection", "")),
        )
        ordered.sort(key=lambda row: row[timestamp_key], reverse=True)
        fields = ("doc_id", "title", "content_url", "parent_id", "parent_title",
                  "collection", "report_doc_id", "collection_title")
        rows = [
            {**{key: row[key] for key in fields if key in row}, "timestamp": row[timestamp_key]}
            for row in ordered
            if (basis == "added" and row[timestamp_key])
            or (basis == "edited" and is_doc_timestamp(row[timestamp_key]))
        ][:limit]
        if published:
            public_titles = {child.collection: child.public_title for child in self.config.collections}
            for row in rows:
                public_title = public_titles.get(row.get("collection", ""))
                if public_title:
                    row["collection_title"] = public_title
        comparable = {
            "schema": DOCS_RECENT_SCHEMA_VERSION,
            "basis": basis,
            "limit": limit,
            "docs": rows,
        }
        return {
            **comparable,
            "generated_at": self.effective_generated_at_for_payload(output_path, comparable),
        }
