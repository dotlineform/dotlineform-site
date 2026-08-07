#!/usr/bin/env python3
"""Publish working public-scope Docs Viewer payloads to public snapshots."""

from __future__ import annotations

import filecmp
import html
import json
import re
import shutil
from pathlib import Path
from typing import Any

from docs_scope_config import (
    DocsScopeConfig,
    DocsSubScopeConfig,
    is_public_readonly_scope,
    load_docs_scope_configs,
    public_documents_path,
    public_search_path,
    published_documents_path,
    published_search_path,
    resolve_location_path,
    resolve_scope_path,
)
from docs_public_mermaid_payload import (
    load_prepared_public_mermaid_projection,
    project_public_mermaid_payload,
    public_mermaid_payload_requires_projection,
    public_mermaid_variant_files,
)
from docs_document_location_projection import (
    SUPPORTED_DOCUMENT_LOCATION_SCOPE_IDS,
    build_document_location_payload,
    document_location_projection_path,
    json_bytes as document_location_json_bytes,
)


PUBLISH_SCHEMA_VERSION = "docs_publish_gate_v1"
MANAGE_MANIFEST_PATH = Path("manage-manifest.json")
LOCAL_FOLDER_ANCHOR_PATTERN = re.compile(r"<a\b(?P<attrs>(?:[^>\"']|\"[^\"]*\"|'[^']*')*)>(?P<label>.*?)</a\s*>", re.IGNORECASE | re.DOTALL)


