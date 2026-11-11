"""Working-only placement and order for the Book collection."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from docs_generated_reads import read_generated_json
from docs_management_document_target import ManagedDocumentCollection, resolve_managed_document_collection
from docs_publication_paths import confined
from docs_source_model import write_text_atomic
from docs_workspace_config import DocsCollectionConfig, document_source_path, generated_documents_path, require_document_authoring


def book_tree_paths(config: DocsCollectionConfig) -> tuple[Path, Path]:
    return (
        confined(document_source_path(config).parent, "index-order.json"),
        confined(generated_documents_path(config), "index-tree.json"),
    )


def book_headings(tree: list[dict[str, Any]]):
    for node in tree:
        yield node
        yield from node.get("sections", [])


def validate_book_tree(tree: Any, book_ids: set[str]) -> None:
    headings: set[str] = set()
    placements: set[str] = set()

    def heading(node: Any, fields: set[str]) -> None:
        if not isinstance(node, dict) or set(node) != fields | {"id", "title", "doc_ids"}:
            raise ValueError("Book headings require an ID, title and document IDs; Parts also require sections")
        node_id, title = node["id"], node["title"]
        if not isinstance(node_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", node_id) or node_id in headings:
            raise ValueError("Book heading IDs must be distinct slugs")
        if not isinstance(title, str) or not title.strip():
            raise ValueError("Book headings require a title")
        headings.add(node_id)
        if not isinstance(node["doc_ids"], list):
            raise ValueError("Book heading document IDs must be a list")
        for doc_id in node["doc_ids"]:
            if not isinstance(doc_id, str) or doc_id not in book_ids or doc_id in placements:
                raise ValueError("Each placement must identify one distinct Book document")
            placements.add(doc_id)

    if not isinstance(tree, list):
        raise ValueError("Book tree must contain a list of headings")
    for node in tree:
        if isinstance(node, dict) and "sections" in node:
            heading(node, {"sections"})
            if not isinstance(node["sections"], list):
                raise ValueError("Book Part sections must be a list")
            for section in node["sections"]:
                heading(section, set())
        else:
            heading(node, set())


def project_book_tree(path: Path, tree: list[dict[str, Any]]) -> None:
    write_text_atomic(path, json.dumps({"tree": tree}, ensure_ascii=False, indent=2) + "\n")


def write_book_tree(paths: tuple[Path, Path], tree: list[dict[str, Any]]) -> None:
    source, generated = paths
    write_text_atomic(source, json.dumps(tree, ensure_ascii=False, indent=2) + "\n")
    project_book_tree(generated, tree)


def save_book_tree(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    if set(body) != {"tree"}:
        raise ValueError("Book tree Save requires the complete tree")
    owner = resolve_managed_document_collection(repo_root, collection="book")
    require_document_authoring(owner.parent_config)
    manifest = confined(generated_documents_path(owner.document_config), "manage-manifest.json")
    tree = body["tree"]
    validate_book_tree(tree, {row["doc_id"] for row in read_generated_json(manifest, "Book inventory")["docs"]})
    write_book_tree(book_tree_paths(owner.document_config), tree)
    return {"ok": True, "tree": tree}


def remove_book_placements(owner: ManagedDocumentCollection, removed: set[str]) -> None:
    paths = book_tree_paths(owner.document_config)
    tree = json.loads(paths[0].read_text(encoding="utf-8"))
    changed = False
    for heading in book_headings(tree):
        previous = heading["doc_ids"]
        remaining = [doc_id for doc_id in previous if doc_id not in removed]
        if remaining != previous:
            heading["doc_ids"] = remaining
            changed = True
    if changed:
        write_book_tree(paths, tree)


def rebuild_book_tree(config: DocsCollectionConfig, book_ids: set[str], *, write: bool) -> None:
    source, generated = book_tree_paths(config)
    tree = json.loads(source.read_text(encoding="utf-8"))
    validate_book_tree(tree, book_ids)
    if write:
        project_book_tree(generated, tree)
