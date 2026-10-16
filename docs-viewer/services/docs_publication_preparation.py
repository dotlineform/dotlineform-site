"""Working generation handoffs for shared documents and public metadata."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from docs_document_media_ownership import DocumentMediaChange, document_media_references, owned_document_files
from docs_publication_ignore import read_publication_ignore_ids
from docs_publication_metadata import PublicMetadata
from docs_publication_paths import confined
from docs_publication_queue import read_queue, save_queue, select_document, select_shared
from docs_publication_transfer import delete_path
from docs_source_model import write_text_atomic
from docs_workspace_config import generated_documents_path, select_workspace_stage


class PublicationHandoffError(RuntimeError):
    """Local generation completed, but its publication handoff is incomplete."""

    def __init__(self, message: str, *, phase: str = "publication handoff", removal_effects: list[dict[str, str]] | None = None) -> None:
        super().__init__(message)
        self.phase = phase
        self.removal_effects = removal_effects or []


def write_json(path: Path, value: Any) -> None:
    write_text_atomic(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def save_media_removals(workspace: Any, pending: dict[str, Any], removals: dict[tuple[str, str, str], Path], effects: list[dict[str, str]]) -> None:
    """Save public removals before applying their exact confined Working paths."""
    save_queue(workspace, pending)
    for (collection, kind, identity), path in tuple(removals.items()):
        try:
            delete_path(path)
        except Exception as error:
            raise PublicationHandoffError(
                f"Queue saved; Working removal failed for {collection or 'workspace'}/source/{kind}/{identity}: {error}. "
                f"Completed Working removals: {len(effects)}.",
                phase="Working media removal", removal_effects=effects,
            ) from error
        effects.append({"collection": collection, "role": "source", "media_type": kind, "identity": identity})
        del removals[(collection, kind, identity)]


def complete_source_media_changes(workspace: Any, changes: list[tuple[str, Any, DocumentMediaChange]]) -> None:
    """Finish imported source differences after its existing generation process.

    Generation has saved current selections. Merge only the removals carried
    from the import's loaded target and candidate; do not re-read either source.
    """
    changes = [(doc_id, owner, change) for doc_id, owner, change in changes if change.removed]
    if not changes:
        return
    try:
        pending = read_queue(workspace)
        removals = {}
        for doc_id, owner, change in changes:
            record = pending["current_documents"][doc_id] if doc_id in pending["current_documents"] else pending["deleted_documents"][doc_id]
            selected = record.setdefault("removed_media", {})
            collection = getattr(owner, "collection", "")
            for kind, names in change.removed.items():
                selected[kind] = sorted(set(selected.get(kind, [])) | set(names))
                for identity in names:
                    removals[(collection, kind, identity)] = confined(owner.media.types[kind].asset_location.path, identity)
        save_media_removals(workspace, pending, removals, [])
    except PublicationHandoffError:
        raise
    except Exception as error:
        raise PublicationHandoffError(f"Imported documents generated, but their media-removal handoff is incomplete: {error}") from error


class PublicationPreparation:
    """Carry selected metadata, media and queue effects through generation.

    References, authoring differences and the current exclusion policy live
    only for this operation. Saved public lists supply prior membership.
    """

    def __init__(self, repo_root: Path, workspace: Any, pending: dict[str, Any], metadata: PublicMetadata, *, changes_only: bool = False) -> None:
        self.repo_root = repo_root
        self.workspace = workspace
        self.pending = pending
        self.media: dict[str, dict[str, list[str]]] = {}
        self.ignored = metadata.ignored
        self.metadata = metadata
        self.catalogue_documents: set[str] = set()
        self.changes_only = changes_only
        self.restored_documents: set[str] = set()
        self.media_removals: dict[str, dict[str, list[str]]] = {}
        self.current_owned_media: dict[str, dict[str, set[str]]] = {}
        self.working_removals: dict[tuple[str, str, str], Path] = {}
        self.removal_effects: list[dict[str, str]] = []

    def prepare(self, builder: Any, docs: list[Any], payloads: dict[str, Any], navigation: dict[str, Any], *, manifest: dict[str, Any] | None, media_changes: dict[str, DocumentMediaChange] | None) -> None:
        """Record selected references and their exact owned-file removals."""
        collection = getattr(builder, "collection_id", "")
        if collection:
            self.metadata.management[collection] = manifest
            if "" not in self.metadata.eligible:
                self.metadata.ordinary(self.metadata.read_management(""))
            self.metadata.collection(collection, manifest)
        else:
            self.metadata.ordinary(navigation)
        self.restored_documents.update(set(payloads) & self.metadata.restored.keys())
        for doc in docs:
            change = (media_changes or {}).get(doc.doc_id)
            media = change.current if change is not None else document_media_references(
                builder.media_owner, doc_id=doc.doc_id, body=doc.body_markdown, metadata=doc.front_matter,
            )
            self.media[doc.doc_id] = media
            self.current_owned_media[doc.doc_id] = owned_document_files(doc.doc_id, collection, media)
            removals = change.removed if change is not None else {}
            self.media_removals[doc.doc_id] = removals
            for kind, identities in removals.items():
                root = builder.media_owner.media.types[kind].asset_location.path
                for identity in identities:
                    self.working_removals[(collection, kind, identity)] = confined(root, identity)
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
            media = self.media.get(doc_id, self.pending["current_documents"].get(doc_id, {}).get("media", {}))
            removals = self.media_removals.get(doc_id, {})
            if self.changes_only:
                pending = doc_id in self.pending["current_documents"] or doc_id in self.pending["deleted_documents"]
                if deleting:
                    if doc_id not in self.metadata.withdrawn and not pending and not removals:
                        continue
                elif doc_id not in changed_ids and doc_id not in self.restored_documents and not pending and not removals and not self.media_changed(builder.media_owner, media):
                    continue
            restored = self.restored_media(builder, doc_id, owner) if doc_id not in deleted else {}
            select_document(self.pending, doc_id, owner, media=media, removed_media=removals, restored_media=restored, delete=deleting)
        self.restored_documents.difference_update(payloads)
        for doc_id in deleted:
            self.metadata.restored.pop(doc_id, None)
        self.metadata.withdrawn.clear()
        self.write_metadata()
        if selected is not None:
            self.selected()

    def restored_media(self, builder: Any, doc_id: str, collection: str) -> dict[str, list[str]]:
        """Cancel only exact pending removals restored with ready Working bytes."""
        pending = (self.pending["current_documents"].get(doc_id) or self.pending["deleted_documents"].get(doc_id) or {}).get("removed_media", {})
        if not pending or doc_id not in self.current_owned_media:
            return {}
        owned = self.current_owned_media[doc_id]
        owner = next(item for item in builder.config.collections if item.collection == collection) if collection else builder.config
        return {kind: [name for name in names if name in owned.get(kind, set()) and confined(owner.media.types[kind].asset_location.path, name).is_file()]
                for kind, names in pending.items()}

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
        save_media_removals(self.workspace, self.pending, self.working_removals, self.removal_effects)
        if self.catalogue_documents or catalogue_pending is not None:
            from studio.services.catalogue.catalogue_pending_publication import merge_document_selections, FILENAME
            from studio.services.catalogue.catalogue_pending_state import load_pending_queue, pending_path, persist_pending_queue

            path = pending_path(self.repo_root, FILENAME, workspace=self.workspace)
            pending = load_pending_queue(path) if catalogue_pending is None else catalogue_pending
            merge_document_selections(pending, self.catalogue_documents)
            persist_pending_queue(path, pending, progress="published")
            self.catalogue_documents.clear()


def load_preparation(repo_root: Path, workspace: Any, *, ignored_ids: frozenset[str] | None = None, navigation: dict[str, Any] | None = None, changes_only: bool = False) -> PublicationPreparation:
    """Read the queue, current policy and required saved management metadata."""
    working = select_workspace_stage(workspace, "working")
    ignored = read_publication_ignore_ids(repo_root, config=working) if ignored_ids is None else ignored_ids
    navigation_text = None
    if navigation is None:
        navigation_text = confined(generated_documents_path(working), "index-tree.json").read_text(encoding="utf-8")
        navigation = json.loads(navigation_text)
    metadata = PublicMetadata(workspace, ignored, navigation=navigation, navigation_text=navigation_text)
    return PublicationPreparation(repo_root, workspace, read_queue(workspace), metadata, changes_only=changes_only)


def load_generation_preparation(builder: Any, previous_navigation: dict[str, Any] | None) -> PublicationPreparation:
    """Load the selected build's queue and current exclusion policy once."""
    return load_preparation(builder.repo_root, builder.workspace, navigation=previous_navigation, changes_only=not builder.targeted_build)


def prepare_generation(builder: Any, docs: list[Any], payloads: dict[str, Any], navigation: dict[str, Any], *, manifest: dict[str, Any] | None = None, preparation: PublicationPreparation | None = None, media_changes: dict[str, DocumentMediaChange] | None = None) -> PublicationPreparation:
    """Prepare publication references from this build's completed metadata."""
    operation = load_generation_preparation(builder, None) if preparation is None else preparation
    operation.prepare(builder, docs, payloads, navigation, manifest=manifest, media_changes=media_changes)
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
    except PublicationHandoffError:
        raise
    except Exception as error:
        raise PublicationHandoffError(
            f"Selected local documents were generated, but their publication handoff is incomplete: {error}. "
            f"Completed Working removals: {len(preparation.removal_effects)}.",
            removal_effects=preparation.removal_effects,
        ) from error


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
