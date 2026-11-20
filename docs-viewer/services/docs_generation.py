"""Explicit document Build orchestration, separate from artifact execution."""

from __future__ import annotations

from functools import cache, partial
from pathlib import Path
import sys
from typing import Any

from docs_book_toc import BookContents, Chapter, book_contents, changed_book_contents, render_book_contents
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
    adopted_works: dict[str, dict[str, Any]] | None = None,
    media_changes: dict[str, Any] | None = None,
    media_writes: dict[str, dict[str, list[str]]] | None = None,
    book_order: dict[str, Any] | None = None,
    book_manifests: dict[str, dict[str, Any]] | None = None,
    book_chapter_sources: tuple[str, list[dict[str, str]]] | None = None,
    book_toc: tuple[str, BookContents] | None = None,
    finalize_publication: bool = True,
) -> dict[str, Any]:
    """Prepare the requested scope, execute it, and hand off completed effects.

    Supplied records are already authored/validated. Explicit Build loads its
    required sources here. Media-write selections distinguish Save's known
    effects (including an empty map) from deliberate Build/Import selection.
    """
    from docs_builder.collection_metadata import CollectionDocumentSummary, merge_collection_manifest, project_context_catalogue_targets
    from docs_builder.common import monotonic_time
    from docs_builder.inline_icons import TOC_DIRECTIVE
    from docs_builder.links_builder import build_document_links, prepare_document_links
    from docs_builder.media_builds import build_collection_media_snapshot
    from docs_builder.ordinary_metadata import navigation_rows, read_saved_navigation, targeted_document_metadata
    from docs_builder.related_links import prepare_related_links
    from docs_catalogue_projection import CatalogueDocumentProjection
    from docs_workspace_config import generated_documents_path, is_curated_book

    collection = getattr(builder, "collection_id", "")
    working_book = builder.config.stage == "working" and is_curated_book(builder.media_owner)
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
    book_refresh = None
    if collection:
        ordered_docs = sorted(docs, key=builder.doc_sort_key)
        supplied_manifest = (book_manifests or {}).get(collection)
        manifest = supplied_manifest if supplied_manifest is not None else (
            builder.manage_manifest_payload(ordered_docs)
            if builder.config.stage == "working" else builder.public_manifest_payload(ordered_docs)
        )
        selected_manifest_rows = manifest["docs"]
        previous_manifest = None
        if builder.targeted_build:
            previous_manifest = builder.saved_collection_metadata()
            manifest = merge_collection_manifest(previous_manifest, manifest, builder.only_doc_ids)
        if working_book and supplied_manifest is None:
            if not builder.targeted_build:
                from docs_book_tree import book_order_path, read_book_order

                book_order = read_book_order(book_order_path(builder.media_owner))
                if write and (builder.output_dir / builder.manifest_filename).is_file():
                    previous_manifest = builder.saved_collection_metadata()
            if book_order is not None:
                manifest["book_order"] = book_order
            if book_chapter_sources is not None:
                from docs_book_tree import project_chapter_sources

                project_chapter_sources(manifest, *book_chapter_sources)
            if write and previous_manifest is not None:
                book_refresh = changed_book_contents(
                    previous_manifest, manifest, builder.media_owner.report_host_doc_id,
                    selected=set(builder.only_doc_ids) if builder.targeted_build else None,
                )
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
        if not builder.targeted_build and publication is not None:
            previous_tree = publication.metadata.management.get("")
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

    if collection:
        started_at = monotonic_time()
        builder.related_documents = related_documents
        context_rows = {row["doc_id"]: row for row in selected_manifest_rows} if collection == "works" else None
        item_payloads = {}
        for doc in selected_docs:
            item_payloads[doc.doc_id] = builder.item_entry(doc, identities)
            if context_rows is not None:
                project_context_catalogue_targets(
                    context_rows[doc.doc_id], builder.related_works, builder.related_galleries,
                )

    if publication is not None:
        publication.prepare(builder, selected_docs, navigation,
                            manifest=manifest, media_changes=media_changes, media_writes=media_writes)
    recent = None
    if not collection and builder.config.stage == "working" and not builder.targeted_build and not builder.skip_recent:
        recent = builder.recent_payload(navigation["docs"], ignored_ids=publication.ignored, output_path=builder.output_dir / "recent.json")

    project_item = None
    if builder.config.stage == "working":
        catalogue_owner = next((owner for owner in builder.config.collections if owner.collection == "catalogue"), None)
        if catalogue_owner is not None:
            projection = CatalogueDocumentProjection(
                builder.repo_root, generated_documents_path(catalogue_owner) / "by-id",
                builder.workspace.catalogue.working, adopted_works,
            )
            project_item = partial(projection.document, collection=collection)
    if collection:
        result = builder.run(
            write=write, manifest_payload=manifest, item_payloads=item_payloads, stale_item_ids=stale_item_ids,
            started_at=started_at, project_item=project_item,
        )
    else:
        toc_renderers = {}
        if publication is not None:
            hosts = {owner.report_host_doc_id: owner for owner in builder.config.collections if is_curated_book(owner)}
            supplied_books = book_manifests or {}

            def render_saved_toc(collection: str, host: Chapter) -> str:
                saved = supplied_books.get(collection)
                if saved is None:
                    saved = publication.metadata.read_management(collection)
                return render_book_contents(collection, host, book_contents(saved, host.doc_id))

            for doc in selected_docs:
                book = hosts.get(doc.doc_id)
                if book is None or TOC_DIRECTIVE not in doc.body_markdown:
                    continue
                host = Chapter(doc.doc_id, doc.title)
                if book_toc is not None and book_toc[0] == doc.doc_id:
                    renderer = partial(render_book_contents, book.collection, host, book_toc[1])
                else:
                    renderer = partial(render_saved_toc, book.collection, host)
                toc_renderers[doc.doc_id] = cache(renderer)
        result = builder.run(
            write=write, documents=selected_docs, document_identities=identities, stale_item_ids=stale_item_ids,
            related_documents=related_documents, project_item=project_item,
            index_tree_payload=navigation, recent_payload=recent, previous_tree_text=previous_tree_text,
            toc_renderers=toc_renderers,
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
            book_refresh=book_refresh, finalize_publication=finalize_publication,
            automatic_book_host=book_toc is not None,
        )
    if emit_diagnostics:
        builder.print_diagnostics(result["diagnostics"])
    return result


