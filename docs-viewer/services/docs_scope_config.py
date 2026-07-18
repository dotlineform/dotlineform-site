#!/usr/bin/env python3
"""Role-first Docs Viewer scope configuration."""

from __future__ import annotations

from dataclasses import dataclass, replace
import json
from pathlib import Path
import re
import sys
from typing import Any, Mapping


_BOOTSTRAP_START = Path(__file__).resolve()
for _candidate in (_BOOTSTRAP_START.parent, *_BOOTSTRAP_START.parents):
    if (_candidate / "site-tools" / "config" / "site-tools.json").exists():
        if str(_candidate) not in sys.path:
            sys.path.insert(0, str(_candidate))
        break

from docs_artifact_locations import (  # noqa: E402
    DELETE_CAPABILITY,
    EXTERNAL_LOCAL_PROVIDER,
    LIST_CAPABILITY,
    LOCAL_STAGING_CAPABILITY,
    R2_PROVIDER,
    READ_CAPABILITY,
    REPLACE_CAPABILITY,
    REPOSITORY_PROVIDER,
    SERVED_REFERENCE_CAPABILITY,
    STAT_CAPABILITY,
    SUPPORTED_LOCATION_PROVIDERS,
    VERIFY_BYTES_CAPABILITY,
    WRITE_CAPABILITY,
    ArtifactLocation,
    filesystem_location_root,
    require_location_capabilities,
)
from studio.shared.python.external_workspace_paths import (  # noqa: E402
    ExternalWorkspaceRoot,
    resolve_external_workspace_root,
    resolve_workspace_path,
)


CONFIG_REL_PATH = Path("docs-viewer/config/scopes/docs_scopes.json")
SCHEMA_VERSION = "docs_scopes_v2"
DOCS_VIEWER_MANAGE_ROUTE_BASE_URL = "/docs/"
PUBLIC_DOCS_OUTPUT_ROOT = Path("site/assets/data/docs/scopes")
PUBLIC_SEARCH_OUTPUT_ROOT = Path("site/assets/data/search")
PUBLISHED_DOCS_OUTPUT_ROOT = Path("docs-viewer/published/docs")
PUBLISHED_SEARCH_OUTPUT_ROOT = Path("docs-viewer/published/search")
SOURCE_DOCUMENTS_PATH = Path("documents")
SOURCE_SUB_SCOPES_PATH = Path("sub-scopes")
PUBLIC_SCOPE_TYPE = "public"
LOCAL_SCOPE_TYPE = "local"
LOCAL_EXTERNAL_SCOPE_TYPE = "local_external"
SUPPORTED_SCOPE_TYPES = {PUBLIC_SCOPE_TYPE, LOCAL_SCOPE_TYPE, LOCAL_EXTERNAL_SCOPE_TYPE}
DOTLINEFORM_PROJECTS_BASE_DIR_ENV = "DOTLINEFORM_PROJECTS_BASE_DIR"
EXTERNAL_DATA_ROOT_MARKER = f"${DOTLINEFORM_PROJECTS_BASE_DIR_ENV}/docs-viewer"
SUB_SCOPE_ID_PATTERN = re.compile(r"\A[a-z0-9][a-z0-9_-]*\Z")
MEDIA_TYPE_PATTERN = re.compile(r"\A[a-z][a-z0-9_-]*\Z")
PUBLISHED_MEDIA_TYPES = frozenset({"files", "html", "img", "svg"})
BUILD_MEDIA_TYPES = frozenset({"mermaid"})

SOURCE_CAPABILITIES = frozenset(
    {
        LIST_CAPABILITY,
        READ_CAPABILITY,
        WRITE_CAPABILITY,
        REPLACE_CAPABILITY,
        DELETE_CAPABILITY,
        STAT_CAPABILITY,
        VERIFY_BYTES_CAPABILITY,
        LOCAL_STAGING_CAPABILITY,
    }
)
PAYLOAD_CAPABILITIES = SOURCE_CAPABILITIES
PUBLISHED_MEDIA_CAPABILITIES = frozenset(
    {
        LIST_CAPABILITY,
        READ_CAPABILITY,
        WRITE_CAPABILITY,
        REPLACE_CAPABILITY,
        DELETE_CAPABILITY,
        STAT_CAPABILITY,
        VERIFY_BYTES_CAPABILITY,
        SERVED_REFERENCE_CAPABILITY,
        LOCAL_STAGING_CAPABILITY,
    }
)


