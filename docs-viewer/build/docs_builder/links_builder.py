"""Synchronous current-document and direct-neighbour Links maintenance.

Existing Links JSON is the only relationship prior state. Targeted refreshes
read selected documents, necessary ancestors and directly affected neighbours.
Records are created only when a document relationship needs either endpoint.
"""

from __future__ import annotations

from collections.abc import Collection
import fcntl
import json
from pathlib import Path
from typing import Any, TYPE_CHECKING
from urllib.parse import unquote, urlsplit

from .common import json_text, render_markdown_to_html
from .links_model import DocumentLinks, DocumentSummary, DocumentTarget
from .links_schema import read_relationship_payload, relationship_payload
from .semantic_tokens import replace_semantic_tokens
from .related_links_directive import RELATED_LINKS_PREFIX, render_without_related_links
from .source import DocRecord
from docs_document_identity import is_document_id, is_immutable_doc_id
from docs_document_location import canonical_document_viewer_url
from docs_rendered_links import collect_anchors, parse_docs_target, resolve_href
from docs_workspace_config import DocsStageConfig, document_source_path, generated_documents_path, resolve_workspace_path
from docs_source_model import parse_source, write_text_atomic
from docs_publication_ignore import WorkingPublicationExclusions, working_ignored_doc_ids

CONFIG_PATH = Path("docs-viewer/config/links-builder.json")

if TYPE_CHECKING:
    from .pipeline import DocsDataBuilder


def links_enabled(repo_root: Path, config: DocsStageConfig) -> bool:
    """Enable the configured Working collections; other stages do not own Links."""
    path = repo_root / CONFIG_PATH
    if not path.is_file():
        return False
    policy = json.loads(path.read_text())
    if not isinstance(policy, dict) or set(policy) != {"stage"}:
        raise ValueError("Links configuration requires only stage")
    if policy["stage"] != "working":
        raise ValueError("Links configuration requires an explicit Working stage")
    return policy["stage"] == config.stage


def _safe_path(root: Path, name: str) -> Path:
    path = root / name
    if root.is_symlink() or path.is_symlink() or path.resolve().parent != root.resolve():
        raise ValueError("Links path must stay inside its configured directory")
    return path


def prepare_document_links(
    builder: DocsDataBuilder, docs: list[DocRecord], built_doc_ids: Collection[str],
    stale_doc_ids: Collection[str],
) -> dict[str, Any] | None:
    """Keep exact changed/deleted identities independent of ordinary rendering."""
    if not links_enabled(builder.repo_root, builder.config):
        return None
    selected = builder.links_doc_ids if builder.links_doc_ids is not None else builder.only_doc_ids
    doc_ids = set(selected if selected is not None else set(built_doc_ids) | set(stale_doc_ids))
    return {"documents": docs, "doc_ids": doc_ids, "built_doc_ids": set(built_doc_ids)}


