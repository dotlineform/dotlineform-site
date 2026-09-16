"""One explicitly configured Docs workspace and its lifecycle storage.

Loading is read-only and never creates a root. Source/generated access requires
an explicit Working or Pre-publish stage; Published belongs to the workspace.
There is no scope registry, process-global configuration, or alternate root.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
from typing import Any, Mapping

from docs_artifact_locations import (
    EXTERNAL_LOCAL_PROVIDER,
    REPOSITORY_PROVIDER,
    R2_PROVIDER,
    ArtifactLocation,
    filesystem_location_root,
)
from docs_document_identity import is_immutable_doc_id
from docs_collection_customisations import (
    DocsCollectionCustomisationConfig,
    normalize_docs_collection_customisation,
)


CONFIG_REL_PATH = Path("docs-viewer/config/workspace/docs-workspace.json")
SCHEMA_VERSION = "docs_workspace_v2"
DOTLINEFORM_DOCS_BASE_DIR_ENV = "DOTLINEFORM_DOCS_BASE_DIR"
EXTERNAL_DATA_ROOT_MARKER = f"${DOTLINEFORM_DOCS_BASE_DIR_ENV}"
STAGES = ("working", "pre-publish")
SOURCE_DOCUMENTS_PATH = Path("documents")
SOURCE_COLLECTIONS_PATH = Path("collections")
PUBLIC_DOCS_OUTPUT_ROOT = Path("site/assets/data/docs")
PUBLIC_SEARCH_OUTPUT_ROOT = Path("site/assets/data/search")
MEDIA_REFERENCE_ROOT = Path("docs")
MANAGED_MEDIA_TYPES = frozenset({"files", "html", "img", "svg"})
BUILD_MEDIA_TYPES = frozenset({"mermaid"})
COLLECTION_ID_PATTERN = re.compile(r"\A[a-z0-9][a-z0-9_-]*\Z")
SOURCE_REVISION_PATTERN = re.compile(r"\Asha256:[0-9a-f]{64}\Z")
COLLECTION_LIFECYCLE_TOOL_ID = "docs-viewer-collection-lifecycle"
# Read only as historical creation provenance, never as an active tool alias.
HISTORICAL_COLLECTION_LIFECYCLE_TOOL_ID = "docs-viewer-scope-lifecycle"
SEARCH_FIELDS = frozenset({"body", "code", "heading", "identity", "last_updated", "parent_title", "summary", "title"})
DEFAULT_DOCS_SEARCH_FIELDS = ("title", "heading", "summary", "body", "code")


@dataclass(frozen=True)
class DocsSourceConfig:
    location: ArtifactLocation
    documents_path: Path = SOURCE_DOCUMENTS_PATH
    collections_path: Path = SOURCE_COLLECTIONS_PATH


@dataclass(frozen=True)
class DocsArtifactConfig:
    location: ArtifactLocation


@dataclass(frozen=True)
class DocsGeneratedConfig:
    documents: DocsArtifactConfig
    search: DocsArtifactConfig


@dataclass(frozen=True)
class DocsPublishedConfig:
    documents: DocsArtifactConfig
    search: DocsArtifactConfig


@dataclass(frozen=True)
class DocsBuildMediaConfig:
    location: ArtifactLocation
    producer: str
    publishes_to: str


@dataclass(frozen=True)
class DocsManagedMediaConfig:
    media_type: str
    reference_prefix: Path
    source_location: ArtifactLocation
    generated_location: ArtifactLocation
    published_location: ArtifactLocation
    served_path_prefix: str
    build_inputs: tuple[str, ...]


@dataclass(frozen=True)
class DocsMediaConfig:
    source_location: ArtifactLocation
    generated_location: ArtifactLocation
    published_location: ArtifactLocation
    types: Mapping[str, DocsManagedMediaConfig]
    build_sources: Mapping[str, DocsBuildMediaConfig]


@dataclass(frozen=True)
class DocsPublicMediaConfig:
    media_type: str
    reference_prefix: Path
    location: ArtifactLocation
    served_path_prefix: str


@dataclass(frozen=True)
class DocsPublicProjectionConfig:
    documents: DocsArtifactConfig
    search: DocsArtifactConfig | None
    media: Mapping[str, DocsPublicMediaConfig]


@dataclass(frozen=True)
class DocsCollectionLifecycleConfig:
    tool_id: str
    report_host_doc_id: str
    report_host_source_revision: str


@dataclass(frozen=True)
class DocsCollectionConfig:
    collection: str
    title: str
    public_title: str
    supports_return_import: bool
    collection_customisation: DocsCollectionCustomisationConfig | None
    lifecycle: DocsCollectionLifecycleConfig | None
    stage: str
    source: DocsSourceConfig
    media: DocsMediaConfig
    generated: DocsGeneratedConfig
    published: DocsPublishedConfig
    public_projection: DocsPublicProjectionConfig | None


@dataclass(frozen=True)
class DocsStageConfig:
    workspace_root: ArtifactLocation
    stage: str
    source: DocsSourceConfig
    media: DocsMediaConfig
    generated: DocsGeneratedConfig
    published: DocsPublishedConfig
    public_projection: DocsPublicProjectionConfig | None
    default_doc_id: str
    non_loadable_doc_ids: tuple[str, ...]
    manage_only_tree_root_ids: tuple[str, ...]
    allow_unresolved_parent_ids: bool
    collections: tuple[DocsCollectionConfig, ...]
    search_fields: tuple[str, ...]

    @property
    def stage_root(self) -> ArtifactLocation:
        """Return this stage's source/generated owner, excluding Published."""
        return location_child(self.workspace_root, Path(self.stage))


