#!/usr/bin/env python3
"""Exact current-public cleanup planning for confirmed document Delete."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from docs_document_location_projection import (
    SUPPORTED_DOCUMENT_LOCATION_SCOPE_IDS,
    build_document_location_payload,
    build_exact_document_location_records,
    document_location_projection_path,
)
from docs_scope_config import (
    DocsScopeConfig,
    DocsSubScopeConfig,
    load_docs_scope_configs,
    public_documents_path,
    public_search_path,
)


MERMAID_PROJECTION_DIRECTORY_PATTERN = re.compile(
    r"^(?P<doc_id>.+)--mermaid-[0-9]{4}$"
)
SEARCH_INDEX_SCHEMA = "docs_viewer_search_index_v2"


class PublicDeleteCleanupApplyError(RuntimeError):
    """A canonical Delete committed before required public follow-through failed."""

    def __init__(self, result: dict[str, Any]) -> None:
        super().__init__(str(result.get("error") or "public Delete cleanup failed"))
        self.result = result


@dataclass(frozen=True)
class PublicDeleteCleanupPlan:
    scope: str
    sub_scope: str
    doc_ids: tuple[str, ...]
    applicable: bool
    projected_doc_ids: tuple[str, ...]
    remove_paths: tuple[Path, ...]
    writes_by_path: Mapping[Path, bytes]
    removed_urls: tuple[str, ...]
    catalogue_targets: tuple[tuple[str, str], ...]

    def response(self, repo_root: Path, *, status: str = "planned") -> dict[str, Any]:
        return {
            "applicable": self.applicable,
            "status": status,
            "scope": self.scope,
            "sub_scope": self.sub_scope,
            "doc_ids": list(self.doc_ids),
            "projected_doc_ids": list(self.projected_doc_ids),
            "remove_paths": [repo_relative(repo_root, path) for path in self.remove_paths],
            "changed_paths": [
                repo_relative(repo_root, path)
                for path in sorted(self.writes_by_path, key=lambda item: item.as_posix())
            ],
            "removed_urls": list(self.removed_urls),
            "catalogue_targets": [
                {"kind": kind, "key": key}
                for kind, key in self.catalogue_targets
            ],
        }


@dataclass(frozen=True)
class PublicScopeDeleteCleanupPlan:
    scope: str
    applicable: bool
    removed_urls: tuple[str, ...]
    catalogue_targets: tuple[tuple[str, str], ...]

    def response(self, *, status: str = "planned") -> dict[str, Any]:
        return {
            "applicable": self.applicable,
            "status": status,
            "scope": self.scope,
            "removed_urls": list(self.removed_urls),
            "catalogue_targets": [
                {"kind": kind, "key": key}
                for kind, key in self.catalogue_targets
            ],
        }


@dataclass(frozen=True)
class _PublicScopeState:
    config: DocsScopeConfig
    docs_root: Path
    search_path: Path
    index_tree: dict[str, Any]
    recent: dict[str, Any]
    search: dict[str, Any]
    parent_documents: Mapping[str, Any]
    sub_scope_manifests: Mapping[str, Any]


def repo_relative(repo_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(f"public Delete cleanup path escapes repo root: {path}") from exc


def json_bytes(payload: Any) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def search_payload_version(payload: Mapping[str, Any]) -> str:
    header = payload.get("header")
    version_payload = {
        "schema": header.get("schema") if isinstance(header, dict) else "",
        "scope": header.get("scope") if isinstance(header, dict) else "",
        "fields": payload.get("fields"),
        "docs": payload.get("docs"),
        "terms": payload.get("terms"),
    }
    canonical = json.dumps(version_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.blake2b(canonical.encode("utf-8"), digest_size=64).digest()[:16].hex()
    return f"blake2b-{digest}"


def read_json_object(path: Path, *, field: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"{field} not found: {path}") from exc
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{field} must be readable UTF-8 JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{field} must be a JSON object: {path}")
    return payload


def flatten_public_tree_rows(rows: Any) -> list[dict[str, Any]]:
    if not isinstance(rows, list):
        raise ValueError("public index tree docs must be an array")
    flattened: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("public index tree document must be an object")
        flattened.append(row)
        flattened.extend(flatten_public_tree_rows(row.get("children", [])))
    return flattened


def configured_public_collection(
    repo_root: Path,
    scope: str,
    sub_scope: str,
) -> tuple[DocsScopeConfig, DocsScopeConfig | DocsSubScopeConfig] | None:
    config = load_docs_scope_configs(repo_root).get(scope)
    if config is None or public_documents_path(config) is None or public_search_path(config) is None:
        return None
    if not sub_scope:
        return config, config
    matches = [item for item in config.sub_scopes if item.sub_scope == sub_scope]
    if len(matches) != 1 or public_documents_path(matches[0]) is None:
        return None
    return config, matches[0]


def load_public_scope_state(
    repo_root: Path,
    config: DocsScopeConfig,
) -> _PublicScopeState | None:
    documents_path = public_documents_path(config)
    search_index_path = public_search_path(config)
    if documents_path is None or search_index_path is None:
        return None
    docs_root = (repo_root / documents_path).resolve()
    search_path = (repo_root / search_index_path).resolve()
    repo_relative(repo_root, docs_root)
    repo_relative(repo_root, search_path)
    if not docs_root.exists() and not search_path.exists():
        return None
    if not docs_root.is_dir() or not search_path.is_file():
        raise FileNotFoundError(
            f"public projection for {config.scope_id} is incomplete"
        )

    index_tree = read_json_object(
        docs_root / "index-tree.json",
        field="public index tree",
    )
    recent = read_json_object(docs_root / "recent.json", field="public Recent")
    search = read_json_object(search_path, field="public search")
    parent_documents = {
        path.stem: read_json_object(path, field="public parent document")
        for path in sorted((docs_root / "by-id").glob("*.json"))
    }
    sub_scope_manifests: dict[str, Any] = {}
    for child in config.sub_scopes:
        child_path = public_documents_path(child)
        if child_path is None:
            continue
        manifest_path = (repo_root / child_path / "manifest.json").resolve()
        repo_relative(repo_root, manifest_path)
        if manifest_path.is_file():
            sub_scope_manifests[child.sub_scope] = read_json_object(
                manifest_path,
                field=f"public {config.scope_id}/{child.sub_scope} manifest",
            )
    return _PublicScopeState(
        config=config,
        docs_root=docs_root,
        search_path=search_path,
        index_tree=index_tree,
        recent=recent,
        search=search,
        parent_documents=parent_documents,
        sub_scope_manifests=sub_scope_manifests,
    )


def filtered_tree_payload(payload: Mapping[str, Any], doc_ids: set[str]) -> dict[str, Any]:
    def filtered_rows(rows: Any) -> list[dict[str, Any]]:
        if not isinstance(rows, list):
            raise ValueError("public index tree docs must be an array")
        result: list[dict[str, Any]] = []
        for raw in rows:
            if not isinstance(raw, dict):
                raise ValueError("public index tree document must be an object")
            if str(raw.get("doc_id") or "").strip() in doc_ids:
                continue
            row = {key: value for key, value in raw.items() if key != "children"}
            children = filtered_rows(raw.get("children", []))
            if children:
                row["children"] = children
            result.append(row)
        return result

    return {**payload, "docs": filtered_rows(payload.get("docs"))}


def filtered_recent_payload(payload: Mapping[str, Any], doc_ids: set[str]) -> dict[str, Any]:
    rows = payload.get("docs")
    if not isinstance(rows, list):
        raise ValueError("public Recent docs must be an array")
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError("public Recent document must be an object")
    return {
        **payload,
        "docs": [
            row
            for row in rows
            if str(row.get("doc_id") or "").strip() not in doc_ids
        ],
    }


def filtered_search_payload(payload: Mapping[str, Any], doc_ids: set[str]) -> dict[str, Any]:
    rows = payload.get("docs")
    header = payload.get("header")
    fields = payload.get("fields")
    terms = payload.get("terms")
    if (
        not isinstance(rows, list)
        or not isinstance(header, dict)
        or header.get("schema") != SEARCH_INDEX_SCHEMA
        or not isinstance(fields, list)
        or not isinstance(terms, dict)
    ):
        raise ValueError("public search requires a v2 header, fields, docs, and terms")
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError("public search document must be an object")

    kept = [
        (position, row)
        for position, row in enumerate(rows)
        if str(row.get("id") or "").strip() not in doc_ids
    ]
    positions = {old: new for new, (old, _row) in enumerate(kept)}
    next_terms: dict[str, dict[str, list[int]]] = {}
    for term, raw_postings in terms.items():
        if not isinstance(raw_postings, dict):
            raise ValueError("public search term postings must be an object")
        next_postings: dict[str, list[int]] = {}
        for field, raw_positions in raw_postings.items():
            if not isinstance(raw_positions, list) or any(not isinstance(item, int) for item in raw_positions):
                raise ValueError("public search field postings must be integer arrays")
            remapped = [positions[item] for item in raw_positions if item in positions]
            if remapped:
                next_postings[field] = remapped
        if next_postings:
            next_terms[term] = next_postings

    result = {
        **payload,
        "header": {**header, "count": len(kept)},
        "docs": [row for _position, row in kept],
        "terms": next_terms,
    }
    result["header"]["version"] = search_payload_version(result)
    return result


def filtered_manifest_payload(payload: Mapping[str, Any], doc_ids: set[str]) -> dict[str, Any]:
    rows = payload.get("docs")
    if not isinstance(rows, list):
        raise ValueError("public sub-scope manifest docs must be an array")
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError("public sub-scope manifest document must be an object")
    return {
        **payload,
        "docs": [
            row
            for row in rows
            if str(row.get("doc_id") or "").strip() not in doc_ids
        ],
    }


def exact_mermaid_paths(docs_root: Path, doc_id: str) -> list[Path]:
    projection_root = docs_root / "projection-assets" / "mermaid"
    if not projection_root.is_dir():
        return []
    paths: list[Path] = []
    for directory in sorted(projection_root.iterdir()):
        if not directory.is_dir():
            continue
        match = MERMAID_PROJECTION_DIRECTORY_PATTERN.fullmatch(directory.name)
        if match is None or match.group("doc_id") != doc_id:
            continue
        for theme in ("dark", "light"):
            path = directory / f"{theme}.svg"
            if path.is_file():
                paths.append(path)
    return paths


def catalogue_targets_for_urls(
    repo_root: Path,
    urls: set[str],
) -> tuple[tuple[str, str], ...]:
    if not urls:
        return ()
    from catalogue.catalogue_document_url_refresh import current_nonempty_targets
    return tuple(
        sorted(
            target
            for target, (_path, _payload, current_urls) in current_nonempty_targets(
                repo_root.resolve()
            ).items()
            if urls.intersection(current_urls)
        )
    )


def plan_public_document_delete_cleanup(
    repo_root: Path,
    *,
    scope: str,
    sub_scope: str = "",
    doc_ids: list[str] | tuple[str, ...],
) -> PublicDeleteCleanupPlan:
    normalized_scope = str(scope or "").strip().lower()
    normalized_sub_scope = str(sub_scope or "").strip().lower()
    normalized_doc_ids = tuple(dict.fromkeys(str(item or "").strip() for item in doc_ids))
    if not normalized_scope or not normalized_doc_ids or any(not item for item in normalized_doc_ids):
        raise ValueError("public Delete cleanup requires exact scope and doc_ids")
    configured = configured_public_collection(
        repo_root,
        normalized_scope,
        normalized_sub_scope,
    )
    if configured is None:
        return PublicDeleteCleanupPlan(
            scope=normalized_scope,
            sub_scope=normalized_sub_scope,
            doc_ids=normalized_doc_ids,
            applicable=False,
            projected_doc_ids=(),
            remove_paths=(),
            writes_by_path={},
            removed_urls=(),
            catalogue_targets=(),
        )

    parent_config, collection_config = configured
    documents_path = public_documents_path(collection_config)
    if documents_path is None:
        raise ValueError("configured public Delete collection has no public documents path")
    collection_root = (repo_root / documents_path).resolve()
    repo_relative(repo_root, collection_root)
    initial_remove_paths: list[Path] = []
    initial_impacted_ids: set[str] = set()
    for doc_id in normalized_doc_ids:
        by_id_path = collection_root / "by-id" / f"{doc_id}.json"
        if by_id_path.is_file():
            initial_remove_paths.append(by_id_path)
            initial_impacted_ids.add(doc_id)
        mermaid_paths = exact_mermaid_paths(collection_root, doc_id)
        if mermaid_paths:
            initial_remove_paths.extend(mermaid_paths)
            initial_impacted_ids.add(doc_id)

    try:
        state = load_public_scope_state(repo_root, parent_config)
    except FileNotFoundError:
        if initial_remove_paths:
            raise
        state = None
    if state is None:
        return PublicDeleteCleanupPlan(
            scope=normalized_scope,
            sub_scope=normalized_sub_scope,
            doc_ids=normalized_doc_ids,
            applicable=True,
            projected_doc_ids=(),
            remove_paths=(),
            writes_by_path={},
            removed_urls=(),
            catalogue_targets=(),
        )

    delete_ids = set(normalized_doc_ids)
    public_parent_doc_ids = set(state.parent_documents).union(
        str(row.get("doc_id") or "").strip()
        for row in flatten_public_tree_rows(state.index_tree.get("docs"))
    ).union(
        str(row.get("doc_id") or "").strip()
        for row in state.recent.get("docs", [])
        if isinstance(row, dict)
    ).union(
        str(row.get("id") or "").strip()
        for row in state.search.get("docs", [])
        if isinstance(row, dict)
    )
    next_tree = state.index_tree
    next_recent = state.recent
    next_search = state.search
    next_parent_documents = dict(state.parent_documents)
    next_sub_scope_manifests = dict(state.sub_scope_manifests)
    remove_paths = list(initial_remove_paths)
    impacted_ids = set(initial_impacted_ids)

    writes_by_path: dict[Path, bytes] = {}
    if normalized_sub_scope:
        current_manifest = state.sub_scope_manifests.get(normalized_sub_scope)
        if current_manifest is None:
            if collection_root.exists():
                raise FileNotFoundError(
                    f"public sub-scope manifest is missing: {normalized_scope}/{normalized_sub_scope}"
                )
        else:
            next_manifest = filtered_manifest_payload(current_manifest, delete_ids)
            if next_manifest != current_manifest:
                impacted_ids.update(
                    str(row.get("doc_id") or "").strip()
                    for row in current_manifest.get("docs", [])
                    if isinstance(row, dict)
                    and str(row.get("doc_id") or "").strip() in delete_ids
                )
                manifest_path = collection_root / "manifest.json"
                writes_by_path[manifest_path] = json_bytes(next_manifest)
                next_sub_scope_manifests[normalized_sub_scope] = next_manifest
    else:
        next_tree = filtered_tree_payload(state.index_tree, delete_ids)
        next_recent = filtered_recent_payload(state.recent, delete_ids)
        next_search = filtered_search_payload(state.search, delete_ids)
        next_parent_documents = {
            doc_id: payload
            for doc_id, payload in state.parent_documents.items()
            if doc_id not in delete_ids
        }
        for path, before, after in (
            (state.docs_root / "index-tree.json", state.index_tree, next_tree),
            (state.docs_root / "recent.json", state.recent, next_recent),
            (state.search_path, state.search, next_search),
        ):
            if before != after:
                writes_by_path[path] = json_bytes(after)
                impacted_ids.update(delete_ids.intersection(public_parent_doc_ids))

    old_exact_locations = build_exact_document_location_records(
        parent_config,
        search_payload=state.search,
        parent_documents=state.parent_documents,
        sub_scope_manifests=state.sub_scope_manifests,
    )
    next_exact_locations = build_exact_document_location_records(
        parent_config,
        search_payload=next_search,
        parent_documents=next_parent_documents,
        sub_scope_manifests=next_sub_scope_manifests,
    )
    next_urls = {str(record["url"]) for record in next_exact_locations}
    removed_location_records = [
        record
        for record in old_exact_locations
        if str(record["url"]) not in next_urls
    ]
    removed_urls = tuple(sorted(str(record["url"]) for record in removed_location_records))
    if removed_urls:
        impacted_ids.update(
            delete_ids.intersection(
                str(record.get("doc_id") or "").strip()
                for record in removed_location_records
            )
        )

    if parent_config.scope_id in SUPPORTED_DOCUMENT_LOCATION_SCOPE_IDS:
        location_path = (
            repo_root / document_location_projection_path(parent_config)
        ).resolve()
        repo_relative(repo_root, location_path)
        if location_path.is_file():
            next_location_payload = build_document_location_payload(
                parent_config,
                search_payload=next_search,
                parent_documents=next_parent_documents,
                sub_scope_manifests=next_sub_scope_manifests,
            )
            next_location_bytes = json_bytes(next_location_payload)
            if location_path.read_bytes() != next_location_bytes:
                writes_by_path[location_path] = next_location_bytes

    removed_url_set = set(removed_urls)
    return PublicDeleteCleanupPlan(
        scope=normalized_scope,
        sub_scope=normalized_sub_scope,
        doc_ids=normalized_doc_ids,
        applicable=True,
        projected_doc_ids=tuple(sorted(impacted_ids)),
        remove_paths=tuple(sorted(set(remove_paths), key=lambda path: path.as_posix())),
        writes_by_path=writes_by_path,
        removed_urls=removed_urls,
        catalogue_targets=catalogue_targets_for_urls(repo_root, removed_url_set),
    )


def plan_public_scope_delete_cleanup(
    repo_root: Path,
    *,
    scope: str,
) -> PublicScopeDeleteCleanupPlan:
    normalized_scope = str(scope or "").strip().lower()
    if not normalized_scope:
        raise ValueError("public scope Delete cleanup requires exact scope")
    configs = load_docs_scope_configs(repo_root)
    config = configs.get(normalized_scope)
    if (
        config is None
        or public_documents_path(config) is None
        or public_search_path(config) is None
    ):
        return PublicScopeDeleteCleanupPlan(
            scope=normalized_scope,
            applicable=False,
            removed_urls=(),
            catalogue_targets=(),
        )
    state = load_public_scope_state(repo_root, config)
    search_docs = state.search.get("docs") if state is not None else None
    if (
        state is None
        or not state.parent_documents
        or (isinstance(search_docs, list) and not search_docs)
    ):
        removed_urls: tuple[str, ...] = ()
    else:
        removed_urls = tuple(
            sorted(
                str(record["url"])
                for record in build_exact_document_location_records(
                    config,
                    search_payload=state.search,
                    parent_documents=state.parent_documents,
                    sub_scope_manifests=state.sub_scope_manifests,
                )
            )
        )
    return PublicScopeDeleteCleanupPlan(
        scope=normalized_scope,
        applicable=True,
        removed_urls=removed_urls,
        catalogue_targets=catalogue_targets_for_urls(repo_root, set(removed_urls)),
    )


def write_bytes_atomic(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.delete-cleanup.tmp")
    temporary.write_bytes(content)
    temporary.replace(path)


def refresh_catalogue_document_urls_strict(repo_root: Path) -> dict[str, Any]:
    from docs_publish_gate import catalogue_document_url_follow_through

    result = catalogue_document_url_follow_through(repo_root)
    if result.get("status") == "stale":
        raise PublicDeleteCleanupApplyError(
            {
                "ok": False,
                "status": "failed",
                "stage": "catalogue_document_urls",
                "catalogue_document_urls": result,
                "error": str(result.get("error") or "Catalogue document URL refresh failed"),
            }
        )
    return result


def apply_public_document_delete_cleanup(
    repo_root: Path,
    plan: PublicDeleteCleanupPlan,
) -> dict[str, Any]:
    if not plan.applicable:
        return plan.response(repo_root, status="not_applicable")
    result = plan.response(repo_root, status="applying")
    try:
        for path in sorted(plan.writes_by_path, key=lambda item: item.as_posix()):
            write_bytes_atomic(path, plan.writes_by_path[path])
        for path in plan.remove_paths:
            path.unlink(missing_ok=True)
        for directory in sorted(
            {
                path.parent
                for path in plan.remove_paths
                if MERMAID_PROJECTION_DIRECTORY_PATTERN.fullmatch(path.parent.name)
            },
            key=lambda item: item.as_posix(),
        ):
            try:
                directory.rmdir()
            except OSError:
                pass
    except Exception as exc:
        result.update(
            {
                "ok": False,
                "status": "failed",
                "stage": "public_products",
                "error": str(exc),
            }
        )
        raise PublicDeleteCleanupApplyError(result) from exc

    try:
        catalogue_result = (
            refresh_catalogue_document_urls_strict(repo_root)
            if plan.removed_urls
            else {
                "status": "unchanged",
                "stale": False,
                "affected_targets": [],
                "updated_paths": [],
            }
        )
    except PublicDeleteCleanupApplyError as exc:
        result.update(exc.result)
        result["status"] = "failed"
        raise PublicDeleteCleanupApplyError(result) from exc

    result.update(
        {
            "ok": True,
            "status": "applied" if plan.remove_paths or plan.writes_by_path else "unchanged",
            "catalogue_document_urls": catalogue_result,
        }
    )
    return result


def apply_public_scope_delete_cleanup(
    repo_root: Path,
    plan: PublicScopeDeleteCleanupPlan,
) -> dict[str, Any]:
    if not plan.applicable:
        return plan.response(status="not_applicable")
    result = plan.response(status="applying")
    try:
        catalogue_result = refresh_catalogue_document_urls_strict(repo_root)
    except PublicDeleteCleanupApplyError as exc:
        result.update(exc.result)
        result["status"] = "failed"
        raise PublicDeleteCleanupApplyError(result) from exc
    result.update(
        {
            "ok": True,
            "status": (
                "applied"
                if plan.removed_urls or catalogue_result.get("status") == "updated"
                else "unchanged"
            ),
            "catalogue_document_urls": catalogue_result,
        }
    )
    return result


__all__ = [
    "PublicDeleteCleanupApplyError",
    "PublicDeleteCleanupPlan",
    "PublicScopeDeleteCleanupPlan",
    "apply_public_document_delete_cleanup",
    "apply_public_scope_delete_cleanup",
    "plan_public_document_delete_cleanup",
    "plan_public_scope_delete_cleanup",
    "refresh_catalogue_document_urls_strict",
]
