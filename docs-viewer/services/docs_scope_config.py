#!/usr/bin/env python3
"""Shared Docs Viewer scope configuration."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import sys
from typing import Any


_BOOTSTRAP_START = Path(__file__).resolve()
for _candidate in (_BOOTSTRAP_START.parent, *_BOOTSTRAP_START.parents):
    if (_candidate / "site-tools" / "config" / "site-tools.json").exists():
        if str(_candidate) not in sys.path:
            sys.path.insert(0, str(_candidate))
        break

from studio.shared.python.external_workspace_paths import (  # noqa: E402
    ExternalWorkspaceRoot,
    resolve_external_workspace_root,
    resolve_workspace_path,
)


CONFIG_REL_PATH = Path("docs-viewer/config/scopes/docs_scopes.json")
SCHEMA_VERSION = "docs_scopes_v1"
DOCS_VIEWER_MANAGE_ROUTE_BASE_URL = "/docs/"
PUBLIC_DOCS_OUTPUT_ROOT = Path("site/assets/data/docs/scopes")
PUBLIC_SEARCH_OUTPUT_ROOT = Path("site/assets/data/search")
WORKING_DOCS_OUTPUT_ROOT = Path("docs-viewer/generated/docs")
WORKING_SEARCH_OUTPUT_ROOT = Path("docs-viewer/generated/search")
LOCAL_EXTERNAL_SCOPE_TYPE = "local_external"
DOTLINEFORM_PROJECTS_BASE_DIR_ENV = "DOTLINEFORM_PROJECTS_BASE_DIR"
EXTERNAL_DATA_ROOT_MARKER = f"${DOTLINEFORM_PROJECTS_BASE_DIR_ENV}/docs-viewer"


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
    non_loadable_doc_ids: tuple[str, ...]
    manage_only_tree_root_ids: tuple[str, ...]
    allow_unresolved_parent_ids: bool
    import_media_storage: DocsImportMediaConfig
    sub_scopes: tuple["DocsSubScopeConfig", ...]


@dataclass(frozen=True)
class DocsSubScopeConfig:
    sub_scope: str
    title: str
    source: Path
    output: Path
    publish_output: Path


SUPPORTED_IMPORT_MEDIA_STORAGE_MODES = {
    "external_assets",
    "repo_assets",
    "r2_upload",
    "staging_manual",
}
SUB_SCOPE_ID_PATTERN = re.compile(r"\A[a-z0-9][a-z0-9_-]*\Z")


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


def safe_scope_data_path(value: Any, *, field: str, allow_external: bool = False) -> Path:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"docs scope config field {field} is required")
    if allow_external and (text == EXTERNAL_DATA_ROOT_MARKER or text.startswith(f"{EXTERNAL_DATA_ROOT_MARKER}/")):
        return resolve_external_data_marker_path(text, field=field)
    path = Path(text)
    if path.is_absolute():
        if not allow_external:
            raise ValueError(f"docs scope config field {field} must be a safe relative path")
        if ".." in path.parts:
            raise ValueError(f"docs scope config field {field} must not contain parent path segments")
        if path.parent == path:
            raise ValueError(f"docs scope config field {field} must not be the filesystem root")
        return path
    if ".." in path.parts:
        raise ValueError(f"docs scope config field {field} must be a safe relative path")
    return path


def resolve_external_data_workspace() -> ExternalWorkspaceRoot:
    try:
        return resolve_external_workspace_root("docs-viewer", require_exists=True)
    except ValueError as exc:
        message = str(exc)
        if f"{DOTLINEFORM_PROJECTS_BASE_DIR_ENV} is required" in message:
            raise ValueError(
                f"{DOTLINEFORM_PROJECTS_BASE_DIR_ENV} is required for external local Docs Viewer scopes"
            ) from exc
        if "external workspace does not exist" in message or "does not exist or is not a directory" in message:
            raise ValueError(f"external_data_root does not exist: {EXTERNAL_DATA_ROOT_MARKER}") from exc
        if "external workspace must be a directory" in message:
            raise ValueError(f"external_data_root must be a directory: {EXTERNAL_DATA_ROOT_MARKER}") from exc
        if "external workspace must be readable and writable" in message:
            raise ValueError(f"external_data_root must be readable and writable: {EXTERNAL_DATA_ROOT_MARKER}") from exc
        raise


def resolve_external_data_root() -> Path:
    return resolve_external_data_workspace().root


def resolve_external_data_marker_path(value: Any, *, field: str) -> Path:
    text = str(value or "").strip()
    if text == EXTERNAL_DATA_ROOT_MARKER:
        return resolve_external_data_workspace().root
    prefix = f"{EXTERNAL_DATA_ROOT_MARKER}/"
    if not text.startswith(prefix):
        raise ValueError(f"docs scope config field {field} must be under {EXTERNAL_DATA_ROOT_MARKER}")
    relative_text = text[len(prefix):]
    relative_path = Path(relative_text)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError(f"docs scope config field {field} must be under {EXTERNAL_DATA_ROOT_MARKER}")
    workspace = resolve_external_data_workspace()
    try:
        return resolve_workspace_path(workspace, relative_path)
    except ValueError as exc:
        raise ValueError(f"docs scope config field {field} must be under {EXTERNAL_DATA_ROOT_MARKER}") from exc


def resolve_scope_path(repo_root: Path, path: Path) -> Path:
    return path.resolve() if path.is_absolute() else repo_root / path


def path_label(repo_root: Path, path: Path) -> str:
    if not path.is_absolute():
        return path.as_posix()
    resolved_root = repo_root.resolve()
    resolved_path = resolve_scope_path(repo_root, path)
    try:
        return resolved_path.relative_to(resolved_root).as_posix()
    except ValueError:
        return resolved_path.as_posix()


def scope_uses_external_data(config: "DocsScopeConfig") -> bool:
    return config.scope_type == LOCAL_EXTERNAL_SCOPE_TYPE or any(
        path.is_absolute() for path in (config.source, config.output, config.search_output)
    )


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


def path_is_strict_relative_to(path: Path, parent: Path) -> bool:
    return path != parent and path_is_relative_to(path, parent)


def normalize_sub_scope_id(value: Any, *, field: str) -> str:
    text = str(value or "").strip().lower()
    if not text:
        raise ValueError(f"docs scope config field {field} is required")
    if not SUB_SCOPE_ID_PATTERN.fullmatch(text):
        raise ValueError(
            f"docs scope config field {field} must start with a lowercase letter or digit "
            "and contain only lowercase letters, digits, hyphens, or underscores"
        )
    return text


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
            f"docs scope config {field_prefix}.output for local scope {scope_id!r} "
            "must not be under site/assets/data/docs/scopes"
        )
    if path_is_relative_to(search_output, PUBLIC_SEARCH_OUTPUT_ROOT):
        raise ValueError(
            f"docs scope config {field_prefix}.search_output for local scope {scope_id!r} "
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
    scope_type: str,
    media_path_prefix: Path,
    public_readonly: bool,
    index: int,
) -> DocsImportMediaConfig:
    raw = item.get("import_media_storage")
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise ValueError(f"docs scope config scopes[{index}].import_media_storage must be an object")

    default_storage_mode = "external_assets" if scope_type == LOCAL_EXTERNAL_SCOPE_TYPE else "staging_manual"
    storage_mode = str(raw.get("storage_mode") or default_storage_mode).strip()
    if storage_mode not in SUPPORTED_IMPORT_MEDIA_STORAGE_MODES:
        supported = ", ".join(sorted(SUPPORTED_IMPORT_MEDIA_STORAGE_MODES))
        raise ValueError(
            f"docs scope config scopes[{index}].import_media_storage.storage_mode "
            f"must be one of: {supported}"
        )
    if scope_type == LOCAL_EXTERNAL_SCOPE_TYPE and storage_mode != "external_assets":
        raise ValueError(
            f"docs scope config scopes[{index}] external local scopes must use "
            "import_media_storage.storage_mode 'external_assets'"
        )
    if storage_mode == "external_assets" and scope_type != LOCAL_EXTERNAL_SCOPE_TYPE:
        raise ValueError(
            f"docs scope config scopes[{index}].import_media_storage.storage_mode "
            "'external_assets' is only valid for external local scopes"
        )
    if storage_mode == "r2_upload" and (scope_type != "public" or not public_readonly):
        raise ValueError(
            f"docs scope config scopes[{index}].import_media_storage.storage_mode "
            "'r2_upload' is only valid for public read-only scopes"
        )
    if storage_mode == "r2_upload" and media_path_prefix != Path("docs") / scope_id:
        raise ValueError(
            f"docs scope config scopes[{index}].media_path_prefix for r2_upload "
            f"must be docs/{scope_id}"
        )
    if scope_type == LOCAL_EXTERNAL_SCOPE_TYPE and (
        "repo_assets_path_prefix" in raw or "repo_assets_public_path_prefix" in raw
    ):
        raise ValueError(
            f"docs scope config scopes[{index}] external local media must not configure repo asset destinations"
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
    output: Path,
    search_output: Path,
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
    return (output, search_output)


def validate_nested_sub_scope_path(
    *,
    scope_id: str,
    sub_scope: str,
    path: Path,
    parent_path: Path,
    field: str,
    parent_field: str,
) -> None:
    if not path_is_strict_relative_to(path, parent_path):
        raise ValueError(
            f"docs scope config {field} for sub-scope {scope_id}/{sub_scope} "
            f"must be under {parent_field}"
        )


def normalize_sub_scope_configs(
    item: dict[str, Any],
    *,
    scope_id: str,
    source: Path,
    output: Path,
    publish_output: Path,
    public_readonly: bool,
    allow_external_data: bool,
    index: int,
) -> tuple[DocsSubScopeConfig, ...]:
    raw_sub_scopes = item.get("sub_scopes")
    if raw_sub_scopes is None:
        return ()
    if not isinstance(raw_sub_scopes, list):
        raise ValueError(f"docs scope config scopes[{index}].sub_scopes must be an array")

    configs: list[DocsSubScopeConfig] = []
    seen: set[str] = set()
    for sub_index, raw_sub_scope in enumerate(raw_sub_scopes):
        field_prefix = f"scopes[{index}].sub_scopes[{sub_index}]"
        if not isinstance(raw_sub_scope, dict):
            raise ValueError(f"docs scope config {field_prefix} must be an object")
        sub_scope = normalize_sub_scope_id(raw_sub_scope.get("sub_scope"), field=f"{field_prefix}.sub_scope")
        if sub_scope in seen:
            raise ValueError(f"docs scope config sub_scope {sub_scope!r} is duplicated in scope {scope_id!r}")
        seen.add(sub_scope)

        sub_source = safe_scope_data_path(
            raw_sub_scope.get("source"),
            field=f"{field_prefix}.source",
            allow_external=allow_external_data,
        )
        sub_output = safe_scope_data_path(
            raw_sub_scope.get("output"),
            field=f"{field_prefix}.output",
            allow_external=allow_external_data,
        )
        if public_readonly:
            sub_publish_output = safe_relative_path(
                raw_sub_scope.get("publish_output"),
                field=f"{field_prefix}.publish_output",
            )
        else:
            sub_publish_output = sub_output

        validate_nested_sub_scope_path(
            scope_id=scope_id,
            sub_scope=sub_scope,
            path=sub_source,
            parent_path=source,
            field=f"{field_prefix}.source",
            parent_field=f"scopes[{index}].source",
        )
        validate_nested_sub_scope_path(
            scope_id=scope_id,
            sub_scope=sub_scope,
            path=sub_output,
            parent_path=output,
            field=f"{field_prefix}.output",
            parent_field=f"scopes[{index}].output",
        )
        if public_readonly:
            validate_nested_sub_scope_path(
                scope_id=scope_id,
                sub_scope=sub_scope,
                path=sub_publish_output,
                parent_path=publish_output,
                field=f"{field_prefix}.publish_output",
                parent_field=f"scopes[{index}].publish_output",
            )

        configs.append(
            DocsSubScopeConfig(
                sub_scope=sub_scope,
                title=str(raw_sub_scope.get("title") or "").strip(),
                source=sub_source,
                output=sub_output,
                publish_output=sub_publish_output,
            )
        )
    return tuple(configs)


def configured_sub_scope_source_relpaths(config: DocsScopeConfig) -> tuple[Path, ...]:
    relpaths: list[Path] = []
    for sub_scope in config.sub_scopes:
        try:
            relpath = sub_scope.source.relative_to(config.source)
        except ValueError:
            continue
        if relpath.parts:
            relpaths.append(relpath)
    return tuple(relpaths)


def path_is_under_configured_sub_scope_source(path: Path, source_dir: Path, config: DocsScopeConfig) -> bool:
    try:
        relpath = path.relative_to(source_dir)
    except ValueError:
        return False
    return any(path_is_relative_to(relpath, sub_scope_relpath) for sub_scope_relpath in configured_sub_scope_source_relpaths(config))


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
        scope_type = str(item.get("scope_type") or "").strip().lower()
        allow_external_data = scope_type == LOCAL_EXTERNAL_SCOPE_TYPE
        if allow_external_data:
            external_data_root = str(item.get("external_data_root") or "").strip()
            if external_data_root != EXTERNAL_DATA_ROOT_MARKER:
                raise ValueError(
                    f"docs scope config scopes[{index}].external_data_root must be {EXTERNAL_DATA_ROOT_MARKER}"
                )
        media_path_prefix = safe_relative_path(
            item.get("media_path_prefix") or f"docs/{scope_id}",
            field=f"scopes[{index}].media_path_prefix",
        )
        output = safe_scope_data_path(
            item.get("output"),
            field=f"scopes[{index}].output",
            allow_external=allow_external_data,
        )
        search_output = safe_scope_data_path(
            item.get("search_output"),
            field=f"scopes[{index}].search_output",
            allow_external=allow_external_data,
        )
        viewer_base_url = normalize_viewer_base_url(item.get("viewer_base_url"))
        include_scope_param = item.get("include_scope_param") is True
        if allow_external_data and is_public_readonly_scope(
            viewer_base_url=viewer_base_url,
            include_scope_param=include_scope_param,
        ):
            raise ValueError(f"docs scope config scopes[{index}] external local scopes must use the management route")
        source = safe_scope_data_path(
            item.get("source"),
            field=f"scopes[{index}].source",
            allow_external=allow_external_data,
        )
        if allow_external_data:
            external_root = resolve_external_data_root()
            if not (
                source.is_absolute()
                and output.is_absolute()
                and search_output.is_absolute()
                and path_is_relative_to(source, external_root)
                and path_is_relative_to(output, external_root)
                and path_is_relative_to(search_output, external_root)
            ):
                raise ValueError(
                    f"docs scope config scopes[{index}] external local scopes must use paths under {EXTERNAL_DATA_ROOT_MARKER}"
                )
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
            output=output,
            search_output=search_output,
            index=index,
        )
        import_media_storage = normalize_import_media_storage(
            item,
            scope_id=scope_id,
            scope_type=scope_type,
            media_path_prefix=media_path_prefix,
            public_readonly=public_readonly,
            index=index,
        )
        sub_scopes = normalize_sub_scope_configs(
            item,
            scope_id=scope_id,
            source=source,
            output=output,
            publish_output=publish_output,
            public_readonly=public_readonly,
            allow_external_data=allow_external_data,
            index=index,
        )
        configs[scope_id] = DocsScopeConfig(
            scope_id=scope_id,
            scope_type=scope_type,
            source=source,
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
            non_loadable_doc_ids=string_tuple(
                item.get("non_loadable_doc_ids"),
                field=f"scopes[{index}].non_loadable_doc_ids",
            ),
            manage_only_tree_root_ids=string_tuple(
                item.get("manage_only_tree_root_ids"),
                field=f"scopes[{index}].manage_only_tree_root_ids",
            ),
            allow_unresolved_parent_ids=item.get("allow_unresolved_parent_ids") is True,
            import_media_storage=import_media_storage,
            sub_scopes=sub_scopes,
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
