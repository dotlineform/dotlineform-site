"""Plan an exact ordinary Working document subtree move to Notes.

The destination and descendant inclusion are server-owned. Preview is read-only;
Apply must reproduce the same source/configuration/media revision.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, unquote, urlencode, urlsplit, urlunsplit

import docs_source_model as source_model
from docs_document_location import canonical_document_viewer_url
from docs_document_placement_references import (
    MediaCopy, relocate_document_media, rewrite_document_references,
)
from docs_management_document_target import (
    ManagedDocumentCollection, ManagedDocumentTarget, confined_source_path,
    resolve_managed_document_collection,
)
from docs_scope_config import DocsScopeConfig, require_document_authoring, resolve_location_path

ARCHIVE_SCOPE = "notes"
RECEIPT_SCHEMA = "docs_archive_receipt_v1"


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def working_document_url(config: DocsScopeConfig, doc_id: str) -> str:
    url = urlsplit(canonical_document_viewer_url(config, doc_id))
    params = dict(parse_qsl(url.query))
    params.update(scope=config.scope_id, stage="working")
    return urlunsplit(("", "", url.path, urlencode(params), url.fragment))


def _confined_destination(root: Path, candidate: Path) -> None:
    if not candidate.resolve().is_relative_to(root.resolve()) or any(
        path.is_symlink() for path in (candidate, *candidate.parents) if path.is_relative_to(root)
    ):
        raise ValueError("Archive destination escapes its configured root or uses a symlink")


@dataclass(frozen=True)
class ArchivedDocument:
    original: source_model.ScopeDoc
    destination: Path
    text: str


@dataclass(frozen=True)
class ArchivePlan:
    source: ManagedDocumentCollection
    target: ManagedDocumentCollection
    requested_ids: tuple[str, ...]
    documents: tuple[ArchivedDocument, ...]
    media: tuple[MediaCopy, ...]
    revision: str

    def receipt(self) -> dict[str, Any]:
        return {
            "schema_version": RECEIPT_SCHEMA,
            "scope": self.source.scope,
            "stage": "working",
            "doc_ids": list(self.requested_ids),
            "revision": self.revision,
        }

    def preview(self) -> dict[str, Any]:
        return {"ok": True, "document_count": len(self.documents), "receipt": self.receipt()}


def archive_collections(repo_root: Path, scope: str, stage: str) -> tuple[ManagedDocumentCollection, ManagedDocumentCollection]:
    if stage != "working":
        raise ValueError("Archive requires Working documents")
    if scope == ARCHIVE_SCOPE:
        raise ValueError("Documents in Notes are already archived")
    source = resolve_managed_document_collection(repo_root, scope=scope, stage=stage)
    target = resolve_managed_document_collection(repo_root, scope=ARCHIVE_SCOPE, stage="working")
    for collection in (source, target):
        require_document_authoring(collection.parent_config)
        root = collection.source_root
        if not root.is_dir() or not os.access(root, os.R_OK | os.W_OK | os.X_OK):
            raise ValueError(f"Archive document root is unavailable for {collection.scope}")
    return source, target


def archive_capability(repo_root: Path, config: DocsScopeConfig) -> dict[str, Any]:
    try:
        archive_collections(repo_root, config.scope_id, config.stage)
    except (OSError, ValueError) as error:
        return {"available": False, "reason": str(error)}
    return {"available": True, "reason": ""}


def _selected_documents(docs: list[source_model.ScopeDoc], requested: tuple[str, ...]) -> list[source_model.ScopeDoc]:
    by_id = {doc.doc_id: doc for doc in docs}
    missing = set(requested) - by_id.keys()
    if missing:
        raise ValueError("Archive documents were not found: " + ", ".join(sorted(missing)))
    selected = set(requested)
    for doc_id in requested:
        selected.update(source_model.descendant_doc_ids(docs, doc_id))
    return sorted((by_id[doc_id] for doc_id in selected), key=source_model.scope_doc_sort_key)


def _rewrite_links(body: str, document: source_model.ScopeDoc, source: ManagedDocumentCollection,
                   target: ManagedDocumentCollection, docs: list[source_model.ScopeDoc], selected: set[str]) -> str:
    by_path = {doc.path.resolve(): doc.doc_id for doc in docs}

    def rewrite(url: str) -> str:
        parsed = urlsplit(url)
        if parsed.scheme or parsed.netloc:
            return url
        entries = parse_qsl(parsed.query, keep_blank_values=True)
        if len({key for key, _ in entries}) != len(entries):
            return url
        params = dict(entries)
        if params.get("stage", "working") != "working":
            return url
        if parsed.path.rstrip("/") == source.parent_config.viewer_base_url.rstrip("/"):
            if params.get("scope", source.scope) != source.scope or params.get("subdoc"):
                return url
            doc_id = params.get("doc", "")
            if doc_id not in selected:
                return url
            params.update(scope=ARCHIVE_SCOPE, stage="working")
            return urlunsplit(("", "", target.parent_config.viewer_base_url, urlencode(params), parsed.fragment))
        if not parsed.path.startswith("/") and parsed.path.endswith(".md"):
            doc_id = by_path.get((document.path.parent / unquote(parsed.path)).resolve())
            if doc_id:
                owner = target if doc_id in selected else source
                dest = urlsplit(working_document_url(owner.parent_config, doc_id))
                params = {**dict(parse_qsl(dest.query)), **{
                    key: value for key, value in params.items() if key not in {"scope", "stage", "doc", "subdoc"}
                }}
                return urlunsplit(("", "", dest.path, urlencode(params), parsed.fragment))
        return url

    return rewrite_document_references(body, rewrite)


def plan_archive(repo_root: Path, body: dict[str, Any]) -> ArchivePlan:
    """Include descendants once and reject unavailable, conflicting or unsafe targets."""
    if not isinstance(body, dict) or set(body) != {"scope", "stage", "doc_ids"}:
        raise ValueError("Archive requires only scope, stage and doc_ids")
    scope = body["scope"]
    if not isinstance(scope, str) or not scope or scope != scope.strip():
        raise ValueError("Archive scope must be exact")
    ids = body["doc_ids"]
    if not isinstance(ids, list) or not ids or any(not isinstance(item, str) or not item or item != item.strip() for item in ids):
        raise ValueError("Select one or more exact document IDs")
    requested = tuple(sorted(set(ids)))
    source, target = archive_collections(repo_root, scope, body["stage"])
    docs = source_model.load_scope_docs_for_config(repo_root, source.parent_config)
    target_docs = source_model.load_scope_docs_for_config(repo_root, target.parent_config)
    selected_docs = _selected_documents(docs, requested)
    selected = {doc.doc_id for doc in selected_docs}
    target_ids = {doc.doc_id for doc in target_docs}
    media: dict[Path, MediaCopy] = {}
    documents = []
    for doc in selected_docs:
        working_document_url(target.parent_config, doc.doc_id)
        if doc.report and doc.report.id == "docs_subscope":
            raise ValueError("Sub-scope report hosts cannot be archived")
        destination = target.source_root / f"{doc.doc_id}.md"
        confined_source_path(source.source_root, doc.path)
        if doc.path.is_symlink():
            raise ValueError("Archive source cannot be a symlink")
        _confined_destination(target.source_root, destination)
        if doc.doc_id in target_ids or destination.exists():
            raise ValueError(f"Notes already contains document {doc.doc_id}")
        exact = ManagedDocumentTarget(
            scope=scope, sub_scope="", doc_id=doc.doc_id, parent_config=source.parent_config,
            document_config=source.document_config, source_root=source.source_root, document=doc, stage="working",
        )
        rewritten = _rewrite_links(doc.body, doc, source, target, docs, selected)
        rewritten, copies = relocate_document_media(repo_root, exact, target, rewritten)
        for copy in copies:
            previous = media.get(copy.destination)
            if previous and previous.content != copy.content:
                raise ValueError(f"Archive media conflict: {copy.destination.name}")
            media[copy.destination] = copy
            for role in target.parent_config.media.types.values():
                source_root = resolve_location_path(repo_root, role.source_location)
                if copy.destination.is_relative_to(source_root):
                    generated_root = resolve_location_path(repo_root, role.generated_location)
                    generated = generated_root / copy.destination.relative_to(source_root)
                    _confined_destination(generated_root, generated)
                    media[generated] = MediaCopy(copy.source, generated, copy.content)
        metadata = dict(doc.front_matter)
        metadata["parent_id"] = doc.parent_id if doc.parent_id in selected else ""
        text = source_model.format_source(metadata, rewritten, sub_scope="")
        documents.append(ArchivedDocument(doc, destination, text))
    copies = tuple(sorted(media.values(), key=lambda item: str(item.destination)))
    for copy in copies:
        if copy.destination.is_symlink() or (copy.destination.exists() and copy.destination.read_bytes() != copy.content):
            raise ValueError(f"Notes media conflicts with Archive: {copy.destination.name}")
    state = {
        "config": [asdict(source.parent_config), asdict(target.parent_config)],
        "requested": requested,
        "documents": [(doc.original.doc_id, str(doc.original.path), _digest(doc.original.source_text.encode()), doc.text) for doc in documents],
        "media": [(str(copy.source), str(copy.destination), _digest(copy.content), copy.destination.exists()) for copy in copies],
    }
    revision = _digest(json.dumps(state, sort_keys=True, default=str).encode())
    return ArchivePlan(source, target, requested, tuple(documents), copies, revision)


def restore_archive(repo_root: Path, receipt: dict[str, Any]) -> ArchivePlan:
    """Replan from canonical Working sources; the browser cannot choose another target."""
    if not isinstance(receipt, dict) or set(receipt) != {"schema_version", "scope", "stage", "doc_ids", "revision"}:
        raise ValueError("Archive receipt is invalid")
    if receipt["schema_version"] != RECEIPT_SCHEMA:
        raise ValueError("Archive receipt is invalid")
    plan = plan_archive(repo_root, {key: receipt[key] for key in ("scope", "stage", "doc_ids")})
    if plan.receipt() != receipt:
        raise ValueError("Archive selection changed; preview Archive again")
    return plan
