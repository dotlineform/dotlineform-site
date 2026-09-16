"""Read selectable authoring document targets without building or writing sources."""

from pathlib import Path

import docs_source_model as source_model
from docs_document_identity import is_immutable_doc_id
from docs_document_location import canonical_document_viewer_url, sub_scope_report_placement
from docs_management_document_target import confined_source_path, resolve_managed_document_collection
from docs_workspace_config import document_source_path, resolve_workspace_path
from docs_publication_ignore import working_ignored_doc_ids


def read_document_link_targets(repo_root: Path, *, stage: str) -> dict[str, object]:
    """List every configured authoring collection with stage-free document locations.

    Stage selects the source and report host, never the authored href. Explicitly
    ignored ordinary targets are omitted; draft readiness and Subject do not filter selection.
    Unavailable collections and ambiguous host placement fail without fallback.
    """
    collection = resolve_managed_document_collection(repo_root, stage=stage)
    config = collection.parent_config
    if config.stage != "working":
        raise ValueError("Document link authoring requires the Working stage.")
    documents = []
    ignored_ids = working_ignored_doc_ids(repo_root, config)
    for owner in (config, *config.sub_scopes):
        sub_scope = getattr(owner, "sub_scope", "")
        root = resolve_workspace_path(repo_root, document_source_path(owner))
        if not root.is_dir():
            raise FileNotFoundError(f"Document collection is unavailable: {config.stage}/{sub_scope}")
        for path in source_model.document_markdown_paths(root):
            confined_source_path(root.resolve(), path)
        records = source_model.load_document_collection_docs_for_config(repo_root, config, owner)
        # Resolve a child host only when the collection contains selectable documents.
        host_id = ""
        if sub_scope and records:
            _config, _sub_scope, host_id = sub_scope_report_placement(
                repo_root, sub_scope, stage=config.stage,
            )
        for document in records:
            if not is_immutable_doc_id(document.doc_id):
                raise ValueError("Document link targets require an immutable doc_id.")
            if not sub_scope and document.doc_id in ignored_ids:
                continue
            href = canonical_document_viewer_url(
                config, host_id if sub_scope else document.doc_id,
                subdoc_id=document.doc_id if sub_scope else "",
            )
            documents.append({
                "target": {"stage": config.stage, "sub_scope": sub_scope, "doc_id": document.doc_id},
                "title": document.title,
                "href": href,
            })
    return {
        "ok": True,
        "schema_version": "docs_document_link_targets_v2",
        "stage": config.stage,
        "sub_scopes": [owner.sub_scope for owner in config.sub_scopes],
        "documents": documents,
    }
