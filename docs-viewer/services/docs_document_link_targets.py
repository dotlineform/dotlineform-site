"""Read selectable authoring document targets without building or writing sources."""

from pathlib import Path

import docs_source_model as source_model
from docs_document_identity import is_document_id
from docs_document_location import canonical_document_viewer_url, collection_report_placement
from docs_management_document_target import confined_source_path, resolve_managed_document_collection
from docs_workspace_config import document_source_path, resolve_workspace_path
from docs_publication_ignore import WorkingLinksExclusions, working_ignored_doc_ids


def read_document_link_targets(repo_root: Path) -> dict[str, object]:
    """List every configured authoring collection with stage-free document locations.

    Workspace configuration owns the source and report host. Explicitly
    ignored ordinary targets and their descendants are omitted; draft readiness
    and Subject do not filter selection.
    Collection configuration supplies host IDs without reading host documents.
    """
    resolved_collection = resolve_managed_document_collection(repo_root)
    config = resolved_collection.parent_config
    documents = []
    exclusions = WorkingLinksExclusions(
        resolve_workspace_path(repo_root, document_source_path(config)),
        working_ignored_doc_ids(repo_root, config),
    )
    for owner in (config, *config.collections):
        collection = getattr(owner, "collection", "")
        root = resolve_workspace_path(repo_root, document_source_path(owner))
        if not root.is_dir():
            raise FileNotFoundError(f"Document collection is unavailable: {collection}")
        for path in source_model.document_markdown_paths(root):
            confined_source_path(root.resolve(), path)
        records = source_model.load_document_collection_docs_for_config(repo_root, config, owner)
        if not collection:
            exclusions.parents.update({doc.doc_id: doc.parent_id for doc in records})
        # Resolve a child host only when the collection contains selectable documents.
        host_id = ""
        if collection and records:
            _config, _collection, host_id = collection_report_placement(
                repo_root, collection,
            )
        for document in records:
            if not is_document_id(document.doc_id, collection=collection):
                raise ValueError("Document link targets require an immutable doc_id.")
            if not collection and exclusions.excludes(document.doc_id):
                continue
            href = canonical_document_viewer_url(
                host_id if collection else document.doc_id,
                subdoc_id=document.doc_id if collection else "",
                subdoc_collection=collection,
            )
            documents.append({
                "target": {"collection": collection, "doc_id": document.doc_id},
                "title": document.title,
                "href": href,
            })
    return {
        "ok": True,
        "schema_version": "docs_document_link_targets_v2",
        "collections": [owner.collection for owner in config.collections],
        "documents": documents,
    }
