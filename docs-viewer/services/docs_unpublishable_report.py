"""Read the workspace's configured Working publication ignore file."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from docs_front_matter import read_front_matter_fields
from docs_management_document_target import confined_source_path
from docs_publication_ignore import read_publication_ignore_ids
from docs_workspace_config import document_source_path, load_docs_working_config


def _source_title(source_path: Path, doc_id: str) -> str:
    """Read only the confined source header, retaining its exact identity boundary."""
    header_error = f"Document front matter could not be parsed in {source_path.name}"
    with source_path.open(encoding="utf-8") as source:
        if source.readline().rstrip() != "---":
            raise ValueError(header_error)
        lines = []
        for line in source:
            if line.rstrip() == "---":
                break
            lines.append(line)
        else:
            raise ValueError(header_error)
    front_matter = {
        field.key: field.value
        for field in read_front_matter_fields("".join(lines), source_name=source_path.name)
    }
    if front_matter.get("doc_id") != doc_id:
        raise ValueError("Ignored document source identity does not match its ID")
    return front_matter["title"]


def build_unpublishable_report(repo_root: Path) -> dict[str, Any]:
    """Read the explicit IDs and only their exact ordinary Working source titles."""
    config = load_docs_working_config(repo_root)
    doc_ids = read_publication_ignore_ids(repo_root, config=config)
    source_root = document_source_path(config)
    documents = []
    for doc_id in doc_ids:
        try:
            source_path = confined_source_path(source_root, source_root / f"{doc_id}.md")
        except FileNotFoundError:
            title = None
        else:
            title = _source_title(source_path, doc_id)
        documents.append({"doc_id": doc_id, "title": title})
    return {
        "ok": True, "schema_version": "docs_unpublishable_report_v4",
        "documents": documents,
    }