@dataclass(frozen=True)
class DocsBuildMediaConfig:
    path: Path
    producer: str
    publishes_to: str


@dataclass(frozen=True)
class DocsSourceConfig:
    location: ArtifactLocation
    documents_path: Path
    build_media: Mapping[str, DocsBuildMediaConfig]
    sub_scopes_path: Path


@dataclass(frozen=True)
class DocsPublishedArtifactConfig:
    location: ArtifactLocation


@dataclass(frozen=True)
class DocsPublishedMediaConfig:
    media_type: str
    reference_prefix: Path
    location: ArtifactLocation
    served_path_prefix: str
    build_inputs: tuple[str, ...]


@dataclass(frozen=True)
class DocsPublishedConfig:
    documents: DocsPublishedArtifactConfig
    search: DocsPublishedArtifactConfig
    media: Mapping[str, DocsPublishedMediaConfig]


@dataclass(frozen=True)
class DocsPublicProjectionConfig:
    documents: DocsPublishedArtifactConfig
    search: DocsPublishedArtifactConfig | None


@dataclass(frozen=True)
class DocsScopeConfig:
    scope_id: str
    scope_type: str
    source: DocsSourceConfig
    published: DocsPublishedConfig
    public_projection: DocsPublicProjectionConfig | None
    viewer_base_url: str
    include_scope_param: bool
    default_doc_id: str
    non_loadable_doc_ids: tuple[str, ...]
    manage_only_tree_root_ids: tuple[str, ...]
    allow_unresolved_parent_ids: bool
    sub_scopes: tuple["DocsSubScopeConfig", ...]


@dataclass(frozen=True)
class DocsSubScopeConfig:
    sub_scope: str
    title: str
    source: DocsSourceConfig
    published: DocsPublishedConfig
    public_projection: DocsPublicProjectionConfig | None


def default_repo_root() -> Path:
    current = Path(__file__).resolve()
    for candidate in [current.parent, *current.parents]:
        if (candidate / "site-tools" / "config" / "site-tools.json").exists():
            return candidate
    raise ValueError("could not resolve repo root")


def safe_relative_path(value: Any, *, field: str, allow_current: bool = False) -> Path:
    text = str(value or "").strip()
    if allow_current and text in {"", "."}:
        return Path(".")
    if not text:
        raise ValueError(f"docs scope config field {field} is required")
    path = Path(text)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"docs scope config field {field} must be a safe relative path")
    if not allow_current and any(part in {"", "."} for part in path.parts):
        raise ValueError(f"docs scope config field {field} must be a safe relative path")
    return path


def safe_scope_data_path(value: Any, *, field: str, allow_external: bool = False) -> Path:
    """Validate a filesystem path used by lifecycle request/preview code."""

    text = str(value or "").strip()
    if not text:
        raise ValueError(f"docs scope config field {field} is required")
    if allow_external and (text == EXTERNAL_DATA_ROOT_MARKER or text.startswith(f"{EXTERNAL_DATA_ROOT_MARKER}/")):
        return resolve_external_data_marker_path(text, field=field)
    path = Path(text)
    if path.is_absolute():
        if not allow_external or ".." in path.parts or path.parent == path:
            raise ValueError(f"docs scope config field {field} must be a safe configured path")
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


def resolve_location_path(repo_root: Path, location: ArtifactLocation) -> Path:
    return filesystem_location_root(repo_root, location)


def path_label(repo_root: Path, path: Path) -> str:
    if not path.is_absolute():
        return path.as_posix()
    resolved_root = repo_root.resolve()
    resolved_path = resolve_scope_path(repo_root, path)
    try:
        return resolved_path.relative_to(resolved_root).as_posix()
    except ValueError:
        return resolved_path.as_posix()


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


