"""Synchronous current-document and direct-neighbour Links maintenance.

Existing Links JSON is the only relationship prior state. A refresh reads no
unrelated Markdown or Links records and never repairs a missing existing record.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Collection
import fcntl
import json
from pathlib import Path
from typing import Any, TYPE_CHECKING
from urllib.parse import quote, unquote, urlsplit

from .common import json_text, render_markdown_to_html
from .links_model import DocumentLinks, DocumentSummary, DocumentTarget, Occurrence, reference_counts, replace_contribution
from .links_schema import read_relationship_payload, relationship_payload
from .semantic_tokens import replace_semantic_tokens
from .source import DocRecord
from docs_document_identity import is_immutable_doc_id
from docs_document_location import canonical_document_viewer_url
from docs_document_subjects import normalize_authoring_subject
from docs_rendered_links import collect_anchors, parse_docs_target, resolve_href
from docs_scope_config import DocsScopeConfig, document_source_path, generated_documents_path, load_docs_scope_configs, resolve_scope_path
from docs_source_model import parse_source, write_text_atomic

CONFIG_PATH = Path("docs-viewer/config/links-builder.json")

if TYPE_CHECKING:
    from .pipeline import DocsDataBuilder


def links_enabled(repo_root: Path, config: DocsScopeConfig) -> bool:
    """Enable all configured collections of the selected scope and Working stage."""
    path = repo_root / CONFIG_PATH
    if not path.is_file():
        return False
    policy = json.loads(path.read_text())
    if not isinstance(policy, dict) or set(policy) != {"scope", "stage"}:
        raise ValueError("Links configuration requires only scope and stage")
    if not isinstance(policy["scope"], str) or not policy["scope"] or policy["scope"] != policy["scope"].strip():
        raise ValueError("Links configuration requires an exact scope")
    if policy["stage"] != "working":
        raise ValueError("Links configuration requires an explicit Working stage")
    return policy["scope"] == config.scope_id and policy["stage"] == config.stage


def _safe_path(root: Path, name: str) -> Path:
    path = root / name
    if root.is_symlink() or path.is_symlink() or path.resolve().parent != root.resolve():
        raise ValueError("Links path must stay inside its configured directory")
    return path


def prepare_document_links(
    builder: DocsDataBuilder, docs: list[DocRecord], built_doc_ids: Collection[str],
    stale_doc_ids: Collection[str],
) -> dict[str, Any] | None:
    """Keep explicit change/creation identities independent of ordinary rendering.

    A create operation or watcher supplies initial creation. Missing files never
    imply creation, and no collection index is read to make that decision.
    """
    if not links_enabled(builder.repo_root, builder.config):
        return None
    selected = builder.links_doc_ids
    doc_ids = set(selected if selected is not None else set(built_doc_ids) | set(stale_doc_ids))
    created = set(builder.links_created_doc_ids)
    if not created <= doc_ids & {doc.doc_id for doc in docs}:
        raise ValueError("Initial Links creation requires exact selected source documents")
    return {"documents": docs, "doc_ids": doc_ids, "new_doc_ids": created, "built_doc_ids": set(built_doc_ids)}


class _DocumentRefresh:
    """Hold only this operation's selected records and affected neighbours."""

    def __init__(self, builder: DocsDataBuilder, plan: dict[str, Any], *, write: bool):
        self.builder = builder
        self.config = builder.config
        self.collection = getattr(builder, "sub_scope_id", "")
        self.owners = {"": self.config, **{owner.sub_scope: owner for owner in self.config.sub_scopes}}
        self.sources = {name: resolve_scope_path(builder.repo_root, document_source_path(owner)) for name, owner in self.owners.items()}
        self.outputs = {name: resolve_scope_path(builder.repo_root, generated_documents_path(owner)) / "by-id" for name, owner in self.owners.items()}
        if builder.source_dir != self.sources[self.collection] or builder.items_dir != self.outputs[self.collection]:
            raise ValueError("Links builder requires the configured source and output locations")
        self.output = self.outputs[""].parent / "links-by-id"
        route = load_docs_scope_configs(builder.repo_root, scope_ids=[builder.scope_id])[builder.scope_id]
        self.routes = tuple({(builder.scope_id, self.config.viewer_base_url), (builder.scope_id, route.viewer_base_url)})
        self.docs = {self.key(doc.doc_id): doc for doc in plan["documents"]}
        self.pending = {self.key(doc_id) for doc_id in plan["built_doc_ids"]} if not write else set()
        self.records: dict[DocumentTarget, DocumentLinks | None] = {}
        self.original: dict[DocumentTarget, str | None] = {}
        self.warnings: list[str] = []
        self.removals: set[DocumentTarget] = set()

    def key(self, doc_id: str) -> DocumentTarget:
        return DocumentTarget(self.config.scope_id, self.collection, doc_id)

    def validate_target(self, target: DocumentTarget) -> None:
        if target.scope != self.config.scope_id or target.sub_scope not in self.owners or not is_immutable_doc_id(target.doc_id):
            raise ValueError("Links requires an exact configured document identity")

    def payload(self, target: DocumentTarget, *, require_eligible: bool = True) -> dict[str, Any] | None:
        """Read one exact generated destination, including its source identity guard."""
        self.validate_target(target)
        source = _safe_path(self.sources[target.sub_scope], f"{target.doc_id}.md")
        doc = self.docs.get(target)
        if not source.is_file():
            return None
        metadata = doc.front_matter if doc else parse_source(source)[0]
        if metadata.get("doc_id") != target.doc_id:
            raise ValueError("Links source document identity does not match")
        if require_eligible and metadata.get("publishable", True) is False:
            return None
        path = _safe_path(self.outputs[target.sub_scope], f"{target.doc_id}.json")
        if target in self.pending and doc:
            return {"doc_id": target.doc_id, "report": doc.report.as_payload() if doc.report else None}
        if not path.is_file():
            return None
        payload = json.loads(path.read_text())
        if not isinstance(payload, dict) or payload.get("doc_id") != target.doc_id:
            raise ValueError("Links target document payload identity does not match")
        return payload

    def viewer_target(self, resolved: dict[str, str]) -> DocumentTarget | None:
        if resolved["scope"] != self.config.scope_id or resolved.get("stage", "") not in {"", self.config.stage}:
            return None
        doc_id, child = resolved["doc_id"], resolved.get("subdoc", "")
        if not is_immutable_doc_id(doc_id) or (child and not is_immutable_doc_id(child)):
            return None
        collection = ""
        if child:
            host = self.payload(DocumentTarget(self.config.scope_id, "", doc_id), require_eligible=False)
            report = host.get("report") if host else None
            if not isinstance(report, dict) or report.get("id") != "docs_subscope":
                return None
            collection = report.get("sub_scope", "")
            if not collection or collection not in self.owners:
                return None
        target = DocumentTarget(self.config.scope_id, collection, child or doc_id)
        return target if self.payload(target) is not None else None

    def summary(self, target: DocumentTarget, doc: DocRecord) -> DocumentSummary:
        resolved = parse_docs_target(resolve_href(doc.viewer_url, "/"), viewer_routes=self.routes)
        if not resolved or self.viewer_target(resolved) != target:
            raise ValueError("Links current document has no exact configured viewer location")
        href = canonical_document_viewer_url(self.config, resolved["doc_id"], subdoc_id=resolved.get("subdoc", ""))
        return DocumentSummary(target, doc.title, href, normalize_authoring_subject(doc.front_matter, folder_supported=True))

    def read(self, target: DocumentTarget, *, deleted: bool = False) -> DocumentLinks | None:
        self.validate_target(target)
        if target in self.records:
            return self.records[target]
        if not deleted and self.payload(target) is None:
            return None
        path = _safe_path(self.output, f"{target.doc_id}.json")
        text = path.read_text() if path.is_file() else None
        if text is not None and deleted:
            payload = json.loads(text)
            owner = DocumentTarget(**payload["self"]["target"])
            if owner != target and owner.scope == target.scope and owner.doc_id == target.doc_id:
                # A completed collection move already transferred this shared
                # filename. The old collection cannot remove the new owner.
                self.validate_target(owner)
                read_relationship_payload(payload, owner)
                if self.payload(owner) is not None:
                    return None
        self.original[target] = text
        record = read_relationship_payload(json.loads(text), target) if text is not None else None
        if record is None:
            self.warnings.append(f"Missing Links JSON for {target.scope}/{self.config.stage}/{target.sub_scope or '(parent)'}/{target.doc_id}; Links update skipped")
        else:
            for neighbour in record.incoming.keys() | record.outgoing.keys():
                self.validate_target(neighbour)
        self.records[target] = record
        return record

    def admit_created(self, target: DocumentTarget, doc: DocRecord) -> None:
        """Initialise explicit creation, or transfer the exact prior move owner.

        A same-ID collection move uses the previous record as its prior state.
        It is accepted only when that old source no longer exists; a live
        duplicate or malformed record still fails without replacement.
        """
        path = _safe_path(self.output, f"{target.doc_id}.json")
        if not path.exists():
            self.records[target] = DocumentLinks(self.summary(target, doc))
            self.original[target] = None
            return
        text = path.read_text()
        payload = json.loads(text)
        owner = DocumentTarget(**payload["self"]["target"])
        self.validate_target(owner)
        record = read_relationship_payload(payload, owner)
        if owner == target:
            return
        if owner.doc_id != target.doc_id or _safe_path(self.sources[owner.sub_scope], f"{owner.doc_id}.md").exists():
            raise ValueError("Links initial creation conflicts with an existing document identity")
        self.records[target] = record
        self.original[target] = text

    def references(self, target: DocumentTarget, doc: DocRecord, href: str) -> dict[DocumentTarget, tuple[Occurrence, ...]]:
        """Parse this document only; resolve viewer hosts or exact relative sources."""
        references = defaultdict(list)
        markdown = replace_semantic_tokens(doc.body_markdown, registry=None, replacer=lambda token: "")
        for anchor in collect_anchors(render_markdown_to_html(markdown)):
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
                    source = self.sources[target.sub_scope] / unquote(raw.path)
                    for collection, root in self.sources.items():
                        if source.resolve().parent == root.resolve() and source.is_file():
                            source = _safe_path(root, source.name)
                            metadata = parse_source(source)[0]
                            doc_id = metadata.get("doc_id")
                            if isinstance(doc_id, str) and is_immutable_doc_id(doc_id):
                                candidate = DocumentTarget(self.config.scope_id, collection, doc_id)
                                if self.payload(candidate) is not None:
                                    neighbour = candidate
                            break
            if neighbour is None:
                continue
            record = self.read(neighbour)
            if record is None:
                continue
            fragment = resolved.get("fragment", "")
            destination = record.document.href + ("#" + quote(unquote(fragment), safe="-._~!$&'()*+,;=:@/?") if fragment else "")
            references[neighbour].append(Occurrence(anchor["text"], destination))
        return {key: tuple(occurrences) for key, occurrences in references.items()}

    def refresh(self, target: DocumentTarget, doc: DocRecord | None) -> tuple[int, int]:
        record = self.read(target, deleted=doc is None)
        if record is None:
            return 0, 0
        before = reference_counts(record.outgoing)
        if doc is None:
            for neighbour in set(record.outgoing) | set(record.incoming):
                other = self.read(neighbour)
                if other is not None:
                    other.incoming.pop(target, None)
                    other.outgoing.pop(target, None)
            self.removals.add(target)
            return 0, sum(before.values())
        summary = self.summary(target, doc)
        previous = record.document
        if previous.target != target:
            # Self-links are rebuilt from current Markdown under the new owner.
            record.incoming.pop(previous.target, None)
            record.outgoing.pop(previous.target, None)
        record.document = summary
        references = self.references(target, doc, summary.href)
        for neighbour in set(record.outgoing) | set(references):
            other = self.read(neighbour)
            if other is not None:
                if previous.target != target:
                    other.incoming.pop(previous.target, None)
                replace_contribution(other.incoming, summary, references.get(neighbour, ()))
        if summary != previous:
            for neighbour in list(record.incoming):
                if neighbour == target:
                    continue
                other = self.read(neighbour)
                if other is not None and previous.target in other.outgoing:
                    occurrences = other.outgoing.pop(previous.target).occurrences
                    if previous.href != summary.href:
                        occurrences = tuple(Occurrence(item.label, summary.href + ("#" + urlsplit(item.href).fragment if urlsplit(item.href).fragment else "")) for item in occurrences)
                        replace_contribution(record.incoming, other.document, occurrences)
                    replace_contribution(other.outgoing, summary, occurrences)
        record.outgoing = {}
        for neighbour, occurrences in references.items():
            replace_contribution(record.outgoing, self.records[neighbour].document, occurrences)
        after = reference_counts(record.outgoing)
        return sum((after - before).values()), sum((before - after).values())


