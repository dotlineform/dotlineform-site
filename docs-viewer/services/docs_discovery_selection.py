"""Shared metadata selection for Working Search and Recents.

Ordinary trees inherit exclusions; collection manifests are flat. Selection
never discovers sources or reads document content, and registration alone does
not include a collection. Callers supply current ordinary metadata in memory.
"""

from pathlib import Path
from dataclasses import dataclass
from typing import Any
import json

from docs_document_identity import is_doc_date, is_document_id
from docs_workspace_config import DocsCollectionConfig, DocsStageConfig, generated_documents_path, resolve_workspace_path


@dataclass(frozen=True)
class DiscoverySelection:
    """One eligible candidate set shared by complete Working Search and Recents."""

    ordinary: dict[str, dict[str, Any]]
    collections: list[tuple[DocsCollectionConfig, dict[str, dict[str, Any]]]]


def read_discovery_metadata(path: Path) -> dict[str, Any]:
    """Require saved Working metadata without a source-scan fallback."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"Discovery requires readable Working metadata: {path}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("docs"), list):
        raise ValueError(f"Discovery metadata docs must be an array: {path}")
    return payload


def _validate_row(row: Any, *, field: str, seen_ids: set[str], collection: str = "") -> str:
    if not isinstance(row, dict):
        raise ValueError(f"{field} must be an object")
    doc_id = row.get("doc_id")
    if not isinstance(doc_id, str) or not is_document_id(doc_id, collection=collection) or doc_id != doc_id.strip():
        raise ValueError(f"{field}.doc_id must use exact immutable document identity")
    if doc_id in seen_ids:
        raise ValueError(f"{field} contains duplicate doc_id {doc_id!r}")
    seen_ids.add(doc_id)
    if not isinstance(row.get("title"), str) or (collection != "catalogue" and not row["title"].strip()):
        raise ValueError(f"{field}.title has invalid representation or authoring metadata")
    if collection == "catalogue":
        if "draft" in row:
            raise ValueError(f"{field}: Catalogue metadata must omit draft")
    elif not isinstance(row.get("draft"), bool):
        raise ValueError(f"{field}.draft must be an explicit boolean")
    return doc_id


def select_ordinary_documents(
    rows: list[Any], ignored_ids: frozenset[str], *, field: str,
) -> dict[str, dict[str, Any]]:
    """Prune ordinary draft/unpublishable branches in one traversal."""
    return _select_ordinary_rows(rows, ignored_ids, field=field)


def _select_ordinary_rows(
    rows: list[Any], ignored_ids: frozenset[str], *, field: str | None,
) -> dict[str, dict[str, Any]]:
    selected: dict[str, dict[str, Any]] = {}
    seen_ids: set[str] = set()

    def visit(nodes: list[Any], parent_id: str) -> None:
        for row in nodes:
            doc_id = row["doc_id"] if field is None else _validate_row(row, field=field, seen_ids=seen_ids)
            if row["draft"] or doc_id in ignored_ids:
                continue
            selected[doc_id] = {**row, "parent_id": parent_id}
            children = row.get("children", [])
            if field is not None and not isinstance(children, list):
                raise ValueError(f"{field}: children must be an array for {doc_id}")
            visit(children, doc_id)

    visit(rows, "")
    return selected


def _select_collection_rows(
    rows: list[Any], collection: DocsCollectionConfig, *, field: str | None,
) -> dict[str, dict[str, Any]]:
    selected: dict[str, dict[str, Any]] = {}
    seen_ids: set[str] = set()
    for index, row in enumerate(rows):
        row_field = f"{field}.docs[{index}]" if field is not None else None
        doc_id = row["doc_id"] if row_field is None else _validate_row(
            row, field=row_field, seen_ids=seen_ids, collection=collection.collection,
        )
        if collection.collection != "catalogue" and row["draft"]:
            continue
        if row_field is not None and (
            "added_date" in row or (row.get("last_updated") != "" and not is_doc_date(row.get("last_updated")))
        ):
            raise ValueError(f"{row_field} requires date-only last_updated and no added_date; rebuild the collection")
        selected[doc_id] = row
    return selected


def select_built_discovery_documents(
    config: DocsStageConfig, tree: list[dict[str, Any]],
    manifests: dict[str, dict[str, Any]], ignored_ids: frozenset[str],
) -> DiscoverySelection:
    """Select completed in-memory builder metadata without saved-file audits.

    Source loading owns identity/readiness validation. Discovery preserves its
    configured coverage, inherited exclusions and eligible collection hosts.
    """
    ordinary = _select_ordinary_rows(tree, ignored_ids, field=None)
    collections = [
        (collection, _select_collection_rows(manifests[collection.collection]["docs"], collection, field=None))
        for collection in sorted(config.site_search_collections, key=lambda item: item.collection)
        if collection.report_host_doc_id in ordinary
    ]
    return DiscoverySelection(ordinary, collections)


def select_collection_documents(
    repo_root: Path, config: DocsStageConfig, ordinary_ids: set[str],
) -> list[tuple[DocsCollectionConfig, dict[str, dict[str, Any]]]]:
    """Select eligible-host collection rows; Catalogue has no draft state."""
    if config.stage != "working":
        raise ValueError("Discovery selection requires Working; Preview copies saved results")
    selections = []
    for collection in sorted(config.site_search_collections, key=lambda item: item.collection):
        if collection.report_host_doc_id not in ordinary_ids:
            continue
        path = resolve_workspace_path(repo_root, generated_documents_path(collection)) / "manage-manifest.json"
        manifest = read_discovery_metadata(path)
        selected = _select_collection_rows(manifest["docs"], collection, field=str(path))
        selections.append((collection, selected))
    return selections
