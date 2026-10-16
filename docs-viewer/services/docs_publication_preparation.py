"""Working generation handoffs for shared documents and public metadata."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from docs_document_images import generated_thumbnail_filename
from docs_publication_ignore import read_publication_ignore_ids
from docs_publication_metadata import PublicMetadata
from docs_publication_paths import confined
from docs_publication_queue import read_queue, save_queue, select_document, select_shared
from docs_publication_media import HTML_START_TAG_PATTERN, MEDIA_URL_ATTRIBUTE_PATTERN, _media_identity_from_url
from docs_source_model import write_text_atomic
from docs_workspace_config import generated_documents_path, select_workspace_stage


class PublicationHandoffError(RuntimeError):
    """Local generation completed, but its publication handoff is incomplete."""


def media_metadata_path(workspace: Any) -> Path:
    working = select_workspace_stage(workspace, "working")
    return confined(generated_documents_path(working), "publication-media.json")


def write_json(path: Path, value: Any) -> None:
    write_text_atomic(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def document_media(owner: Any, payload: dict[str, Any]) -> dict[str, list[str]]:
    """Extract exact references from completed HTML without media reads."""
    if owner.media is None:
        return {}
    collection = getattr(owner, "collection", "")
    prefix = f"collections/{collection}" if collection else "workspace"
    references: dict[str, set[str]] = {}
    thumbnail = generated_thumbnail_filename(payload, doc_id=payload["doc_id"], collection=collection)
    if thumbnail:
        references["thumbs"] = {thumbnail}
    for tag in HTML_START_TAG_PATTERN.finditer(payload["content_html"]):
        for attribute in MEDIA_URL_ATTRIBUTE_PATTERN.finditer(tag["body"]):
            value = attribute["quoted_value"] if attribute["quote"] else attribute["unquoted_value"]
            for kind in owner.media.types:
                identity = _media_identity_from_url(value, f"docs-media:{prefix}/{kind}")
                if identity:
                    references.setdefault(kind, set()).add(identity)
                    break
    return {kind: sorted(names) for kind, names in references.items()}


class PublicationPreparation:
    """Carry selected metadata, media and queue effects through generation.

    Persistent private data contains only referenced-media/diagram information
    and the last applied exclusion input. Public lists own prior membership;
    management metadata owns hierarchy, Draft and reader fields.
    """

    def __init__(self, repo_root: Path, workspace: Any, media: dict[str, Any], saved_text: str, pending: dict[str, Any], ignored: frozenset[str], *, changes_only: bool = False) -> None:
        self.repo_root = repo_root
        self.workspace = workspace
        self.media = media
        self.saved_text = saved_text
        self.pending = pending
        self.ignored = ignored
        self.metadata = PublicMetadata(workspace, ignored, policy_changed=set(media["ignored"]) != ignored)
        self.policy_applied = False
        self.catalogue_documents: set[str] = set()
        self.mermaid_runtime: Any = None
        self.changes_only = changes_only
        self.restored_documents: set[str] = set()

    def prepare(self, builder: Any, docs: list[Any], payloads: dict[str, Any], navigation: dict[str, Any], *, previous_navigation: dict[str, Any] | None, manifest: dict[str, Any] | None, previous_manifest: dict[str, Any] | None, write: bool) -> None:
        """Finish eligible shared HTML before the builder compares/writes it."""
        collection = getattr(builder, "collection_id", "")
        if self.metadata.policy_changed and not self.policy_applied and collection:
            self.metadata.ordinary(self.metadata.read_management(""), None)
            self.policy_applied = True
        if collection:
            self.metadata.collection(collection, manifest, previous_manifest)
        else:
            self.metadata.ordinary(navigation, previous_navigation)
            self.policy_applied = True
        eligible = self.metadata.membership(collection)
        self.restored_documents.update(set(payloads) & self.metadata.restored.keys())
        records = self.media["documents"]
        for doc in docs:
            previous = records.get(doc.doc_id)
            payload = payloads[doc.doc_id]
            diagrams = []
            if doc.doc_id in eligible:
                from docs_mermaid_preparation import prepare_document_mermaid

                payload, diagrams, self.mermaid_runtime = prepare_document_mermaid(
                    self.repo_root, builder.media_owner, doc, payload, previous,
                    force=not builder.targeted_build, runtime=self.mermaid_runtime, write=write,
                )
                payloads[doc.doc_id] = payload
            media = document_media(builder.media_owner, payload)
            if media or diagrams:
                records[doc.doc_id] = {"collection": collection, "media": media, "mermaid": diagrams}
            else:
                records.pop(doc.doc_id, None)
            self.metadata.restored.pop(doc.doc_id, None)

    def documents(self, builder: Any, payloads: dict[str, Any], deleted: list[str], *, selected: dict[str, Any] | None, changed_ids: set[str], catalogue_work_selection: bool = True) -> None:
        """Queue completed document effects and write only changed public lists."""
        collection = getattr(builder, "collection_id", "")
        eligible = self.metadata.membership(collection)
        if collection == "catalogue" and catalogue_work_selection:
            self.catalogue_documents.update(set(payloads) & eligible)
        targets = {doc_id: collection for doc_id in set(payloads) | set(deleted)}
        targets.update(self.metadata.withdrawn)
        for doc_id, owner in targets.items():
            deleting = doc_id in deleted or doc_id not in self.metadata.membership(owner)
            if owner == "catalogue" and catalogue_work_selection and not deleting:
                continue
            media = self.media["documents"].get(doc_id, {}).get("media", {})
            if self.changes_only:
                pending = doc_id in self.pending["current_documents"] or doc_id in self.pending["deleted_documents"]
                if deleting:
                    if doc_id not in self.metadata.withdrawn and not pending:
                        continue
                elif doc_id not in changed_ids and doc_id not in self.restored_documents and not pending and not self.media_changed(builder.media_owner, media):
                    continue
            select_document(self.pending, doc_id, owner, media=media, delete=deleting)
        self.restored_documents.difference_update(payloads)
        for doc_id in deleted:
            self.media["documents"].pop(doc_id, None)
            self.metadata.restored.pop(doc_id, None)
        self.metadata.withdrawn.clear()
        self.write_metadata()
        if selected is not None:
            self.selected()

    def media_changed(self, owner: Any, media: dict[str, list[str]]) -> bool:
        """Maintenance compares exact referenced local bytes, without a hash ledger."""
        if not media:
            return False
        preview = select_workspace_stage(self.workspace, "preview")
        collection = getattr(owner, "collection", "")
        destination = next(item for item in preview.collections if item.collection == collection) if collection else preview
        for kind, names in media.items():
            for name in names:
                source = confined(owner.media.types[kind].asset_location.path, name)
                target = confined(destination.media.types[kind].asset_location.path, name)
                with source.open("rb") as current:
                    try:
                        saved = target.open("rb")
                    except FileNotFoundError:
                        return True
                    with saved:
                        while block := current.read(1024 * 1024):
                            if block != saved.read(len(block)):
                                return True
                        if saved.read(1):
                            return True
        return False

    def write_metadata(self) -> None:
        for collection, path, payload in self.metadata.changes():
            write_json(path, payload)
            select_shared(self.pending, collection or "workspace", "collection_manifest" if collection else "ordinary_index")
            self.metadata.public[collection] = payload
            self.metadata.public_members[collection] = self.metadata.membership(collection)
        self.metadata.projected.clear()

    def selected(self) -> None:
        """Select the saved author-owned list without filtering or copying it."""
        select_shared(self.pending, "workspace", "selected")

    def shared(self, owner: str, output: str) -> None:
        """Select an already completed shared file without another representation."""
        select_shared(self.pending, owner, output)

    def save(self, *, catalogue_pending: dict[str, Any] | None = None) -> None:
        self.media["ignored"] = sorted(self.ignored)
        text = json.dumps(self.media, ensure_ascii=False, indent=2) + "\n"
        if text != self.saved_text:
            write_text_atomic(media_metadata_path(self.workspace), text)
            self.saved_text = text
        save_queue(self.workspace, self.pending)
        if self.catalogue_documents or catalogue_pending is not None:
            from studio.services.catalogue.catalogue_pending_publication import merge_document_selections, FILENAME
            from studio.services.catalogue.catalogue_pending_state import load_pending_queue, pending_path, persist_pending_queue

            path = pending_path(self.repo_root, FILENAME, workspace=self.workspace)
            pending = load_pending_queue(path) if catalogue_pending is None else catalogue_pending
            merge_document_selections(pending, self.catalogue_documents)
            persist_pending_queue(path, pending, progress="published")
            self.catalogue_documents.clear()


def load_preparation(repo_root: Path, workspace: Any, *, ignored_ids: frozenset[str] | None = None, changes_only: bool = False) -> PublicationPreparation:
    """Read media/policy preparation state and the queue, without corpus metadata."""
    text = media_metadata_path(workspace).read_text(encoding="utf-8")
    media = json.loads(text)
    ignored = frozenset(media["ignored"]) if ignored_ids is None else ignored_ids
    return PublicationPreparation(repo_root, workspace, media, text, read_queue(workspace), ignored, changes_only=changes_only)


def prepare_generation(builder: Any, docs: list[Any], payloads: dict[str, Any], navigation: dict[str, Any], *, previous_navigation: dict[str, Any] | None = None, manifest: dict[str, Any] | None = None, previous_manifest: dict[str, Any] | None = None, preparation: PublicationPreparation | None = None, write: bool) -> PublicationPreparation:
    """Prepare one common document form from this build's completed metadata."""
    if preparation is None:
        ignored = None if builder.targeted_build else read_publication_ignore_ids(builder.repo_root, config=builder.config)
        operation = load_preparation(builder.repo_root, builder.workspace, ignored_ids=ignored, changes_only=not builder.targeted_build)
    else:
        operation = preparation
    operation.prepare(builder, docs, payloads, navigation, previous_navigation=previous_navigation,
                      manifest=manifest, previous_manifest=previous_manifest, write=write)
    return operation


