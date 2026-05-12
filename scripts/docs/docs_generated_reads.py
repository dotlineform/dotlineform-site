#!/usr/bin/env python3
"""Read helpers for generated Docs Viewer JSON artifacts."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlparse

from docs_scope_config import DOCS_SCOPE_CONFIGS


SAFE_DOC_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def generated_docs_output_root(repo_root: Path, scope: str) -> Path:
    config = DOCS_SCOPE_CONFIGS.get(scope)
    if config is None:
        raise ValueError(f"unsupported docs scope: {scope}")
    return repo_root / config.output


def generated_docs_index_path(repo_root: Path, scope: str) -> Path:
    return generated_docs_output_root(repo_root, scope) / "index.json"


def generated_doc_payload_path(repo_root: Path, scope: str, doc_id: str) -> Path:
    if not SAFE_DOC_ID_PATTERN.match(doc_id):
        raise ValueError("doc_id contains unsupported characters")
    return generated_docs_output_root(repo_root, scope) / "by-id" / f"{doc_id}.json"


def generated_search_index_path(repo_root: Path, scope: str) -> Path:
    return repo_root / "assets" / "data" / "search" / scope / "index.json"


def read_generated_json(path: Path, label: str) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"{label} not found: {path.name}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{label} is not valid JSON: {path.name}") from exc


def generated_scope_data_available(repo_root: Path, scope: str) -> bool:
    return generated_docs_index_path(repo_root, scope).exists()


def generated_search_data_available(repo_root: Path, scope: str) -> bool:
    return generated_search_index_path(repo_root, scope).exists()


def read_generated_docs_index(repo_root: Path, scope: str) -> Dict[str, Any]:
    return read_generated_json(
        generated_docs_index_path(repo_root, scope),
        f"generated docs index for {scope}",
    )


def read_generated_search_index(repo_root: Path, scope: str) -> Dict[str, Any]:
    return read_generated_json(
        generated_search_index_path(repo_root, scope),
        f"generated search index for {scope}",
    )


def read_generated_doc_payload(repo_root: Path, scope: str, doc_id: str) -> Dict[str, Any]:
    if not SAFE_DOC_ID_PATTERN.match(doc_id):
        raise ValueError("doc_id contains unsupported characters")

    index_payload = read_generated_docs_index(repo_root, scope)
    docs = index_payload.get("docs")
    if not isinstance(docs, list):
        raise RuntimeError(f"generated docs index for {scope} is missing docs")

    record = next((doc for doc in docs if isinstance(doc, dict) and doc.get("doc_id") == doc_id), None)
    if record is None:
        raise FileNotFoundError(f"generated doc payload for {doc_id} not found")

    expected_path = (DOCS_SCOPE_CONFIGS[scope].output / "by-id" / f"{doc_id}.json").as_posix()
    expected_url = f"/{expected_path}"
    content_url = str(record.get("content_url") or "").strip()
    if content_url and urlparse(content_url).path != expected_url:
        raise RuntimeError(f"generated docs index for {scope} has an unexpected payload path for {doc_id}")

    return read_generated_json(
        generated_doc_payload_path(repo_root, scope, doc_id),
        f"generated doc payload for {doc_id}",
    )