class _DocumentRefresh:
    """Hold only this operation's selected records and affected neighbours."""

    def __init__(self, builder: DocsDataBuilder, plan: dict[str, Any]):
        self.builder = builder
        self.config = builder.config
        self.collection = getattr(builder, "collection_id", "")
        self.owners = {"": self.config, **{owner.collection: owner for owner in self.config.collections}}
        self.collection_by_host = {owner.report_host_doc_id: owner.collection for owner in self.config.collections}
        self.sources = {name: resolve_workspace_path(builder.repo_root, document_source_path(owner)) for name, owner in self.owners.items()}
        self.outputs = {name: resolve_workspace_path(builder.repo_root, generated_documents_path(owner)) / "by-id" for name, owner in self.owners.items()}
        if builder.source_dir != self.sources[self.collection] or builder.items_dir != self.outputs[self.collection]:
            raise ValueError("Links builder requires the configured source and output locations")
        self.output = self.outputs[""].parent / "links-by-id"
        self.routes = ("/docs/", builder.workspace.public_viewer_base_url)
        self.docs = {self.key(doc.doc_id): doc for doc in plan["documents"]}
        self.metadata = {target: doc.front_matter for target, doc in self.docs.items()}
        self.exclusions = WorkingPublicationExclusions(
            self.sources[""], working_ignored_doc_ids(builder.repo_root, self.config),
            {doc.doc_id: doc.parent_id for doc in plan["documents"]} if not self.collection else None,
        )
        self.pending = {self.key(doc_id) for doc_id in plan["built_doc_ids"]}
        self.records: dict[DocumentTarget, DocumentLinks | None] = {}
        self.original: dict[DocumentTarget, str | None] = {}
        self.removals: set[DocumentTarget] = set()

    def key(self, doc_id: str) -> DocumentTarget:
        return DocumentTarget(self.collection, doc_id)

    def validate_target(self, target: DocumentTarget) -> None:
        if target.collection not in self.owners or not is_document_id(target.doc_id, collection=target.collection):
            raise ValueError("Links requires an exact configured document identity")

    def excluded(self, target: DocumentTarget) -> bool:
        return not target.collection and self.exclusions.excludes(target.doc_id)

    def payload(self, target: DocumentTarget) -> dict[str, Any] | None:
        """Read one exact generated destination, including its source identity guard."""
        self.validate_target(target)
        source = _safe_path(self.sources[target.collection], f"{target.doc_id}.md")
        doc = self.docs.get(target)
        if not source.is_file():
            return None
        metadata = self.metadata.get(target)
        if metadata is None:
            metadata = parse_source(source)[0]
            self.metadata[target] = metadata
        if metadata.get("doc_id") != target.doc_id:
            raise ValueError("Links source document identity does not match")
        if self.excluded(target):
            return None
        path = _safe_path(self.outputs[target.collection], f"{target.doc_id}.json")
        if target in self.pending and doc:
            return {"doc_id": target.doc_id, "report": doc.report.as_payload() if doc.report else None}
        if not path.is_file():
            return None
        payload = json.loads(path.read_text())
        if not isinstance(payload, dict) or payload.get("doc_id") != target.doc_id:
            raise ValueError("Links target document payload identity does not match")
        return payload

    def viewer_target(self, resolved: dict[str, str]) -> DocumentTarget | None:
        if resolved.get("kind") != "viewer":
            return None
        doc_id, child = resolved["doc_id"], resolved.get("subdoc", "")
        if not is_immutable_doc_id(doc_id):
            return None
        collection = ""
        if child:
            collection = self.collection_by_host.get(doc_id, "")
            if not collection or not is_document_id(child, collection=collection):
                return None
        target = DocumentTarget(collection, child or doc_id)
        return target if self.payload(target) is not None else None

    def summary(self, target: DocumentTarget, doc: DocRecord | None = None) -> DocumentSummary:
        if doc is None:
            payload = self.payload(target)
            if payload is None:
                raise ValueError("Links endpoint requires its exact source and generated document")
            metadata = self.metadata[target]
            title = str(metadata.get("title") or payload["title"]).strip()
            return DocumentSummary(target, title)
        resolved = parse_docs_target(resolve_href(doc.viewer_url, "/"), viewer_routes=self.routes)
        if not resolved or self.viewer_target(resolved) != target:
            raise ValueError("Links current document has no exact configured viewer location")
        return DocumentSummary(target, doc.title)

    def location(self, target: DocumentTarget) -> str:
        """Derive navigation from exact identity and configured report placement."""
        self.validate_target(target)
        host_id = self.owners[target.collection].report_host_doc_id if target.collection else target.doc_id
        return canonical_document_viewer_url(host_id, subdoc_id=target.doc_id if target.collection else "", subdoc_collection=target.collection)

    def read(self, target: DocumentTarget, *, deleted: bool = False) -> DocumentLinks | None:
        self.validate_target(target)
        if target in self.records:
            return self.records[target]
        if not deleted and self.payload(target) is None:
            return None
        path = _safe_path(self.output, f"{target.doc_id}.json")
        text = path.read_text() if path.is_file() else None
        record = None
        if text is not None:
            payload = json.loads(text)
            owner = DocumentTarget(payload["self"]["collection"], payload["self"]["doc_id"])
            self.validate_target(owner)
            record = read_relationship_payload(payload, owner)
            if owner != target:
                if owner.doc_id != target.doc_id:
                    raise ValueError("Links record identity does not match its exact document")
                # A completed collection move already transferred this shared
                # filename. The old collection cannot remove the new owner.
                if deleted and self.payload(owner) is not None:
                    return None
                if _safe_path(self.sources[owner.collection], f"{owner.doc_id}.md").exists():
                    raise ValueError("Links record conflicts with an existing document identity")
        self.original[target] = text
        if record is not None:
            for neighbour in record.incoming.keys() | record.outgoing.keys():
                self.validate_target(neighbour)
        self.records[target] = record
        return record

    def initialise_endpoint(self, target: DocumentTarget, summary: DocumentSummary | None = None) -> DocumentLinks:
        """Create an available endpoint only when a resolved relationship needs it."""
        record = self.read(target)
        if record is not None:
            return record
        record = DocumentLinks(summary or self.summary(target, self.docs.get(target)))
        self.records[target] = record
        return record

    def references(self, target: DocumentTarget, doc: DocRecord, href: str) -> dict[DocumentTarget, DocumentSummary]:
        """Resolve this document's anchors to unique available endpoint summaries."""
        references = {}
        markdown = replace_semantic_tokens(doc.body_markdown, registry=None, replacer=lambda token: "")
        rendered = render_without_related_links(markdown) if RELATED_LINKS_PREFIX in markdown else render_markdown_to_html(markdown)
        for anchor in collect_anchors(rendered):
            authored = anchor["href"]
            if not authored or authored.startswith("#"):
                continue
            resolved = parse_docs_target(resolve_href(authored, href), viewer_routes=self.routes)
            neighbour = None
            if resolved and resolved["kind"] == "viewer":
                neighbour = self.viewer_target(resolved)
            elif resolved and resolved["kind"] == "source_markdown":
                raw = urlsplit(authored)
                if not raw.scheme and not raw.netloc:
                    source = self.sources[target.collection] / unquote(raw.path)
                    for collection, root in self.sources.items():
                        if source.resolve().parent == root.resolve() and source.is_file():
                            source = _safe_path(root, source.name)
                            metadata = parse_source(source)[0]
                            doc_id = metadata.get("doc_id")
                            if isinstance(doc_id, str) and is_document_id(doc_id, collection=collection):
                                candidate = DocumentTarget(collection, doc_id)
                                if self.payload(candidate) is not None:
                                    neighbour = candidate
                            break
            if neighbour is None:
                continue
            if neighbour not in references:
                endpoint = self.initialise_endpoint(neighbour)
                references[neighbour] = (endpoint.document if endpoint.document.target == neighbour
                                         else self.summary(neighbour, self.docs.get(neighbour)))
        return references

    def refresh(self, target: DocumentTarget, doc: DocRecord | None) -> tuple[int, int]:
        record = self.read(target, deleted=doc is None)
        if doc is None:
            if record is None:
                return 0, 0
            before = set(record.outgoing)
            for neighbour in set(record.outgoing) | set(record.incoming):
                other = self.read(neighbour)
                if other is not None:
                    other.incoming.pop(target, None)
                    other.outgoing.pop(target, None)
            self.removals.add(target)
            return 0, len(before)
        summary = self.summary(target, doc)
        previous = record.document if record is not None else summary
        before = set(record.outgoing) if record is not None else set()
        if record is not None and previous.target != target:
            # Self-links are rebuilt from current Markdown under the new owner.
            record.incoming.pop(previous.target, None)
            record.outgoing.pop(previous.target, None)
        if record is not None:
            record.document = summary
            record.incoming = {key: value for key, value in record.incoming.items() if not self.excluded(key)}
        references = self.references(target, doc, self.location(target))
        if record is None:
            if not references:
                return 0, 0
            record = self.initialise_endpoint(target, summary)
        for neighbour in set(record.outgoing) | set(references):
            other = self.read(neighbour)
            if other is not None:
                if previous.target != target:
                    other.incoming.pop(previous.target, None)
                if neighbour in references:
                    other.incoming[target] = summary
                else:
                    other.incoming.pop(target, None)
        if summary != previous:
            for neighbour in list(record.incoming):
                if neighbour == target:
                    continue
                other = self.read(neighbour)
                if other is not None and previous.target in other.outgoing:
                    other.outgoing.pop(previous.target)
                    if previous.target != summary.target:
                        record.incoming[neighbour] = other.document
                    other.outgoing[target] = summary
        record.outgoing = references
        after = set(record.outgoing)
        return len(after - before), len(before - after)


