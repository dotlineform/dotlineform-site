"""Read selectable authoring document targets without building or writing sources."""

from pathlib import Path

from docs_front_matter import FRONT_MATTER_PATTERN, read_front_matter_fields
from docs_index_order import read_index_order, tree_parent_ids
from docs_document_location import canonical_document_viewer_url
from docs_management_document_target import confined_source_path, resolve_managed_document_collection
from docs_workspace_config import document_source_path, resolve_workspace_path


def read_document_link_targets(repo_root: Path) -> dict[str, object]:
    """List every configured authoring collection with stage-free document locations.

    Workspace configuration owns the exact source collections. Discovery reads
    identity/title metadata without validating Subjects or publication readiness.
    """
    resolved_collection = resolve_managed_document_collection(repo_root)
    config = resolved_collection.parent_config
    documents = []
    for owner in (config, *config.collections):
        collection = getattr(owner, "collection", "")
        root = resolve_workspace_path(repo_root, document_source_path(owner)).resolve()
        if collection:
            if not root.is_dir():
                raise FileNotFoundError(f"Document collection is unavailable: {collection}")
            paths = sorted(root.glob("*.md"))
        else:
            paths = [root / f"{doc_id}.md" for doc_id in tree_parent_ids(read_index_order(root))]
        for path in paths:
            source = confined_source_path(root, path).read_text(encoding="utf-8")
            header = FRONT_MATTER_PATTERN.match(source)
            if header is None:
                raise ValueError(f"Document link target front matter could not be parsed in {path.name}")
            metadata = {
                field.key: field.value
                for field in read_front_matter_fields(header.group(1), source_name=path.name)
            }
            doc_id = metadata.get("doc_id")
            if not isinstance(doc_id, str) or doc_id != path.stem:
                raise ValueError("Document link targets require an immutable doc_id.")
            title = metadata["title"]
            href = canonical_document_viewer_url(
                doc_id, collection=collection,
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
