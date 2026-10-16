"""Explicit IDP cutover setup from the completed Full Build/Publish baseline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from docs_builder.runtime_bootstrap import apply_repo_local_env

if __name__ == "__main__":
    apply_repo_local_env()

from docs_builder.collection import CollectionDocsBuilder
from docs_builder.pipeline import DocsDataBuilder
from docs_builder.rendering_inputs import RenderingInputs
from docs_index_order import index_order_path, read_index_order, tree_parent_ids
from docs_publication_ignore import read_publication_ignore_ids
from docs_publication_preparation import PublicationPreparation, confined, preparation_root
from docs_publication_queue import empty_queue
from docs_selected_documents import read_selected
from docs_workspace_config import generated_documents_path, load_docs_workspace_config, select_workspace_stage
from studio.services.catalogue.catalogue_pending_publication import FILENAME
from studio.services.catalogue.catalogue_pending_state import load_pending_queue, pending_path, persist_pending_queue


def initialise(repo_root: Path) -> dict[str, int]:
    """Read sources and completed local payloads once; never render or publish."""
    workspace = load_docs_workspace_config(repo_root)
    config = select_workspace_stage(workspace, "working")
    root = preparation_root(workspace)
    if root.exists():
        raise ValueError("Publication preparation is already initialised")
    rendering = RenderingInputs.load(repo_root)
    parents = tree_parent_ids(read_index_order(index_order_path(config)))
    state = {"documents": {}, "navigation": {}, "eligible": []}
    operation = PublicationPreparation(repo_root, workspace, state, empty_queue(), read_publication_ignore_ids(repo_root, config=config))
    selected = read_selected(config)
    owners = [config, *config.collections]
    for owner in owners:
        collection = getattr(owner, "collection", "")
        arguments = {"repo_root": repo_root, "config": config, "workspace": workspace, "rendering_inputs": rendering, "skip_media_builds": True}
        builder = CollectionDocsBuilder(**arguments, collection=owner) if collection else DocsDataBuilder(**arguments, skip_recent=True)
        docs = builder.load_docs(**({"parent_ids": parents} if not collection else {}))
        output = generated_documents_path(owner)
        payloads = {doc.doc_id: json.loads((output / "by-id" / f"{doc.doc_id}.json").read_bytes()) for doc in docs}
        navigation = json.loads((output / "index-tree.json").read_bytes()) if not collection else {}
        operation.documents(builder, docs, payloads, navigation, [], selected=None, baseline=True)
    operation.selected(selected)
    operation.shared("workspace", "recent", json.loads((generated_documents_path(config) / "recent.json").read_bytes()))
    operation.pending = empty_queue()
    operation.catalogue_documents.clear()
    operation.save()
    catalogue_path = pending_path(repo_root, FILENAME, workspace=workspace)
    catalogue = load_pending_queue(catalogue_path)
    catalogue["header"]["schema"] = "catalogue_publish_pending_v5"
    persist_pending_queue(catalogue_path, catalogue, progress="published")
    confined(workspace.workspace_root.path / "preview", "preview-manifest.json").unlink(missing_ok=True)
    return {"documents": len(state["documents"]), "eligible": len(state["eligible"])}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", required=True, help="Initialise against the user-confirmed published baseline.")
    parser.parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    print(json.dumps(initialise(repo_root)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