def build_document_links(builder: DocsDataBuilder, plan: dict[str, Any] | None, *, write: bool) -> dict[str, Any] | None:
    """Complete selected refreshes and writes under the existing scope/stage lock."""
    if plan is None:
        return None

    def run() -> dict[str, Any]:
        refresh = _DocumentRefresh(builder, plan, write=write)
        # Admit only genuinely new selected documents before resolving mutual links.
        for doc_id in sorted(plan["new_doc_ids"]):
            key = refresh.key(doc_id)
            doc = refresh.docs[key]
            if doc.publishable:
                refresh.admit_created(key, doc)
        added = deleted = 0
        for doc_id in sorted(plan["doc_ids"]):
            key = refresh.key(doc_id)
            doc = refresh.docs.get(key)
            if doc is not None and not doc.publishable:
                continue
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
        return {"written": [path.name for path in writes], "removed": [path.name for path in removals],
                "occurrences_added": added, "occurrences_deleted": deleted, "warnings": refresh.warnings}

    if write:
        private = builder.repo_root / "var/docs-viewer/links-builder" / builder.scope_id / builder.config.stage
        private.mkdir(parents=True, exist_ok=True)
        with _safe_path(private, "build.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            result = run()
    else:
        result = run()
    builder.warnings.extend(result["warnings"])
    print(f"  links: {len(result['written'])} written; {len(result['removed'])} removed; {result['occurrences_added']} occurrences added; {result['occurrences_deleted']} deleted")
    for warning in result["warnings"]:
        print(f"  warning: {warning}")
    return result
