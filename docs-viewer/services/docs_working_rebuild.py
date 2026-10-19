"""Complete synchronous Working document, media and discovery generation."""

from __future__ import annotations

from pathlib import Path
import sys
import time
from typing import Any, Callable

from docs_build_manifest import remove_build_manifest, write_working_build_completion
from docs_discovery_selection import DiscoverySelection, read_discovery_metadata, select_built_discovery_documents
from docs_discovery_refresh import write_recent
from docs_index_order import index_order_path, read_index_order, tree_parent_ids
from docs_publication_ignore import read_publication_ignore_ids
from docs_selected_documents import read_selected, refresh_workspace_selected
from docs_publication_preparation import load_preparation
from docs_generation import generate_documents, prepare_dependencies, prepare_restored
from docs_workspace_config import generated_documents_path, load_docs_workspace_config, require_document_authoring, select_workspace_stage


def rebuild_working_docs_and_search(repo_root: Path) -> dict[str, Any]:
    """Carry one set of validated inputs through every required Working output.

    Catalogue generation stays with Regenerate. Changed relationship records
    select exact dependencies after bulk rendering; Search and Recents consume
    one completed discovery selection. Failure retains completed effects.
    """
    build_dir = repo_root / "docs-viewer/build"
    if str(build_dir) not in sys.path:
        sys.path.insert(0, str(build_dir))
    from build_search import DocsViewerSearchDataBuilder, search_records_from_build
    from docs_builder.browser_config import write_browser_config
    from docs_builder.collection import CollectionDocsBuilder
    from docs_builder.common import DOCS_VIEWER_BROWSER_CONFIG_PATH
    from docs_builder.links_builder import build_workspace_document_links
    from docs_builder.links_model import DocumentTarget
    from docs_builder.media_builds import build_collection_media_snapshot
    from docs_builder.pipeline import DocsDataBuilder
    from docs_builder.rendering_inputs import RenderingInputs

    payload: dict[str, Any] = {"ok": False, "phase": "inputs", "steps": [], "diagnostics": {"collections": {}}}

    def perform(label: str, operation: Callable[[], Any]) -> Any:
        payload["phase"] = label
        started_at = time.perf_counter()
        result = operation()
        payload["steps"].append({"phase": label, "elapsed_seconds": round(time.perf_counter() - started_at, 3)})
        return result

    try:
        workspace = load_docs_workspace_config(repo_root)
        config = select_workspace_stage(workspace, "working")
        publication = load_preparation(repo_root, workspace, ignored_ids=read_publication_ignore_ids(repo_root, config=config), changes_only=True)
        require_document_authoring(config)
        remove_build_manifest(repo_root, config)
        rendering_inputs = RenderingInputs.load(repo_root)
        ordinary = DocsDataBuilder(
            repo_root=repo_root, config=config, workspace=workspace, rendering_inputs=rendering_inputs,
            skip_media_builds=True, skip_recent=True,
        )
        builders = {"": ordinary, **{
            owner.collection: CollectionDocsBuilder(
                repo_root=repo_root, config=config, collection=owner, workspace=workspace,
                rendering_inputs=rendering_inputs, skip_media_builds=True,
            ) for owner in config.collections if owner.collection != "catalogue"
        }}
        parents = tree_parent_ids(read_index_order(index_order_path(config)))
        selected = read_selected(config)
        documents = {}
        stale_ids = {}
        for name, builder in builders.items():
            def load_sources() -> Any:
                docs = builder.load_docs(parent_ids=parents if not name else {}, capture_source_text=True)
                builder.validate_canonical_doc_ids(docs)
                builder.validate_docs(docs, known_doc_ids=parents if not name else None)
                return docs

            documents[name] = perform(f"sources/{name or 'documents'}", load_sources)
            stale_ids[name] = builder.stale_doc_payload_ids([doc.doc_id for doc in documents[name]])

        media = {}
        for name, builder in builders.items():
            if builder.media_owner.media is None:
                continue
            media[name or "documents"] = perform(f"media/{name or 'documents'}", lambda: build_collection_media_snapshot(
                repo_root, builder.media_owner, write=True,
                markdown_sources=[doc.source_text for doc in documents[name]],
            ))

        all_documents = {DocumentTarget(name, doc.doc_id): doc for name, docs in documents.items() for doc in docs}
        deleted = [DocumentTarget(name, doc_id) for name, ids in stale_ids.items() for doc_id in ids]
        payload["diagnostics"]["relationships"], related_records = perform("relationships", lambda: build_workspace_document_links(
            ordinary, all_documents, deleted,
        ))
        results = {}
        for name, builder in builders.items():
            results[name] = perform(f"documents/{name or 'ordinary'}", lambda: generate_documents(builder,
                write=True, documents=documents[name], related_records=related_records,
                stale_item_ids=stale_ids[name], update_selected=False, publication=publication, expand_dependencies=False,
                **({"parent_ids": parents} if not name else {}),
            ))
            diagnostics = results[name]["diagnostics"]
            diagnostics["source_files_scanned"] = len(documents[name])
            payload["diagnostics"]["collections"][name or "documents"] = diagnostics

        def rebuild_dependencies() -> None:
            changed = {Path(name).stem for name in payload["diagnostics"]["relationships"]["written"]}
            supplied = {target.doc_id for target in all_documents} | {target.doc_id for target in deleted}
            prepare_dependencies(ordinary, {target: record for target, record in related_records.items() if target.doc_id in changed}, supplied, publication)
            prepare_restored(ordinary, related_records, publication)

        perform("document dependencies", rebuild_dependencies)
        updated_selected = perform("selected", lambda: refresh_workspace_selected(
            config, [(builder.media_owner, documents[name]) for name, builder in builders.items()], payload=selected,
        ))
        if updated_selected != selected:
            publication.selected()
            perform("Selected publication handoff", publication.save)

        tree = results[""]["index_tree_payload"]["docs"]

        def select_discovery() -> DiscoverySelection:
            manifests = {name: result["manifest_payload"] for name, result in results.items() if name}
            eligible = publication.metadata.membership("")
            for owner in config.site_search_collections:
                if owner.collection not in builders and owner.report_host_doc_id in eligible:
                    manifests[owner.collection] = read_discovery_metadata(generated_documents_path(owner) / "manage-manifest.json")
            return select_built_discovery_documents(config, tree, manifests, publication.ignored)

        discovery = perform("discovery-selection", select_discovery)

        payload["diagnostics"]["recent"] = perform("recent", lambda: write_recent(
            workspace, config, discovery, {doc.doc_id: doc.last_updated for doc in documents[""]},
        ))
        if payload["diagnostics"]["recent"]["wrote"]:
            publication.shared("workspace", "recent")
        perform("publication handoff", publication.save)
        search_builder = DocsViewerSearchDataBuilder(repo_root=repo_root, stage="working", config=config)

        def rebuild_search() -> dict[str, Any]:
            built_discovery = DiscoverySelection(discovery.ordinary, [entry for entry in discovery.collections if entry[0].collection in documents])
            search_documents = search_records_from_build(built_discovery, documents)
            for owner, selection in discovery.collections:
                if owner.collection not in documents:
                    search_documents.extend(search_builder.load_named_collection_docs(owner, selection))
            return search_builder.run(write=True, force=False, documents=search_documents)

        search = perform("search", rebuild_search)
        payload["diagnostics"]["search"] = search["diagnostics"]
        if search["diagnostics"]["wrote"]:
            publication.shared("workspace", "search")
            perform("Search publication handoff", publication.save)
        perform("browser-configuration", lambda: write_browser_config(
            repo_root, workspace, path=DOCS_VIEWER_BROWSER_CONFIG_PATH, label="Docs Viewer browser config",
        ))
        payload["build_manifest"] = perform("completion", lambda: write_working_build_completion(repo_root, config))
        payload.update(
            ok=True, phase="complete", media=media,
            docs={"mode": "full", "doc_ids": [], "reason": "complete Working rebuild requested"},
            search={"mode": "full", "doc_ids": []}, summary_text="Docs and Search rebuilt.",
        )
    except Exception as error:
        detail = str(error) or error.__class__.__name__
        payload.update(error=f"Rebuild failed during {payload['phase']}: {detail}", summary_text="Working rebuild incomplete.")
    return payload