@dataclass(frozen=True)
class DocsWorkspaceConfig:
    workspace_root: ArtifactLocation
    public_viewer_base_url: str
    public_projection: DocsPublicProjectionConfig
    published: DocsPublishedConfig
    search_fields: tuple[str, ...]
    recent_limit: int
    stages: tuple[DocsStageConfig, ...]


def default_repo_root() -> Path:
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "site-tools/config/site-tools.json").is_file():
            return candidate
    raise ValueError("could not resolve repository root")


def resolve_external_data_root() -> Path:
    """Require the existing explicit Docs root without creating or inferring it."""
    value = str(os.environ.get(DOTLINEFORM_DOCS_BASE_DIR_ENV) or "").strip()
    if not value:
        raise ValueError(f"{DOTLINEFORM_DOCS_BASE_DIR_ENV} is required")
    path = Path(value).expanduser()
    if not path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{DOTLINEFORM_DOCS_BASE_DIR_ENV} must be an absolute path without parent segments")
    root = path.resolve()
    if not root.is_dir():
        raise ValueError(f"Docs workspace root is unavailable: {EXTERNAL_DATA_ROOT_MARKER}")
    if not os.access(root, os.R_OK | os.W_OK):
        raise ValueError(f"Docs workspace root must be readable and writable: {EXTERNAL_DATA_ROOT_MARKER}")
    return root


def safe_relative_path(value: Any, *, field: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-blank relative path")
    text = value.strip()
    path = Path(text)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in text.split("/")) or "\\" in text or "\0" in text:
        raise ValueError(f"{field} must be a safe relative path")
    return path


def resolve_external_data_marker_path(value: Any, *, field: str) -> Path:
    """Resolve a marked path only within the configured existing workspace."""
    if value == EXTERNAL_DATA_ROOT_MARKER:
        return resolve_external_data_root()
    prefix = f"{EXTERNAL_DATA_ROOT_MARKER}/"
    if not isinstance(value, str) or not value.startswith(prefix):
        raise ValueError(f"{field} must be under {EXTERNAL_DATA_ROOT_MARKER}")
    relative = safe_relative_path(value[len(prefix):], field=field)
    root = resolve_external_data_root()
    resolved = (root / relative).resolve()
    if not resolved.is_relative_to(root):
        raise ValueError(f"{field} escapes {EXTERNAL_DATA_ROOT_MARKER}")
    return resolved


