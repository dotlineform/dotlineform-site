#!/usr/bin/env python3
"""Read helpers for generated Docs Viewer JSON artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from docs_document_identity import is_document_id, is_immutable_doc_id
from docs_workspace_config import (
    generated_documents_path,
    generated_search_path,
    load_docs_working_config,
    resolve_workspace_path,
)


EXTERNAL_COLLECTION_GENERATED_PREFIX = "/docs/generated/external/"


def generated_docs_output_root(repo_root: Path) -> Path:
    config = load_docs_working_config(repo_root)
    return resolve_workspace_path(repo_root, generated_documents_path(config))


def external_collection_payload_path(repo_root: Path, request_path: str) -> Path:
    if not request_path.startswith(EXTERNAL_COLLECTION_GENERATED_PREFIX):
        raise ValueError("Invalid external Docs collection payload route")
    parts = request_path.removeprefix(EXTERNAL_COLLECTION_GENERATED_PREFIX).split("/")
    if len(parts) < 2:
        raise ValueError("Generated collection route requires collection and artifact")
    collection, *artifact = parts
    config = load_docs_working_config(repo_root)
    selected = next((child for child in config.collections if child.collection == collection), None)
    if selected is None:
        raise FileNotFoundError(f"Docs collection not found: {collection}")
    if len(artifact) == 1 and artifact[0] == "manage-manifest.json":
        relative_path = Path(artifact[0])
    elif len(artifact) == 2 and artifact[0] == "by-id" and artifact[1].endswith(".json") and is_document_id(artifact[1][:-5], collection=collection):
        relative_path = Path(*artifact)
    else:
        raise ValueError("Invalid external Docs collection payload route")
    output_root = resolve_workspace_path(repo_root, generated_documents_path(selected))
    path = (output_root / relative_path).resolve()
    if not path.is_relative_to(output_root):
        raise ValueError("Generated collection payload escapes its configured output")
    if not path.is_file():
        raise FileNotFoundError(f"Generated collection payload not found: {collection}/{relative_path}")
    return path


def generated_docs_index_tree_path(repo_root: Path) -> Path:
    return generated_docs_output_root(repo_root) / "index-tree.json"


def generated_recent_path(repo_root: Path) -> Path:
    return generated_docs_output_root(repo_root) / "recent.json"


def generated_doc_payload_path(repo_root: Path, doc_id: str) -> Path:
    if not is_immutable_doc_id(doc_id):
        raise ValueError("doc_id must use the immutable document ID format")
    return generated_docs_output_root(repo_root) / "by-id" / f"{doc_id}.json"


def generated_search_index_path(repo_root: Path) -> Path:
    config = load_docs_working_config(repo_root)
    return resolve_workspace_path(repo_root, generated_search_path(config))


def read_generated_workspace_links(repo_root: Path) -> Dict[str, Any]:
    """Read the saved Working aggregate without building or scanning records."""
    output = generated_docs_output_root(repo_root).resolve()
    path = output / "links.json"
    if path.is_symlink():
        raise ValueError("Workspace Links data must remain in its configured directory")
    payload = read_generated_json(path, "generated workspace Links")
    if (
        not isinstance(payload, dict) or payload.get("schema_version") != 4
        or "scope" in payload or "stage" in payload
        or not isinstance(payload.get("documents"), list)
    ):
        raise ValueError("Workspace Links data does not match Working")
    return payload


def read_generated_json(path: Path, label: str) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"{label} not found: {path.name}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{label} is not valid JSON: {path.name}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"{label} must contain a JSON object: {path.name}")
    return payload


def generated_data_available(repo_root: Path) -> bool:
    return generated_docs_index_tree_path(repo_root).exists()


def generated_search_data_available(repo_root: Path) -> bool:
    return generated_search_index_path(repo_root).exists()


def read_generated_docs_index_tree(repo_root: Path) -> Dict[str, Any]:
    return read_generated_json(
        generated_docs_index_tree_path(repo_root),
        "generated docs index tree",
    )


def read_generated_recent(repo_root: Path) -> Dict[str, Any]:
    return read_generated_json(
        generated_recent_path(repo_root),
        "generated Recent docs",
    )


def read_generated_search_index(repo_root: Path) -> Dict[str, Any]:
    return read_generated_json(
        generated_search_index_path(repo_root),
        "generated search index",
    )


def read_generated_doc_payload(repo_root: Path, doc_id: str) -> Dict[str, Any]:
    """Read the exact Working by-ID file without consulting the document index."""
    return read_generated_json(
        generated_doc_payload_path(repo_root, doc_id),
        f"generated doc payload for {doc_id}",
    )
