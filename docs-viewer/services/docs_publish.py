"""One awaited queue-only publication operation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping

from docs_catalogue_publication import publish_catalogue_shared, publish_catalogue_works
from docs_catalogue_static import CatalogueStaticInputs
from docs_catalogue_media_transfer import CatalogueMediaTransfers
from docs_publication_queue import has_selections, read_queue
from docs_publication_transfer import SelectedTransfers
from docs_selected_publication import publish_selected_documents
from docs_workspace_config import load_docs_workspace_config
from studio.services.catalogue.catalogue_pending_publication import FILENAME
from studio.services.catalogue.catalogue_pending_state import load_pending_queue, pending_path
from studio.services.catalogue.catalogue_shared_changes import SHARED_FIELDS


def publish_docs(repo_root: Path, body: dict[str, Any], *, client: object | None = None, env_files: Iterable[Path] | None = None, environ: Mapping[str, str] | None = None) -> dict[str, Any]:
    if not isinstance(body, dict) or body:
        raise ValueError("Publish requires an empty request object; its workspace and destinations are configured")
    result: dict[str, Any] = {"ok": False, "complete": False, "phase": "queues", "completed": []}
    try:
        workspace = load_docs_workspace_config(repo_root)
        docs = read_queue(workspace)
        path = pending_path(repo_root, FILENAME, workspace=workspace)
        catalogue = load_pending_queue(path)
        if not has_selections(docs) and not any(catalogue[family] for family in ("current_works", "deleted_works", *SHARED_FIELDS)):
            result.update(ok=True, complete=True, phase="complete", summary_text="Nothing queued for publication.")
            return result
        transfers = SelectedTransfers(repo_root, client=client, env_files=env_files, environ=environ)
        inputs = CatalogueStaticInputs(repo_root, workspace)
        work_media = CatalogueMediaTransfers(repo_root, workspace, transfers, result)
        publish_catalogue_works(repo_root, workspace, catalogue, path, work_media, inputs, result)
        publish_selected_documents(repo_root, workspace, docs, transfers, work_media, inputs, result)
        publish_catalogue_shared(repo_root, workspace, catalogue, path, result)
    except Exception as error:
        detail = str(error) or type(error).__name__
        result.update(error=detail, summary_text=f"Publish stopped during {result['phase']} ({result.get('target', 'queue')}): {detail}. Completed effects were retained.")
        return result
    result.update(ok=True, complete=True, phase="complete", summary_text="Publish complete.")
    result.pop("target", None)
    return result