def normalize_sub_scope_id(value: Any, *, field: str) -> str:
    text = str(value or "").strip().lower()
    if not SUB_SCOPE_ID_PATTERN.fullmatch(text):
        raise ValueError(
            f"docs scope config field {field} must start with a lowercase letter or digit "
            "and contain only lowercase letters, digits, hyphens, or underscores"
        )
    return text


def normalize_served_path_prefix(value: Any, *, field: str) -> str:
    text = str(value or "").strip()
    is_absolute_url = text.startswith(("https://", "http://"))
    if not text or (not text.startswith("/") and not is_absolute_url):
        raise ValueError(f"docs scope config field {field} must be an absolute path or URL")
    path_text = text.split("://", 1)[-1].partition("/")[2] if is_absolute_url else text.lstrip("/")
    if ".." in Path(path_text).parts:
        raise ValueError(f"docs scope config field {field} must not contain parent path segments")
    return text.rstrip("/")


def path_is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def path_is_strict_relative_to(path: Path, parent: Path) -> bool:
    return path != parent and path_is_relative_to(path, parent)


def is_public_readonly_scope(*, viewer_base_url: str, include_scope_param: bool) -> bool:
    return not include_scope_param and normalize_viewer_base_url(viewer_base_url) != DOCS_VIEWER_MANAGE_ROUTE_BASE_URL


def normalize_location(raw: Any, *, field: str) -> ArtifactLocation:
    if not isinstance(raw, dict):
        raise ValueError(f"docs scope config field {field} must be an object")
    provider = str(raw.get("provider") or "").strip().lower()
    if provider not in SUPPORTED_LOCATION_PROVIDERS:
        supported = ", ".join(sorted(SUPPORTED_LOCATION_PROVIDERS))
        raise ValueError(f"docs scope config field {field}.provider must be one of: {supported}")
    path_text = str(raw.get("path") or "").strip()
    if not path_text:
        raise ValueError(f"docs scope config field {field}.path is required")
    if provider == REPOSITORY_PROVIDER:
        path = safe_relative_path(path_text, field=f"{field}.path")
    elif provider == EXTERNAL_LOCAL_PROVIDER:
        path = resolve_external_data_marker_path(path_text, field=f"{field}.path")
    else:
        path = safe_relative_path(path_text, field=f"{field}.path")
    return ArtifactLocation(provider=provider, path=path)


def normalize_artifact(raw: Any, *, field: str) -> DocsPublishedArtifactConfig:
    if not isinstance(raw, dict):
        raise ValueError(f"docs scope config field {field} must be an object")
    return DocsPublishedArtifactConfig(location=normalize_location(raw.get("location"), field=f"{field}.location"))


def normalize_build_media(raw: Any, *, field: str) -> dict[str, DocsBuildMediaConfig]:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ValueError(f"docs scope config field {field} must be an object")
    result: dict[str, DocsBuildMediaConfig] = {}
    for media_type, item in raw.items():
        normalized_type = str(media_type or "").strip().lower()
        item_field = f"{field}.{normalized_type}"
        if not MEDIA_TYPE_PATTERN.fullmatch(normalized_type) or not isinstance(item, dict):
            raise ValueError(f"docs scope config field {item_field} must be a named media object")
        if normalized_type not in BUILD_MEDIA_TYPES:
            supported = ", ".join(sorted(BUILD_MEDIA_TYPES))
            raise ValueError(
                f"docs scope config field {item_field} uses an unsupported build media type; "
                f"supported: {supported}"
            )
        producer = str(item.get("producer") or "").strip()
        publishes_to = str(item.get("publishes_to") or "").strip().lower()
        if not producer or not publishes_to:
            raise ValueError(f"docs scope config field {item_field} requires producer and publishes_to")
        path = safe_relative_path(item.get("path"), field=f"{item_field}.path")
        expected_path = Path("media") / normalized_type
        if path != expected_path:
            raise ValueError(
                f"docs scope config field {item_field}.path must be {expected_path.as_posix()}"
            )
        result[normalized_type] = DocsBuildMediaConfig(
            path=path,
            producer=producer,
            publishes_to=publishes_to,
        )
    return result


