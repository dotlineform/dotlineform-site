"""Shared metadata selection for Working Search and Recents.

Ordinary trees inherit exclusions; collection manifests are flat. Selection
never discovers sources or reads document content, and registration alone does
not include a collection. Callers supply current ordinary metadata in memory.
"""

from pathlib import Path
from typing import Any
import json

from docs_document_identity import is_immutable_doc_id
from docs_workspace_config import DocsCollectionConfig, DocsStageConfig, generated_documents_path, resolve_workspace_path


def read_discovery_metadata(path: Path) -> dict[str, Any]:
    """Require saved Working metadata without a source-scan fallback."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"Discovery requires readable Working metadata: {path}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("docs"), list):
        raise ValueError(f"Discovery metadata docs must be an array: {path}")
    return payload


def _validate_row(row: Any, *, field: str, seen_ids: set[str]) -> str:
    if not isinstance(row, dict):
        raise ValueError(f"{field} must be an object")
    doc_id = row.get("doc_id")
    if not isinstance(doc_id, str) or not is_immutable_doc_id(doc_id) or doc_id != doc_id.strip():
        raise ValueError(f"{field}.doc_id must use exact immutable document identity")
    if doc_id in seen_ids:
        raise ValueError(f"{field} contains duplicate doc_id {doc_id!r}")
    seen_ids.add(doc_id)
    if not isinstance(row.get("title"), str) or not row["title"].strip():
        raise ValueError(f"{field}.title must not be empty")
    if not isinstance(row.get("draft"), bool):
        raise ValueError(f"{field}.draft must be an explicit boolean")
    return doc_id


def select_ordinary_documents(
    rows: list[Any], ignored_ids: frozenset[str], *, field: str,
) -> dict[str, dict[str, Any]]:
    """Prune ordinary draft/unpublishable branches in one traversal."""
    selected: dict[str, dict[str, Any]] = {}
    seen_ids: set[str] = set()

    def visit(nodes: list[Any], parent_id: str) -> None:
        for row in nodes:
            doc_id = _validate_row(row, field=field, seen_ids=seen_ids)
            if row["draft"] or doc_id in ignored_ids:
                continue
            selected[doc_id] = {**row, "parent_id": parent_id}
            children = row.get("children", [])
            if not isinstance(children, list):
                raise ValueError(f"{field}: children must be an array for {doc_id}")
            visit(children, doc_id)

    visit(rows, "")
    return selected


def select_collection_documents(
    repo_root: Path, config: DocsStageConfig, ordinary_ids: set[str],
) -> list[tuple[DocsCollectionConfig, dict[str, dict[str, Any]]]]:
    """Read only included, eligible-host manifests and select flat non-draft rows."""
    if config.stage != "working":
        raise ValueError("Discovery selection requires Working; Preview copies saved results")
    selections = []
    for collection in sorted(config.site_search_collections, key=lambda item: item.collection):
        if collection.report_host_doc_id not in ordinary_ids:
            continue
        path = resolve_workspace_path(repo_root, generated_documents_path(collection)) / "manage-manifest.json"
        manifest = read_discovery_metadata(path)
        selected: dict[str, dict[str, Any]] = {}
        seen_ids: set[str] = set()
        for index, row in enumerate(manifest["docs"]):
            field = f"{path}.docs[{index}]"
            doc_id = _validate_row(row, field=field, seen_ids=seen_ids)
            if row["draft"]:
                continue
            if not isinstance(row.get("last_updated"), str):
                raise ValueError(f"{field}.last_updated must be a string")
            selected[doc_id] = row
        selections.append((collection, selected))
    return selections
