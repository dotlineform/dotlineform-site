"""Explicit Search and Recent generation from completed Working metadata."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import time
from typing import Any, Mapping

from docs_discovery_selection import DiscoverySelection, read_discovery_selection
from docs_publication_ignore import read_publication_ignore_ids
from docs_publication_paths import shared_path
from docs_publication_queue import read_queue, save_queue, select_shared
from docs_recent_exclusions import read_recent_exclusions
from docs_recent_payload import build_recent_payload, recent_candidates
from docs_source_model import write_text_atomic
from docs_workspace_config import load_docs_workspace_config, select_workspace_stage


def write_recent(workspace: Any, config: Any, discovery: DiscoverySelection, ordinary_updated: Mapping[str, str], pending: dict[str, Any]) -> dict[str, int]:
    """Write and select only changed Recent output; the caller persists the queue."""
    path = shared_path(workspace, "workspace", "recent")
    try:
        previous = json.loads(path.read_bytes())
    except FileNotFoundError:
        previous = None
    payload = build_recent_payload(
        recent_candidates(discovery, ordinary_updated), limit=workspace.recent_limit,
        generated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), exclusions=read_recent_exclusions(config),
    )
    comparable = {key: value for key, value in payload.items() if key != "generated_at"}
    changed = previous is None or {key: value for key, value in previous.items() if key != "generated_at"} != comparable
    if changed:
        write_text_atomic(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
        select_shared(pending, "workspace", "recent")
    return {"docs": len(payload["docs"]), "wrote": int(changed), "skipped": int(not changed)}


def refresh_search_and_recent(repo_root: Path) -> dict[str, Any]:
    """Share discovery selection and queue state without document/media generation."""
    result: dict[str, Any] = {"ok": False, "phase": "discovery", "diagnostics": {}}
    try:
        workspace = load_docs_workspace_config(repo_root)
        config = select_workspace_stage(workspace, "working")
        selection = read_discovery_selection(repo_root, config, read_publication_ignore_ids(repo_root, config=config))
        pending = read_queue(workspace)
        result["phase"] = "selected content"
        build_dir = str(repo_root / "docs-viewer/build")
        if build_dir not in sys.path:
            sys.path.insert(0, build_dir)
        from build_search import DocsViewerSearchDataBuilder

        search = DocsViewerSearchDataBuilder(repo_root=repo_root, stage="working", config=config)
        documents = search.load_discovery_documents(selection)
        result["phase"] = "Recent"
        recent = write_recent(workspace, config, selection, {doc.doc_id: doc.last_updated for doc in documents if not doc.collection}, pending)
        result["diagnostics"]["recent"] = recent
        if recent["wrote"]:
            save_queue(workspace, pending)
        result["phase"] = "Search"
        result["diagnostics"]["search"] = search.run(write=True, force=False, documents=documents, pending=pending)["diagnostics"]
        result.update(ok=True, phase="complete")
    except Exception as error:
        result["error"] = f"Search and Recent refresh failed during {result['phase']}: {error}. Completed effects were retained."
    return result