def resolve_workspace_path(repo_root: Path, path: Path) -> Path:
    return (path if path.is_absolute() else repo_root / path).resolve()


def resolve_location_path(repo_root: Path, location: ArtifactLocation) -> Path:
    return filesystem_location_root(repo_root, location)


def path_label(repo_root: Path, path: Path) -> str:
    resolved = resolve_workspace_path(repo_root, path)
    return resolved.relative_to(repo_root.resolve()).as_posix() if resolved.is_relative_to(repo_root.resolve()) else resolved.as_posix()


def location_child(location: ArtifactLocation, relative: Path) -> ArtifactLocation:
    path = location.path / relative
    if location.provider == EXTERNAL_LOCAL_PROVIDER and path.resolve() != path:
        raise ValueError("Docs workspace artifact paths must not traverse symlinks")
    return ArtifactLocation(provider=location.provider, path=path)


def _object(raw: Any, *, field: str, required: set[str], optional: set[str] | None = None) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError(f"{field} must be an object")
    missing = required - set(raw)
    unknown = set(raw) - required - (optional or set())
    if missing:
        raise ValueError(f"{field} is missing: {', '.join(sorted(missing))}")
    if unknown:
        raise ValueError(f"{field} contains unsupported fields: {', '.join(sorted(unknown))}")
    return raw


def _strings(raw: Any, *, field: str) -> tuple[str, ...]:
    if not isinstance(raw, list) or any(not isinstance(value, str) or not value.strip() for value in raw):
        raise ValueError(f"{field} must be an array of non-blank strings")
    result = tuple(value.strip() for value in raw)
    if len(set(result)) != len(result):
        raise ValueError(f"{field} contains duplicates")
    return result


def _boolean(raw: Any, *, field: str) -> bool:
    if not isinstance(raw, bool):
        raise ValueError(f"{field} must be true or false")
    return raw


def _doc_id(raw: Any, *, field: str, allow_empty: bool = False) -> str:
    if isinstance(raw, str) and ((allow_empty and raw == "") or is_immutable_doc_id(raw)):
        return raw
    raise ValueError(f"{field} must use immutable document identity")


def _doc_ids(raw: Any, *, field: str) -> tuple[str, ...]:
    return tuple(_doc_id(value, field=field) for value in _strings(raw, field=field))


def normalize_collection_id(raw: Any, *, field: str) -> str:
    if not isinstance(raw, str) or not COLLECTION_ID_PATTERN.fullmatch(raw):
        raise ValueError(f"{field} must identify one collection")
    return raw


def _location(raw: Any, *, field: str, providers: set[str]) -> ArtifactLocation:
    item = _object(raw, field=field, required={"provider", "path"})
    if not isinstance(item["provider"], str) or item["provider"] not in providers:
        raise ValueError(f"{field}.provider must be one of: {', '.join(sorted(providers))}")
    return ArtifactLocation(provider=item["provider"], path=safe_relative_path(item["path"], field=f"{field}.path"))


def _public_artifact(raw: Any, *, field: str, root: Path) -> DocsArtifactConfig:
    item = _object(raw, field=field, required={"location"})
    location = _location(item["location"], field=f"{field}.location", providers={REPOSITORY_PROVIDER})
    if not location.path.is_relative_to(root):
        raise ValueError(f"{field} must remain under {root.as_posix()}")
    return DocsArtifactConfig(location)