def normalize_source(raw: Any, *, field: str) -> DocsSourceConfig:
    if not isinstance(raw, dict):
        raise ValueError(f"docs scope config field {field} must be an object")
    documents_path = safe_relative_path(
        raw.get("documents_path"),
        field=f"{field}.documents_path",
    )
    if documents_path != SOURCE_DOCUMENTS_PATH:
        raise ValueError(
            f"docs scope config field {field}.documents_path must be {SOURCE_DOCUMENTS_PATH.as_posix()}"
        )
    sub_scopes_path = safe_relative_path(
        raw.get("sub_scopes_path"),
        field=f"{field}.sub_scopes_path",
    )
    if sub_scopes_path != SOURCE_SUB_SCOPES_PATH:
        raise ValueError(
            f"docs scope config field {field}.sub_scopes_path must be {SOURCE_SUB_SCOPES_PATH.as_posix()}"
        )
    source = DocsSourceConfig(
        location=normalize_location(raw.get("location"), field=f"{field}.location"),
        documents_path=documents_path,
        build_media=normalize_build_media(raw.get("build_media"), field=f"{field}.build_media"),
        sub_scopes_path=sub_scopes_path,
    )
    require_location_capabilities(source.location, SOURCE_CAPABILITIES, role=f"{field}.documents")
    return source


def normalize_published_media(raw: Any, *, scope_id: str, field: str) -> dict[str, DocsPublishedMediaConfig]:
    if not isinstance(raw, dict) or not raw:
        raise ValueError(f"docs scope config field {field} must be a non-empty object")
    result: dict[str, DocsPublishedMediaConfig] = {}
    for media_type, item in raw.items():
        normalized_type = str(media_type or "").strip().lower()
        item_field = f"{field}.{normalized_type}"
        if not MEDIA_TYPE_PATTERN.fullmatch(normalized_type) or not isinstance(item, dict):
            raise ValueError(f"docs scope config field {item_field} must be a named media object")
        if normalized_type not in PUBLISHED_MEDIA_TYPES:
            supported = ", ".join(sorted(PUBLISHED_MEDIA_TYPES))
            raise ValueError(
                f"docs scope config field {item_field} uses an unsupported published media type; "
                f"supported: {supported}"
            )
        reference_prefix = safe_relative_path(item.get("reference_prefix"), field=f"{item_field}.reference_prefix")
        expected_reference = Path("docs") / scope_id / normalized_type
        if reference_prefix != expected_reference:
            raise ValueError(
                f"docs scope config field {item_field}.reference_prefix must be {expected_reference.as_posix()}"
            )
        location = normalize_location(item.get("location"), field=f"{item_field}.location")
        served_path_prefix = normalize_served_path_prefix(
            item.get("served_path_prefix"),
            field=f"{item_field}.served_path_prefix",
        )
        build_inputs = string_tuple(item.get("build_inputs"), field=f"{item_field}.build_inputs")
        require_location_capabilities(location, PUBLISHED_MEDIA_CAPABILITIES, role=item_field)
        result[normalized_type] = DocsPublishedMediaConfig(
            media_type=normalized_type,
            reference_prefix=reference_prefix,
            location=location,
            served_path_prefix=served_path_prefix,
            build_inputs=build_inputs,
        )
    return result


def normalize_published(raw: Any, *, scope_id: str, field: str, require_media: bool = True) -> DocsPublishedConfig:
    if not isinstance(raw, dict):
        raise ValueError(f"docs scope config field {field} must be an object")
    documents = normalize_artifact(raw.get("documents"), field=f"{field}.documents")
    search = normalize_artifact(raw.get("search"), field=f"{field}.search")
    require_location_capabilities(documents.location, PAYLOAD_CAPABILITIES, role=f"{field}.documents")
    require_location_capabilities(search.location, PAYLOAD_CAPABILITIES, role=f"{field}.search")
    media_raw = raw.get("media")
    media = normalize_published_media(media_raw, scope_id=scope_id, field=f"{field}.media") if require_media else (
        normalize_published_media(media_raw, scope_id=scope_id, field=f"{field}.media") if media_raw else {}
    )
    return DocsPublishedConfig(documents=documents, search=search, media=media)


