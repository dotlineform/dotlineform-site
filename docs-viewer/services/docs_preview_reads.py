#!/usr/bin/env python3
"""Validated reads from accepted Docs Viewer workspace snapshots."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from docs_document_identity import is_immutable_doc_id
from docs_workspace_config import load_docs_stage, safe_relative_path
from docs_preview_snapshot import validate_preview_snapshot


EXTERNAL_COLLECTION_PREVIEW_PREFIX = "/docs/preview/external/"
PREVIEW_MEDIA_PREFIX = "/docs/preview/media/"



def _read_json(data: bytes, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{label} is not valid UTF-8 JSON") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"{label} must contain a JSON object")
    return payload


def _snapshot_file(repo_root: Path, relative_path: Path) -> bytes:
    _manifest, _root, files = validate_preview_snapshot(repo_root)
    data = files.get(relative_path)
    if data is None:
        raise FileNotFoundError(
            f"preview snapshot file not found: {relative_path.as_posix()}"
        )
    return data


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
    if not is_immutable_doc_id(doc_id):
        raise ValueError("doc_id must use the immutable document ID format")
    index = read_preview_docs_index_tree(repo_root)
    stack = [row for row in index.get("docs", []) if isinstance(row, dict)]
    found = False
    while stack:
        row = stack.pop(0)
        if row.get("doc_id") == doc_id:
            found = True
            break
        stack.extend(
            child for child in row.get("children", []) if isinstance(child, dict)
        )
    if not found:
        raise FileNotFoundError(f"preview doc payload for {doc_id} not found")
    return _read_json(
        _snapshot_file(
            repo_root,
            Path("documents/by-id") / f"{doc_id}.json",
        ),
        f"preview doc payload for {doc_id}",
    )


def external_collection_payload_path(repo_root: Path, request_path: str) -> Path:
    if not request_path.startswith(EXTERNAL_COLLECTION_PREVIEW_PREFIX):
        raise ValueError("Invalid preview Docs collection payload route")
    parts = request_path.removeprefix(EXTERNAL_COLLECTION_PREVIEW_PREFIX).split("/")
    if len(parts) == 2 and parts[1] in {
        "manifest.json",
        "subject-associations.json",
    }:
        collection, filename = parts
        relative_path = Path("collections") / collection / "documents" / filename
    elif len(parts) == 3 and parts[1] == "by-id" and parts[2].endswith(".json"):
        collection, _, filename = parts
        doc_id = filename.removesuffix(".json")
        if not is_immutable_doc_id(doc_id):
            raise ValueError("Preview Docs collection payload doc_id must use immutable identity")
        relative_path = Path("collections") / collection / "documents/by-id" / filename
    else:
        raise ValueError("Invalid preview Docs collection payload route")

    config = load_docs_stage(repo_root, "preview")
    if not any(item.collection == collection for item in config.collections):
        raise FileNotFoundError(f"Docs collection not found: {collection}")
    _manifest, root, files = validate_preview_snapshot(repo_root)
    if relative_path not in files:
        raise FileNotFoundError(
            f"Preview Docs collection payload not found: "
            f"{collection}/{Path(*parts[1:]).as_posix()}"
        )
    return root / relative_path


def preview_media_path(repo_root: Path, request_path: str) -> tuple[Path, str]:
    if not request_path.startswith(PREVIEW_MEDIA_PREFIX):
        raise ValueError("Invalid preview Docs media route")
    parts = request_path.removeprefix(PREVIEW_MEDIA_PREFIX).split("/")
    if len(parts) < 2:
        raise ValueError("Preview Docs media route requires type and identity")
    collection = ""
    if parts[0] == "collections":
        if len(parts) < 4:
            raise ValueError("Preview child media requires collection, type, and identity")
        _, collection, *parts = parts
    media_type, *identity_parts = parts
    identity = safe_relative_path("/".join(identity_parts), field="preview media identity")
    config = load_docs_stage(repo_root, "preview")
    resolved_collection = config
    if collection:
        resolved_collection = next((child for child in config.collections if child.collection == collection), None)
    if resolved_collection is None or media_type not in resolved_collection.media.types:
        raise FileNotFoundError(f"Preview Docs media type not found: {media_type}")
    relative_path = resolved_collection.media.types[media_type].preview_location.path.relative_to(config.workspace_root.path / "preview") / identity
    _manifest, root, files = validate_preview_snapshot(repo_root)
    if relative_path not in files:
        raise FileNotFoundError(
            f"Preview Docs media not found: {media_type}/{identity.as_posix()}"
        )
    return root / relative_path, media_type


__all__ = [
    "EXTERNAL_COLLECTION_PREVIEW_PREFIX",
    "PREVIEW_MEDIA_PREFIX",
    "external_collection_payload_path",
    "read_preview_backlinks",
    "read_preview_doc_payload",
    "read_preview_docs_index_tree",
    "read_preview_recent",
    "read_preview_search_index",
    "read_preview_semantic_tokens_index",
    "preview_media_path",
]
