"""Docs management capability and source-config read helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import docs_deploy_repo
import docs_local_links
from docs_workspace_config import (
    load_docs_workspace_config,
    select_workspace_stage,
    document_source_path,
    path_label,
    generated_documents_path,
    generated_search_path,
    resolve_workspace_path,
)
from docs_document_packages.workspace import workspace_status


def workspace_capabilities(repo_root: Path, config: Any) -> dict[str, Any]:
    """Project the configured authoring workspace's capabilities through the owning services."""
    root = resolve_workspace_path(repo_root, document_source_path(config))
    generated_data_path = resolve_workspace_path(repo_root, generated_documents_path(config)) / "index-tree.json"
    record = {
        "available": root.exists(),
        "root": path_label(repo_root, document_source_path(config)),
        "generated_data_reads": generated_data_path.exists(),
        "generated_search_reads": resolve_workspace_path(repo_root, generated_search_path(config)).exists(),
    }

    record["document_authoring"] = record["available"]
    return record


def capabilities_payload(repo_root: Path) -> Dict[str, Any]:
    data_sharing_workspace = workspace_status(repo_root)
    docs_import_workspace = workspace_status(repo_root, required_paths=("import_staging",))
    workspace = load_docs_workspace_config(repo_root)
    selected = select_workspace_stage(workspace, "working")
    local = workspace_capabilities(repo_root, selected)
    destination = docs_deploy_repo.deploy_repo_capability(repo_root, workspace)
    publication = {
        "available": bool(local["available"] and destination["available"]),
        "reason": destination["reason"] if local["available"] else "The Docs workspace is unavailable.",
    }
    return {
        "ok": True,
        "capabilities": {
            "docs_management": True,
            "generated_data_reads": True,
            "source_editor": True,
            "local_folder_links": docs_local_links.local_folder_links_capability(repo_root),
            "html_import": docs_import_workspace["available"],
            "document_packages": {
                "available": data_sharing_workspace["available"],
                "message": data_sharing_workspace["message"],
                "prepare": data_sharing_workspace["available"],
                "context": True,
                "review_returned": data_sharing_workspace["available"],
                "atomic_return": True,
            },
            "docs_import": {
                "available": docs_import_workspace["available"],
                "message": docs_import_workspace["message"],
                "staging_root": (
                    docs_import_workspace.get("paths", {}).get("import_staging")
                    if docs_import_workspace["available"]
                    else docs_import_workspace["root"]
                ),
            },
            "docs_review": {
                "available": data_sharing_workspace["available"],
                "message": data_sharing_workspace["message"],
                "workspace_root": data_sharing_workspace["root"],
            },
            "publish": publication,
            "workspace": local,
        },
    }
