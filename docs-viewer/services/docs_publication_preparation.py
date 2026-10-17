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


def remove_working_media(removals: dict[tuple[str, str, str], Path], effects: list[dict[str, str]]) -> None:
    """Apply exact owned removals after the workflow has saved their selections."""
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
        self.media_writes: dict[str, dict[str, list[str]]] = {}
        self.ignored = metadata.ignored
        self.metadata = metadata
        self.catalogue_documents: set[str] = set()
        self.changes_only = changes_only
        self.restored_documents: set[str] = set()
        self.media_removals: dict[str, dict[str, list[str]]] = {}
        self.current_owned_media: dict[str, dict[str, set[str]]] = {}
        self.ready_media: dict[str, dict[str, list[str]]] = {}
        self.working_removals: dict[tuple[str, str, str], Path] = {}
        self.removal_effects: list[dict[str, str]] = []

    def prepare(self, builder: Any, docs: list[Any], navigation: dict[str, Any], *, manifest: dict[str, Any] | None, media_changes: dict[str, DocumentMediaChange] | None, media_writes: dict[str, dict[str, list[str]]] | None) -> None:
        """Record selected references and their exact owned-file removals."""
        collection = getattr(builder, "collection_id", "")
        if collection:
            self.metadata.management[collection] = manifest
            if "" not in self.metadata.eligible:
                self.metadata.ordinary(self.metadata.read_management(""))
            self.metadata.collection(collection, manifest)
        else:
            self.metadata.ordinary(navigation)
        self.restored_documents.update({doc.doc_id for doc in docs} & self.metadata.restored.keys())
        for doc in docs:
            change = (media_changes or {}).get(doc.doc_id)
            media = change.current if change is not None else document_media_references(
                builder.media_owner, doc_id=doc.doc_id, body=doc.body_markdown, metadata=doc.front_matter,
            )
            self.media[doc.doc_id] = media
            if media_writes is not None and doc.doc_id in media_writes:
                self.media_writes[doc.doc_id] = media_writes[doc.doc_id]
            else:
                self.media_writes.pop(doc.doc_id, None)
            self.current_owned_media[doc.doc_id] = owned_document_files(doc.doc_id, collection, media)
            self.ready_media[doc.doc_id] = change.ready if change is not None else {}
            removals = change.removed if change is not None else {}
            self.media_removals[doc.doc_id] = removals
            for kind, identities in removals.items():
                root = builder.media_owner.media.types[kind].asset_location.path
                for identity in identities:
                    self.working_removals[(collection, kind, identity)] = confined(root, identity)
            self.metadata.restored.pop(doc.doc_id, None)

    def documents(self, builder: Any, doc_ids: set[str], deleted: list[str], *, changed_ids: set[str], catalogue_work_selection: bool = True) -> None:
        """Select completed document effects under the prepared membership."""
        collection = getattr(builder, "collection_id", "")
        eligible = self.metadata.membership(collection)
        if collection == "catalogue" and catalogue_work_selection:
            self.catalogue_documents.update(doc_ids & eligible)
        targets = {doc_id: collection for doc_id in doc_ids | set(deleted)}
        targets.update(self.metadata.withdrawn)
        for doc_id, owner in targets.items():
            deleting = doc_id in deleted or doc_id not in self.metadata.membership(owner)
            if owner == "catalogue" and catalogue_work_selection and not deleting:
                continue
            media = self.media.get(doc_id, self.pending["current_documents"].get(doc_id, {}).get("media", {}))
            removals = self.media_removals.get(doc_id, {})
            pending = doc_id in self.pending["current_documents"] or doc_id in self.pending["deleted_documents"]
            if deleting:
                # An already-excluded Save has no new withdrawal. Preserve
                # explicit Delete and all pending document/media effects.
                if (doc_id not in self.metadata.withdrawn and not pending and not removals
                        and (self.changes_only or doc_id not in deleted)):
                    continue
            elif self.changes_only and doc_id not in changed_ids and doc_id not in self.restored_documents and not pending and not removals and not self.media_changed(builder.media_owner, media):
                continue
            restored = self.restored_media(builder, doc_id, owner) if doc_id not in deleted else {}
            writes = media if doc_id in self.restored_documents else self.media_writes.get(doc_id, media)
            select_document(self.pending, doc_id, owner, media=writes, current_media=media,
                            removed_media=removals, restored_media=restored, delete=deleting)
        self.restored_documents.difference_update(doc_ids)
        for doc_id in deleted:
            self.metadata.restored.pop(doc_id, None)
        self.metadata.withdrawn.clear()

    def restored_media(self, builder: Any, doc_id: str, collection: str) -> dict[str, list[str]]:
        """Cancel only exact pending removals restored with ready Working bytes."""
        pending = (self.pending["current_documents"].get(doc_id) or self.pending["deleted_documents"].get(doc_id) or {}).get("removed_media", {})
        if not pending or doc_id not in self.current_owned_media:
            return {}
        owned = self.current_owned_media[doc_id]
        ready = self.ready_media[doc_id]
        owner = next(item for item in builder.config.collections if item.collection == collection) if collection else builder.config
        return {kind: [name for name in names if name in owned.get(kind, set()) and
                       (name in ready.get(kind, []) or confined(owner.media.types[kind].asset_location.path, name).is_file())]
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

    def save(self) -> None:
        """Persist the carried Docs selections through their one queue writer."""
        save_queue(self.workspace, self.pending)


def load_preparation(repo_root: Path, workspace: Any, *, ignored_ids: frozenset[str] | None = None, navigation: dict[str, Any] | None = None, navigation_text: str | None = None, changes_only: bool = False) -> PublicationPreparation:
    """Read the queue, current policy and required saved management metadata."""
    working = select_workspace_stage(workspace, "working")
    ignored = read_publication_ignore_ids(repo_root, config=working) if ignored_ids is None else ignored_ids
    if navigation is None:
        navigation_text = confined(generated_documents_path(working), "index-tree.json").read_text(encoding="utf-8")
        navigation = json.loads(navigation_text)
    metadata = PublicMetadata(workspace, ignored, navigation=navigation, navigation_text=navigation_text)
    return PublicationPreparation(repo_root, workspace, read_queue(workspace), metadata, changes_only=changes_only)
