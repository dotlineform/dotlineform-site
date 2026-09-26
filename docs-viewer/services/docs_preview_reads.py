#!/usr/bin/env python3
"""Read requested Preview files; preparation and deployment validate the snapshot."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from docs_document_identity import is_immutable_doc_id
from docs_workspace_config import load_docs_stage, location_child, safe_relative_path
from docs_selected_documents import validate_selected_payload


EXTERNAL_COLLECTION_PREVIEW_PREFIX = "/docs/preview/external/"



def _read_json(data: bytes, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{label} is not valid UTF-8 JSON") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"{label} must contain a JSON object")
    return payload


def _snapshot_file(repo_root: Path, relative_path: Path) -> bytes:
    """Open one confined file without reading a completion manifest or other files."""
    config = load_docs_stage(repo_root, "preview")
    relative_path = safe_relative_path(relative_path.as_posix(), field="Preview file")
    path = location_child(config.workspace_root, Path("preview") / relative_path).path
    if not path.is_file():
        raise FileNotFoundError(
            f"preview snapshot file not found: {relative_path.as_posix()}"
        )
    return path.read_bytes()


def read_preview_docs_index_tree(repo_root: Path) -> dict[str, Any]:
    return _read_json(
        _snapshot_file(repo_root, Path("documents/index-tree.json")),
        "preview docs index tree in the workspace",
    )


def read_preview_recent(repo_root: Path) -> dict[str, Any]:
    return _read_json(
        _snapshot_file(repo_root, Path("documents/recent.json")),
        "preview Recent docs in the workspace",
    )


def read_preview_selected(repo_root: Path) -> dict[str, Any]:
    payload = _read_json(_snapshot_file(repo_root, Path("documents/selected.json")), "preview Selected Documents")
    validate_selected_payload(payload)
    return payload


def read_preview_backlinks(repo_root: Path) -> dict[str, Any]:
    return _read_json(
        _snapshot_file(repo_root, Path("documents/backlinks.json")),
        "preview backlinks in the workspace",
    )


def read_preview_semantic_tokens_index(repo_root: Path) -> dict[str, Any]:
    return _read_json(
        _snapshot_file(
            repo_root,
            Path("documents/semantic-tokens/index.json"),
        ),
        "preview semantic-token usage index in the workspace",
    )


def read_preview_search_index(repo_root: Path) -> dict[str, Any]:
    return _read_json(
        _snapshot_file(repo_root, Path("search/index.json")),
        "preview Search index in the workspace",
    )


def read_preview_doc_payload(
    repo_root: Path,
    doc_id: str,
) -> dict[str, Any]:
    """Read the exact by-ID document without an index-membership lookup."""
    if not is_immutable_doc_id(doc_id):
        raise ValueError("doc_id must use the immutable document ID format")
    return _read_json(
        _snapshot_file(
            repo_root,
            Path("documents/by-id") / f"{doc_id}.json",
        ),
        f"preview doc payload for {doc_id}",
    )


def external_collection_payload_path(repo_root: Path, request_path: str) -> Path:
    """Resolve only the requested artifact within its configured Preview collection."""
    if not request_path.startswith(EXTERNAL_COLLECTION_PREVIEW_PREFIX):
        raise ValueError("Invalid preview Docs collection payload route")
    parts = request_path.removeprefix(EXTERNAL_COLLECTION_PREVIEW_PREFIX).split("/")
    if len(parts) == 2 and parts[1] in {
        "manifest.json",
        "subject-associations.json",
    }:
        collection, filename = parts
        relative_path = Path(filename)
    elif len(parts) == 3 and parts[1] == "by-id" and parts[2].endswith(".json"):
        collection, _, filename = parts
        doc_id = filename.removesuffix(".json")
        if not is_immutable_doc_id(doc_id):
            raise ValueError("Preview Docs collection payload doc_id must use immutable identity")
        relative_path = Path("by-id") / filename
    else:
        raise ValueError("Invalid preview Docs collection payload route")

    config = load_docs_stage(repo_root, "preview")
    selected = next((item for item in config.collections if item.collection == collection), None)
    if selected is None:
        raise FileNotFoundError(f"Docs collection not found: {collection}")
    path = location_child(selected.preview.documents.location, relative_path).path
    if not path.is_file():
        raise FileNotFoundError(
            f"Preview Docs collection payload not found: "
            f"{collection}/{Path(*parts[1:]).as_posix()}"
        )
    return path


__all__ = [
    "EXTERNAL_COLLECTION_PREVIEW_PREFIX",
    "external_collection_payload_path",
    "read_preview_backlinks",
    "read_preview_doc_payload",
    "read_preview_docs_index_tree",
    "read_preview_recent",
    "read_preview_search_index",
    "read_preview_semantic_tokens_index",
]
