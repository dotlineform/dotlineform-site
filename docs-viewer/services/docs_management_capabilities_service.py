"""Docs management capability and source-config read helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import docs_deploy_repo
import docs_local_links
import docs_static_html_export
from docs_preview_snapshot import PREVIEW_MANIFEST_FILENAME
from docs_workspace_config import (
    load_docs_workspace_config,
    document_source_path,
    path_label,
    generated_documents_path,
    generated_search_path,
    preview_documents_path,
    resolve_workspace_path,
)
from docs_document_packages.workspace import workspace_status


def stage_capabilities(repo_root: Path, config: Any, static_html_export: dict[str, Any]) -> dict[str, Any]:
    """Project one exact source stage's capabilities through the owning services."""
    root = resolve_workspace_path(repo_root, document_source_path(config))
    generated_data_path = resolve_workspace_path(repo_root, generated_documents_path(config)) / "index-tree.json"
    preview_root = resolve_workspace_path(repo_root, preview_documents_path(config)).parent
    preview_manifest_path = preview_root / PREVIEW_MANIFEST_FILENAME
    preview_available = preview_manifest_path.is_file() and not preview_manifest_path.is_symlink()
    record = {
        "available": root.exists(),
        "root": path_label(repo_root, document_source_path(config)),
        "generated_data_reads": generated_data_path.exists(),
        "generated_search_reads": resolve_workspace_path(repo_root, generated_search_path(config)).exists(),
        "preview_data_reads": preview_available,
        "preview_search_reads": preview_available,
        "collection_lifecycle": {
            "create_eligible": True,
            "delete_eligible": False,
            "collections": [
                {
                    "collection": collection.collection,
                    "title": collection.title,
                    "source": path_label(repo_root, document_source_path(collection)),
                    "output": path_label(repo_root, generated_documents_path(collection)),
                    "publish_output": path_label(repo_root, preview_documents_path(collection)),
                }
                for collection in config.collections
                if collection.lifecycle is not None
            ],
        },
        "deploy_repo": {"available": False, "preview": False, "apply": False},
        "static_html_export": docs_static_html_export.stage_static_html_export_capability(
            repo_root,
            config,
            workspace_available=static_html_export["preview"] and static_html_export["apply"],
        ),
    }

    authoring = config.stage == "working"
    record["document_authoring"] = record["available"] and authoring
    if config.stage:
        record["stage"] = config.stage
        record["prepare_preview"] = {"preview": authoring, "apply": authoring}
        record["deploy_repo"] = {"available": False, "preview": False, "apply": False}
        if not authoring:
            record["collection_lifecycle"].update(create_eligible=False, delete_eligible=False)
    return record


def capabilities_payload(repo_root: Path) -> Dict[str, Any]:
    data_sharing_workspace = workspace_status(repo_root)
    docs_import_workspace = workspace_status(repo_root, required_paths=("import_staging",))
    static_html_export = docs_static_html_export.static_html_export_capability()
    workspace = load_docs_workspace_config(repo_root)
    stages = {
        selected.stage: stage_capabilities(repo_root, selected, static_html_export)
        for selected in workspace.stages if selected.stage == "working"
    }
    deployment = docs_deploy_repo.deploy_repo_capability(repo_root, workspace)
    preview_root = resolve_workspace_path(repo_root, preview_documents_path(workspace)).parent
    completion = preview_root / PREVIEW_MANIFEST_FILENAME
    preview_available = completion.is_file() and not completion.is_symlink()
    stages["preview"] = {
        "available": preview_available, "stage": "preview", "document_authoring": False,
        "generated_data_reads": False, "generated_search_reads": False,
        "preview_data_reads": preview_available, "preview_search_reads": preview_available,
        "prepare_preview": {"preview": False, "apply": False},
        "deploy_repo": deployment,
        "collection_lifecycle": {"create_eligible": False, "delete_eligible": False, "collections": []},
        "static_html_export": {"preview": False, "apply": False},
    }
    return {
        "ok": True,
        "capabilities": {
            "docs_management": True,
            "generated_data_reads": True,
            "source_config_settings_reads": True,
            "source_config_settings_writes": True,
            "source_editor": True,
            "local_folder_links": docs_local_links.local_folder_links_capability(repo_root),
            "html_import": docs_import_workspace["available"],
            "docs_export": True,
            "document_packages": {
                "available": data_sharing_workspace["available"],
                "message": data_sharing_workspace["message"],
                "prepare": data_sharing_workspace["available"],
                "context": True,
                "review_returned": data_sharing_workspace["available"],
                "atomic_return": True,
            },
            "document_delete": {
                "preview": True,
                "apply": True,
                "collection_detail": True,
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
            "collection_lifecycle": {
                "create_preview": True,
                "create_apply": True,
                "delete_preview": True,
                "delete_apply": True,
            },
            "deploy_repo": {
                "preview": True,
                "apply": True,
            },
            "static_html_export": static_html_export,
            "stages": stages,
        },
    }
