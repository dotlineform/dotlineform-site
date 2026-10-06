"""Read exact document targets excluded only from the shared Recent list."""

import json
from pathlib import Path

from docs_document_identity import is_document_id
from docs_workspace_config import DocsStageConfig, document_source_path


RECENT_EXCLUSIONS_FILENAME = "recent-exclusions.json"


def recent_exclusions_path(config: DocsStageConfig) -> Path:
    """Resolve the Working policy file without creating or substituting it."""
    if config.stage != "working":
        raise ValueError("Recent exclusions belong to Working")
    root = document_source_path(config)
    path = root / RECENT_EXCLUSIONS_FILENAME
    if path.is_symlink() or path.resolve().parent != root.resolve():
        raise ValueError("Recent exclusions must stay in their configured source directory")
    return path


def parse_recent_exclusions(data: bytes, config: DocsStageConfig) -> frozenset[tuple[str, str]]:
    """Require an array of exact targets; exclusions never include descendants."""
    try:
        rows = json.loads(data)
    except (json.JSONDecodeError, UnicodeError) as error:
        raise ValueError("recent-exclusions.json must contain a JSON array of document targets") from error
    if not isinstance(rows, list):
        raise ValueError("recent-exclusions.json must contain a JSON array of document targets")
    collections = {collection.collection for collection in config.collections}
    targets: set[tuple[str, str]] = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) not in ({"doc_id"}, {"collection", "doc_id"}):
            raise ValueError("Recent exclusions require doc_id and optional collection only")
        collection = row.get("collection", "")
        if "collection" in row and (not isinstance(collection, str) or collection not in collections):
            raise ValueError("Recent exclusions require exact configured collection identities")
        doc_id = row["doc_id"]
        if not isinstance(doc_id, str) or not is_document_id(doc_id, collection=collection) or doc_id != doc_id.strip():
            raise ValueError("Recent exclusions require exact document identities")
        target = (collection, doc_id)
        if target in targets:
            raise ValueError("Recent exclusions contain a duplicate document target")
        targets.add(target)
    return frozenset(targets)


def read_recent_exclusions(config: DocsStageConfig) -> frozenset[tuple[str, str]]:
    """Missing, unreadable and invalid policy files fail visibly."""
    return parse_recent_exclusions(recent_exclusions_path(config).read_bytes(), config)
