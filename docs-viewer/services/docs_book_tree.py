"""Working-only placement and order for the Book collection."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from docs_book_toc import BookContents, changed_book_contents
from docs_generation import rebuild_book_host
from docs_generated_reads import read_generated_json
from docs_management_document_target import ManagedDocumentCollection, resolve_managed_document_collection
from docs_publication_paths import confined
from docs_source_model import write_text_atomic
from docs_workspace_config import DocsCollectionConfig, DocsStageConfig, document_source_path, generated_documents_path, is_curated_book, require_document_authoring


def resolve_book_collection(
    repo_root: Path, collection: Any, *, config: DocsStageConfig | None = None,
) -> ManagedDocumentCollection:
    if collection is None:
        raise ValueError("Choose a configured Book collection")
    owner = resolve_managed_document_collection(repo_root, collection=collection, config=config)
    if not is_curated_book(owner.document_config):
        raise ValueError("Choose a configured Book collection")
    return owner


def book_order_path(config: DocsCollectionConfig) -> Path:
    return confined(document_source_path(config).parent, "index-order.json")


def book_manifest_path(config: DocsCollectionConfig) -> Path:
    return confined(generated_documents_path(config), "manage-manifest.json")


def project_chapter_sources(
    manifest: dict[str, Any], doc_id: str, sources: list[dict[str, str]],
) -> dict[str, Any]:
    """Carry completed provenance into the private chapter row."""
    row = next((row for row in manifest["docs"] if row["doc_id"] == doc_id), None)
    if row is None:
        raise ValueError(f"Chapter {doc_id} is missing from the Book management manifest")
    if sources:
        row["library_sources"] = sources
    else:
        row.pop("library_sources", None)
    return row


def read_book_order(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def book_order_text(order: dict[str, Any]) -> str:
    return json.dumps(order, ensure_ascii=False, indent=2) + "\n"


def book_headings(tree: list[dict[str, Any]]):
    for node in tree:
        yield node
        yield from node.get("sections", [])


def placement_list(order: dict[str, Any], heading_id: str, *, section_only: bool = False) -> list[str]:
    if heading_id == "":
        return order["root"]
    for heading in book_headings(order["tree"]):
        if heading["id"] == heading_id and (not section_only or "sections" not in heading):
            return heading["doc_ids"]
    raise ValueError("Choose Root or a heading in the selected Book")


def validate_book_order(order: Any, book_ids: set[str]) -> None:
    headings: set[str] = set()
    placements: set[str] = set()

    def documents(values: Any) -> None:
        if not isinstance(values, list):
            raise ValueError("Book placement document IDs must be a list")
        for doc_id in values:
            if not isinstance(doc_id, str) or doc_id not in book_ids or doc_id in placements:
                raise ValueError("Each placement must identify one distinct Book document")
            placements.add(doc_id)

    def heading(node: Any, fields: set[str]) -> None:
        if not isinstance(node, dict) or set(node) != fields | {"id", "title", "doc_ids"}:
            raise ValueError("Book headings require an ID, title and document IDs; Parts also require sections")
        node_id, title = node["id"], node["title"]
        if not isinstance(node_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", node_id) or node_id in headings:
            raise ValueError("Book heading IDs must be distinct slugs")
        if not isinstance(title, str) or not title.strip():
            raise ValueError("Book headings require a title")
        headings.add(node_id)
        documents(node["doc_ids"])

    if not isinstance(order, dict) or set(order) != {"root", "tree"} or not isinstance(order["tree"], list):
        raise ValueError("Book order requires Root documents and a list of headings")
    documents(order["root"])
    for node in order["tree"]:
        if isinstance(node, dict) and "sections" in node:
            heading(node, {"sections"})
            if not isinstance(node["sections"], list):
                raise ValueError("Book Part sections must be a list")
            for section in node["sections"]:
                heading(section, set())
        else:
            heading(node, set())
    if placements != book_ids:
        raise ValueError("Book order must place every document")


def commit_book_order(config: DocsCollectionConfig, order: Any) -> BookContents | None:
    """Save browser-authored placement and project it using the inventory already read."""
    manifest_path = book_manifest_path(config)
    manifest = read_generated_json(manifest_path, "Book inventory")
    if order == manifest["book_order"]:
        return None
    validate_book_order(order, {row["doc_id"] for row in manifest["docs"]})
    completed = {**manifest, "book_order": order}
    contents = changed_book_contents(manifest, completed)
    write_text_atomic(book_order_path(config), book_order_text(order))
    write_text_atomic(manifest_path, json.dumps(completed, ensure_ascii=False, indent=2) + "\n")
    return contents


def save_book_tree(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    if set(body) != {"collection", "book_order"}:
        raise ValueError("Book order Save requires a Book collection and the complete order")
    owner = resolve_book_collection(repo_root, body["collection"])
    require_document_authoring(owner.parent_config)
    order = body["book_order"]
    contents = commit_book_order(owner.document_config, order)
    result = {"ok": True, "book_order": order}
    if contents is not None:
        try:
            host = rebuild_book_host(repo_root, owner.parent_config, owner.workspace, owner.document_config, contents)
            if host is not None:
                result["book_toc"] = host
        except (OSError, RuntimeError, ValueError) as error:
            return {**result, "ok": False, "error": f"Book order saved, but its table of contents refresh failed: {error}"}
    return result


def remove_book_placements(owner: ManagedDocumentCollection, removed: set[str]) -> dict[str, Any]:
    path = book_order_path(owner.document_config)
    order = read_book_order(path)
    order["root"] = [doc_id for doc_id in order["root"] if doc_id not in removed]
    for heading in book_headings(order["tree"]):
        heading["doc_ids"] = [doc_id for doc_id in heading["doc_ids"] if doc_id not in removed]
    write_text_atomic(path, book_order_text(order))
    return order