def _served_prefix(raw: Any, *, field: str) -> str:
    from urllib.parse import urlsplit

    if not isinstance(raw, str) or not raw or raw.endswith("/") or "\\" in raw:
        raise ValueError(f"{field} must be a URL prefix without a trailing slash")
    parts = urlsplit(raw)
    if parts.query or parts.fragment or parts.username or parts.password:
        raise ValueError(f"{field} must not contain credentials, a query, or a fragment")
    if parts.scheme:
        if parts.scheme not in {"http", "https"} or not parts.netloc:
            raise ValueError(f"{field} must be an HTTP(S) URL or site-relative prefix")
    elif not raw.startswith("/") or raw.startswith("//"):
        raise ValueError(f"{field} must be an HTTP(S) URL or site-relative prefix")
    safe_relative_path(parts.path.lstrip("/"), field=f"{field} path")
    return raw


def _public_projection(raw: Any) -> DocsPublicProjectionConfig:
    item = _object(raw, field="public_projection", required={"documents", "search", "media"})
    documents = _public_artifact(item["documents"], field="public_projection.documents", root=PUBLIC_DOCS_OUTPUT_ROOT)
    search = _public_artifact(item["search"], field="public_projection.search", root=PUBLIC_SEARCH_OUTPUT_ROOT)
    raw_media = item["media"]
    if not isinstance(raw_media, dict) or not raw_media or set(raw_media) - MANAGED_MEDIA_TYPES:
        raise ValueError("public_projection.media must configure supported media types")
    media = {}
    for media_type, raw_record in raw_media.items():
        field = f"public_projection.media.{media_type}"
        record = _object(raw_record, field=field, required={"location", "served_path_prefix"})
        location = _location(record["location"], field=f"{field}.location", providers={REPOSITORY_PROVIDER, R2_PROVIDER})
        if location.provider == REPOSITORY_PROVIDER and location.path != documents.location.path / "media" / media_type:
            raise ValueError(f"{field}.location must derive from the public documents destination")
        prefix = _served_prefix(record["served_path_prefix"], field=f"{field}.served_path_prefix")
        if not prefix.endswith(f"/media/{media_type}"):
            raise ValueError(f"{field}.served_path_prefix must end with /media/{media_type}")
        media[media_type] = DocsPublicMediaConfig(media_type, MEDIA_REFERENCE_ROOT / media_type, location, prefix)
    return DocsPublicProjectionConfig(documents, search, media)


def _media(raw: Any, *, source_root: ArtifactLocation, generated_root: ArtifactLocation,
           published_root: ArtifactLocation, stage: str, collection: str = "") -> DocsMediaConfig:
    field = f"stages.{stage}.media"
    item = _object(raw, field=field, required={"types", "build_sources"})
    types = item["types"]
    if not isinstance(types, dict) or not types or set(types) - MANAGED_MEDIA_TYPES:
        raise ValueError(f"{field}.types must configure supported media types")
    source_media = location_child(source_root, Path("media"))
    generated_media = location_child(generated_root, Path("media"))
    published_media = location_child(published_root, Path("media"))
    reference_root = MEDIA_REFERENCE_ROOT / "collections" / collection if collection else MEDIA_REFERENCE_ROOT
    served_root = f"/docs/media/{stage}" + (f"/collections/{collection}" if collection else "")
    raw_builds = item["build_sources"]
    if not isinstance(raw_builds, dict) or set(raw_builds) - BUILD_MEDIA_TYPES:
        raise ValueError(f"{field}.build_sources contains unsupported producers")
    builds = {}
    for name, raw_build in raw_builds.items():
        build = _object(raw_build, field=f"{field}.build_sources.{name}", required={"producer", "publishes_to"})
        if build["producer"] != "mermaid" or build["publishes_to"] != "svg" or "svg" not in types:
            raise ValueError(f"{field}.build_sources.{name} must use the Mermaid SVG producer")
        builds[name] = DocsBuildMediaConfig(location_child(source_media, Path("build-source") / name), "mermaid", "svg")
    managed = {}
    for media_type, raw_type in types.items():
        record = _object(raw_type, field=f"{field}.types.{media_type}", required={"build_inputs"})
        inputs = _strings(record["build_inputs"], field=f"{field}.types.{media_type}.build_inputs")
        if any(name not in builds or builds[name].publishes_to != media_type for name in inputs):
            raise ValueError(f"{field}.types.{media_type}.build_inputs must name a matching configured producer")
        managed[media_type] = DocsManagedMediaConfig(
            media_type, reference_root / media_type,
            location_child(source_media, Path(media_type)), location_child(generated_media, Path(media_type)),
            location_child(published_media, Path(media_type)), f"{served_root}/{media_type}", inputs,
        )
    return DocsMediaConfig(source_media, generated_media, published_media, managed, builds)


