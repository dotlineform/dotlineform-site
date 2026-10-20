"""Metadata discovery and exact source inputs for application package preparation."""

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from docs_document_identity import is_document_id
from docs_front_matter import STRICT_FRONT_MATTER_PATTERN, read_front_matter_fields
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
            "parent_id": "",
        }


def selected_ids(owner: ManagedDocumentCollection, values: Any) -> list[str]:
    """Bind a nonempty selection to exact filenames in its configured owner."""
    if not isinstance(values, list) or not values:
        raise ValueError("Package preparation requires a nonempty doc_ids array")
    for value in values:
        if not isinstance(value, str) or not is_document_id(value, collection=owner.collection):
            raise ValueError("Package doc_ids must be exact document identities for their collection")
    return list(dict.fromkeys(values))


def read_sources(owner: ManagedDocumentCollection, doc_ids: list[str]) -> list[PackageSource]:
    """Parse required fields without Subject, readiness, report or corpus validation."""
    sources = []
    for doc_id in doc_ids:
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
        sources.append(PackageSource(path, text, fields, text[match.end():]))
    return sources


def option_records(owner: ManagedDocumentCollection, doc_ids: list[str]) -> list[dict[str, Any]]:
    """Read only metadata for the exact checked collection targets."""
    return [source.metadata() for source in read_sources(owner, doc_ids)]


def _saved_metadata(owner: ManagedDocumentCollection) -> list[dict[str, Any]]:
    path = generated_documents_path(owner.document_config) / "manage-manifest.json"
    if path.resolve() != path:
        raise ValueError("Package metadata must not traverse symlinks")
    payload = json.loads(path.read_bytes())
    return [{"doc_id": row["doc_id"], "title": row["title"], "parent_id": ""} for row in payload["docs"]]


def prepare_selected_context(
    repo_root: Path, owner: ManagedDocumentCollection, doc_ids: list[str], *, profile: dict[str, Any],
) -> tuple[DocumentPackageSourceContext, list[dict[str, Any]], list[dict[str, Any]]]:
    """Carry exact source reads and saved relationship metadata into lazy rendering.

    Unselected document bodies are never opened. Saved collection metadata supplies
    link identities; tree-only profiles construct no rendering owner.
    """
    sources = read_sources(owner, doc_ids)
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
        from docs_builder.collection import CollectionDocsBuilder
        from docs_builder.related_links import prepare_related_links
        from docs_builder.summary_formatting import render_summary_paragraphs

        arguments = {"repo_root": repo_root, "config": owner.parent_config, "workspace": owner.workspace}
        builder = CollectionDocsBuilder(**arguments, collection=owner.document_config)
        for source in sources:
            report = builder.document_report(source.text, source.fields, source.body, source_name=source.path.name)
            source_docs.append(builder.document_record(
                path=source.path, front_matter=source.fields, body_markdown=source.body,
                doc_id=source.doc_id, title=source.title, parent_id="",
                report=report, source_text=source.text,
            ))
        identities.update({doc.doc_id: doc for doc in source_docs})
        builder.related_documents = prepare_related_links(builder, source_docs, {})
    context = DocumentPackageSourceContext(
        repo_root=repo_root, collection=owner.collection,
        return_import_enabled=owner.document_config.supports_return_import,
        workspace_config=owner.parent_config, source_root=owner.source_root, builder=builder,
        source_docs=source_docs, records=[], records_by_id={}, source_docs_by_id=identities,
        children_by_parent={}, render_cache={},
        render_document=(lambda doc: builder.document_content_html(
            doc, identities, summary_html=render_summary_paragraphs(doc.summary),
        )) if render_content else None,
    )
    return context, docs, selected
