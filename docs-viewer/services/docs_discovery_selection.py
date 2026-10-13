"""Shared metadata selection for Working Search and Recents.

Ordinary trees inherit exclusions; collection manifests are flat. Selection
never discovers sources or reads document content, and registration alone does
not include a collection. Callers supply current ordinary metadata in memory.
"""

from pathlib import Path
from dataclasses import dataclass
from typing import Any
import json

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
    return payload


def select_ordinary_documents(
    rows: list[dict[str, Any]], ignored_ids: frozenset[str],
) -> dict[str, dict[str, Any]]:
    """Prune ordinary draft/unpublishable branches in one traversal."""
    selected: dict[str, dict[str, Any]] = {}

    def visit(nodes: list[dict[str, Any]], parent_id: str) -> None:
        for row in nodes:
            doc_id = row["doc_id"]
            if row["draft"] or doc_id in ignored_ids:
                continue
            selected[doc_id] = {**row, "parent_id": parent_id}
            visit(row.get("children", []), doc_id)

    visit(rows, "")
    return selected


def _select_collection_rows(
    rows: list[dict[str, Any]], collection: DocsCollectionConfig,
) -> dict[str, dict[str, Any]]:
    return {
        row["doc_id"]: row for row in rows
        if collection.collection == "catalogue" or not row["draft"]
    }


def select_built_discovery_documents(
    config: DocsStageConfig, tree: list[dict[str, Any]],
    manifests: dict[str, dict[str, Any]], ignored_ids: frozenset[str],
) -> DiscoverySelection:
    """Select completed in-memory builder metadata without saved-file audits.

    Source loading owns identity/readiness validation. Discovery preserves its
    configured coverage, inherited exclusions and eligible collection hosts.
    """
    ordinary = select_ordinary_documents(tree, ignored_ids)
    collections = [
        (collection, _select_collection_rows(manifests[collection.collection]["docs"], collection))
        for collection in sorted(config.site_search_collections, key=lambda item: item.collection)
        if collection.report_host_doc_id in ordinary
    ]
    return DiscoverySelection(ordinary, collections)


def select_collection_documents(
    repo_root: Path, config: DocsStageConfig, ordinary_ids: set[str],
) -> list[tuple[DocsCollectionConfig, dict[str, dict[str, Any]]]]:
    """Select eligible-host collection rows; Catalogue has no draft state."""
    selections = []
    for collection in sorted(config.site_search_collections, key=lambda item: item.collection):
        if collection.report_host_doc_id not in ordinary_ids:
            continue
        path = resolve_workspace_path(repo_root, generated_documents_path(collection)) / "manage-manifest.json"
        manifest = read_discovery_metadata(path)
        selected = _select_collection_rows(manifest["docs"], collection)
        selections.append((collection, selected))
    return selections
