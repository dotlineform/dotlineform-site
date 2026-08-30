#!/usr/bin/env python3
"""Validated reads from accepted Docs Viewer scope snapshots."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from docs_document_identity import is_immutable_doc_id
from docs_scope_config import load_docs_scope_configs
from docs_scope_publish import validate_published_snapshot


EXTERNAL_SUB_SCOPE_PUBLISHED_PREFIX = "/docs/published/external/"
PUBLISHED_MEDIA_PREFIX = "/docs/published/media/"


def _read_json(data: bytes, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{label} is not valid UTF-8 JSON") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"{label} must contain a JSON object")
    return payload


def _snapshot_file(repo_root: Path, scope: str, relative_path: Path) -> bytes:
    _manifest, _root, files = validate_published_snapshot(repo_root, scope)
    data = files.get(relative_path)
    if data is None:
        raise FileNotFoundError(
            f"published snapshot file for {scope} not found: {relative_path.as_posix()}"
        )
    return data


def read_published_docs_index_tree(repo_root: Path, scope: str) -> dict[str, Any]:
    return _read_json(
        _snapshot_file(repo_root, scope, Path("documents/index-tree.json")),
        f"published docs index tree for {scope}",
    )


def read_published_recent(repo_root: Path, scope: str) -> dict[str, Any]:
    return _read_json(
        _snapshot_file(repo_root, scope, Path("documents/recent.json")),
        f"published Recent docs for {scope}",
    )


def read_published_backlinks(repo_root: Path, scope: str) -> dict[str, Any]:
    return _read_json(
        _snapshot_file(repo_root, scope, Path("documents/backlinks.json")),
        f"published backlinks for {scope}",
    )


def read_published_semantic_tokens_index(repo_root: Path, scope: str) -> dict[str, Any]:
    return _read_json(
        _snapshot_file(
            repo_root,
            scope,
            Path("documents/semantic-tokens/index.json"),
        ),
        f"published semantic-token usage index for {scope}",
    )


def read_published_search_index(repo_root: Path, scope: str) -> dict[str, Any]:
    return _read_json(
        _snapshot_file(repo_root, scope, Path("search/index.json")),
        f"published Search index for {scope}",
    )


def read_published_doc_payload(
    repo_root: Path,
    scope: str,
    doc_id: str,
) -> dict[str, Any]:
    if not is_immutable_doc_id(doc_id):
        raise ValueError("doc_id must use the immutable document ID format")
    index = read_published_docs_index_tree(repo_root, scope)
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
        raise FileNotFoundError(f"published doc payload for {doc_id} not found")
    return _read_json(
        _snapshot_file(
            repo_root,
            scope,
            Path("documents/by-id") / f"{doc_id}.json",
        ),
        f"published doc payload for {doc_id}",
    )


def external_sub_scope_payload_path(repo_root: Path, request_path: str) -> Path:
    if not request_path.startswith(EXTERNAL_SUB_SCOPE_PUBLISHED_PREFIX):
        raise ValueError("Invalid published Docs sub-scope payload route")
    parts = request_path.removeprefix(EXTERNAL_SUB_SCOPE_PUBLISHED_PREFIX).split("/")
    if len(parts) == 3 and parts[2] in {
        "manifest.json",
        "subject-associations.json",
    }:
        scope, sub_scope, filename = parts
        relative_path = Path("documents/sub-scopes") / sub_scope / filename
    elif len(parts) == 4 and parts[2] == "by-id" and parts[3].endswith(".json"):
        scope, sub_scope, _, filename = parts
        doc_id = filename.removesuffix(".json")
        if not is_immutable_doc_id(doc_id):
            raise ValueError("Published Docs sub-scope payload doc_id must use immutable identity")
        relative_path = Path("documents/sub-scopes") / sub_scope / "by-id" / filename
    else:
        raise ValueError("Invalid published Docs sub-scope payload route")

    config = load_docs_scope_configs(repo_root, scope_ids=(scope,)).get(scope)
    if config is None:
        raise FileNotFoundError(f"Published Docs scope not found: {scope!r}")
    if not any(item.sub_scope == sub_scope for item in config.sub_scopes):
        raise FileNotFoundError(f"Docs sub-scope not found: {scope}/{sub_scope}")
    _manifest, root, files = validate_published_snapshot(repo_root, scope)
    if relative_path not in files:
        raise FileNotFoundError(
            f"Published Docs sub-scope payload not found: "
            f"{scope}/{sub_scope}/{Path(*parts[2:]).as_posix()}"
        )
    return root / relative_path


def published_media_path(repo_root: Path, request_path: str) -> tuple[Path, str]:
    if not request_path.startswith(PUBLISHED_MEDIA_PREFIX):
        raise ValueError("Invalid published Docs media route")
    parts = request_path.removeprefix(PUBLISHED_MEDIA_PREFIX).split("/")
    if len(parts) < 3:
        raise ValueError("Published Docs media route requires scope, type, and identity")
    scope, media_type, *identity_parts = parts
    identity = Path(*identity_parts)
    if (
        not scope
        or not media_type
        or identity.is_absolute()
        or any(part in {"", ".", ".."} for part in identity.parts)
    ):
        raise ValueError("Invalid published Docs media identity")
    config = load_docs_scope_configs(repo_root, scope_ids=(scope,)).get(scope)
    if config is None or media_type not in config.media.types:
        raise FileNotFoundError(f"Published Docs media type not found: {scope}/{media_type}")
    relative_path = Path("media") / media_type / identity
    _manifest, root, files = validate_published_snapshot(repo_root, scope)
    if relative_path not in files:
        raise FileNotFoundError(
            f"Published Docs media not found: {scope}/{media_type}/{identity.as_posix()}"
        )
    return root / relative_path, media_type


__all__ = [
    "EXTERNAL_SUB_SCOPE_PUBLISHED_PREFIX",
    "PUBLISHED_MEDIA_PREFIX",
    "external_sub_scope_payload_path",
    "read_published_backlinks",
    "read_published_doc_payload",
    "read_published_docs_index_tree",
    "read_published_recent",
    "read_published_search_index",
    "read_published_semantic_tokens_index",
    "published_media_path",
]
