"""Read selectable authoring document targets without building or writing sources."""

from pathlib import Path

import docs_source_model as source_model
from docs_document_identity import is_document_id
from docs_index_order import read_index_order, tree_parent_ids
from docs_document_location import canonical_document_viewer_url, collection_report_placement
from docs_management_document_target import confined_source_path, resolve_managed_document_collection
from docs_workspace_config import document_source_path, resolve_workspace_path


def read_document_link_targets(repo_root: Path) -> dict[str, object]:
    """List every configured authoring collection with stage-free document locations.

    Workspace configuration owns the source and report host. Discovery reads
    identity/title metadata without validating editing or publication readiness.
    Collection configuration supplies host IDs without reading host documents.
    """
    resolved_collection = resolve_managed_document_collection(repo_root)
    config = resolved_collection.parent_config
    documents = []
    for owner in (config, *config.collections):
        collection = getattr(owner, "collection", "")
        root = resolve_workspace_path(repo_root, document_source_path(owner))
        if not root.is_dir():
            raise FileNotFoundError(f"Document collection is unavailable: {collection}")
        paths = source_model.document_markdown_paths(root)
        for path in paths:
            if path.is_symlink():
                raise ValueError("Document link target source must not be a symlink.")
            confined_source_path(root.resolve(), path)
        if not collection:
            paths = [root / f"{doc_id}.md" for doc_id in tree_parent_ids(read_index_order(root))]
        # Resolve a child host only when the collection contains selectable documents.
        host_id = ""
        if collection and paths:
            _config, _collection, host_id = collection_report_placement(
                repo_root, collection,
            )
        for path in paths:
            confined_source_path(root.resolve(), path)
            metadata, _body = source_model.parse_source(path)
            doc_id = metadata.get("doc_id")
            if not isinstance(doc_id, str) or not is_document_id(doc_id, collection=collection) or doc_id != path.stem:
                raise ValueError("Document link targets require an immutable doc_id.")
            title = str(metadata.get("title") or source_model.humanize(doc_id)).strip() or doc_id
            href = canonical_document_viewer_url(
                host_id if collection else doc_id,
                subdoc_id=doc_id if collection else "",
                subdoc_collection=collection,
            )
            documents.append({
                "target": {"collection": collection, "doc_id": doc_id},
                "title": title,
                "href": href,
            })
    return {
        "ok": True,
        "schema_version": "docs_document_link_targets_v2",
        "collections": [owner.collection for owner in config.collections],
        "documents": documents,
    }
