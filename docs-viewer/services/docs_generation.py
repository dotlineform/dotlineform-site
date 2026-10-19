"""Explicit document Build orchestration, separate from artifact execution."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from docs_index_order import index_order_path, read_index_order, tree_parent_ids
from docs_publication_preparation import PublicationHandoffError, load_preparation, remove_working_media
from docs_selected_documents import read_selected, refresh_selected_documents


def generate_documents(
    builder: Any, *, write: bool, emit_diagnostics: bool = False,
    documents: list[Any] | None = None, parent_ids: dict[str, str] | None = None,
    selected_payload: dict[str, Any] | None = None,
    related_records: dict[Any, Any] | None = None, stale_item_ids: list[str] | None = None,
    update_selected: bool = True,
    publication: Any = None, expand_dependencies: bool = True,
    catalogue_work_selection: bool = True,
    catalogue_pending: dict[str, Any] | None = None,
    media_changes: dict[str, Any] | None = None,
    media_writes: dict[str, dict[str, list[str]]] | None = None,
) -> dict[str, Any]:
    """Prepare the requested scope, execute it, and hand off completed effects.

    Supplied records are already authored/validated. Explicit Build loads its
    required sources here. Media-write selections distinguish Save's known
    effects (including an empty map) from deliberate Build/Import selection.
    """
    from docs_builder.collection_metadata import CollectionDocumentSummary, merge_collection_manifest
    from docs_builder.links_builder import build_document_links, prepare_document_links
    from docs_builder.media_builds import build_collection_media_snapshot
    from docs_builder.ordinary_metadata import navigation_rows, read_saved_navigation, targeted_document_metadata
    from docs_builder.related_links import prepare_related_links

    collection = getattr(builder, "collection_id", "")
    builder.warnings = []
    if not collection and parent_ids is None:
        parent_ids = tree_parent_ids(read_index_order(index_order_path(builder.config)))
    if documents is None:
        source_ids = builder.only_doc_ids
        if not collection and source_ids is not None:
            source_ids = list(set(source_ids) | set(builder.links_doc_ids or []))
        docs = builder.load_docs(
            source_ids, capture_source_text=not builder.skip_media_builds,
            **({"parent_ids": parent_ids} if not collection else {}),
        )
        if not collection or not builder.targeted_build:
            builder.validate_canonical_doc_ids(docs)
            builder.validate_docs(docs, **({"known_doc_ids": parent_ids} if not collection else {}))
    else:
        docs = documents
        builder.source_files_scanned = 0

    previous_tree = None
    previous_tree_text = None
    if collection:
        ordered_docs = sorted(docs, key=builder.doc_sort_key)
        manifest = (builder.manage_manifest_payload(ordered_docs, subjects_by_doc_id=builder.private_authoring_subjects(ordered_docs))
                    if builder.config.stage == "working" else builder.public_manifest_payload(ordered_docs))
        if builder.targeted_build:
            manifest = merge_collection_manifest(builder.saved_collection_metadata(), manifest, builder.only_doc_ids)
        identities = {row["doc_id"]: CollectionDocumentSummary(row["doc_id"], row["title"]) for row in manifest["docs"]}
        selected_docs = ordered_docs
        navigation = {}
    else:
        metadata_docs = docs
        if builder.targeted_build:
            if publication is None:
                rows, previous_tree, previous_tree_text = read_saved_navigation(builder)
            else:
                previous_tree = publication.metadata.read_management("")
                previous_tree_text = publication.metadata.navigation_text
                rows = navigation_rows(previous_tree)
            metadata_docs = targeted_document_metadata(docs, parent_ids, rows)
        identities = {doc.doc_id: doc for doc in metadata_docs}
        target_ids = builder.only_doc_ids if builder.targeted_build else [doc.doc_id for doc in docs]
        target_set = set(target_ids)
        selected_docs = [doc for doc in docs if doc.doc_id in target_set]
        manifest = None

    if publication is None and builder.config.stage == "working":
        publication = load_preparation(builder.repo_root, builder.workspace, navigation=previous_tree,
                                       navigation_text=previous_tree_text, changes_only=not builder.targeted_build)
    if not collection:
        if previous_tree is None and publication is not None:
            previous_tree = publication.metadata.read_management("")
            previous_tree_text = publication.metadata.navigation_text
        navigation = builder.index_tree_payload(identities, previous_payload=previous_tree)
    if update_selected and selected_payload is None:
        selected_payload = builder.selected_documents() if collection else read_selected(builder.config)
    media_snapshot = None
    if not builder.skip_media_builds and (not collection or not builder.targeted_build) and builder.media_owner.media is not None:
        media_snapshot = build_collection_media_snapshot(
            builder.repo_root, builder.media_owner, write=write,
            markdown_sources=[doc.source_text for doc in docs if doc.source_text is not None],
        )
    target_ids = [doc.doc_id for doc in selected_docs]
    if stale_item_ids is None:
        stale_item_ids = builder.stale_doc_payload_ids(
            target_ids, target_doc_ids=builder.only_doc_ids if builder.targeted_build else None,
        )
    links_build = None
    if related_records is None:
        links_plan = prepare_document_links(builder, docs, builder.only_doc_ids if not collection and builder.targeted_build else target_ids,
                                            stale_item_ids, document_identities=identities)
        related_records = {}
        links_build = build_document_links(builder, links_plan, write=write, related_records=related_records)
    related_documents = prepare_related_links(builder, selected_docs, related_records)

    if publication is not None:
        publication.prepare(builder, selected_docs, navigation,
                            manifest=manifest, media_changes=media_changes, media_writes=media_writes)
    recent = None
    if not collection and builder.config.stage == "working" and not builder.targeted_build and not builder.skip_recent:
        candidates = builder.recent_candidates(docs, navigation["docs"], ignored_ids=publication.ignored)
        recent = builder.recent_payload(candidates, output_path=builder.output_dir / "recent.json")

    result = builder.run(
        write=write, documents=selected_docs, document_identities=identities, stale_item_ids=stale_item_ids,
        related_documents=related_documents,
        **({"manifest_payload": manifest} if collection else {
            "index_tree_payload": navigation, "recent_payload": recent, "previous_tree_text": previous_tree_text,
        }),
    )
    result.update(media_snapshot=media_snapshot, links_build=links_build)
    if write and publication is not None and not collection:
        publication.metadata.navigation_text = result["write_plan"]["index_tree_text"]
    selected_changed = False
    if builder.config.stage == "working" and update_selected:
        selected = refresh_selected_documents(builder.config, builder.media_owner, selected_docs, write=write, payload=selected_payload)
        selected_changed = selected != selected_payload
        if write and collection:
            builder.selected_payload = selected
    if write and publication is not None:
        complete_generation(
            builder, result, stale_item_ids, publication, selected_changed=selected_changed,
            related_records=related_records, expand_dependencies=expand_dependencies,
            catalogue_work_selection=catalogue_work_selection,
            catalogue_pending=catalogue_pending,
        )
    if emit_diagnostics:
        builder.print_diagnostics(result["diagnostics"])
    return result


def complete_generation(
    builder: Any, result: dict[str, Any], deleted: list[str], publication: Any, *,
    selected_changed: bool, related_records: dict[Any, Any], expand_dependencies: bool,
    catalogue_work_selection: bool,
    catalogue_pending: dict[str, Any] | None,
) -> None:
    """Record completed artifacts, finish bounded dependent work, then persist."""
    try:
        publication.documents(builder, set(result["item_payloads"]), deleted,
                              changed_ids=set(result["write_plan"]["changed_item_ids"]),
                              catalogue_work_selection=catalogue_work_selection)
        publication.write_metadata()
        if selected_changed:
            publication.selected()
        if result["write_plan"].get("recent_write"):
            publication.shared("workspace", "recent")
        if expand_dependencies:
            links = result["links_build"]
            changed = {Path(name).stem for name in links["written"]} if links is not None else set()
            prepare_dependencies(builder, {target: record for target, record in related_records.items() if target.doc_id in changed},
                                 set(result["item_payloads"]) | set(deleted), publication)
            prepare_restored(builder, related_records, publication)
        publication.save()
        if publication.catalogue_documents:
            complete_catalogue_handoff(publication, pending=catalogue_pending)
        remove_working_media(publication.working_removals, publication.removal_effects)
    except PublicationHandoffError:
        raise
    except Exception as error:
        raise PublicationHandoffError(
            f"Selected local documents were generated, but their publication handoff is incomplete: {error}. "
            f"Completed Working removals: {len(publication.removal_effects)}.", removal_effects=publication.removal_effects,
        ) from error


def complete_catalogue_handoff(publication: Any, *, pending: dict[str, Any] | None = None) -> None:
    """Keep Catalogue document selections with their existing Work queue owner."""
    from studio.services.catalogue.catalogue_pending_publication import FILENAME, merge_document_selections
    from studio.services.catalogue.catalogue_pending_state import load_pending_queue, pending_path, persist_pending_queue

    path = pending_path(publication.repo_root, FILENAME, workspace=publication.workspace)
    pending = load_pending_queue(path) if pending is None else pending
    merge_document_selections(pending, publication.catalogue_documents)
    persist_pending_queue(path, pending, progress="published")
    publication.catalogue_documents.clear()


def prepare_dependencies(builder: Any, related_records: dict[Any, Any], supplied: set[str], operation: Any) -> None:
    targets = [target for target, record in related_records.items() if target.doc_id not in supplied and record is not None]
    render_targets(builder, targets, related_records, operation)


def prepare_restored(builder: Any, related_records: dict[Any, Any], operation: Any) -> None:
    from docs_builder.links_model import DocumentTarget

    targets = [DocumentTarget(collection, doc_id) for doc_id, collection in operation.metadata.restored.items()]
    render_targets(builder, targets, related_records, operation)


def render_targets(builder: Any, targets: list[Any], related_records: dict[Any, Any], operation: Any) -> None:
    """Execute only the supplied dependent/restored targets, without expansion."""
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
        # A dependency render has no authored media writes. Preparation still
        # selects complete media for an actual eligibility restoration.
        generate_documents(neighbour, write=True, documents=docs, related_records=related_records,
                           publication=operation, expand_dependencies=False, update_selected=False,
                           media_writes={target.doc_id: {}},
                           catalogue_work_selection=False, **hierarchy)
