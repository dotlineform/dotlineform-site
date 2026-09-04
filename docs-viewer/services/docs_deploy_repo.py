#!/usr/bin/env python3
"""Deploy one accepted Analysis Published snapshot to configured public outputs."""

from __future__ import annotations

import datetime as dt
import hashlib
import html
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

import docs_catalogue_document_url_follow_through as catalogue_follow_through
import docs_document_publication_lineage as publication_lineage
from docs_catalogue_document_urls import (
    project_catalogue_documents_from_subject_associations,
)
from docs_document_location_projection import (
    build_document_location_payload,
    build_exact_document_location_records,
    document_location_projection_path,
    json_bytes as document_location_json_bytes,
)
from docs_public_media_reconciliation import (
    apply_public_media_reconciliation,
    plan_public_media_reconciliation,
    referenced_public_media,
)
from docs_public_mermaid_payload import public_mermaid_payload_requires_projection
from docs_report_source import REPORT_HOST_HTML
from docs_scope_config import (
    DocsScopeConfig,
    DocsSubScopeConfig,
    load_docs_scope_configs,
    public_documents_path,
    public_search_path,
)
from docs_scope_publish import validate_published_snapshot
from docs_subscope_customisations import (
    sub_scope_customisation_authoring_subject_fields,
)
from docs_write_rebuild import rebuild_sub_scope_outputs