def normalize_public_projection(raw: Any, *, field: str, search_required: bool = True) -> DocsPublicProjectionConfig | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError(f"docs scope config field {field} must be an object or null")
    documents = normalize_artifact(raw.get("documents"), field=f"{field}.documents")
    search = normalize_artifact(raw.get("search"), field=f"{field}.search") if raw.get("search") is not None else None
    if search_required and search is None:
        raise ValueError(f"docs scope config field {field}.search is required")
    for name, artifact in (("documents", documents), ("search", search)):
        if artifact is not None and artifact.location.provider != REPOSITORY_PROVIDER:
            raise ValueError(f"docs scope config field {field}.{name} must use provider 'repository'")
    return DocsPublicProjectionConfig(documents=documents, search=search)


def location_child_path(location: ArtifactLocation, relative: Path) -> Path:
    return location.path if relative == Path(".") else location.path / relative


def source_container_path(config: DocsScopeConfig | DocsSubScopeConfig) -> Path:
    return config.source.location.path


def document_source_path(config: DocsScopeConfig | DocsSubScopeConfig) -> Path:
    return location_child_path(config.source.location, config.source.documents_path)


def published_documents_path(config: DocsScopeConfig | DocsSubScopeConfig) -> Path:
    return config.published.documents.location.path


def published_search_path(config: DocsScopeConfig | DocsSubScopeConfig) -> Path:
    return config.published.search.location.path


def public_documents_path(config: DocsScopeConfig | DocsSubScopeConfig) -> Path | None:
    return config.public_projection.documents.location.path if config.public_projection else None


def public_search_path(config: DocsScopeConfig | DocsSubScopeConfig) -> Path | None:
    projection = config.public_projection
    return projection.search.location.path if projection and projection.search else None


def publication_documents_path(config: DocsScopeConfig | DocsSubScopeConfig) -> Path:
    return public_documents_path(config) or published_documents_path(config)


def publication_search_path(config: DocsScopeConfig | DocsSubScopeConfig) -> Path:
    return public_search_path(config) or published_search_path(config)


def scope_media_reference_root(config: DocsScopeConfig) -> Path:
    return Path("docs") / config.scope_id


def published_media_config(config: DocsScopeConfig, media_type: str) -> DocsPublishedMediaConfig:
    normalized = str(media_type or "").strip().lower()
    try:
        return config.published.media[normalized]
    except KeyError as exc:
        supported = ", ".join(sorted(config.published.media))
        raise ValueError(
            f"Docs scope {config.scope_id!r} has no published media role {normalized!r}; configured: {supported}"
        ) from exc


def scope_uses_external_data(config: DocsScopeConfig) -> bool:
    locations = [
        config.source.location,
        config.published.documents.location,
        config.published.search.location,
        *(media.location for media in config.published.media.values()),
    ]
    return any(location.provider == EXTERNAL_LOCAL_PROVIDER for location in locations)