def _published(root: ArtifactLocation) -> DocsPublishedConfig:
    return DocsPublishedConfig(DocsArtifactConfig(location_child(root, Path("documents"))),
                               DocsArtifactConfig(location_child(root, Path("search/index.json"))))


def _generated(root: ArtifactLocation) -> DocsGeneratedConfig:
    return DocsGeneratedConfig(DocsArtifactConfig(location_child(root, Path("documents"))),
                               DocsArtifactConfig(location_child(root, Path("search/index.json"))))


def _lifecycle(raw: Any, *, field: str) -> DocsCollectionLifecycleConfig | None:
    if raw is None:
        return None
    item = _object(raw, field=field, required={"tool_id", "report_host_doc_id", "report_host_source_revision"})
    if item["tool_id"] not in {COLLECTION_LIFECYCLE_TOOL_ID, HISTORICAL_COLLECTION_LIFECYCLE_TOOL_ID}:
        raise ValueError(f"{field}.tool_id is not a recognised collection creation receipt")
    doc_id = _doc_id(item["report_host_doc_id"], field=f"{field}.report_host_doc_id")
    revision = item["report_host_source_revision"]
    if not isinstance(revision, str) or not SOURCE_REVISION_PATTERN.fullmatch(revision):
        raise ValueError(f"{field}.report_host_source_revision must be a sha256 receipt")
    return DocsCollectionLifecycleConfig(item["tool_id"], doc_id, revision)


def _collections(raw: Any, *, workspace_root: ArtifactLocation, stage: str,
                media_settings: Any, projection: DocsPublicProjectionConfig | None) -> tuple[DocsCollectionConfig, ...]:
    if not isinstance(raw, list):
        raise ValueError(f"stages.{stage}.collections must be an array")
    result = []
    seen = set()
    for index, raw_item in enumerate(raw):
        field = f"stages.{stage}.collections[{index}]"
        item = _object(raw_item, field=field, required={"collection", "title"}, optional={
            "public_title", "supports_return_import", "collection_customisation", "lifecycle",
        })
        child = normalize_collection_id(item["collection"], field=f"{field}.collection")
        if child in seen:
            raise ValueError(f"{field}.collection is duplicated: {child}")
        seen.add(child)
        if not isinstance(item["title"], str) or not isinstance(item.get("public_title", ""), str):
            raise ValueError(f"{field} titles must be strings")
        source_root = location_child(workspace_root, Path(stage) / "source/collections" / child)
        generated_root = location_child(workspace_root, Path(stage) / "generated/collections" / child)
        published_root = location_child(workspace_root, Path("published/collections") / child)
        child_projection = None
        if projection is not None:
            public_media = {}
            for media_type, media in projection.media.items():
                # Public object addresses stay stable across the local directory rename.
                suffix = Path("sub-scopes") / child / "media" / media_type
                public_media[media_type] = DocsPublicMediaConfig(
                    media_type, MEDIA_REFERENCE_ROOT / "collections" / child / media_type,
                    ArtifactLocation(media.location.provider, media.location.path.parent.parent / suffix),
                    media.served_path_prefix.removesuffix(f"/media/{media_type}") + f"/{suffix.as_posix()}",
                )
            child_projection = DocsPublicProjectionConfig(
                DocsArtifactConfig(location_child(projection.documents.location, Path(child))), None, public_media,
            )
        result.append(DocsCollectionConfig(
            collection=child, title=item["title"], public_title=item.get("public_title", item["title"]),
            supports_return_import=_boolean(item.get("supports_return_import", False), field=f"{field}.supports_return_import"),
            collection_customisation=normalize_docs_collection_customisation(item.get("collection_customisation"), field=f"{field}.collection_customisation"),
            lifecycle=_lifecycle(item.get("lifecycle"), field=f"{field}.lifecycle"), stage=stage,
            source=DocsSourceConfig(source_root), generated=_generated(generated_root), published=_published(published_root),
            media=_media(media_settings, source_root=source_root, generated_root=generated_root,
                         published_root=published_root, stage=stage, collection=child),
            public_projection=child_projection,
        ))
    return tuple(result)


