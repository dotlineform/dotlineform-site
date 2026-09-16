"""Docs management capability and source-config read helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import docs_deploy_repo
import docs_local_links
import docs_static_html_export
from docs_publish import PUBLISH_MANIFEST_FILENAME
from docs_workspace_config import (
    load_docs_workspace_config,
    document_source_path,
    path_label,
    generated_documents_path,
    generated_search_path,
    published_documents_path,
    published_search_path,
    resolve_workspace_path,
)
from docs_document_packages.workspace import workspace_status


def stage_capabilities(repo_root: Path, config: Any, static_html_export: dict[str, Any]) -> dict[str, Any]:
    """Project one exact source stage's capabilities through the owning services."""
    root = resolve_workspace_path(repo_root, document_source_path(config))
    generated_data_path = resolve_workspace_path(repo_root, generated_documents_path(config)) / "index-tree.json"
    published_root = resolve_workspace_path(repo_root, published_documents_path(config)).parent
    published_manifest_path = published_root / PUBLISH_MANIFEST_FILENAME
    published_available = published_manifest_path.is_file() and not published_manifest_path.is_symlink()
    record = {
        "available": root.exists(),
        "root": path_label(repo_root, document_source_path(config)),
        "generated_data_reads": generated_data_path.exists(),
        "generated_search_reads": resolve_workspace_path(repo_root, generated_search_path(config)).exists(),
        "published_data_reads": published_available,
        "published_search_reads": published_available,
        "sub_scope_lifecycle": {
            "create_eligible": True,
            "delete_eligible": False,
            "sub_scopes": [
                {
                    "sub_scope": sub_scope.sub_scope,
                    "title": sub_scope.title,
                    "source": path_label(repo_root, document_source_path(sub_scope)),
                    "output": path_label(repo_root, generated_documents_path(sub_scope)),
                    "publish_output": path_label(repo_root, published_documents_path(sub_scope)),
                }
                for sub_scope in config.sub_scopes
                if sub_scope.lifecycle is not None
            ],
        },
        "publishing": {
            "status": True,
            "confirm": True,
            "apply": True,
            "published_available": published_available,
            "published_docs_root": path_label(
                repo_root,
                published_documents_path(config),
            ),
            "published_search_index": path_label(
                repo_root,
                published_search_path(config),
            ),
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
        record["pre_publish"] = {"preview": authoring, "apply": authoring}
        record["publishing"].update({key: config.stage == "pre-publish" for key in ("status", "confirm", "apply")})
        record["deploy_repo"] = {"available": False, "preview": False, "apply": False}
        if not authoring:
            record["sub_scope_lifecycle"].update(create_eligible=False, delete_eligible=False)
    return record


def capabilities_payload(repo_root: Path) -> Dict[str, Any]:
    data_sharing_workspace = workspace_status(repo_root)
    docs_import_workspace = workspace_status(repo_root, required_paths=("import_staging",))
    static_html_export = docs_static_html_export.static_html_export_capability()
    workspace = load_docs_workspace_config(repo_root)
    stages = {
        selected.stage: stage_capabilities(repo_root, selected, static_html_export)
        for selected in workspace.stages
    }
    deployment = docs_deploy_repo.deploy_repo_capability(repo_root, workspace)
    stages["pre-publish"]["deploy_repo"] = deployment
    published_root = resolve_workspace_path(repo_root, published_documents_path(workspace)).parent
    completion = published_root / PUBLISH_MANIFEST_FILENAME
    published_available = completion.is_file() and not completion.is_symlink()
    stages["published"] = {
        "available": published_available, "stage": "published", "document_authoring": False,
        "generated_data_reads": False, "generated_search_reads": False,
        "published_data_reads": published_available, "published_search_reads": published_available,
        "pre_publish": {"preview": False, "apply": False},
        "publishing": {"status": False, "confirm": False, "apply": False},
        "deploy_repo": deployment,
        "sub_scope_lifecycle": {"create_eligible": False, "delete_eligible": False, "sub_scopes": []},
        "static_html_export": {"preview": False, "apply": False},
    }
    return {
        "ok": True,
        "capabilities": {
            "docs_management": True,
            "generated_data_reads": True,
            "source_config_reads": True,
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
                "sub_scope_detail": True,
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
            "sub_scope_lifecycle": {
                "create_preview": True,
                "create_apply": True,
                "delete_preview": True,
                "delete_apply": True,
            },
            "publishing": {
                "status": True,
                "confirm": True,
                "apply": True,
            },
            "deploy_repo": {
                "preview": True,
                "apply": True,
            },
            "static_html_export": static_html_export,
            "stages": stages,
        },
    }