DEPLOY_REPO_PREVIEW_SCHEMA_VERSION = "docs_deploy_repo_preview_v1"
DEPLOYABLE_SCOPE = "analysis"
IGNORED_FILENAMES = frozenset({".DS_Store", ".gitkeep"})
LOCAL_FOLDER_ANCHOR_PATTERN = re.compile(
    r"<a\b(?P<attrs>(?:[^>\"']|\"[^\"]*\"|'[^']*')*)>(?P<label>.*?)</a\s*>",
    re.IGNORECASE | re.DOTALL,
)
HTML_START_TAG_PATTERN = re.compile(
    r"<(?P<body>[A-Za-z][A-Za-z0-9:-]*(?:[^>\"']|\"[^\"]*\"|'[^']*')*)>",
    re.DOTALL,
)
MEDIA_URL_ATTRIBUTE_PATTERN = re.compile(
    r"(?P<prefix>(?<![\w:-])(?:src|href)\s*=\s*)"
    r"(?:(?P<quote>[\"'])(?P<quoted_value>.*?)(?P=quote)|(?P<unquoted_value>[^\s\"'=<>`]+))",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class DeployRepoPlan:
    preview: dict[str, Any]
    config: DocsScopeConfig
    desired_repository_files: Mapping[Path, bytes]
    current_repository_files: Mapping[Path, bytes]
    media_references: Mapping[tuple[str, str], tuple[str, ...]]
    catalogue_plan: Any
    lineage_workflows: tuple[publication_lineage.DocumentLineageWorkflow, ...]
    current_lineages: Mapping[str, publication_lineage.DocumentLineageTable | None]
    desired_lineages: Mapping[str, publication_lineage.DocumentLineageTable | None]


def utc_now() -> str:
    return (
        dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def json_bytes(payload: Any) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def read_json_bytes(data: bytes, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{label} is not valid UTF-8 JSON") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"{label} must be a JSON object")
    return payload


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def plan_revision(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(canonical).hexdigest()}"


def deployable_config(repo_root: Path, value: Any) -> DocsScopeConfig:
    scope = str(value or "").strip().lower()
    if scope != DEPLOYABLE_SCOPE:
        raise ValueError("Deploy Repo is available only for the Analysis scope")
    config = load_docs_scope_configs(repo_root, scope_ids=(scope,)).get(scope)
    if config is None or config.public_projection is None:
        raise ValueError("Analysis has no configured public projection")
    if public_documents_path(config) is None or public_search_path(config) is None:
        raise ValueError("Analysis public documents and Search destinations are required")
    return config


def _writable_repository_destination(
    repo_root: Path,
    relative_path: Path,
    *,
    directory: bool,
) -> bool:
    target = repository_path(repo_root, relative_path)
    if target.is_symlink():
        return False
    if target.exists():
        if directory and not target.is_dir():
            return False
        if not directory and not target.is_file():
            return False
        required = os.W_OK | (os.X_OK if directory else 0)
        return os.access(target, required)

    ancestor = target if directory else target.parent
    resolved_root = repo_root.resolve()
    while not ancestor.exists() and ancestor != resolved_root:
        ancestor = ancestor.parent
    return (
        ancestor.is_dir()
        and not ancestor.is_symlink()
        and os.access(ancestor, os.W_OK | os.X_OK)
    )


def deploy_repo_capability(
    repo_root: Path,
    config: DocsScopeConfig,
) -> dict[str, Any]:
    """Project a browser-safe capability from configured destination authority."""

    unavailable = {
        "available": False,
        "preview": False,
        "apply": False,
        "reason": "Deploy Repo is available only for Analysis.",
    }
    if config.scope_id != DEPLOYABLE_SCOPE:
        return unavailable
    try:
        deployable = deployable_config(repo_root, config.scope_id)
    except (FileNotFoundError, ValueError):
        return {
            **unavailable,
            "reason": "Analysis has no configured repository projection.",
        }

    projection = deployable.public_projection
    if projection is None:
        return {
            **unavailable,
            "reason": "Analysis has no configured repository projection.",
        }
    destinations: list[tuple[Path, bool]] = [
        (projection.documents.location.path, True),
        (projection.search.location.path, False),
        (document_location_projection_path(deployable), False),
    ]
    destinations.extend(
        (sub_scope.public_projection.documents.location.path, True)
        for sub_scope in deployable.sub_scopes
        if sub_scope.public_projection is not None
    )
    destinations.extend(
        (media.location.path, True)
        for media in projection.media.values()
        if media.location.provider == "repository"
    )
    try:
        writable = all(
            _writable_repository_destination(
                repo_root.resolve(),
                path,
                directory=directory,
            )
            for path, directory in destinations
        )
    except ValueError:
        writable = False
    if not writable:
        return {
            **unavailable,
            "reason": "The configured repository projection is unavailable.",
        }
    return {
        "available": True,
        "preview": True,
        "apply": True,
        "reason": "",
    }


def repository_path(repo_root: Path, path: Path) -> Path:
    resolved = (repo_root / path).resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise ValueError(f"repository deployment path escapes the repository: {path}") from exc
    return resolved


def repo_relative(repo_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(f"path escapes the repository: {path}") from exc


def public_url_prefix(path: Path) -> str:
    if not path.parts or path.parts[0] != "site":
        raise ValueError(f"repository public destination must remain beneath site/: {path}")
    remainder = Path(*path.parts[1:]).as_posix()
    return f"/{remainder}" if remainder != "." else "/"


def collection_public_url_prefix(
    collection: DocsScopeConfig | DocsSubScopeConfig,
) -> str:
    path = public_documents_path(collection)
    if path is None:
        raise ValueError("public document collection has no configured destination")
    return public_url_prefix(path)


def project_content_urls(value: Any, prefix: str) -> Any:
    if isinstance(value, list):
        return [project_content_urls(item, prefix) for item in value]
    if not isinstance(value, dict):
        return value
    projected = {
        key: project_content_urls(item, prefix)
        for key, item in value.items()
    }
    doc_id = str(projected.get("doc_id") or "").strip()
    if doc_id and "content_url" in projected:
        projected["content_url"] = f"{prefix}/by-id/{doc_id}.json"
    return projected


def project_public_local_folder_links(content_html: str) -> str:
    def replace(match: re.Match[str]) -> str:
        attrs = match.group("attrs").lower()
        if "data-docs-viewer-local-target" not in attrs and not re.search(
            r"\bhref\s*=\s*(?:[\"']dlf-local:|dlf-local:)",
            attrs,
            re.IGNORECASE,
        ):
            return match.group(0)
        label = html.unescape(re.sub(r"<[^>]*>", "", match.group("label"))).strip()
        if not label or label.startswith("/") or label.lower().startswith(("file:", "dlf-local:")):
            label = "[local file or folder]"
        return html.escape(label)

    return LOCAL_FOLDER_ANCHOR_PATTERN.sub(replace, content_html)


def public_media_url_projection(config: DocsScopeConfig) -> dict[str, str]:
    projection = config.public_projection
    if projection is None:
        return {}
    return {
        f"/docs/published/media/{config.scope_id}/{media_type}":
        projection.media[media_type].served_path_prefix.rstrip("/")
        for media_type in config.media.types
    }


def project_public_media_urls(content_html: str, projection: Mapping[str, str]) -> str:
    def replace_attribute(match: re.Match[str]) -> str:
        quote = match.group("quote") or ""
        value = match.group("quoted_value") if quote else match.group("unquoted_value")
        projected = value
        for published_prefix, public_prefix in projection.items():
            if value == published_prefix:
                projected = public_prefix
                break
            if value.startswith(f"{published_prefix}/"):
                projected = f"{public_prefix}/{value.removeprefix(f'{published_prefix}/')}"
                break
        return f"{match.group('prefix')}{quote}{projected}{quote}"

    def replace_tag(match: re.Match[str]) -> str:
        body = MEDIA_URL_ATTRIBUTE_PATTERN.sub(replace_attribute, match.group("body"))
        return f"<{body}>"

    return HTML_START_TAG_PATTERN.sub(replace_tag, content_html)


def project_public_report_payload(payload: dict[str, Any]) -> None:
    report = payload.get("report")
    if report is None:
        return
    if not isinstance(report, dict):
        raise ValueError("accepted document report must be an object")
    content_html = payload.get("content_html")
    if not isinstance(content_html, str) or content_html.count(REPORT_HOST_HTML) != 1:
        raise ValueError("accepted report document must contain exactly one generated host")
    access = str(report.get("access") or "").strip()
    if access == "public":
        return
    if access != "local":
        raise ValueError(f"accepted document report has invalid access: {access!r}")
    payload.pop("report")
    payload["content_html"] = content_html.replace(REPORT_HOST_HTML, "", 1)


def project_document_payload(
    data: bytes,
    *,
    label: str,
    media_projection: Mapping[str, str],
) -> bytes:
    payload = read_json_bytes(data, label)
    project_public_report_payload(payload)
    content_html = payload.get("content_html")
    if isinstance(content_html, str):
        payload["content_html"] = project_public_media_urls(
            project_public_local_folder_links(content_html),
            media_projection,
        )
    if public_mermaid_payload_requires_projection(payload):
        raise RuntimeError(
            f"{label} requires a public Mermaid projection that is not present in the accepted Published snapshot"
        )
    return json_bytes(payload)


def project_public_search(
    config: DocsScopeConfig,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Project configured public collection names without rebuilding postings."""

    header = payload.get("header")
    docs = payload.get("docs")
    if (
        not isinstance(header, dict)
        or header.get("schema") != "docs_viewer_search_index_v2"
        or header.get("scope") != config.scope_id
        or not isinstance(docs, list)
    ):
        raise ValueError("accepted Search has the wrong schema or scope identity")
    public_titles = {
        sub_scope.sub_scope: sub_scope.public_title
        for sub_scope in config.sub_scopes
        if sub_scope.public_title
    }
    changed = False
    projected_docs: list[Any] = []
    for raw_document in docs:
        if not isinstance(raw_document, dict):
            projected_docs.append(raw_document)
            continue
        document = dict(raw_document)
        sub_scope = str(document.get("sub_scope") or "").strip().lower()
        public_title = public_titles.get(sub_scope, "")
        current_title = str(document.get("collection_title") or "").strip()
        if public_title and current_title and public_title != current_title:
            document["collection_title"] = public_title
            display_meta = str(document.get("display_meta") or "").strip()
            if display_meta == current_title:
                document["display_meta"] = public_title
            elif display_meta.endswith(f" • {current_title}"):
                document["display_meta"] = (
                    display_meta.removesuffix(current_title) + public_title
                )
            changed = True
        projected_docs.append(document)
    if not changed:
        return payload

    projected = {**payload, "docs": projected_docs}
    version_payload = {
        "schema": header["schema"],
        "scope": header["scope"],
        "fields": projected.get("fields", []),
        "docs": projected_docs,
        "terms": projected.get("terms", {}),
    }
    canonical = json.dumps(
        version_payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    version = hashlib.blake2b(canonical, digest_size=64).digest()[:16].hex()
    projected["header"] = {**header, "version": f"blake2b-{version}"}
    return projected


def accepted_document_collections(
    config: DocsScopeConfig,
    published_files: Mapping[Path, bytes],
) -> tuple[
    dict[Path, bytes],
    dict[str, dict[Path, bytes]],
    dict[str, Any],
    dict[str, dict[str, Any]],
    dict[str, Any],
]:
    media_projection = public_media_url_projection(config)
    parent_files: dict[Path, bytes] = {}
    parent_documents: dict[str, dict[str, Any]] = {}
    parent_prefix = collection_public_url_prefix(config)
    index_path = Path("documents/index-tree.json")
    recent_path = Path("documents/recent.json")
    search_path = Path("search/index.json")
    for required in (index_path, recent_path, search_path):
        if required not in published_files:
            raise FileNotFoundError(f"accepted Published snapshot is missing {required.as_posix()}")

    parent_files[Path("index-tree.json")] = json_bytes(
        project_content_urls(
            read_json_bytes(published_files[index_path], "accepted index tree"),
            parent_prefix,
        )
    )
    parent_files[Path("recent.json")] = json_bytes(
        project_content_urls(
            read_json_bytes(published_files[recent_path], "accepted Recent"),
            parent_prefix,
        )
    )
    for relative_path, data in published_files.items():
        if (
            len(relative_path.parts) == 3
            and relative_path.parts[:2] == ("documents", "by-id")
            and relative_path.suffix == ".json"
        ):
            projected = project_document_payload(
                data,
                label=f"accepted parent document {relative_path.stem}",
                media_projection=media_projection,
            )
            parent_files[Path("by-id") / relative_path.name] = projected
            parent_documents[relative_path.stem] = read_json_bytes(
                projected,
                f"projected parent document {relative_path.stem}",
            )

    sub_scope_files: dict[str, dict[Path, bytes]] = {}
    sub_scope_manifests: dict[str, dict[str, Any]] = {}
    subject_associations: dict[tuple[str, str], Mapping[str, Any]] = {}
    for sub_scope in config.sub_scopes:
        prefix = Path("documents/sub-scopes") / sub_scope.sub_scope
        files: dict[Path, bytes] = {}
        for relative_path, data in published_files.items():
            try:
                collection_relative = relative_path.relative_to(prefix)
            except ValueError:
                continue
            if collection_relative == Path("subject-associations.json"):
                subject_associations[(config.scope_id, sub_scope.sub_scope)] = read_json_bytes(
                    data,
                    f"accepted subject associations {config.scope_id}/{sub_scope.sub_scope}",
                )
                continue
            if (
                len(collection_relative.parts) == 2
                and collection_relative.parts[0] == "by-id"
                and collection_relative.suffix == ".json"
            ):
                files[collection_relative] = project_document_payload(
                    data,
                    label=(
                        f"accepted document {config.scope_id}/{sub_scope.sub_scope}/"
                        f"{collection_relative.stem}"
                    ),
                    media_projection=media_projection,
                )
            else:
                files[collection_relative] = data
        manifest_bytes = files.get(Path("manifest.json"))
        if manifest_bytes is None:
            raise FileNotFoundError(
                f"accepted Published snapshot is missing {prefix.as_posix()}/manifest.json"
            )
        sub_scope_files[sub_scope.sub_scope] = files
        sub_scope_manifests[sub_scope.sub_scope] = read_json_bytes(
            manifest_bytes,
            f"accepted sub-scope manifest {sub_scope.sub_scope}",
        )
        if (
            sub_scope_customisation_authoring_subject_fields(
                sub_scope.sub_scope_customisation
            )
            and (config.scope_id, sub_scope.sub_scope) not in subject_associations
        ):
            raise FileNotFoundError(
                f"accepted Published snapshot is missing deployment subject associations for "
                f"{config.scope_id}/{sub_scope.sub_scope}"
            )

    search_payload = project_public_search(
        config,
        read_json_bytes(published_files[search_path], "accepted Search"),
    )
    _validate_complete_document_set(
        search_payload,
        parent_documents,
        sub_scope_files,
        sub_scope_manifests,
    )
    return (
        parent_files,
        sub_scope_files,
        search_payload,
        sub_scope_manifests,
        subject_associations,
    )


def _validate_complete_document_set(
    search_payload: Mapping[str, Any],
    parent_documents: Mapping[str, Any],
    sub_scope_files: Mapping[str, Mapping[Path, bytes]],
    sub_scope_manifests: Mapping[str, Mapping[str, Any]],
) -> None:
    raw_search_docs = search_payload.get("docs")
    if not isinstance(raw_search_docs, list):
        raise ValueError("accepted Search docs must be an array")
    search_ids = {
        str(row.get("id") or "").strip()
        for row in raw_search_docs
        if isinstance(row, Mapping) and str(row.get("id") or "").strip()
    }
    accepted_ids = set(parent_documents)
    for sub_scope, files in sub_scope_files.items():
        by_id_ids = {
            path.stem
            for path in files
            if len(path.parts) == 2 and path.parts[0] == "by-id" and path.suffix == ".json"
        }
        raw_manifest_docs = sub_scope_manifests[sub_scope].get("docs")
        if not isinstance(raw_manifest_docs, list):
            raise ValueError(f"accepted sub-scope manifest {sub_scope} docs must be an array")
        manifest_ids = {
            str(row.get("doc_id") or "").strip()
            for row in raw_manifest_docs
            if isinstance(row, Mapping) and str(row.get("doc_id") or "").strip()
        }
        if by_id_ids != manifest_ids:
            raise RuntimeError(
                f"accepted {sub_scope} manifest and by-ID document identities do not match"
            )
        accepted_ids.update(by_id_ids)
    if search_ids != accepted_ids:
        raise RuntimeError("accepted Search and document identities do not match")


def desired_repository_projection(
    repo_root: Path,
    config: DocsScopeConfig,
    published_files: Mapping[Path, bytes],
) -> tuple[
    dict[Path, bytes],
    dict[tuple[str, str], tuple[str, ...]],
    list[dict[str, str]],
    Mapping[str, Mapping[str, list[str]]],
]:
    (
        parent_files,
        sub_scope_files,
        search_payload,
        sub_scope_manifests,
        subject_associations,
    ) = accepted_document_collections(config, published_files)
    parent_root_path = public_documents_path(config)
    search_target_path = public_search_path(config)
    if parent_root_path is None or search_target_path is None:
        raise ValueError("Analysis public documents and Search destinations are required")
    parent_root = repository_path(repo_root, parent_root_path)
    desired: dict[Path, bytes] = {
        parent_root / relative_path: data
        for relative_path, data in parent_files.items()
    }
    configured_sub_scopes = {item.sub_scope: item for item in config.sub_scopes}
    for sub_scope_id, files in sub_scope_files.items():
        sub_scope_path = public_documents_path(configured_sub_scopes[sub_scope_id])
        if sub_scope_path is None:
            raise ValueError(f"Analysis/{sub_scope_id} has no public destination")
        sub_scope_root = repository_path(repo_root, sub_scope_path)
        desired.update(
            {sub_scope_root / relative_path: data for relative_path, data in files.items()}
        )
    search_target = repository_path(repo_root, search_target_path)
    desired[search_target] = json_bytes(search_payload)

    exact_locations = build_exact_document_location_records(
        config,
        search_payload=search_payload,
        parent_documents={
            path.stem: read_json_bytes(data, f"projected parent document {path.stem}")
            for path, data in parent_files.items()
            if len(path.parts) == 2 and path.parts[0] == "by-id"
        },
        sub_scope_manifests=sub_scope_manifests,
    )
    location_payload = build_document_location_payload(
        config,
        search_payload=search_payload,
        parent_documents={
            path.stem: read_json_bytes(data, f"projected parent document {path.stem}")
            for path, data in parent_files.items()
            if len(path.parts) == 2 and path.parts[0] == "by-id"
        },
        sub_scope_manifests=sub_scope_manifests,
    )
    location_target = repository_path(
        repo_root,
        document_location_projection_path(config),
    )
    desired[location_target] = document_location_json_bytes(location_payload)

    payload_collections: list[tuple[str, Mapping[Path, bytes]]] = [
        (config.scope_id, parent_files),
        *[
            (f"{config.scope_id}/{sub_scope}", files)
            for sub_scope, files in sorted(sub_scope_files.items())
        ],
    ]
    media_references = referenced_public_media(config, payload_collections)
    catalogue_projection = project_catalogue_documents_from_subject_associations(
        exact_locations=exact_locations,
        subject_associations_by_collection=subject_associations,
    )
    return desired, media_references, exact_locations, catalogue_projection


def iter_managed_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        return ()
    return (
        path
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.name not in IGNORED_FILENAMES
    )


def current_repository_projection(
    repo_root: Path,
    config: DocsScopeConfig,
) -> dict[Path, bytes]:
    parent_path = public_documents_path(config)
    search_path = public_search_path(config)
    if parent_path is None or search_path is None:
        raise ValueError("Analysis public documents and Search destinations are required")
    parent_root = repository_path(repo_root, parent_path)
    excluded_roots = [
        repository_path(repo_root, public_documents_path(sub_scope) or Path("."))
        for sub_scope in config.sub_scopes
    ]
    excluded_roots.extend(
        repository_path(repo_root, media.location.path)
        for media in (config.public_projection.media.values() if config.public_projection else ())
        if media.location.provider == "repository"
    )
    current: dict[Path, bytes] = {}
    for path in iter_managed_files(parent_root):
        if any(path == excluded or path.is_relative_to(excluded) for excluded in excluded_roots):
            continue
        current[path] = path.read_bytes()
    for sub_scope in config.sub_scopes:
        sub_scope_path = public_documents_path(sub_scope)
        if sub_scope_path is None:
            continue
        sub_scope_root = repository_path(repo_root, sub_scope_path)
        current.update({path: path.read_bytes() for path in iter_managed_files(sub_scope_root)})
    search_target = repository_path(repo_root, search_path)
    if search_target.is_file():
        current[search_target] = search_target.read_bytes()
    location_target = repository_path(repo_root, document_location_projection_path(config))
    if location_target.is_file():
        current[location_target] = location_target.read_bytes()
    return current


def repository_diff(
    repo_root: Path,
    current: Mapping[Path, bytes],
    desired: Mapping[Path, bytes],
) -> dict[str, Any]:
    current_paths = set(current)
    desired_paths = set(desired)
    added = desired_paths - current_paths
    removed = current_paths - desired_paths
    changed = {
        path for path in current_paths & desired_paths if current[path] != desired[path]
    }
    unchanged = (current_paths & desired_paths) - changed

    def rows(paths: Iterable[Path], action: str) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for path in sorted(paths):
            data = desired.get(path, current.get(path, b""))
            result.append(
                {
                    "path": repo_relative(repo_root, path),
                    "action": action,
                    "size": len(data),
                    "sha256": sha256_bytes(data),
                }
            )
        return result

    changes = [
        *rows(added, "add"),
        *rows(changed, "change"),
        *rows(removed, "remove"),
    ]
    return {
        "changes": sorted(changes, key=lambda row: row["path"]),
        "added_count": len(added),
        "changed_count": len(changed),
        "removed_count": len(removed),
        "unchanged_count": len(unchanged),
        "file_count": len(desired),
    }


def lineage_projections(
    exact_locations: Iterable[Mapping[str, Any]],
    workflows: Iterable[publication_lineage.DocumentLineageWorkflow],
    current: Mapping[str, publication_lineage.DocumentLineageTable | None],
) -> dict[str, publication_lineage.DocumentLineageTable | None]:
    locations = tuple(exact_locations)
    desired: dict[str, publication_lineage.DocumentLineageTable | None] = {}
    for workflow in workflows:
        table = current[workflow.contract_id]
        if table is None:
            desired[workflow.contract_id] = None
            continue
        editorial = workflow.editorial_collection
        publication_urls = {
            str(record.get("doc_id") or "").strip(): str(record.get("url") or "").strip()
            for record in locations
            if str(record.get("scope_id") or "").strip() == editorial.scope
            and str(record.get("sub_scope") or "").strip().lower() == editorial.sub_scope
            and str(record.get("doc_id") or "").strip()
            and str(record.get("url") or "").strip()
        }
        desired[workflow.contract_id] = publication_lineage.project_publications(
            table,
            editorial_scope=editorial.scope,
            editorial_sub_scope=editorial.sub_scope,
            publication_urls=publication_urls,
        )
    return desired


def lineage_preview(
    workflows: Iterable[publication_lineage.DocumentLineageWorkflow],
    current: Mapping[str, publication_lineage.DocumentLineageTable | None],
    desired: Mapping[str, publication_lineage.DocumentLineageTable | None],
) -> dict[str, Any]:
    records = []
    for workflow in workflows:
        current_table = current[workflow.contract_id]
        desired_table = desired[workflow.contract_id]
        current_bytes = (
            publication_lineage.render_table(current_table)
            if current_table is not None
            else b""
        )
        desired_bytes = (
            publication_lineage.render_table(desired_table)
            if desired_table is not None
            else b""
        )
        records.append(
            {
                "contract_id": workflow.contract_id,
                "path": (
                    f"{workflow.working_collection.scope}/"
                    f"{workflow.working_collection.sub_scope}/data/"
                    f"{publication_lineage.LINEAGE_FILENAME}"
                ),
                "working_collection": workflow.working_collection.payload(),
                "editorial_collection": workflow.editorial_collection.payload(),
                "changed": current_bytes != desired_bytes,
                "current_sha256": (
                    sha256_bytes(current_bytes) if current_bytes else ""
                ),
                "desired_sha256": (
                    sha256_bytes(desired_bytes) if desired_bytes else ""
                ),
            }
        )
    return {
        "changed": any(record["changed"] for record in records),
        "changed_count": sum(int(record["changed"]) for record in records),
        "workflows": records,
    }


def catalogue_preview(repo_root: Path, plan: Any) -> dict[str, Any]:
    paths = [
        {
            "path": repo_relative(repo_root, path),
            "sha256": sha256_bytes(json_bytes(payload)),
        }
        for path, payload in sorted(plan.payloads_by_path.items())
    ]
    return {
        "affected_targets": [
            {"kind": kind, "key": key} for kind, key in plan.affected_targets
        ],
        "changed_paths": paths,
        "changed_count": len(paths),
    }


def build_deploy_repo_plan(
    repo_root: Path,
    body: Mapping[str, Any],
    *,
    client: object | None = None,
    env_files: Iterable[Path] | None = None,
    environ: Mapping[str, str] | None = None,
) -> DeployRepoPlan:
    repo_root = repo_root.resolve()
    config = deployable_config(repo_root, body.get("scope"))
    manifest, _published_root, published_files = validate_published_snapshot(
        repo_root,
        config.scope_id,
    )
    timestamp = str(body.get("deployment_timestamp") or "").strip() or utc_now()
    desired, media_references, exact_locations, catalogue_projection = (
        desired_repository_projection(repo_root, config, published_files)
    )
    current = current_repository_projection(repo_root, config)
    repository = repository_diff(repo_root, current, desired)
    media = plan_public_media_reconciliation(
        repo_root,
        config,
        media_references,
        client=client,
        env_files=env_files,
        environ=environ,
    )
    if catalogue_follow_through.CATALOGUE_SITE_PROJECTION_PAUSED:
        catalogue_plan = None
        catalogue = catalogue_follow_through.paused_result()
        catalogue_summary = "Catalogue paused"
    else:
        from catalogue.catalogue_document_url_refresh import (
            build_catalogue_document_url_refresh_plan,
        )

        catalogue_plan = build_catalogue_document_url_refresh_plan(
            repo_root,
            catalogue_projection,
            generated_at_utc=timestamp,
        )
        catalogue = catalogue_preview(repo_root, catalogue_plan)
        catalogue_summary = f"{catalogue['changed_count']} Catalogue change"
    lineage_workflows = tuple(
        workflow
        for workflow in publication_lineage.configured_workflows(repo_root)
        if workflow.editorial_collection.scope == config.scope_id
    )
    current_lineages = publication_lineage.load_tables(repo_root)
    desired_lineages = lineage_projections(
        exact_locations,
        lineage_workflows,
        current_lineages,
    )
    lineage = lineage_preview(
        lineage_workflows,
        current_lineages,
        desired_lineages,
    )
    plan_basis = {
        "scope": config.scope_id,
        "published_revision": manifest["published_revision"],
        "deployment_timestamp": timestamp,
        "repository": repository,
        "media": media,
        "catalogue": catalogue,
        "lineage": lineage,
    }
    revision = plan_revision(plan_basis)
    change_count = (
        repository["added_count"]
        + repository["changed_count"]
        + repository["removed_count"]
        + int(media.get("copy_count") or 0)
        + int(media.get("remove_count") or 0)
        + catalogue["changed_count"]
        + int(lineage["changed_count"])
    )
    preview = {
        "ok": True,
        "schema_version": DEPLOY_REPO_PREVIEW_SCHEMA_VERSION,
        "operation": "preview",
        "scope": config.scope_id,
        "published_revision": manifest["published_revision"],
        "deployment_timestamp": timestamp,
        "plan_revision": revision,
        "repository": repository,
        "media": media,
        "catalogue_document_urls": catalogue,
        "publication_lineage": lineage,
        "document_count": len(exact_locations),
        "change_count": change_count,
        "error_count": int(media.get("error_count") or 0),
        "up_to_date": change_count == 0 and int(media.get("error_count") or 0) == 0,
        "summary_text": (
            f"Deploy Repo preview for {config.scope_id} at {manifest['published_revision']}: "
            f"{repository['added_count']} repository add, "
            f"{repository['changed_count']} change, {repository['removed_count']} remove; "
            f"{media.get('copy_count', 0)} media copy, {media.get('remove_count', 0)} remove; "
            f"{catalogue_summary}; "
            f"{lineage['changed_count']} lineage change"
            f"{'s' if lineage['changed_count'] != 1 else ''}."
        ),
    }
    return DeployRepoPlan(
        preview=preview,
        config=config,
        desired_repository_files=desired,
        current_repository_files=current,
        media_references=media_references,
        catalogue_plan=catalogue_plan,
        lineage_workflows=lineage_workflows,
        current_lineages=current_lineages,
        desired_lineages=desired_lineages,
    )


def preview_deploy_repo(
    repo_root: Path,
    body: dict[str, Any],
    *,
    client: object | None = None,
    env_files: Iterable[Path] | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    return build_deploy_repo_plan(
        repo_root,
        body,
        client=client,
        env_files=env_files,
        environ=environ,
    ).preview


def apply_repository_projection(repo_root: Path, plan: DeployRepoPlan) -> None:
    desired = plan.desired_repository_files
    current = plan.current_repository_files
    for path in sorted(set(current) - set(desired)):
        if path.is_symlink():
            raise ValueError(f"repository deployment target must not be a symlink: {repo_relative(repo_root, path)}")
        path.unlink(missing_ok=True)
    for path in sorted(desired):
        expected = desired[path]
        if current.get(path) == expected:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.is_symlink():
            raise ValueError(f"repository deployment target must not be a symlink: {repo_relative(repo_root, path)}")
        path.write_bytes(expected)
    actual = current_repository_projection(repo_root, plan.config)
    if set(actual) != set(desired):
        raise RuntimeError("repository deployment file set did not verify")
    for path, expected in desired.items():
        if actual[path] != expected:
            raise RuntimeError(f"repository deployment bytes did not verify: {repo_relative(repo_root, path)}")


def apply_deploy_repo(
    repo_root: Path,
    body: dict[str, Any],
    *,
    client: object | None = None,
    env_files: Iterable[Path] | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    if body.get("confirm") is not True:
        raise ValueError("confirm must be true to Deploy Repo")
    timestamp = str(body.get("deployment_timestamp") or "").strip()
    if not timestamp:
        raise ValueError("deployment_timestamp must match the reviewed Deploy Repo preview")
    plan = build_deploy_repo_plan(
        repo_root,
        body,
        client=client,
        env_files=env_files,
        environ=environ,
    )
    preview = plan.preview
    if body.get("published_revision") != preview["published_revision"]:
        raise ValueError("accepted Published revision does not match the reviewed Deploy Repo preview")
    if body.get("plan_revision") != preview["plan_revision"]:
        raise ValueError("Deploy Repo preview is stale; preview again")

    apply_repository_projection(repo_root.resolve(), plan)
    media = apply_public_media_reconciliation(
        repo_root.resolve(),
        plan.config,
        plan.media_references,
        client=client,
        env_files=env_files,
        environ=environ,
    )

    catalogue_error = ""
    catalogue_written: list[str] = []
    if catalogue_follow_through.CATALOGUE_SITE_PROJECTION_PAUSED:
        catalogue_status = "paused"
    else:
        from catalogue.catalogue_document_url_refresh import (
            apply_catalogue_document_url_refresh_plan,
        )

        try:
            catalogue_result = apply_catalogue_document_url_refresh_plan(plan.catalogue_plan)
            catalogue_written = [
                repo_relative(repo_root.resolve(), path)
                for path in catalogue_result.written_paths
            ]
        except Exception as exc:
            catalogue_error = str(exc)
        catalogue_status = "stale" if catalogue_error else ("updated" if catalogue_written else "unchanged")

    lineage_results = []
    for workflow in plan.lineage_workflows:
        current_lineage = plan.current_lineages[workflow.contract_id]
        desired_lineage = plan.desired_lineages[workflow.contract_id]
        lineage_status = "unchanged"
        lineage_error = ""
        rebuild_status = "not_required"
        rebuild_error = ""
        if desired_lineage is not None and desired_lineage != current_lineage:
            rebuild_status = "not_run"
            try:
                publication_lineage.write_table_atomic(
                    repo_root.resolve(),
                    desired_lineage,
                    contract_id=workflow.contract_id,
                )
                lineage_status = "updated"
            except Exception as exc:
                lineage_status = "stale"
                lineage_error = str(exc)
            else:
                try:
                    rebuild_sub_scope_outputs(
                        repo_root.resolve(),
                        workflow.working_collection.scope,
                        workflow.working_collection.sub_scope,
                    )
                    rebuild_status = "updated"
                except Exception as exc:
                    rebuild_status = "stale"
                    rebuild_error = str(exc)
        lineage_results.append(
            {
                "contract_id": workflow.contract_id,
                "status": lineage_status,
                "error": lineage_error,
                "working_rebuild": {
                    "status": rebuild_status,
                    "error": rebuild_error,
                },
            }
        )

    lineage_errors = sum(
        int(bool(record["error"]))
        + int(bool(record["working_rebuild"]["error"]))
        for record in lineage_results
    )
    lineage_status = (
        "stale"
        if any(record["error"] for record in lineage_results)
        else "updated"
        if any(record["status"] == "updated" for record in lineage_results)
        else "unchanged"
    )

    error_count = (
        int(media.get("error_count") or 0)
        + int(bool(catalogue_error))
        + lineage_errors
    )
    result = dict(preview)
    result.update(
        {
            "operation": "apply",
            "applied": True,
            "complete": error_count == 0,
            "error_count": error_count,
            "media": media,
            "catalogue_document_urls": {
                **preview["catalogue_document_urls"],
                "status": catalogue_status,
                "updated_paths": catalogue_written,
                "error": catalogue_error,
            },
            "publication_lineage": {
                **preview["publication_lineage"],
                "status": lineage_status,
                "workflows": [
                    {
                        **preview_record,
                        **next(
                            record
                            for record in lineage_results
                            if record["contract_id"]
                            == preview_record["contract_id"]
                        ),
                    }
                    for preview_record in preview["publication_lineage"]["workflows"]
                ],
            },
            "summary_text": (
                f"Deployed accepted Analysis revision {preview['published_revision']} to the repository projection. "
                f"Media: {media.get('copied_count', 0)} copied, {media.get('removed_count', 0)} removed, "
                f"{media.get('error_count', 0)} errors. "
                f"Catalogue: {catalogue_status}. "
                f"Lineage: {lineage_status}; "
                f"{sum(int(record['working_rebuild']['status'] == 'updated') for record in lineage_results)} "
                "Working rebuilds updated."
            ),
        }
    )
    return result


__all__ = [
    "DEPLOY_REPO_PREVIEW_SCHEMA_VERSION",
    "DEPLOYABLE_SCOPE",
    "apply_deploy_repo",
    "build_deploy_repo_plan",
    "deploy_repo_capability",
    "preview_deploy_repo",
    "project_document_payload",
]
