"""Metadata discovery and exact source inputs for application package preparation."""

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from docs_document_identity import is_document_id
from docs_front_matter import STRICT_FRONT_MATTER_PATTERN, read_front_matter_fields
from docs_index_order import index_order_path, read_index_order, tree_parent_ids
from docs_management_document_target import ManagedDocumentCollection
from docs_workspace_config import generated_documents_path
from docs_document_packages.export_common import flatten_summary
from docs_document_packages.source_context import DocumentPackageSourceContext


@dataclass(frozen=True)
class PackageIdentity:
    """Saved identity/title used by rendering without an unselected source body."""

    doc_id: str
    title: str


@dataclass(frozen=True)
class PackageSource:
    """One confined source read, retained for metadata and optional content rendering."""

    path: Path
    text: str
    fields: dict[str, Any]
    body: str
    parent_id: str

    @property
    def doc_id(self) -> str:
        return self.fields["doc_id"]

    @property
    def title(self) -> str:
        return self.fields["title"]

    def metadata(self) -> dict[str, Any]:
        return {
            "doc_id": self.doc_id, "title": self.title,
            "summary": flatten_summary(self.fields.get("summary", "")),
            "last_updated": self.fields.get("last_updated", ""),
            "parent_id": self.parent_id,
        }


def selected_ids(owner: ManagedDocumentCollection, values: Any) -> list[str]:
    """Bind a nonempty selection to exact filenames in its configured owner."""
    if not isinstance(values, list) or not values:
        raise ValueError("Package preparation requires a nonempty doc_ids array")
    for value in values:
        if not isinstance(value, str) or not is_document_id(value, collection=owner.collection):
            raise ValueError("Package doc_ids must be exact document identities for their collection")
    return list(dict.fromkeys(values))


def read_sources(owner: ManagedDocumentCollection, doc_ids: list[str], parents: dict[str, str]) -> list[PackageSource]:
    """Parse required fields without Subject, readiness, report or corpus validation."""
    sources = []
    for doc_id in doc_ids:
        if not owner.collection and doc_id not in parents:
            raise FileNotFoundError(f"Package document is not in Index: {doc_id}")
        path = owner.source_root / f"{doc_id}.md"
        if path.is_symlink() or path.resolve().parent != owner.source_root:
            raise ValueError("Package source must stay inside its configured collection")
        text = path.read_bytes().decode("utf-8")
        match = STRICT_FRONT_MATTER_PATTERN.match(text)
        if match is None:
            raise ValueError(f"Package source front matter is unavailable: {path.name}")
        fields = {field.key: field.value for field in read_front_matter_fields(match[1], source_name=path.name, strict=True)}
        if fields.get("doc_id") != doc_id:
            raise ValueError(f"Package source identity does not match its filename: {path.name}")
        if not isinstance(fields.get("title"), str):
            raise ValueError(f"Package source title must retain string representation: {path.name}")
        sources.append(PackageSource(path, text, fields, text[match.end():], parents.get(doc_id, "")))
    return sources


def option_records(owner: ManagedDocumentCollection, doc_ids: list[str]) -> list[dict[str, Any]]:
    """Read only metadata for the invoked ordinary subtree or checked flat targets."""
    parents = {} if owner.collection else tree_parent_ids(read_index_order(index_order_path(owner.parent_config)))
    if not owner.collection:
        for doc_id in doc_ids:
            if doc_id not in parents:
                raise FileNotFoundError(f"Package target is not in Index: {doc_id}")
        included = set(doc_ids)
        for doc_id, parent in parents.items():
            if parent in included:
                included.add(doc_id)
        doc_ids = [doc_id for doc_id in parents if doc_id in included]
        if not doc_ids:
            raise FileNotFoundError("Package target is not in Index")
    return [source.metadata() for source in read_sources(owner, doc_ids, parents)]


def _saved_metadata(owner: ManagedDocumentCollection) -> list[dict[str, Any]]:
    filename = "manage-manifest.json" if owner.collection else "index-tree.json"
    path = generated_documents_path(owner.document_config) / filename
    if path.resolve() != path:
        raise ValueError("Package metadata must not traverse symlinks")
    payload = json.loads(path.read_bytes())
    if owner.collection:
        return [{"doc_id": row["doc_id"], "title": row["title"], "parent_id": ""} for row in payload["docs"]]
    records = []

    def collect(rows: list[dict[str, Any]], parent: str = "") -> None:
        for row in rows:
            records.append({"doc_id": row["doc_id"], "title": row["title"], "parent_id": parent})
            collect(row.get("children", []), row["doc_id"])

    collect(payload["docs"])
    return records


def prepare_selected_context(
    repo_root: Path, owner: ManagedDocumentCollection, doc_ids: list[str], *, profile: dict[str, Any],
) -> tuple[DocumentPackageSourceContext, list[dict[str, Any]], list[dict[str, Any]]]:
    """Carry exact source reads and saved relationship metadata into lazy rendering.

    Unselected document bodies are never opened. Saved metadata supplies ancestor,
    child and link identities; tree-only profiles construct no rendering owner.
    """
    parents = {} if owner.collection else tree_parent_ids(read_index_order(index_order_path(owner.parent_config)))
    sources = read_sources(owner, doc_ids, parents)
    tree_only = profile["target"]["record_shape"] == "document_tree"
    render_content = not tree_only and any(mapping["source"] in {"content", "headings"} for mapping in profile["document_fields"])
    metadata = {} if tree_only else {row["doc_id"]: row for row in _saved_metadata(owner)}
    for source in sources:
        metadata[source.doc_id] = source.metadata()
    docs = list(metadata.values())
    selected = [metadata[doc_id] for doc_id in doc_ids]
    builder = None
    source_docs = []
    identities = {row["doc_id"]: PackageIdentity(row["doc_id"], row["title"]) for row in docs}
    if render_content:
        from docs_builder.pipeline import DocsDataBuilder
        from docs_builder.collection import CollectionDocsBuilder
        from docs_builder.related_links import prepare_related_links
        from docs_builder.rendering_inputs import prepare_catalogue_works

        arguments = {"repo_root": repo_root, "config": owner.parent_config, "workspace": owner.workspace}
        builder = CollectionDocsBuilder(**arguments, collection=owner.document_config) if owner.collection else DocsDataBuilder(**arguments)
        for source in sources:
            report = builder.document_report(source.text, source.fields, source.body, source_name=source.path.name)
            source_docs.append(builder.document_record(
                path=source.path, front_matter=source.fields, body_markdown=source.body,
                doc_id=source.doc_id, title=source.title, parent_id=source.parent_id,
                report=report, source_text=source.text,
            ))
        identities.update({doc.doc_id: doc for doc in source_docs})
        builder.related_documents = prepare_related_links(builder, source_docs, {})
        builder._catalogue_work_cache = prepare_catalogue_works(builder, source_docs, {})
    context = DocumentPackageSourceContext(
        repo_root=repo_root, collection=owner.collection,
        return_import_enabled=not owner.collection or owner.document_config.supports_return_import,
        workspace_config=owner.parent_config, source_root=owner.source_root, builder=builder,
        source_docs=source_docs, records=[], records_by_id={}, source_docs_by_id=identities,
        children_by_parent={}, render_cache={},
        render_document=(lambda doc: builder.document_content_html(doc, identities)) if render_content else None,
    )
    return context, docs, selected