def repo_relative(repo_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(f"path escapes repo root: {path}") from exc


def normalize_scope(repo_root: Path, value: Any) -> tuple[str, DocsScopeConfig]:
    scope = str(value or "").strip().lower()
    if not scope:
        raise ValueError("scope is required")
    configs = load_docs_scope_configs(repo_root)
    config = configs.get(scope)
    if config is None:
        raise ValueError(f"unsupported docs scope: {scope}")
    if not is_public_readonly_scope(
        viewer_base_url=config.viewer_base_url,
        include_scope_param=config.include_scope_param,
    ):
        raise ValueError(f"scope {scope!r} is not a public read-only scope")
    return scope, config


def validate_publish_paths(repo_root: Path, config: DocsScopeConfig) -> dict[str, Path]:
    paths = {
        "working_docs_root": resolve_scope_path(repo_root, published_documents_path(config)),
        "working_search_index": resolve_scope_path(repo_root, published_search_path(config)),
        "published_docs_root": (repo_root / (public_documents_path(config) or Path("."))).resolve(),
        "published_search_index": (repo_root / (public_search_path(config) or Path("."))).resolve(),
    }
    if public_documents_path(config) is None or public_search_path(config) is None:
        raise ValueError(f"scope {config.scope_id!r} has no public projection")
    for label, path in paths.items():
        repo_relative(repo_root, path)
    if paths["working_docs_root"] == paths["published_docs_root"]:
        raise ValueError("working docs root and published docs root must be separate")
    if paths["working_search_index"] == paths["published_search_index"]:
        raise ValueError("working search index and published search index must be separate")
    if not paths["working_docs_root"].is_dir():
        raise FileNotFoundError(f"working docs output not found: {repo_relative(repo_root, paths['working_docs_root'])}")
    if not paths["working_search_index"].is_file():
        raise FileNotFoundError(f"working search output not found: {repo_relative(repo_root, paths['working_search_index'])}")
    return paths


def validate_sub_scope_publish_paths(repo_root: Path, config: DocsScopeConfig) -> dict[str, dict[str, Path]]:
    paths_by_sub_scope: dict[str, dict[str, Path]] = {}
    for sub_scope in config.sub_scopes:
        paths = {
            "working_docs_root": resolve_scope_path(repo_root, published_documents_path(sub_scope)),
            "published_docs_root": (
                repo_root / (public_documents_path(sub_scope) or Path("."))
            ).resolve(),
        }
        if public_documents_path(sub_scope) is None:
            raise ValueError(f"sub-scope {sub_scope.sub_scope} has no public projection")
        for label, path in paths.items():
            repo_relative(repo_root, path)
        if paths["working_docs_root"] == paths["published_docs_root"]:
            raise ValueError(f"sub-scope {sub_scope.sub_scope} working docs root and published docs root must be separate")
        if not paths["working_docs_root"].is_dir():
            raise FileNotFoundError(
                f"sub-scope {sub_scope.sub_scope} working docs output not found: "
                f"{repo_relative(repo_root, paths['working_docs_root'])}"
            )
        manifest_path = paths["working_docs_root"] / "manifest.json"
        if not manifest_path.is_file():
            raise FileNotFoundError(
                f"sub-scope {sub_scope.sub_scope} manifest not found: "
                f"{repo_relative(repo_root, manifest_path)}"
            )
        paths_by_sub_scope[sub_scope.sub_scope] = paths
    return paths_by_sub_scope


def iter_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*") if path.is_file())


def json_bytes(payload: Any) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def clean_doc_id(value: Any) -> str:
    return str(value or "").strip()


def flatten_tree_docs(rows: Any, *, parent_id: str = "") -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    if not isinstance(rows, list):
        return docs
    for row in rows:
        if not isinstance(row, dict):
            continue
        doc_id = clean_doc_id(row.get("doc_id"))
        if not doc_id:
            continue
        item = dict(row)
        item["_parent_id"] = parent_id
        docs.append(item)
        docs.extend(flatten_tree_docs(row.get("children"), parent_id=doc_id))
    return docs


def hidden_doc_ids_from_tree(index_tree: dict[str, Any]) -> set[str]:
    rows = flatten_tree_docs(index_tree.get("docs"))
    roots = {
        clean_doc_id(value)
        for value in (index_tree.get("viewer_options") or {}).get("manage_only_tree_root_ids", [])
    }
    roots.update(clean_doc_id(row.get("doc_id")) for row in rows if row.get("publishable") is False)
    roots.discard("")
    by_parent: dict[str, list[str]] = {}
    for row in rows:
        doc_id = clean_doc_id(row.get("doc_id"))
        parent_id = clean_doc_id(row.get("_parent_id"))
        if doc_id and parent_id:
            by_parent.setdefault(parent_id, []).append(doc_id)
    hidden = set(roots)
    queue = list(roots)
    while queue:
        current = queue.pop(0)
        for child_id in by_parent.get(current, []):
            if child_id in hidden:
                continue
            hidden.add(child_id)
            queue.append(child_id)
    return hidden


def public_tree_node(row: Any, hidden_doc_ids: set[str]) -> dict[str, Any] | None:
    if not isinstance(row, dict):
        return None
    doc_id = clean_doc_id(row.get("doc_id"))
    if not doc_id or doc_id in hidden_doc_ids:
        return None
    node = {
        key: value
        for key, value in row.items()
        if key not in {"children", "publishable"}
    }
    children = [
        child
        for child in (public_tree_node(child, hidden_doc_ids) for child in row.get("children", []))
        if child is not None
    ]
    if children:
        node["children"] = children
    return node


def public_index_tree_payload(payload: Any, hidden_doc_ids: set[str]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return payload
    rows = [
        row
        for row in (public_tree_node(row, hidden_doc_ids) for row in payload.get("docs", []))
        if row is not None
    ]
    return {**payload, "docs": rows}


def doc_id_for_by_id_path(relative_path: Path) -> str:
    if len(relative_path.parts) == 2 and relative_path.parts[0] == "by-id" and relative_path.suffix == ".json":
        return relative_path.stem
    return ""


def manifest_doc_ids(working_root: Path) -> set[str] | None:
    manifest_path = working_root / "manifest.json"
    if not manifest_path.is_file():
        return None
    rows = read_json(manifest_path).get("docs")
    if not isinstance(rows, list):
        return None
    return {
        doc_id
        for row in rows
        if isinstance(row, dict)
        for doc_id in [clean_doc_id(row.get("doc_id"))]
        if doc_id
    }


def project_public_local_folder_links(content_html: str) -> str:
    def replace(match: re.Match[str]) -> str:
        attrs = match.group("attrs").lower()
        if "data-docs-viewer-local-target" not in attrs and not re.search(r"\bhref\s*=\s*(?:[\"']dlf-local:|dlf-local:)", attrs, re.IGNORECASE):
            return match.group(0)
        label = html.unescape(re.sub(r"<[^>]*>", "", match.group("label"))).strip()
        if not label or label.startswith("/") or label.lower().startswith(("file:", "dlf-local:")):
            label = "[local file or folder]"
        return html.escape(label)

    return LOCAL_FOLDER_ANCHOR_PATTERN.sub(replace, content_html)


def publishable_docs_files(
    working_root: Path,
    published_root: Path,
    *,
    projection_scope: str = "",
    require_publication_recent: bool = False,
) -> dict[Path, bytes]:
    index_tree_path = working_root / "index-tree.json"
    hidden_doc_ids: set[str] = set()
    if index_tree_path.exists():
        hidden_doc_ids = hidden_doc_ids_from_tree(read_json(index_tree_path))
    listed_manifest_doc_ids = (
        None
        if index_tree_path.exists()
        else manifest_doc_ids(working_root)
    )
    publication_recent_path = working_root / ".publish/recent.json"
    if require_publication_recent and not publication_recent_path.is_file():
        raise FileNotFoundError(f"working publication Recent projection not found: {publication_recent_path}")
    mermaid_projection = load_prepared_public_mermaid_projection(
        working_root,
        scope=projection_scope,
    )
    used_mermaid_projection_ids: set[str] = set()

    files: dict[Path, bytes] = {}
    for source_path in iter_files(working_root):
        relative_path = source_path.relative_to(working_root)
        if relative_path == MANAGE_MANIFEST_PATH:
            continue
        if relative_path.parts and relative_path.parts[0] == ".publish":
            continue
        if relative_path.parts and relative_path.parts[0] in {"references", "semantic-tokens"}:
            continue
        by_id_doc_id = doc_id_for_by_id_path(relative_path)
        if by_id_doc_id and by_id_doc_id in hidden_doc_ids:
            continue
        if (
            by_id_doc_id
            and listed_manifest_doc_ids is not None
            and by_id_doc_id not in listed_manifest_doc_ids
        ):
            continue
        if relative_path == Path("index-tree.json"):
            files[relative_path] = json_bytes(public_index_tree_payload(read_json(source_path), hidden_doc_ids))
            continue
        if relative_path == Path("recent.json"):
            if publication_recent_path.is_file():
                files[relative_path] = publication_recent_path.read_bytes()
            else:
                files[relative_path] = source_path.read_bytes()
            continue
        if by_id_doc_id:
            payload = read_json(source_path)
            payload_changed = False
            content_html = payload.get("content_html") if isinstance(payload, dict) else None
            if isinstance(content_html, str):
                projected_html = project_public_local_folder_links(content_html)
                payload_changed = projected_html != content_html
                payload["content_html"] = projected_html
            records = mermaid_projection.records_by_doc_id.get(by_id_doc_id, ())
            if records or public_mermaid_payload_requires_projection(payload):
                payload, used_projection_ids = project_public_mermaid_payload(
                    payload,
                    doc_id=by_id_doc_id,
                    records=records,
                )
                used_mermaid_projection_ids.update(used_projection_ids)
                payload_changed = True
            files[relative_path] = json_bytes(payload) if payload_changed else source_path.read_bytes()
            continue
        files[relative_path] = source_path.read_bytes()

    mermaid_variant_files = public_mermaid_variant_files(
        mermaid_projection,
        used_projection_ids=frozenset(used_mermaid_projection_ids),
    )
    collisions = sorted(set(files) & set(mermaid_variant_files))
    if collisions:
        raise RuntimeError(
            "public Mermaid projection refuses existing public file identities: "
            + ", ".join(path.as_posix() for path in collisions)
        )
    files.update(mermaid_variant_files)
    return files


def media_relative_prefixes(repo_root: Path, config: DocsScopeConfig, root: Path) -> tuple[Path, ...]:
    resolved_root = root.resolve()
    prefixes: list[Path] = []
    for media in config.published.media.values():
        try:
            media_root = resolve_location_path(repo_root, media.location).resolve()
        except ValueError:
            continue
        if media_root != resolved_root and path_is_relative_to(media_root, resolved_root):
            prefixes.append(media_root.relative_to(resolved_root))
    return tuple(sorted(set(prefixes)))


def sub_scope_relative_prefixes(
    repo_root: Path,
    config: DocsScopeConfig,
    root: Path,
) -> tuple[Path, ...]:
    resolved_root = root.resolve()
    prefixes: list[Path] = []
    for sub_scope in config.sub_scopes:
        locations = [sub_scope.published.documents.location]
        if sub_scope.public_projection is not None:
            locations.append(sub_scope.public_projection.documents.location)
        for location in locations:
            sub_scope_root = resolve_location_path(repo_root, location).resolve()
            if sub_scope_root != resolved_root and path_is_relative_to(sub_scope_root, resolved_root):
                prefixes.append(sub_scope_root.relative_to(resolved_root))
    return tuple(sorted(set(prefixes)))


def publishable_parent_docs_files(
    repo_root: Path,
    config: DocsScopeConfig,
    working_root: Path,
    published_root: Path,
) -> dict[Path, bytes]:
    files = publishable_docs_files(
        working_root,
        published_root,
        projection_scope=config.scope_id,
        require_publication_recent=True,
    )
    excluded_prefixes = sub_scope_relative_prefixes(repo_root, config, working_root) + media_relative_prefixes(
        repo_root,
        config,
        working_root,
    )
    if not excluded_prefixes:
        return files
    return {
        rel: source_bytes
        for rel, source_bytes in files.items()
        if not any(path_is_relative_to(rel, prefix) for prefix in excluded_prefixes)
    }


def path_is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def docs_diff(
    repo_root: Path,
    working_root: Path,
    published_root: Path,
    *,
    publishable_files: dict[Path, bytes] | None = None,
    ignored_existing_prefixes: tuple[Path, ...] = (),
) -> dict[str, list[str]]:
    if publishable_files is None:
        publishable_files = publishable_docs_files(working_root, published_root.relative_to(repo_root.resolve()))
    changed: list[str] = []
    removed: list[str] = []
    for rel, source_bytes in publishable_files.items():
        target_path = published_root / rel
        if not target_path.exists() or target_path.read_bytes() != source_bytes:
            changed.append(repo_relative(repo_root, target_path))
    for target_path in iter_files(published_root):
        rel = target_path.relative_to(published_root)
        if any(path_is_relative_to(rel, prefix) for prefix in ignored_existing_prefixes):
            continue
        if rel not in publishable_files:
            removed.append(repo_relative(repo_root, target_path))
    return {"changed": changed, "removed": removed}


def parent_docs_diff(repo_root: Path, config: DocsScopeConfig, working_root: Path, published_root: Path) -> dict[str, list[str]]:
    ignored_prefixes = (
        sub_scope_relative_prefixes(repo_root, config, published_root)
        + media_relative_prefixes(repo_root, config, published_root)
    )
    return docs_diff(
        repo_root,
        working_root,
        published_root,
        publishable_files=publishable_parent_docs_files(
            repo_root,
            config,
            working_root,
            published_root.relative_to(repo_root.resolve()),
        ),
        ignored_existing_prefixes=ignored_prefixes,
    )


def sub_scope_docs_diff(
    repo_root: Path,
    scope: str,
    sub_scope: DocsSubScopeConfig,
    paths: dict[str, Path],
) -> dict[str, Any]:
    diff = docs_diff(
        repo_root,
        paths["working_docs_root"],
        paths["published_docs_root"],
        publishable_files=publishable_docs_files(
            paths["working_docs_root"],
            paths["published_docs_root"].relative_to(repo_root.resolve()),
            projection_scope=f"{scope}/{sub_scope.sub_scope}",
        ),
    )
    return {
        "sub_scope": sub_scope.sub_scope,
        "changed": diff["changed"],
        "removed": diff["removed"],
        "changed_count": len(diff["changed"]),
        "removed_count": len(diff["removed"]),
    }


def search_diff(repo_root: Path, working_index: Path, published_index: Path) -> dict[str, list[str]]:
    if not published_index.exists() or not filecmp.cmp(working_index, published_index, shallow=False):
        return {"changed": [repo_relative(repo_root, published_index)], "removed": []}
    return {"changed": [], "removed": []}


def prospective_document_location_projection(
    repo_root: Path,
    config: DocsScopeConfig,
    paths: dict[str, Path],
    sub_scope_paths: dict[str, dict[str, Path]],
) -> tuple[Path, bytes] | None:
    """Build the location index from the exact files eligible for publication."""

    if config.scope_id not in SUPPORTED_DOCUMENT_LOCATION_SCOPE_IDS:
        return None

    parent_files = publishable_parent_docs_files(
        repo_root,
        config,
        paths["working_docs_root"],
        paths["published_docs_root"].relative_to(repo_root.resolve()),
    )
    parent_documents = {
        relative_path.stem: json.loads(source_bytes.decode("utf-8"))
        for relative_path, source_bytes in parent_files.items()
        if doc_id_for_by_id_path(relative_path)
    }
    configured_sub_scopes = {
        sub_scope.sub_scope: sub_scope for sub_scope in config.sub_scopes
    }
    placed_sub_scope_ids = {
        str(payload.get("viewer_report_subscope") or "").strip().lower()
        for payload in parent_documents.values()
        if isinstance(payload, dict)
        and str(payload.get("viewer_report") or "").strip() == "docs_subscope"
        and str(payload.get("viewer_report_access") or "").strip() == "public"
    }
    sub_scope_manifests: dict[str, Any] = {}
    for sub_scope_id in sorted(placed_sub_scope_ids):
        sub_scope = configured_sub_scopes.get(sub_scope_id)
        if sub_scope is None:
            raise ValueError(
                f"public report references unsupported sub-scope {sub_scope_id!r}"
            )
        sub_paths = sub_scope_paths[sub_scope_id]
        public_files = publishable_docs_files(
            sub_paths["working_docs_root"],
            sub_paths["published_docs_root"].relative_to(repo_root.resolve()),
            projection_scope=f"{config.scope_id}/{sub_scope.sub_scope}",
        )
        manifest_bytes = public_files.get(Path("manifest.json"))
        if manifest_bytes is None:
            raise FileNotFoundError(
                f"publishable sub-scope {sub_scope.sub_scope} manifest not found"
            )
        sub_scope_manifests[sub_scope_id] = json.loads(
            manifest_bytes.decode("utf-8")
        )

    payload = build_document_location_payload(
        config,
        search_payload=read_json(paths["working_search_index"]),
        parent_documents=parent_documents,
        sub_scope_manifests=sub_scope_manifests,
    )
    output_path = resolve_scope_path(
        repo_root,
        document_location_projection_path(config),
    )
    return output_path, document_location_json_bytes(payload)


def document_location_diff(
    repo_root: Path,
    projection: tuple[Path, bytes] | None,
) -> dict[str, list[str]]:
    if projection is None:
        return {"changed": [], "removed": []}
    output_path, output_bytes = projection
    if not output_path.is_file() or output_path.read_bytes() != output_bytes:
        return {"changed": [repo_relative(repo_root, output_path)], "removed": []}
    return {"changed": [], "removed": []}


def publish_status(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    scope, config = normalize_scope(repo_root, body.get("scope"))
    paths = validate_publish_paths(repo_root, config)
    sub_scope_paths = validate_sub_scope_publish_paths(repo_root, config)
    docs = parent_docs_diff(repo_root, config, paths["working_docs_root"], paths["published_docs_root"])
    sub_scopes = [
        sub_scope_docs_diff(repo_root, scope, sub_scope, sub_scope_paths[sub_scope.sub_scope])
        for sub_scope in config.sub_scopes
    ]
    search = search_diff(repo_root, paths["working_search_index"], paths["published_search_index"])
    document_locations = document_location_diff(
        repo_root,
        prospective_document_location_projection(
            repo_root,
            config,
            paths,
            sub_scope_paths,
        ),
    )
    changed = (
        len(docs["changed"])
        + len(search["changed"])
        + len(document_locations["changed"])
        + sum(item["changed_count"] for item in sub_scopes)
    )
    removed = (
        len(docs["removed"])
        + len(search["removed"])
        + len(document_locations["removed"])
        + sum(item["removed_count"] for item in sub_scopes)
    )
    return {
        "ok": True,
        "schema_version": PUBLISH_SCHEMA_VERSION,
        "action": "publish_docs",
        "operation": "status",
        "scope": scope,
        "changed_count": changed,
        "removed_count": removed,
        "up_to_date": changed == 0 and removed == 0,
        "paths": {key: repo_relative(repo_root, value) for key, value in paths.items()},
        "docs": docs,
        "sub_scopes": sub_scopes,
        "search": search,
        "document_locations": document_locations,
        "summary_text": f"Publish status for {scope}: {changed} changed, {removed} stale.",
    }


def publish_confirm(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    payload = publish_status(repo_root, body)
    payload["operation"] = "confirm"
    payload["summary_text"] = (
        f"Publish confirmation for {payload['scope']}: "
        f"{payload['changed_count']} changed, {payload['removed_count']} stale."
    )
    return payload


def copy_tree(
    repo_root: Path,
    source_root: Path,
    target_root: Path,
    *,
    publishable_files: dict[Path, bytes] | None = None,
    ignored_existing_prefixes: tuple[Path, ...] = (),
) -> None:
    target_root.mkdir(parents=True, exist_ok=True)
    if publishable_files is None:
        publishable_files = publishable_docs_files(source_root, target_root.relative_to(repo_root.resolve()))
    for rel, source_bytes in publishable_files.items():
        target_path = target_root / rel
        target_path.parent.mkdir(parents=True, exist_ok=True)
        write_bytes_atomic(target_path, source_bytes)
    for target_path in reversed(iter_files(target_root)):
        rel = target_path.relative_to(target_root)
        if any(path_is_relative_to(rel, prefix) for prefix in ignored_existing_prefixes):
            continue
        if rel not in publishable_files:
            target_path.unlink()
    for directory in sorted((path for path in target_root.rglob("*") if path.is_dir()), key=lambda path: len(path.parts), reverse=True):
        try:
            directory.rmdir()
        except OSError:
            pass


def write_bytes_atomic(target_path: Path, source_bytes: bytes) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = target_path.with_name(f".{target_path.name}.tmp")
    temp_path.write_bytes(source_bytes)
    temp_path.replace(target_path)


def copy_file_atomic(source_path: Path, target_path: Path) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = target_path.with_name(f".{target_path.name}.tmp")
    shutil.copy2(source_path, temp_path)
    temp_path.replace(target_path)


def stale_catalogue_document_url_result(
    error: Exception,
    *,
    affected_targets: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return {
        "status": "stale",
        "stale": True,
        "affected_targets": affected_targets or [],
        "updated_paths": [],
        "error": str(error),
    }


def catalogue_document_url_follow_through(repo_root: Path) -> dict[str, Any]:
    """Refresh only exact generated Catalogue targets after Docs Publish."""

    affected_targets: list[dict[str, str]] = []
    try:
        from docs_catalogue_document_urls import load_public_catalogue_document_urls
        from catalogue.catalogue_document_url_refresh import (
            apply_catalogue_document_url_refresh_plan,
            build_catalogue_document_url_refresh_plan,
        )

        projection = load_public_catalogue_document_urls(repo_root)
        plan = build_catalogue_document_url_refresh_plan(repo_root, projection)
        affected_targets = [
            {"kind": kind, "key": key}
            for kind, key in plan.affected_targets
        ]
        result = apply_catalogue_document_url_refresh_plan(plan)
    except Exception as exc:  # Publication remains complete when follow-through fails.
        return stale_catalogue_document_url_result(
            exc,
            affected_targets=affected_targets,
        )

    updated_paths = [repo_relative(repo_root, path) for path in result.written_paths]
    return {
        "status": "updated" if updated_paths else "unchanged",
        "stale": False,
        "affected_targets": affected_targets,
        "updated_paths": updated_paths,
    }


def publish_apply(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    if body.get("confirm") is not True:
        raise ValueError("confirm must be true to publish docs")
    payload = publish_confirm(repo_root, body)
    _scope, config = normalize_scope(repo_root, payload["scope"])
    paths = validate_publish_paths(repo_root, config)
    sub_scope_paths = validate_sub_scope_publish_paths(repo_root, config)
    document_location_projection = prospective_document_location_projection(
        repo_root,
        config,
        paths,
        sub_scope_paths,
    )
    copy_tree(
        repo_root,
        paths["working_docs_root"],
        paths["published_docs_root"],
        publishable_files=publishable_parent_docs_files(
            repo_root,
            config,
            paths["working_docs_root"],
            paths["published_docs_root"].relative_to(repo_root.resolve()),
        ),
        ignored_existing_prefixes=(
            sub_scope_relative_prefixes(repo_root, config, paths["published_docs_root"])
            + media_relative_prefixes(repo_root, config, paths["published_docs_root"])
        ),
    )
    for sub_scope in config.sub_scopes:
        sub_paths = sub_scope_paths[sub_scope.sub_scope]
        copy_tree(
            repo_root,
            sub_paths["working_docs_root"],
            sub_paths["published_docs_root"],
            publishable_files=publishable_docs_files(
                sub_paths["working_docs_root"],
                sub_paths["published_docs_root"].relative_to(repo_root.resolve()),
                projection_scope=f"{config.scope_id}/{sub_scope.sub_scope}",
            ),
        )
    copy_file_atomic(paths["working_search_index"], paths["published_search_index"])
    if document_location_projection is not None:
        output_path, output_bytes = document_location_projection
        write_bytes_atomic(output_path, output_bytes)
    payload["operation"] = "apply"
    payload["applied"] = True
    payload["summary_text"] = (
        f"Published docs for {payload['scope']}: "
        f"{payload['changed_count']} changed, {payload['removed_count']} stale."
    )
    try:
        catalogue_document_urls = catalogue_document_url_follow_through(repo_root)
    except Exception as exc:  # Defensive: post-success follow-through never rolls back Docs.
        catalogue_document_urls = stale_catalogue_document_url_result(exc)
    payload["catalogue_document_urls"] = catalogue_document_urls
    if catalogue_document_urls["status"] == "updated":
        payload["summary_text"] += (
            " Updated "
            f"{len(catalogue_document_urls['updated_paths'])} Catalogue document URL payloads."
        )
    elif catalogue_document_urls["status"] == "stale":
        payload["summary_text"] += " Catalogue document URL follow-through is stale."
    return payload
