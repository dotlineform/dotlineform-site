#!/usr/bin/env python3
"""Read helpers for generated Docs Viewer JSON artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlparse

from docs_document_identity import is_immutable_doc_id
from docs_scope_config import (
    DocsScopeConfig,
    generated_documents_path,
    generated_search_path,
    load_docs_scope_stage,
    publication_documents_path,
    resolve_scope_path,
    scope_uses_external_data,
)


EXTERNAL_SUB_SCOPE_GENERATED_PREFIX = "/docs/generated/external/"


def browser_path_for_repo_relative(path: Path) -> str:
    rel = Path(path.as_posix().lstrip("/"))
    if len(rel.parts) >= 2 and rel.parts[0] == "site":
        rel = Path(*rel.parts[1:])
    return rel.as_posix().lstrip("/")


def generated_scope_config(repo_root: Path, scope: str, stage: str | None = None) -> DocsScopeConfig:
    return load_docs_scope_stage(repo_root, scope, stage)


def generated_docs_output_root(repo_root: Path, scope: str, stage: str | None = None) -> Path:
    config = generated_scope_config(repo_root, scope, stage)
    return resolve_scope_path(repo_root, generated_documents_path(config))


def external_sub_scope_payload_path(repo_root: Path, request_path: str, stage: str | None = None) -> Path:
    if not request_path.startswith(EXTERNAL_SUB_SCOPE_GENERATED_PREFIX):
        raise ValueError("Invalid external Docs sub-scope payload route")
    parts = request_path.removeprefix(EXTERNAL_SUB_SCOPE_GENERATED_PREFIX).split("/")
    if len(parts) > 1 and parts[1] in {"working", "pre-publish"}:
        route_stage = parts.pop(1)
        if stage is not None and stage != route_stage:
            raise ValueError("Conflicting generated stage target")
        stage = route_stage
    if len(parts) == 3 and parts[2] in {
        "manifest.json",
        "manage-manifest.json",
        "subject-associations.json",
    }:
        scope, sub_scope, filename = parts
        relative_path = Path(filename)
    elif len(parts) == 4 and parts[2] == "by-id" and parts[3].endswith(".json"):
        scope, sub_scope, _, filename = parts
        doc_id = filename.removesuffix(".json")
        if not is_immutable_doc_id(doc_id):
            raise ValueError("External Docs sub-scope payload doc_id must use immutable identity")
        relative_path = Path("by-id") / filename
    else:
        raise ValueError("Invalid external Docs sub-scope payload route")

    config = load_docs_scope_stage(repo_root, scope, stage)
    if config is None or not scope_uses_external_data(config):
        raise FileNotFoundError(f"External Docs scope not found: {scope!r}")
    selected = next((item for item in config.sub_scopes if item.sub_scope == sub_scope), None)
    if selected is None:
        raise FileNotFoundError(f"Docs sub-scope not found: {scope}/{sub_scope}")

    output_root = resolve_scope_path(repo_root, generated_documents_path(selected)).resolve()
    path = (output_root / relative_path).resolve()
    try:
        path.relative_to(output_root)
    except ValueError as exc:
        raise ValueError("External Docs sub-scope payload must remain under its configured output") from exc
    if not path.is_file():
        raise FileNotFoundError(f"External Docs sub-scope payload not found: {scope}/{sub_scope}/{relative_path}")
    return path


def generated_docs_index_tree_path(repo_root: Path, scope: str, stage: str | None = None) -> Path:
    return generated_docs_output_root(repo_root, scope, stage) / "index-tree.json"


def generated_recent_path(repo_root: Path, scope: str, stage: str | None = None) -> Path:
    return generated_docs_output_root(repo_root, scope, stage) / "recent.json"


def generated_backlinks_path(repo_root: Path, scope: str, stage: str | None = None) -> Path:
    return generated_docs_output_root(repo_root, scope, stage) / "backlinks.json"


def generated_semantic_tokens_index_path(repo_root: Path, scope: str, stage: str | None = None) -> Path:
    return generated_docs_output_root(repo_root, scope, stage) / "semantic-tokens" / "index.json"


def generated_doc_payload_path(repo_root: Path, scope: str, doc_id: str, stage: str | None = None) -> Path:
    if not is_immutable_doc_id(doc_id):
        raise ValueError("doc_id must use the immutable document ID format")
    return generated_docs_output_root(repo_root, scope, stage) / "by-id" / f"{doc_id}.json"


def generated_search_index_path(repo_root: Path, scope: str, stage: str | None = None) -> Path:
    config = generated_scope_config(repo_root, scope, stage)
    return resolve_scope_path(repo_root, generated_search_path(config))


def read_generated_doc_links(
    repo_root: Path, scope: str, doc_id: str, sub_scope: str = "", stage: str | None = None,
) -> Dict[str, Any]:
    """Read one configured relationship file and require its exact requested identity.

    This read does not build, repair, or search another collection or stage.
    """
    if not is_immutable_doc_id(doc_id):
        raise ValueError("doc_id must use the immutable document ID format")
    config = generated_scope_config(repo_root, scope, stage)
    if sub_scope and sub_scope not in {child.sub_scope for child in config.sub_scopes}:
        raise ValueError("Links sub_scope must be an exact configured collection")
    output = resolve_scope_path(repo_root, generated_documents_path(config)).resolve()
    directory = output / "links-by-id"
    path = directory / f"{doc_id}.json"
    if directory.is_symlink() or path.is_symlink() or path.resolve().parent != directory.resolve():
        raise ValueError("Links data must remain in its configured directory")
    payload = read_generated_json(path, "generated document Links")
    expected = {"scope": scope, "sub_scope": sub_scope, "doc_id": doc_id}
    summary = payload.get("self") if isinstance(payload, dict) else None
    if not isinstance(summary, dict) or summary.get("target") != expected:
        raise ValueError("Links data does not match the requested document")
    return payload


def read_generated_json(path: Path, label: str) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"{label} not found: {path.name}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{label} is not valid JSON: {path.name}") from exc


def generated_scope_data_available(repo_root: Path, scope: str, stage: str | None = None) -> bool:
    return generated_docs_index_tree_path(repo_root, scope, stage).exists()


def generated_search_data_available(repo_root: Path, scope: str, stage: str | None = None) -> bool:
    return generated_search_index_path(repo_root, scope, stage).exists()


def read_generated_docs_index_tree(repo_root: Path, scope: str, stage: str | None = None) -> Dict[str, Any]:
    return read_generated_json(
        generated_docs_index_tree_path(repo_root, scope, stage),
        f"generated docs index tree for {scope}",
    )


def read_generated_recent(repo_root: Path, scope: str, stage: str | None = None) -> Dict[str, Any]:
    return read_generated_json(
        generated_recent_path(repo_root, scope, stage),
        f"generated Recent docs for {scope}",
    )


def read_generated_backlinks(repo_root: Path, scope: str, stage: str | None = None) -> Dict[str, Any]:
    return read_generated_json(
        generated_backlinks_path(repo_root, scope, stage),
        f"generated backlinks for {scope}",
    )


def read_generated_semantic_tokens_index(repo_root: Path, scope: str, stage: str | None = None) -> Dict[str, Any]:
    return read_generated_json(
        generated_semantic_tokens_index_path(repo_root, scope, stage),
        f"generated semantic-token usage index for {scope}",
    )


def read_generated_search_index(repo_root: Path, scope: str, stage: str | None = None) -> Dict[str, Any]:
    return read_generated_json(
        generated_search_index_path(repo_root, scope, stage),
        f"generated search index for {scope}",
    )


def read_generated_doc_payload(repo_root: Path, scope: str, doc_id: str, stage: str | None = None) -> Dict[str, Any]:
    if not is_immutable_doc_id(doc_id):
        raise ValueError("doc_id must use the immutable document ID format")

    index_payload = read_generated_docs_index_tree(repo_root, scope, stage)
    docs = index_payload.get("docs")
    if not isinstance(docs, list):
        raise RuntimeError(f"generated docs index tree for {scope} is missing docs")

    record = find_generated_doc_record(docs, doc_id)
    if record is None:
        raise FileNotFoundError(f"generated doc payload for {doc_id} not found")

    config = generated_scope_config(repo_root, scope, stage)
    expected_paths = {"docs/doc"}
    if not scope_uses_external_data(config):
        expected_paths.update(
            {
                browser_path_for_repo_relative(generated_documents_path(config) / "by-id" / f"{doc_id}.json"),
                browser_path_for_repo_relative(publication_documents_path(config) / "by-id" / f"{doc_id}.json"),
            }
        )
    content_url = str(record.get("content_url") or "").strip()
    content_path = urlparse(content_url).path.lstrip("/") if content_url else ""
    if content_path and content_path not in expected_paths:
        raise RuntimeError(f"generated docs index tree for {scope} has an unexpected payload path for {doc_id}")

    return read_generated_json(
        generated_doc_payload_path(repo_root, scope, doc_id, stage),
        f"generated doc payload for {doc_id}",
    )


def find_generated_doc_record(docs: list[Any], doc_id: str) -> Dict[str, Any] | None:
    stack = [doc for doc in docs if isinstance(doc, dict)]
    while stack:
        record = stack.pop(0)
        if record.get("doc_id") == doc_id:
            return record
        children = record.get("children")
        if isinstance(children, list):
            stack.extend(child for child in children if isinstance(child, dict))
    return None