def complete_generation(
    builder: Any, result: dict[str, Any], deleted: list[str], publication: Any, *,
    selected_changed: bool, related_records: dict[Any, Any], expand_dependencies: bool,
    catalogue_work_selection: bool,
    catalogue_pending: dict[str, Any] | None,
    book_refresh: BookContents | None = None,
    finalize_publication: bool, automatic_book_host: bool,
) -> None:
    """Record completed artifacts, finish bounded dependent work, then persist."""
    try:
        doc_ids = set(result["item_payloads"])
        changed_ids = set(result["write_plan"]["changed_item_ids"])
        if automatic_book_host:
            doc_ids &= changed_ids | publication.restored_documents
        publication.documents(builder.media_owner, doc_ids, deleted, changed_ids=changed_ids,
                              catalogue_work_selection=catalogue_work_selection)
        if not finalize_publication:
            return
        supplied = set(result["item_payloads"]) | set(deleted)
        if book_refresh is not None:
            host = rebuild_book_host(
                builder.repo_root, builder.config, builder.workspace, builder.media_owner, book_refresh,
                publication=publication, rendering_inputs=builder.rendering_inputs, related_records=related_records,
            )
            if host is not None:
                result["book_toc"] = host
                supplied.add(host["doc_id"])
        publication.write_metadata()
        if selected_changed:
            publication.selected()
        if result["write_plan"].get("recent_write"):
            publication.shared("workspace", "recent")
        if expand_dependencies:
            links = result["links_build"]
            changed = {Path(name).stem for name in links["written"]} if links is not None else set()
            prepare_dependencies(builder, {target: record for target, record in related_records.items() if target.doc_id in changed},
                                 supplied, publication)
            prepare_restored(builder.config, related_records, publication, rendering_inputs=builder.rendering_inputs)
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


