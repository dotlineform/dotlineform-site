#!/usr/bin/env python3
"""Read helpers for generated Docs Viewer JSON artifacts."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlparse

from docs_scope_config import DocsScopeConfig, load_docs_scope_configs, resolve_scope_path, scope_uses_external_data


SAFE_DOC_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
SAFE_REF_KIND_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
SAFE_REF_TARGET_SLUG_PATTERN = re.compile(r"^[A-Za-z0-9_.%+-]+$")


def browser_path_for_repo_relative(path: Path) -> str:
    rel = Path(path.as_posix().lstrip("/"))
    if len(rel.parts) >= 2 and rel.parts[0] == "site":
        rel = Path(*rel.parts[1:])
    return rel.as_posix().lstrip("/")


def generated_scope_config(repo_root: Path, scope: str) -> DocsScopeConfig:
    config = load_docs_scope_configs(repo_root).get(scope)
    if config is None:
        raise ValueError(f"unsupported docs scope: {scope}")
    return config


def generated_docs_output_root(repo_root: Path, scope: str) -> Path:
    config = generated_scope_config(repo_root, scope)
    return resolve_scope_path(repo_root, config.output)


def generated_docs_index_tree_path(repo_root: Path, scope: str) -> Path:
    return generated_docs_output_root(repo_root, scope) / "index-tree.json"


def generated_recently_added_path(repo_root: Path, scope: str) -> Path:
    return generated_docs_output_root(repo_root, scope) / "recently-added.json"


def generated_doc_payload_path(repo_root: Path, scope: str, doc_id: str) -> Path:
    if not SAFE_DOC_ID_PATTERN.match(doc_id):
        raise ValueError("doc_id contains unsupported characters")
    return generated_docs_output_root(repo_root, scope) / "by-id" / f"{doc_id}.json"


def generated_search_index_path(repo_root: Path, scope: str) -> Path:
    config = generated_scope_config(repo_root, scope)
    return resolve_scope_path(repo_root, config.search_output)


def generated_references_index_path(repo_root: Path, scope: str) -> Path:
    return generated_docs_output_root(repo_root, scope) / "references" / "index.json"


def generated_reference_target_path(repo_root: Path, scope: str, target_kind: str, target_slug: str) -> Path:
    if not SAFE_REF_KIND_PATTERN.match(target_kind):
        raise ValueError("target_kind contains unsupported characters")
    if not SAFE_REF_TARGET_SLUG_PATTERN.match(target_slug):
        raise ValueError("target_slug contains unsupported characters")
    return generated_docs_output_root(repo_root, scope) / "references" / "by-target" / target_kind / f"{target_slug}.json"


def read_generated_json(path: Path, label: str) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"{label} not found: {path.name}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{label} is not valid JSON: {path.name}") from exc


def generated_scope_data_available(repo_root: Path, scope: str) -> bool:
    return generated_docs_index_tree_path(repo_root, scope).exists()


def generated_search_data_available(repo_root: Path, scope: str) -> bool:
    return generated_search_index_path(repo_root, scope).exists()


def read_generated_docs_index_tree(repo_root: Path, scope: str) -> Dict[str, Any]:
    return read_generated_json(
        generated_docs_index_tree_path(repo_root, scope),
        f"generated docs index tree for {scope}",
    )


def read_generated_recently_added(repo_root: Path, scope: str) -> Dict[str, Any]:
    return read_generated_json(
        generated_recently_added_path(repo_root, scope),
        f"generated recently added docs for {scope}",
    )


def read_generated_search_index(repo_root: Path, scope: str) -> Dict[str, Any]:
    return read_generated_json(
        generated_search_index_path(repo_root, scope),
        f"generated search index for {scope}",
    )


def read_generated_references_index(repo_root: Path, scope: str) -> Dict[str, Any]:
    return read_generated_json(
        generated_references_index_path(repo_root, scope),
        f"generated references index for {scope}",
    )


def read_generated_reference_target(repo_root: Path, scope: str, target_kind: str, target_slug: str) -> Dict[str, Any]:
    return read_generated_json(
        generated_reference_target_path(repo_root, scope, target_kind, target_slug),
        f"generated reference target for {scope}",
    )


def read_generated_doc_payload(repo_root: Path, scope: str, doc_id: str) -> Dict[str, Any]:
    if not SAFE_DOC_ID_PATTERN.match(doc_id):
        raise ValueError("doc_id contains unsupported characters")

    index_payload = read_generated_docs_index_tree(repo_root, scope)
    docs = index_payload.get("docs")
    if not isinstance(docs, list):
        raise RuntimeError(f"generated docs index tree for {scope} is missing docs")

    record = find_generated_doc_record(docs, doc_id)
    if record is None:
        raise FileNotFoundError(f"generated doc payload for {doc_id} not found")

    config = generated_scope_config(repo_root, scope)
    expected_paths = {f"docs/generated/payload"}
    if not scope_uses_external_data(config):
        expected_paths.update(
            {
                browser_path_for_repo_relative(config.output / "by-id" / f"{doc_id}.json"),
                browser_path_for_repo_relative(config.publish_output / "by-id" / f"{doc_id}.json"),
            }
        )
    content_url = str(record.get("content_url") or "").strip()
    content_path = urlparse(content_url).path.lstrip("/") if content_url else ""
    if content_path and content_path not in expected_paths:
        raise RuntimeError(f"generated docs index tree for {scope} has an unexpected payload path for {doc_id}")

    return read_generated_json(
        generated_doc_payload_path(repo_root, scope, doc_id),
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
