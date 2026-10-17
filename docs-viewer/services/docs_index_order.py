"""Ordinary document hierarchy: nested IDs in their authored array order."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

from docs_workspace_config import DocsStageConfig, source_control_path

INDEX_ORDER_FILENAME = "index-order.json"


def index_order_path(config: DocsStageConfig) -> Path:
    """Resolve the source-root hierarchy independently of the Markdown directory."""
    return source_control_path(config, INDEX_ORDER_FILENAME)


def read_index_order(path: Path) -> list[dict[str, Any]]:
    """Read the exact file already confined by index_order_path."""
    tree = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(tree, list):
        raise ValueError("index-order.json must contain an array")
    return tree


def index_order_text(tree: list[dict[str, Any]]) -> str:
    """Serialize hierarchy records with children only on branches."""
    def node_payload(node: dict[str, Any]) -> dict[str, Any]:
        payload = dict(node)
        children = node.get("children", [])
        if children:
            payload["children"] = [node_payload(child) for child in children]
        else:
            payload.pop("children", None)
        return payload

    return json.dumps([node_payload(node) for node in tree], ensure_ascii=False, indent=2) + "\n"


def tree_groups(tree: list[dict[str, Any]], parent_id: str = "") -> Iterator[tuple[list[dict[str, Any]], str]]:
    yield tree, parent_id
    for node in tree:
        yield from tree_groups(node.get("children", []), node["doc_id"])


def tree_parent_ids(tree: list[dict[str, Any]]) -> dict[str, str]:
    """Return parent lookups in depth-first authored order."""
    parents: dict[str, str] = {}

    def visit(nodes: list[dict[str, Any]], parent_id: str) -> None:
        for node in nodes:
            if node["doc_id"] in parents:
                raise ValueError(f"Duplicate document ID in index-order.json: {node['doc_id']}")
            parents[node["doc_id"]] = parent_id
            visit(node.get("children", []), node["doc_id"])

    visit(tree, "")
    return parents


def node_location(tree: list[dict[str, Any]], doc_id: str) -> tuple[list[dict[str, Any]], int, str]:
    for siblings, parent_id in tree_groups(tree):
        for index, node in enumerate(siblings):
            if node["doc_id"] == doc_id:
                return siblings, index, parent_id
    raise ValueError(f"Document is not in index-order.json: {doc_id}")


def insert_node(tree: list[dict[str, Any]], node: dict[str, Any], target_id: str, placement: str) -> str:
    """Insert a node Before/After a target or Inside it; empty target is Root."""
    if placement not in {"before", "after", "inside"}:
        raise ValueError("placement must be before, after or inside")
    if target_id in tree_parent_ids([node]):
        raise ValueError("Cannot position a document inside its own subtree")
    if not target_id:
        if placement != "inside":
            raise ValueError("Root placement must be inside")
        tree.append(node)
        return ""
    siblings, index, parent_id = node_location(tree, target_id)
    if placement == "inside":
        siblings[index].setdefault("children", []).append(node)
        return target_id
    siblings.insert(index + (placement == "after"), node)
    return parent_id


def exclude_nodes(tree: list[dict[str, Any]], doc_ids: set[str]) -> list[dict[str, Any]]:
    """Omit complete branches for Delete or Preview without reordering survivors."""
    return [
        {"doc_id": node["doc_id"], "children": exclude_nodes(node.get("children", []), doc_ids)}
        for node in tree if node["doc_id"] not in doc_ids
    ]
