#!/usr/bin/env python3
"""Shared Docs Viewer scope configuration."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


CONFIG_REL_PATH = Path("docs-viewer/config/scopes/docs_scopes.json")
SCHEMA_VERSION = "docs_scopes_v1"
DOCS_VIEWER_MANAGE_ROUTE_BASE_URL = "/docs/"
PUBLIC_DOCS_OUTPUT_ROOT = Path("site/assets/data/docs/scopes")
PUBLIC_SEARCH_OUTPUT_ROOT = Path("site/assets/data/search")
WORKING_DOCS_OUTPUT_ROOT = Path("docs-viewer/generated/docs")
WORKING_SEARCH_OUTPUT_ROOT = Path("docs-viewer/generated/search")


@dataclass(frozen=True)
class DocsImportMediaConfig:
    storage_mode: str
    media_path_prefix: Path
    repo_assets_path_prefix: Path
    repo_assets_public_path_prefix: str


@dataclass(frozen=True)
class DocsScopeConfig:
    scope_id: str
    scope_type: str
    source: Path
    media_path_prefix: Path
    output: Path
    search_output: Path
    publish_output: Path
    publish_search_output: Path
    viewer_base_url: str
    include_scope_param: bool
    default_doc_id: str
    allow_nested_source: bool
    non_loadable_doc_ids: tuple[str, ...]
    manage_only_tree_root_ids: tuple[str, ...]
    show_updated_date: bool
    allow_unresolved_parent_ids: bool
    import_media_storage: DocsImportMediaConfig


SUPPORTED_IMPORT_MEDIA_STORAGE_MODES = {"repo_assets", "staging_manual", "r2_upload"}


def default_repo_root() -> Path:
    current = Path(__file__).resolve()
    for candidate in [current.parent, *current.parents]:
        if (candidate / "site-tools" / "config" / "site-tools.json").exists():
            return candidate
    raise ValueError("could not resolve repo root")


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


def path_is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def is_public_readonly_scope(*, viewer_base_url: str, include_scope_param: bool) -> bool:
    return not include_scope_param and normalize_viewer_base_url(viewer_base_url) != DOCS_VIEWER_MANAGE_ROUTE_BASE_URL


def validate_generated_output_contract(
    *,
    scope_id: str,
    output: Path,
    search_output: Path,
    viewer_base_url: str,
    include_scope_param: bool,
    field_prefix: str,
) -> None:
    if is_public_readonly_scope(viewer_base_url=viewer_base_url, include_scope_param=include_scope_param):
        if path_is_relative_to(output, PUBLIC_DOCS_OUTPUT_ROOT):
            raise ValueError(
                f"docs scope config {field_prefix}.output for public scope {scope_id!r} "
                "must be working generated output under docs-viewer/generated/docs"
            )
        if path_is_relative_to(search_output, PUBLIC_SEARCH_OUTPUT_ROOT):
            raise ValueError(
                f"docs scope config {field_prefix}.search_output for public scope {scope_id!r} "
                "must be working generated output under docs-viewer/generated/search"
            )
        return
    if path_is_relative_to(output, PUBLIC_DOCS_OUTPUT_ROOT):
        raise ValueError(
            f"docs scope config {field_prefix}.output for manage-mode scope {scope_id!r} "
            "must not be under site/assets/data/docs/scopes"
        )
    if path_is_relative_to(search_output, PUBLIC_SEARCH_OUTPUT_ROOT):
        raise ValueError(
            f"docs scope config {field_prefix}.search_output for manage-mode scope {scope_id!r} "
            "must not be under site/assets/data/search"
        )


def normalize_doc_id(value: Any, *, field: str) -> str:
    text = str(value or "").strip()
    return text


def normalize_public_path_prefix(value: Any, *, fallback: str, field: str) -> str:
    text = str(value or "").strip() or fallback
    if not text.startswith("/"):
        text = f"/{text}"
    if ".." in Path(text.lstrip("/")).parts:
        raise ValueError(f"docs scope config field {field} must not contain parent path segments")
    return text.rstrip("/")


def public_url_fallback_for_repo_assets_path(path: Path) -> str:
    parts = path.parts
    if len(parts) >= 2 and parts[0] == "site" and parts[1] == "assets":
        return "/" + Path(*parts[1:]).as_posix()
    return f"/{path.as_posix().strip('/')}"


def normalize_import_media_storage(
    item: dict[str, Any],
    *,
    scope_id: str,
    media_path_prefix: Path,
    index: int,
) -> DocsImportMediaConfig:
    raw = item.get("import_media_storage")
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise ValueError(f"docs scope config scopes[{index}].import_media_storage must be an object")

    storage_mode = str(raw.get("storage_mode") or "staging_manual").strip()
    if storage_mode not in SUPPORTED_IMPORT_MEDIA_STORAGE_MODES:
        supported = ", ".join(sorted(SUPPORTED_IMPORT_MEDIA_STORAGE_MODES))
        raise ValueError(
            f"docs scope config scopes[{index}].import_media_storage.storage_mode "
            f"must be one of: {supported}"
        )
    repo_assets_path_prefix = safe_relative_path(
        raw.get("repo_assets_path_prefix") or f"site/assets/docs/{scope_id}",
        field=f"scopes[{index}].import_media_storage.repo_assets_path_prefix",
    )
    public_path_prefix = normalize_public_path_prefix(
        raw.get("repo_assets_public_path_prefix"),
        fallback=public_url_fallback_for_repo_assets_path(repo_assets_path_prefix),
        field=f"scopes[{index}].import_media_storage.repo_assets_public_path_prefix",
    )
    return DocsImportMediaConfig(
        storage_mode=storage_mode,
        media_path_prefix=media_path_prefix,
        repo_assets_path_prefix=repo_assets_path_prefix,
        repo_assets_public_path_prefix=public_path_prefix,
    )


def publish_output_paths_for(
    item: dict[str, Any],
    *,
    scope_id: str,
    public_readonly: bool,
    index: int,
) -> tuple[Path, Path]:
    if public_readonly:
        publish_output = safe_relative_path(
            item.get("publish_output"),
            field=f"scopes[{index}].publish_output",
        )
        publish_search_output = safe_relative_path(
            item.get("publish_search_output"),
            field=f"scopes[{index}].publish_search_output",
        )
        expected_docs_parent = PUBLIC_DOCS_OUTPUT_ROOT
        expected_search_parent = PUBLIC_SEARCH_OUTPUT_ROOT / scope_id
        if not path_is_relative_to(publish_output, expected_docs_parent):
            raise ValueError(
                f"docs scope config scopes[{index}].publish_output for public scope {scope_id!r} "
                "must be under site/assets/data/docs/scopes"
            )
        if not path_is_relative_to(publish_search_output, expected_search_parent):
            raise ValueError(
                f"docs scope config scopes[{index}].publish_search_output for public scope {scope_id!r} "
                f"must be under {expected_search_parent.as_posix()}"
            )
        return publish_output, publish_search_output
    return (
        safe_relative_path(item.get("output"), field=f"scopes[{index}].output"),
        safe_relative_path(item.get("search_output"), field=f"scopes[{index}].search_output"),
    )


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
        media_path_prefix = safe_relative_path(
            item.get("media_path_prefix") or f"docs/{scope_id}",
            field=f"scopes[{index}].media_path_prefix",
        )
        output = safe_relative_path(item.get("output"), field=f"scopes[{index}].output")
        search_output = safe_relative_path(
            item.get("search_output"),
            field=f"scopes[{index}].search_output",
        )
        viewer_base_url = normalize_viewer_base_url(item.get("viewer_base_url"))
        include_scope_param = item.get("include_scope_param") is True
        public_readonly = is_public_readonly_scope(
            viewer_base_url=viewer_base_url,
            include_scope_param=include_scope_param,
        )
        validate_generated_output_contract(
            scope_id=scope_id,
            output=output,
            search_output=search_output,
            viewer_base_url=viewer_base_url,
            include_scope_param=include_scope_param,
            field_prefix=f"scopes[{index}]",
        )
        publish_output, publish_search_output = publish_output_paths_for(
            item,
            scope_id=scope_id,
            public_readonly=public_readonly,
            index=index,
        )
        configs[scope_id] = DocsScopeConfig(
            scope_id=scope_id,
            scope_type=str(item.get("scope_type") or "").strip().lower(),
            source=safe_relative_path(item.get("source"), field=f"scopes[{index}].source"),
            media_path_prefix=media_path_prefix,
            output=output,
            search_output=search_output,
            publish_output=publish_output,
            publish_search_output=publish_search_output,
            viewer_base_url=viewer_base_url,
            include_scope_param=include_scope_param,
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
            import_media_storage=normalize_import_media_storage(
                item,
                scope_id=scope_id,
                media_path_prefix=media_path_prefix,
                index=index,
            ),
        )
    return configs


DOCS_SCOPE_CONFIGS = load_docs_scope_configs()
SCOPE_ROOTS = {scope: config.source for scope, config in DOCS_SCOPE_CONFIGS.items()}
MEDIA_PATH_PREFIXES = {
    scope: config.media_path_prefix for scope, config in DOCS_SCOPE_CONFIGS.items()
}
IMPORT_MEDIA_CONFIGS = {
    scope: config.import_media_storage for scope, config in DOCS_SCOPE_CONFIGS.items()
}
NESTED_SOURCE_SCOPES = {
    scope for scope, config in DOCS_SCOPE_CONFIGS.items() if config.allow_nested_source
}
