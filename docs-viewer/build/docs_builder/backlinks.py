from __future__ import annotations

from typing import Any

from .common import read_json, scope_uses_external_data
from .source import DocRecord
from docs_rendered_links import collect_anchors, parse_docs_target, resolve_href


DOCS_BACKLINKS_SCHEMA_VERSION = "docs_backlinks_v1"


class BacklinksMixin:
    @property
    def backlinks_supported(self) -> bool:
        return not scope_uses_external_data(self.config)

    def backlinks_payload(
        self,
        docs: list[DocRecord],
        item_payloads: dict[str, dict[str, Any]],
    ) -> dict[str, Any] | None:
        if not self.backlinks_supported:
            return None

        current_ids = {doc.doc_id for doc in docs}
        docs_by_id = {doc.doc_id: doc for doc in docs}
        payloads_by_id: dict[str, dict[str, Any]] = {}
        for doc in docs:
            payload = item_payloads.get(doc.doc_id)
            if payload is None:
                payload = read_json(self.items_dir / f"{doc.doc_id}.json")
            if not isinstance(payload, dict):
                raise RuntimeError(
                    "Backlink generation requires an existing rendered payload for "
                    f"{self.scope_id}/{doc.doc_id}"
                )
            payloads_by_id[doc.doc_id] = payload

        source_ids_by_target: dict[str, set[str]] = {}
        viewer_routes = ((self.scope_id, self.viewer_base_url),)
        for source_doc in docs:
            content_html = str(
                payloads_by_id[source_doc.doc_id].get("content_html") or ""
            )
            for anchor in collect_anchors(content_html):
                resolved_href = resolve_href(
                    str(anchor.get("href") or ""),
                    self.viewer_url_for(source_doc.doc_id),
                )
                target = parse_docs_target(
                    resolved_href,
                    viewer_routes=viewer_routes,
                )
                if target is None or target.get("kind") != "viewer":
                    continue
                target_scope = str(target.get("scope") or "").strip().lower()
                target_doc_id = str(target.get("doc_id") or "").strip()
                if (
                    target_scope != self.scope_id
                    or target_doc_id not in current_ids
                    or target_doc_id == source_doc.doc_id
                ):
                    continue
                source_ids_by_target.setdefault(target_doc_id, set()).add(
                    source_doc.doc_id
                )

        by_target: dict[str, list[dict[str, str]]] = {}
        for target_doc_id in sorted(source_ids_by_target):
            rows = [
                {
                    "doc_id": source_doc_id,
                    "title": docs_by_id[source_doc_id].title,
                    "viewer_url": self.viewer_url_for(source_doc_id),
                }
                for source_doc_id in source_ids_by_target[target_doc_id]
            ]
            rows.sort(key=lambda row: (row["title"].casefold(), row["doc_id"]))
            by_target[target_doc_id] = rows

        comparable = {
            "schema": DOCS_BACKLINKS_SCHEMA_VERSION,
            "scope": self.scope_id,
            "by_target": by_target,
        }
        return {
            **comparable,
            "generated_at": self.effective_generated_at_for_payload(
                self.output_dir / "backlinks.json",
                comparable,
            ),
        }