def validate_scope_policy(config: DocsScopeConfig, *, field: str) -> None:
    expected_provider = EXTERNAL_LOCAL_PROVIDER if config.scope_type == LOCAL_EXTERNAL_SCOPE_TYPE else REPOSITORY_PROVIDER
    if config.source.location.provider != expected_provider:
        raise ValueError(
            f"docs scope config {field}.source.location for {config.scope_type!r} scope must use provider {expected_provider!r}"
        )
    for role_name, artifact in (
        ("published.documents", config.published.documents),
        ("published.search", config.published.search),
    ):
        if artifact.location.provider != expected_provider:
            raise ValueError(
                f"docs scope config {field}.{role_name} for {config.scope_type!r} scope "
                f"must use provider {expected_provider!r}"
            )
    if expected_provider == REPOSITORY_PROVIDER:
        if not path_is_relative_to(config.published.documents.location.path, PUBLISHED_DOCS_OUTPUT_ROOT):
            raise ValueError(
                f"docs scope config {field}.published.documents must remain under "
                f"{PUBLISHED_DOCS_OUTPUT_ROOT.as_posix()}"
            )
        if not path_is_relative_to(config.published.search.location.path, PUBLISHED_SEARCH_OUTPUT_ROOT):
            raise ValueError(
                f"docs scope config {field}.published.search must remain under "
                f"{PUBLISHED_SEARCH_OUTPUT_ROOT.as_posix()}"
            )
    public_readonly = is_public_readonly_scope(
        viewer_base_url=config.viewer_base_url,
        include_scope_param=config.include_scope_param,
    )
    if config.scope_type == LOCAL_EXTERNAL_SCOPE_TYPE and public_readonly:
        raise ValueError(f"docs scope config {field} external local scopes must use the management route")
    if public_readonly != (config.public_projection is not None):
        requirement = "configure" if public_readonly else "not configure"
        raise ValueError(f"docs scope config {field} must {requirement} public_projection")
    if config.public_projection is not None:
        if not path_is_relative_to(config.public_projection.documents.location.path, PUBLIC_DOCS_OUTPUT_ROOT):
            raise ValueError(
                f"docs scope config {field}.public_projection.documents must remain under "
                f"{PUBLIC_DOCS_OUTPUT_ROOT.as_posix()}"
            )
        if config.public_projection.search is not None and not path_is_relative_to(
            config.public_projection.search.location.path,
            PUBLIC_SEARCH_OUTPUT_ROOT,
        ):
            raise ValueError(
                f"docs scope config {field}.public_projection.search must remain under "
                f"{PUBLIC_SEARCH_OUTPUT_ROOT.as_posix()}"
            )
    if config.scope_type == LOCAL_EXTERNAL_SCOPE_TYPE:
        source_root = config.source.location.path
        external_root = resolve_external_data_root()
        if not source_root.is_relative_to(external_root):
            raise ValueError(f"docs scope config {field}.source must remain under {EXTERNAL_DATA_ROOT_MARKER}")
        for role_name, artifact in (
            ("published.documents", config.published.documents),
            ("published.search", config.published.search),
        ):
            if not artifact.location.path.is_relative_to(external_root):
                raise ValueError(
                    f"docs scope config {field}.{role_name} must remain under {EXTERNAL_DATA_ROOT_MARKER}"
                )
        for media_type, media in config.published.media.items():
            if media.location.provider != EXTERNAL_LOCAL_PROVIDER:
                raise ValueError(
                    f"docs scope config {field}.published.media.{media_type} for external local scope "
                    "must use provider 'external_local'"
                )
            if not media.location.path.is_relative_to(source_root):
                raise ValueError(
                    f"docs scope config {field}.published.media.{media_type}.location must remain beneath the source scope"
                )
    else:
        for media_type, media in config.published.media.items():
            if media.location.provider == EXTERNAL_LOCAL_PROVIDER:
                raise ValueError(
                    f"docs scope config {field}.published.media.{media_type} for repository-backed scope "
                    "must use provider 'repository' or 'r2'"
                )
    for build_type, build in config.source.build_media.items():
        if build.publishes_to not in config.published.media:
            raise ValueError(
                f"docs scope config {field}.source.build_media.{build_type}.publishes_to "
                f"references unconfigured media type {build.publishes_to!r}"
            )
        declared_inputs = config.published.media[build.publishes_to].build_inputs
        if build_type not in declared_inputs:
            raise ValueError(
                f"docs scope config {field}.published.media.{build.publishes_to}.build_inputs "
                f"must include {build_type!r}"
            )
    producer_targets: dict[str, str] = {}
    for build_type, build in config.source.build_media.items():
        competing = producer_targets.get(build.publishes_to)
        if competing is not None:
            raise ValueError(
                f"docs scope config {field} build media types {competing!r} and {build_type!r} "
                f"compete for published media {build.publishes_to!r}"
            )
        producer_targets[build.publishes_to] = build_type
    for media_type, media in config.published.media.items():
        if len(set(media.build_inputs)) != len(media.build_inputs):
            raise ValueError(
                f"docs scope config {field}.published.media.{media_type}.build_inputs must not contain duplicates"
            )
        for build_type in media.build_inputs:
            build = config.source.build_media.get(build_type)
            if build is None or build.publishes_to != media_type:
                raise ValueError(
                    f"docs scope config {field}.published.media.{media_type}.build_inputs references "
                    f"unconfigured build media {build_type!r}"
                )