def complete_generation(builder: Any, payloads: dict[str, Any], deleted: list[str], *, selected: dict[str, Any] | None, changed_ids: set[str], related_records: dict[Any, Any], dependency_ids: set[str], preparation: PublicationPreparation, expand_dependencies: bool = True, recent_changed: bool = False, catalogue_work_selection: bool = True) -> None:
    """Persist completed local writes and their exact publication selections."""
    try:
        preparation.documents(builder, payloads, deleted, selected=selected, changed_ids=changed_ids, catalogue_work_selection=catalogue_work_selection)
        if recent_changed:
            preparation.shared("workspace", "recent")
        if expand_dependencies:
            prepare_dependencies(builder, {target: record for target, record in related_records.items() if target.doc_id in dependency_ids}, set(payloads) | set(deleted), preparation)
            prepare_restored(builder, related_records, preparation)
        preparation.save()
    except Exception as error:
        raise PublicationHandoffError(f"Selected local documents were generated, but their publication handoff is incomplete: {error}") from error


def prepare_dependencies(builder: Any, related_records: dict[Any, Any], supplied: set[str], operation: PublicationPreparation) -> None:
    """Render exact affected saved neighbours with the existing rendering owner."""
    targets = [target for target, record in related_records.items() if target.doc_id not in supplied and record is not None]
    render_targets(builder, targets, related_records, operation)