def load_docs_workspace_config(repo_root: Path | None = None) -> DocsWorkspaceConfig:
    """Read checked workspace settings and resolve the existing external root.

    Stage paths are derived without creating them. Callers must check the
    selected source/generated/Published artifact before reading or writing it.
    """
    root = repo_root or default_repo_root()
    try:
        raw = json.loads((root / CONFIG_REL_PATH).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid Docs workspace JSON: {exc}") from exc
    payload = _object(raw, field="Docs workspace", required={
        "schema_version", "public_viewer_base_url", "public_projection", "search_fields", "recent_limit", "stages",
    })
    if payload["schema_version"] != SCHEMA_VERSION:
        raise ValueError(f"Docs workspace schema_version must be {SCHEMA_VERSION}")
    public_url = payload["public_viewer_base_url"]
    if not isinstance(public_url, str) or not public_url.startswith("/") or public_url.startswith("//") or not public_url.endswith("/"):
        raise ValueError("public_viewer_base_url must be a site-relative directory URL")
    safe_relative_path(public_url.strip("/"), field="public_viewer_base_url")
    if "?" in public_url or "#" in public_url or public_url == "/docs/":
        raise ValueError("public_viewer_base_url must name a public section without query or fragment")
    fields = _strings(payload["search_fields"], field="search_fields")
    if not fields or set(fields) - SEARCH_FIELDS:
        raise ValueError("search_fields must select supported fields")
    recent_limit = payload["recent_limit"]
    if type(recent_limit) is not int or recent_limit < 1:
        raise ValueError("recent_limit must be a positive integer")
    settings = _object(payload["stages"], field="stages", required=set(STAGES))
    workspace_root = ArtifactLocation(EXTERNAL_LOCAL_PROVIDER, resolve_external_data_root())
    published = _published(location_child(workspace_root, Path("published")))
    projection = _public_projection(payload["public_projection"])
    stages = []
    for stage in STAGES:
        field = f"stages.{stage}"
        item = _object(settings[stage], field=field, required={
            "media", "default_doc_id", "collections", "non_loadable_doc_ids",
            "manage_only_tree_root_ids", "allow_unresolved_parent_ids",
        })
        source_root = location_child(workspace_root, Path(stage) / "source")
        generated_root = location_child(workspace_root, Path(stage) / "generated")
        media = _media(item["media"], source_root=source_root, generated_root=generated_root,
                       published_root=location_child(workspace_root, Path("published")), stage=stage)
        if set(media.types) != set(projection.media):
            raise ValueError(f"{field}.media types must match the public projection")
        stage_projection = projection if stage == "pre-publish" else None
        stages.append(DocsStageConfig(
            workspace_root=workspace_root, stage=stage, source=DocsSourceConfig(source_root),
            generated=_generated(generated_root), media=media, published=published, public_projection=stage_projection,
            default_doc_id=_doc_id(item["default_doc_id"], field=f"{field}.default_doc_id", allow_empty=True),
            non_loadable_doc_ids=_doc_ids(item["non_loadable_doc_ids"], field=f"{field}.non_loadable_doc_ids"),
            manage_only_tree_root_ids=_doc_ids(item["manage_only_tree_root_ids"], field=f"{field}.manage_only_tree_root_ids"),
            allow_unresolved_parent_ids=_boolean(item["allow_unresolved_parent_ids"], field=f"{field}.allow_unresolved_parent_ids"),
            collections=_collections(item["collections"], workspace_root=workspace_root, stage=stage,
                                   media_settings=item["media"], projection=stage_projection), search_fields=fields,
        ))
    return DocsWorkspaceConfig(workspace_root, public_url, projection, published, fields, recent_limit, tuple(stages))


def select_workspace_stage(config: DocsWorkspaceConfig, stage: str | None) -> DocsStageConfig:
    """Select Working or Pre-publish explicitly; never default to another owner."""
    for candidate in config.stages:
        if candidate.stage == stage:
            return candidate
    raise ValueError("stage must be working or pre-publish")


def load_docs_stage(repo_root: Path, stage: str | None) -> DocsStageConfig:
    return select_workspace_stage(load_docs_workspace_config(repo_root), stage)


def require_selected_stage(config: DocsStageConfig | DocsCollectionConfig) -> None:
    if not isinstance(config, (DocsStageConfig, DocsCollectionConfig)) or config.stage not in STAGES:
        raise ValueError("an explicit Working or Pre-publish stage is required")


def require_document_authoring(config: DocsStageConfig | DocsCollectionConfig) -> None:
    require_selected_stage(config)
    if config.stage != "working":
        raise ValueError("document authoring is only available in Working")


def source_container_path(config: DocsStageConfig | DocsCollectionConfig) -> Path:
    require_selected_stage(config)
    return config.source.location.path


def document_source_path(config: DocsStageConfig | DocsCollectionConfig) -> Path:
    return source_container_path(config) / config.source.documents_path


def generated_documents_path(config: DocsStageConfig | DocsCollectionConfig) -> Path:
    require_selected_stage(config)
    return config.generated.documents.location.path


def generated_search_path(config: DocsStageConfig | DocsCollectionConfig) -> Path:
    require_selected_stage(config)
    return config.generated.search.location.path


def published_documents_path(config: DocsWorkspaceConfig | DocsStageConfig | DocsCollectionConfig) -> Path:
    return config.published.documents.location.path


def published_search_path(config: DocsWorkspaceConfig | DocsStageConfig | DocsCollectionConfig) -> Path:
    return config.published.search.location.path


def public_documents_path(config: DocsWorkspaceConfig | DocsStageConfig | DocsCollectionConfig) -> Path | None:
    return config.public_projection.documents.location.path if config.public_projection else None


def public_search_path(config: DocsWorkspaceConfig | DocsStageConfig | DocsCollectionConfig) -> Path | None:
    projection = config.public_projection
    return projection.search.location.path if projection and projection.search else None


def managed_media_config(config: DocsStageConfig | DocsCollectionConfig, media_type: str) -> DocsManagedMediaConfig:
    require_selected_stage(config)
    if media_type not in config.media.types:
        raise ValueError(f"unconfigured media type: {media_type}")
    return config.media.types[media_type]


def load_docs_media_owner(repo_root: Path, stage: str | None, collection: str = "") -> DocsStageConfig | DocsCollectionConfig:
    config = load_docs_stage(repo_root, stage)
    if not collection:
        return config
    for child in config.collections:
        if child.collection == collection:
            return child
    raise ValueError(f"unconfigured collection: {collection}")


def public_media_bindings(config: DocsStageConfig) -> dict[str, tuple[DocsStageConfig | DocsCollectionConfig, DocsPublicMediaConfig]]:
    """Bind media to its exact ordinary/collection owner for public deployment."""
    bindings = {}
    for collection in (config, *config.collections):
        if collection.public_projection is not None:
            child = getattr(collection, "collection", "")
            for media_type, media in collection.public_projection.media.items():
                bindings[f"{child}/{media_type}" if child else media_type] = (collection, media)
    return bindings
