#!/usr/bin/env python3
"""Shared Docs Viewer scope configuration."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


CONFIG_REL_PATH = Path("scripts/docs/docs_scopes.json")
SCHEMA_VERSION = "docs_scopes_v1"


@dataclass(frozen=True)
class DocsScopeConfig:
    scope_id: str
    source: Path
    output: Path
    viewer_base_url: str
    include_scope_param: bool
    default_doc_id: str
    allow_nested_source: bool
    non_loadable_doc_ids: tuple[str, ...]
    manage_only_tree_root_ids: tuple[str, ...]
    show_updated_date: bool
    allow_unresolved_parent_ids: bool


def default_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def safe_relative_path(value: Any, *, field: str) -> Path:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"docs scope config field {field} is required")
    path = Path(text)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"docs scope config field {field} must be a safe relative path")
    return path


def string_tuple(value: Any, *, field: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError(f"docs scope config field {field} must be an array")
    return tuple(str(item).strip() for item in value if str(item).strip())


def normalize_viewer_base_url(value: Any) -> str:
    text = str(value or "").strip() or "/docs/"
    if not text.startswith("/"):
        text = f"/{text}"
    return text if text.endswith("/") else f"{text}/"


def normalize_doc_id(value: Any, *, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"docs scope config field {field} is required")
    return text


def load_docs_scope_configs(repo_root: Path | None = None) -> dict[str, DocsScopeConfig]:
    root = repo_root or default_repo_root()
    config_path = root / CONFIG_REL_PATH
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"docs scope config is invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("docs scope config must be a JSON object")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"docs scope config schema_version must be {SCHEMA_VERSION}")
    raw_scopes = payload.get("scopes")
    if not isinstance(raw_scopes, list):
        raise ValueError("docs scope config scopes must be an array")

    configs: dict[str, DocsScopeConfig] = {}
    for index, item in enumerate(raw_scopes):
        if not isinstance(item, dict):
            raise ValueError(f"docs scope config scopes[{index}] must be an object")
        scope_id = str(item.get("scope_id") or "").strip().lower()
        if not scope_id:
            raise ValueError(f"docs scope config scopes[{index}].scope_id is required")
        if scope_id in configs:
            raise ValueError(f"docs scope config scope_id {scope_id!r} is duplicated")
        configs[scope_id] = DocsScopeConfig(
            scope_id=scope_id,
            source=safe_relative_path(item.get("source"), field=f"scopes[{index}].source"),
            output=safe_relative_path(item.get("output"), field=f"scopes[{index}].output"),
            viewer_base_url=normalize_viewer_base_url(item.get("viewer_base_url")),
            include_scope_param=item.get("include_scope_param") is True,
            default_doc_id=normalize_doc_id(
                item.get("default_doc_id"),
                field=f"scopes[{index}].default_doc_id",
            ),
            allow_nested_source=item.get("allow_nested_source") is True,
            non_loadable_doc_ids=string_tuple(
                item.get("non_loadable_doc_ids"),
                field=f"scopes[{index}].non_loadable_doc_ids",
            ),
            manage_only_tree_root_ids=string_tuple(
                item.get("manage_only_tree_root_ids"),
                field=f"scopes[{index}].manage_only_tree_root_ids",
            ),
            show_updated_date=item.get("show_updated_date") is not False,
            allow_unresolved_parent_ids=item.get("allow_unresolved_parent_ids") is True,
        )
    return configs


DOCS_SCOPE_CONFIGS = load_docs_scope_configs()
SCOPE_ROOTS = {scope: config.source for scope, config in DOCS_SCOPE_CONFIGS.items()}
NESTED_SOURCE_SCOPES = {
    scope for scope, config in DOCS_SCOPE_CONFIGS.items() if config.allow_nested_source
}
