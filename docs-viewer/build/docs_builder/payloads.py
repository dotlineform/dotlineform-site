from __future__ import annotations

import json
from typing import Any

from .common import (
    CONFIG_REL_PATH,
    DEFAULT_RECENTLY_ADDED_LIMIT,
    DOCS_INDEX_TREE_SCHEMA_VERSION,
    DOCS_RECENTLY_ADDED_SCHEMA_VERSION,
    plain_text_from_html,
    read_json,
    render_markdown_to_html,
    utc_timestamp,
)
from .rendering import add_missing_image_titles
from .source import DocRecord


class PayloadBuilderMixin:
    def item_entry(
        self,
        doc: DocRecord,
        docs: list[DocRecord],
        semantic_references_by_doc: dict[str, list[dict[str, Any]]],
    ) -> dict[str, Any]:
        resolved = self.resolve_content_tokens(doc.body_markdown, doc=doc, references_by_doc=semantic_references_by_doc)
        content_html = add_missing_image_titles(
            self.rewrite_doc_links(render_markdown_to_html(resolved), current_doc=doc, docs=docs)
        )
        entry = self.by_id_metadata_entry(doc, docs)
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
        if not doc.viewable:
            entry["viewable"] = False
        if doc.ui_status:
            entry["ui_status"] = doc.ui_status
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

    def recently_added_limit(self) -> int:
        try:
            payload = json.loads((self.repo_root / CONFIG_REL_PATH).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return DEFAULT_RECENTLY_ADDED_LIMIT
        settings = payload.get("docs_viewer") if isinstance(payload, dict) else None
        raw_limit = settings.get("recently_added_limit") if isinstance(settings, dict) else None
        try:
            limit = int(raw_limit)
        except (TypeError, ValueError):
            return DEFAULT_RECENTLY_ADDED_LIMIT
        return limit if limit > 0 else DEFAULT_RECENTLY_ADDED_LIMIT

    def recently_added_entry(self, doc: DocRecord, docs: list[DocRecord], title_by_id: dict[str, str]) -> dict[str, Any]:
        entry: dict[str, Any] = {
            "doc_id": doc.doc_id,
            "title": doc.title,
            "content_url": doc.content_url,
            "added_date": doc.added_date,
        }
        parent_id = self.effective_parent_id(doc, docs)
        if parent_id and parent_id in title_by_id:
            entry["parent_id"] = parent_id
            entry["parent_title"] = title_by_id[parent_id]
        return entry

    def recently_added_payload(self, docs: list[DocRecord]) -> dict[str, Any]:
        limit = self.recently_added_limit()
        included_docs = docs
        title_by_id = {doc.doc_id: doc.title for doc in included_docs}
        ordered_docs = sorted(included_docs, key=lambda doc: (doc.title.lower(), doc.doc_id))
        ordered_docs.sort(key=lambda doc: doc.added_date, reverse=True)
        rows = [
            self.recently_added_entry(doc, docs, title_by_id)
            for doc in ordered_docs
            if doc.added_date
        ][:limit]
        comparable = {
            "schema": DOCS_RECENTLY_ADDED_SCHEMA_VERSION,
            "limit": limit,
            "docs": rows,
        }
        return {
            **comparable,
            "generated_at": self.effective_generated_at_for_payload(self.output_dir / "recently-added.json", comparable),
        }