def prepare_restored(builder: Any, related_records: dict[Any, Any], operation: PublicationPreparation) -> None:
    """Complete exact newly eligible documents before their shared files are queued."""
    from docs_builder.links_model import DocumentTarget

    targets = [DocumentTarget(collection, doc_id) for doc_id, collection in operation.metadata.restored.items()]
    render_targets(builder, targets, related_records, operation)


def render_targets(builder: Any, targets: list[Any], related_records: dict[Any, Any], operation: PublicationPreparation) -> None:
    """Read/render only restored or directly dependent sources, with no expansion."""
    if not targets:
        return
    from docs_builder.collection import CollectionDocsBuilder
    from docs_builder.pipeline import DocsDataBuilder

    owners = {owner.collection: owner for owner in builder.config.collections}
    parents: dict[str, str] = {}

    def collect(rows: list[dict[str, Any]], parent: str = "") -> None:
        for row in rows:
            parents[row["doc_id"]] = parent
            collect(row.get("children", []), row["doc_id"])

    collect(operation.metadata.read_management("")["docs"])
    for target in targets:
        arguments = {"repo_root": builder.repo_root, "config": builder.config, "workspace": builder.workspace,
                     "rendering_inputs": builder.rendering_inputs, "only_doc_ids": [target.doc_id], "links_doc_ids": [], "skip_media_builds": True}
        neighbour = CollectionDocsBuilder(**arguments, collection=owners[target.collection]) if target.collection else DocsDataBuilder(**arguments, skip_recent=True)
        hierarchy = {"parent_ids": parents} if not target.collection else {}
        docs = neighbour.load_docs([target.doc_id], **hierarchy)
        if not docs:
            raise FileNotFoundError(f"Required publication document source is unavailable: {target.doc_id}")
        selection = {"catalogue_work_selection": False} if target.collection == "catalogue" else {}
        neighbour.run(write=True, documents=docs, related_records=related_records, publication=operation, expand_dependencies=False,
                      update_selected=False, catalogue_works=builder._catalogue_work_cache, **hierarchy, **selection)


def queue_shared_file(config: Any, output: str, *, pending: dict[str, Any] | None = None) -> None:
    """Queue completed shared bytes without reading or rewriting the input."""
    pending = read_queue(config) if pending is None else pending
    select_shared(pending, "workspace", output)
    save_queue(config, pending)