def normalize_sub_scope_configs(
    raw: Any,
    *,
    parent: DocsScopeConfig,
    field: str,
) -> tuple[DocsSubScopeConfig, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise ValueError(f"docs scope config field {field} must be an array")
    configs: list[DocsSubScopeConfig] = []
    seen: set[str] = set()
    for index, item in enumerate(raw):
        item_field = f"{field}[{index}]"
        if not isinstance(item, dict):
            raise ValueError(f"docs scope config field {item_field} must be an object")
        sub_scope = str(item.get("sub_scope") or "").strip().lower()
        if not SUB_SCOPE_ID_PATTERN.fullmatch(sub_scope):
            raise ValueError(f"docs scope config field {item_field}.sub_scope is invalid")
        if sub_scope in seen:
            raise ValueError(f"docs scope config sub_scope {sub_scope!r} is duplicated in scope {parent.scope_id!r}")
        seen.add(sub_scope)
        source = normalize_source(item.get("source"), field=f"{item_field}.source")
        published = normalize_published(
            item.get("published"),
            scope_id=parent.scope_id,
            field=f"{item_field}.published",
            require_media=False,
        )
        projection = normalize_public_projection(
            item.get("public_projection"),
            field=f"{item_field}.public_projection",
            search_required=False,
        )
        if source.location.provider != parent.source.location.provider:
            raise ValueError(f"docs scope config sub-scope {parent.scope_id}/{sub_scope} must use its parent source provider")
        expected_source = location_child_path(parent.source.location, parent.source.sub_scopes_path) / sub_scope
        if source.location.path != expected_source:
            raise ValueError(
                f"docs scope config sub-scope {parent.scope_id}/{sub_scope} source must be "
                f"{expected_source.as_posix()}"
            )
        if (
            published.documents.location.provider != parent.published.documents.location.provider
            or published.search.location.provider != parent.published.search.location.provider
        ):
            raise ValueError(f"docs scope config sub-scope {parent.scope_id}/{sub_scope} must use its parent payload provider")
        expected_published_documents = parent.published.documents.location.path / SOURCE_SUB_SCOPES_PATH / sub_scope
        if published.documents.location.path != expected_published_documents:
            raise ValueError(
                f"docs scope config sub-scope {parent.scope_id}/{sub_scope} published documents must be "
                f"{expected_published_documents.as_posix()}"
            )
        expected_published_search = (
            parent.published.search.location.path.parent / SOURCE_SUB_SCOPES_PATH / sub_scope / "index.json"
        )
        if published.search.location.path != expected_published_search:
            raise ValueError(
                f"docs scope config sub-scope {parent.scope_id}/{sub_scope} published search must be "
                f"{expected_published_search.as_posix()}"
            )
        if bool(projection) != bool(parent.public_projection):
            raise ValueError(
                f"docs scope config sub-scope {parent.scope_id}/{sub_scope} public_projection must match its parent exposure"
            )
        if projection and parent.public_projection:
            expected_public_documents = parent.public_projection.documents.location.path / sub_scope
            if projection.documents.location.path != expected_public_documents:
                raise ValueError(
                    f"docs scope config sub-scope {parent.scope_id}/{sub_scope} public documents must be "
                    f"{expected_public_documents.as_posix()}"
                )
        configs.append(
            DocsSubScopeConfig(
                sub_scope=sub_scope,
                title=str(item.get("title") or "").strip(),
                source=source,
                published=published,
                public_projection=projection,
            )
        )
    return tuple(configs)


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
        field = f"scopes[{index}]"
        if not isinstance(item, dict):
            raise ValueError(f"docs scope config {field} must be an object")
        scope_id = str(item.get("scope_id") or "").strip().lower()
        if not scope_id:
            raise ValueError(f"docs scope config {field}.scope_id is required")
        if scope_id in configs:
            raise ValueError(f"docs scope config scope_id {scope_id!r} is duplicated")
        scope_type = str(item.get("scope_type") or "").strip().lower()
        if scope_type not in SUPPORTED_SCOPE_TYPES:
            supported = ", ".join(sorted(SUPPORTED_SCOPE_TYPES))
            raise ValueError(f"docs scope config {field}.scope_type must be one of: {supported}")
        viewer_base_url = normalize_viewer_base_url(item.get("viewer_base_url"))
        include_scope_param = item.get("include_scope_param") is True
        preliminary = DocsScopeConfig(
            scope_id=scope_id,
            scope_type=scope_type,
            source=normalize_source(item.get("source"), field=f"{field}.source"),
            published=normalize_published(item.get("published"), scope_id=scope_id, field=f"{field}.published"),
            public_projection=normalize_public_projection(
                item.get("public_projection"),
                field=f"{field}.public_projection",
            ),
            viewer_base_url=viewer_base_url,
            include_scope_param=include_scope_param,
            default_doc_id=str(item.get("default_doc_id") or "").strip(),
            non_loadable_doc_ids=string_tuple(
                item.get("non_loadable_doc_ids"),
                field=f"{field}.non_loadable_doc_ids",
            ),
            manage_only_tree_root_ids=string_tuple(
                item.get("manage_only_tree_root_ids"),
                field=f"{field}.manage_only_tree_root_ids",
            ),
            allow_unresolved_parent_ids=item.get("allow_unresolved_parent_ids") is True,
            sub_scopes=(),
        )
        validate_scope_policy(preliminary, field=field)
        config = replace(
            preliminary,
            sub_scopes=normalize_sub_scope_configs(
                item.get("sub_scopes"),
                parent=preliminary,
                field=f"{field}.sub_scopes",
            ),
        )
        configs[scope_id] = config
    return configs


DOCS_SCOPE_CONFIGS = load_docs_scope_configs()
DOCUMENT_SOURCE_ROOTS = {
    scope: document_source_path(config)
    for scope, config in DOCS_SCOPE_CONFIGS.items()
}


__all__ = [
    "CONFIG_REL_PATH",
    "DOCS_SCOPE_CONFIGS",
    "DOCUMENT_SOURCE_ROOTS",
    "DOCS_VIEWER_MANAGE_ROUTE_BASE_URL",
    "DOTLINEFORM_PROJECTS_BASE_DIR_ENV",
    "DocsBuildMediaConfig",
    "DocsPublicProjectionConfig",
    "DocsPublishedArtifactConfig",
    "DocsPublishedConfig",
    "DocsPublishedMediaConfig",
    "DocsScopeConfig",
    "DocsSourceConfig",
    "DocsSubScopeConfig",
    "EXTERNAL_DATA_ROOT_MARKER",
    "LOCAL_EXTERNAL_SCOPE_TYPE",
    "LOCAL_SCOPE_TYPE",
    "PUBLISHED_DOCS_OUTPUT_ROOT",
    "PUBLISHED_MEDIA_TYPES",
    "PUBLISHED_SEARCH_OUTPUT_ROOT",
    "PUBLIC_DOCS_OUTPUT_ROOT",
    "PUBLIC_SCOPE_TYPE",
    "PUBLIC_SEARCH_OUTPUT_ROOT",
    "BUILD_MEDIA_TYPES",
    "SCHEMA_VERSION",
    "SOURCE_DOCUMENTS_PATH",
    "SOURCE_SUB_SCOPES_PATH",
    "default_repo_root",
    "document_source_path",
    "is_public_readonly_scope",
    "load_docs_scope_configs",
    "location_child_path",
    "normalize_viewer_base_url",
    "normalize_sub_scope_id",
    "path_is_relative_to",
    "path_is_strict_relative_to",
    "path_label",
    "public_documents_path",
    "public_search_path",
    "publication_documents_path",
    "publication_search_path",
    "published_documents_path",
    "published_media_config",
    "published_search_path",
    "resolve_external_data_marker_path",
    "resolve_external_data_root",
    "resolve_external_data_workspace",
    "resolve_location_path",
    "resolve_scope_path",
    "safe_relative_path",
    "safe_scope_data_path",
    "scope_uses_external_data",
    "scope_media_reference_root",
    "source_container_path",
]