def rebuild_book_host(
    repo_root: Path, config: Any, workspace: Any, book: Any, contents: BookContents, *,
    publication: Any = None, rendering_inputs: Any = None, related_records: dict[Any, Any] | None = None,
) -> dict[str, Any] | None:
    """Render the exact host as an ordinary document with the completed Book order."""
    build_dir = str(repo_root / "docs-viewer/build")
    if build_dir not in sys.path:
        sys.path.insert(0, build_dir)
    from docs_builder.inline_icons import TOC_DIRECTIVE
    from docs_builder.pipeline import DocsDataBuilder

    standalone = publication is None
    if standalone:
        publication = load_preparation(repo_root, workspace)
    parents = saved_navigation_parents(publication)
    host_id = book.report_host_doc_id
    if host_id not in parents:
        raise FileNotFoundError(f"Book host is unavailable in the Index: {host_id}")
    builder = DocsDataBuilder(
        repo_root=repo_root, config=config, workspace=workspace, rendering_inputs=rendering_inputs,
        only_doc_ids=[host_id], links_doc_ids=[], skip_media_builds=True, skip_recent=True,
    )
    docs = builder.load_docs([host_id], parent_ids={host_id: parents[host_id]})
    if not docs:
        raise FileNotFoundError(f"Book host source is unavailable: {host_id}")
    if TOC_DIRECTIVE not in docs[0].body_markdown:
        return None
    result = generate_documents(
        builder, write=True, documents=docs, parent_ids=parents, stale_item_ids=[],
        update_selected=False, publication=publication, related_records=related_records or {},
        expand_dependencies=standalone, finalize_publication=standalone,
        media_writes={host_id: {}}, book_toc=(host_id, contents),
    )
    if host_id in result["write_plan"]["changed_item_ids"]:
        return result["item_payloads"][host_id]
    return None


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
    render_targets(builder.config, targets, related_records, operation, rendering_inputs=builder.rendering_inputs)


def prepare_restored(
    config: Any, related_records: dict[Any, Any], operation: Any, *,
    rendering_inputs: Any = None, finalize_publication: bool = True,
) -> Any:
    """Prepare restored documents and carry their rendering inputs forward."""
    if not operation.metadata.restored:
        return rendering_inputs
    build_dir = str(operation.repo_root / "docs-viewer/build")
    if build_dir not in sys.path:
        sys.path.insert(0, build_dir)
    from docs_builder.links_model import DocumentTarget

    targets = [DocumentTarget(collection, doc_id) for doc_id, collection in operation.metadata.restored.items()]
    return render_targets(config, targets, related_records, operation,
                          rendering_inputs=rendering_inputs, finalize_publication=finalize_publication)


def render_targets(
    config: Any, targets: list[Any], related_records: dict[Any, Any], operation: Any, *,
    rendering_inputs: Any, finalize_publication: bool = True,
) -> Any:
    """Execute only the supplied dependent/restored targets, without expansion."""
    if not targets:
        return rendering_inputs
    from docs_builder.collection import CollectionDocsBuilder
    from docs_builder.pipeline import DocsDataBuilder
    from docs_builder.rendering_inputs import RenderingInputs

    if rendering_inputs is None:
        rendering_inputs = RenderingInputs.load(operation.repo_root)
    owners = {owner.collection: owner for owner in config.collections}
    parents = saved_navigation_parents(operation) if any(not target.collection for target in targets) else None
    for target in targets:
        arguments = {"repo_root": operation.repo_root, "config": config, "workspace": operation.workspace,
                     "rendering_inputs": rendering_inputs, "only_doc_ids": [target.doc_id], "links_doc_ids": [], "skip_media_builds": True}
        neighbour = CollectionDocsBuilder(**arguments, collection=owners[target.collection]) if target.collection else DocsDataBuilder(**arguments, skip_recent=True)
        if target.collection:
            neighbour.collection_manifest = operation.metadata.management.get(target.collection)
        hierarchy = {"parent_ids": parents} if not target.collection else {}
        docs = neighbour.load_docs([target.doc_id], **hierarchy)
        if not docs:
            raise FileNotFoundError(f"Required publication document source is unavailable: {target.doc_id}")
        # A dependency render has no authored media writes. Preparation still
        # selects complete media for an actual eligibility restoration.
        generate_documents(neighbour, write=True, documents=docs, related_records=related_records,
                           publication=operation, expand_dependencies=False, update_selected=False,
                           media_writes={target.doc_id: {}},
                           catalogue_work_selection=False, finalize_publication=finalize_publication, **hierarchy)
    return rendering_inputs


def saved_navigation_parents(publication: Any) -> dict[str, str]:
    parents: dict[str, str] = {}

    def collect(rows: list[dict[str, Any]], parent: str = "") -> None:
        for row in rows:
            parents[row["doc_id"]] = parent
            collect(row.get("children", []), row["doc_id"])

    collect(publication.metadata.read_management("")["docs"])
    return parents
