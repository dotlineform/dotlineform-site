"""Read configured document membership and source fields for local inspection."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from docs_document_identity import is_document_id
from docs_front_matter import FRONT_MATTER_PATTERN, read_front_matter_fields
from docs_index_order import read_index_order, tree_groups
from docs_workspace_config import DocsCollectionConfig, DocsStageConfig, document_source_path, resolve_workspace_path


@dataclass(frozen=True)
class InspectionSource:
    doc_id: str
    title: str
    metadata: dict[str, Any]
    source_text: str
    body: str


def inspection_source_paths(repo_root: Path, owner: DocsStageConfig | DocsCollectionConfig) -> tuple[Path, list[Path]]:
    """Select canonical ordinary membership or one flat named collection, without reading source text."""
    collection = getattr(owner, "collection", "")
    root = resolve_workspace_path(repo_root, document_source_path(owner))
    if not root.is_dir():
        raise FileNotFoundError(f"Document collection is unavailable: {collection or 'ordinary documents'}")
    paths = sorted(root.glob("*.md")) if collection else [
        root / f"{node['doc_id']}.md"
        for siblings, _parent_id in tree_groups(read_index_order(root)) for node in siblings
    ]
    return root, paths


def read_inspection_source(root: Path, path: Path, *, collection: str) -> InspectionSource:
    """Read and parse one confined source without Subject/readiness/parent/report audits."""
    if path.parent != root or path.is_symlink():
        raise ValueError(f"Document source must remain within its owner without symlinks: {path.name}")
    source = path.read_text(encoding="utf-8")
    header = FRONT_MATTER_PATTERN.match(source)
    if header is None:
        raise ValueError(f"Document front matter could not be parsed in {path.name}")
    metadata = {
        field.key: field.value
        for field in read_front_matter_fields(header.group(1), source_name=path.name)
    }
    doc_id = metadata.get("doc_id")
    if not isinstance(doc_id, str) or doc_id != path.stem or not is_document_id(doc_id, collection=collection):
        raise ValueError(f"Document source identity does not match its owner and filename: {path.name}")
    title = metadata.get("title")
    if not isinstance(title, str):
        raise ValueError(f"Document title must be a string: {path.name}")
    return InspectionSource(doc_id, title, metadata, source, source[header.end():])
