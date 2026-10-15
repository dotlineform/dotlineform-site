"""Complete synchronous Working document, media and discovery generation."""

from __future__ import annotations

from pathlib import Path
import sys
import time
from typing import Any, Callable

from docs_build_manifest import remove_build_manifest, write_working_build_completion
from docs_discovery_selection import select_built_discovery_documents
from docs_index_order import index_order_path, read_index_order, tree_parent_ids
from docs_publication_ignore import read_publication_ignore_ids
from docs_selected_documents import read_selected, refresh_workspace_selected
from docs_workspace_config import load_docs_workspace_config, require_document_authoring, select_workspace_stage


def rebuild_working_docs_and_search(repo_root: Path) -> dict[str, Any]:
    """Carry one set of validated inputs through every required Working output.

    Media and relationships finish before rendering; Search and Recents consume
    one completed discovery selection. Failure stops at the reached phase and
    retains completed effects, with no rollback or completion receipt.
    """
    build_dir = repo_root / "docs-viewer/build"
    if str(build_dir) not in sys.path:
        sys.path.insert(0, str(build_dir))
    from build_search import DocsViewerSearchDataBuilder, search_records_from_build
    from docs_builder.browser_config import write_browser_config
    from docs_builder.collection import CollectionDocsBuilder
    from docs_builder.common import DOCS_VIEWER_BROWSER_CONFIG_PATH, json_text, write_text
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
            ) for owner in config.collections
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
        catalogue_works: dict[str, dict[str, Any]] = {}
        results = {}
        for name, builder in builders.items():
            results[name] = perform(f"documents/{name or 'ordinary'}", lambda: builder.run(
                write=True, documents=documents[name], related_records=related_records,
                stale_item_ids=stale_ids[name], update_selected=False, catalogue_works=catalogue_works,
                **({"parent_ids": parents} if not name else {}),
            ))
            diagnostics = results[name]["diagnostics"]
            diagnostics["source_files_scanned"] = len(documents[name])
            payload["diagnostics"]["collections"][name or "documents"] = diagnostics
        perform("selected", lambda: refresh_workspace_selected(
            config, [(builder.media_owner, documents[name]) for name, builder in builders.items()], payload=selected,
        ))

        tree = results[""]["index_tree_payload"]["docs"]
        discovery = perform("discovery-selection", lambda: select_built_discovery_documents(
            config, tree, {name: result["manifest_payload"] for name, result in results.items() if name},
            read_publication_ignore_ids(repo_root, config=config),
        ))

        def rebuild_recent() -> dict[str, Any]:
            path = ordinary.output_dir / "recent.json"
            recent = ordinary.recent_payload(
                ordinary.recent_candidates(documents[""], tree, discovery=discovery), output_path=path,
            )
            write_text(path, json_text(recent))
            return {"docs": len(recent["docs"])}

        payload["diagnostics"]["recent"] = perform("recent", rebuild_recent)
        search_builder = DocsViewerSearchDataBuilder(repo_root=repo_root, stage="working", config=config)
        search = perform("search", lambda: search_builder.run(
            write=True, force=False, documents=search_records_from_build(discovery, documents),
        ))
        payload["diagnostics"]["search"] = search["diagnostics"]
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
