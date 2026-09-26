"""Browser-safe, live file and document-reference reads for exact Docs media owners."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import docs_source_model as source_model
from docs_media_inventory import list_collection_media, source_media_references
from docs_workspace_config import DocsCollectionConfig, DocsStageConfig, load_docs_stage


def _working_owner(
    repo_root: Path, stage: str, collection: str,
) -> tuple[DocsStageConfig, DocsStageConfig | DocsCollectionConfig]:
    if stage != "working":
        raise ValueError("Live Docs media reads require Working")
    config = load_docs_stage(repo_root, stage)
    if not collection:
        return config, config
    for child in config.collections:
        if child.collection == collection:
            return config, child
    raise ValueError(f"unconfigured collection: {collection}")


def read_media_files(repo_root: Path, *, stage: str, collection: str = "") -> dict[str, object]:
    """List one Working owner's files without document scans or presentation policy."""
    _config, owner = _working_owner(repo_root, stage, collection)
    return {
        "ok": True,
        "schema_version": "docs_media_files_v1",
        "stage": stage,
        "collection": collection,
        "files": [asdict(item) for item in list_collection_media(repo_root, owner)],
    }


def read_media_references(repo_root: Path, *, stage: str, collection: str = "") -> dict[str, object]:
    """Read live references to one media owner across all Working document collections.

    Only documents with references to this owner are returned, including missing
    file identities. Configured hosts describe every nonempty source collection.
    Callers construct links and file associations; build sources have no inferred
    relationship to same-basename output assets.
    """
    config, owner = _working_owner(repo_root, stage, collection)
    documents: list[dict[str, object]] = []
    hosts: list[dict[str, str]] = []
    collections = (("", config), *((child.collection, child) for child in config.collections))
    for document_collection, document_config in collections:
        sources = source_model.load_document_collection_docs_for_config(repo_root, config, document_config)
        if not sources:
            continue
        if isinstance(document_config, DocsCollectionConfig):
            hosts.append({
                "collection": document_collection,
                "report_host_doc_id": document_config.report_host_doc_id,
            })
        for document in sources:
            references = source_media_references(owner, document.source_text, doc_id=document.doc_id)
            if not references:
                continue
            documents.append({
                "target": {"stage": stage, "collection": document_collection, "doc_id": document.doc_id},
                "title": document.title,
                "references": [
                    {"role": "source", "media_type": reference.media_type, "identity": reference.identity}
                    for reference in references
                ],
            })
    return {
        "ok": True,
        "schema_version": "docs_media_references_v1",
        "stage": stage,
        "collection": collection,
        "collection_hosts": hosts,
        "documents": documents,
    }