def build_document_links(
    builder: DocsDataBuilder, plan: dict[str, Any] | None, *, write: bool,
    related_records: dict[DocumentTarget, DocumentLinks | None] | None = None,
) -> dict[str, Any] | None:
    """Refresh selected Links before rendering; share the resulting records."""
    if plan is None:
        return None

    def run() -> dict[str, Any]:
        refresh = _DocumentRefresh(builder, plan)
        added = deleted = 0
        for doc_id in sorted(plan["doc_ids"]):
            key = refresh.key(doc_id)
            doc = refresh.docs.get(key)
            if refresh.excluded(key):
                if not _safe_path(refresh.output, f"{key.doc_id}.json").exists():
                    continue
                doc = None
            new, removed = refresh.refresh(key, doc)
            added += new
            deleted += removed
        writes = {}
        for key, record in sorted(refresh.records.items()):
            if record is None or key in refresh.removals:
                continue
            content = json_text(relationship_payload(record))
            if content != refresh.original[key]:
                writes[_safe_path(refresh.output, f"{key.doc_id}.json")] = content
        removals = [_safe_path(refresh.output, f"{key.doc_id}.json") for key in sorted(refresh.removals)]
        if write:
            for path, content in writes.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                write_text_atomic(path, content)
            for path in removals:
                path.unlink()
        if related_records is not None:
            related_records.update(refresh.records)
            for key in refresh.removals:
                related_records[key] = None
            for doc_id in plan["doc_ids"]:
                related_records.setdefault(refresh.key(doc_id), None)
        return {"written": [path.name for path in writes], "removed": [path.name for path in removals],
                "relationships_added": added, "relationships_removed": deleted}

    if write:
        private = builder.repo_root / "var/docs-viewer/links-builder" / builder.config.stage
        private.mkdir(parents=True, exist_ok=True)
        with _safe_path(private, "build.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            result = run()
    else:
        result = run()
    print(f"  links: {len(result['written'])} written; {len(result['removed'])} removed; {result['relationships_added']} relationships added; {result['relationships_removed']} removed")
    return result
