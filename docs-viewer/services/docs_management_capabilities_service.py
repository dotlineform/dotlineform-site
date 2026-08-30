"""Docs management capability and source-config read helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import docs_scope_manifest
import docs_scope_rename
import docs_local_links
import docs_source_config_settings
import docs_static_html_export
import docs_document_transfer
from docs_scope_publish import PUBLISH_MANIFEST_FILENAME
from docs_scope_config import (
    DOCS_SCOPE_CONFIGS,
    document_source_path,
    is_public_readonly_scope,
    path_label,
    generated_documents_path,
    generated_search_path,
    published_documents_path,
    published_search_path,
    resolve_scope_path,
)
from docs_document_packages.workspace import workspace_status


def capability_scope_root_label(repo_root: Path, scope: str, config: Any) -> str:
    del repo_root, config
    return (Path("docs-viewer/scopes") / scope).as_posix()


def capabilities_payload(repo_root: Path) -> Dict[str, Any]:
    data_sharing_workspace = workspace_status(repo_root)
    docs_import_workspace = workspace_status(repo_root, required_paths=("import_staging",))
    static_html_export = docs_static_html_export.static_html_export_capability()
    scopes: Dict[str, Any] = {}
    try:
        manifest = docs_scope_manifest.load_manifest(repo_root)
    except (FileNotFoundError, ValueError):
        manifest = {"scopes": []}
    manifest_scopes = docs_scope_manifest.manifest_scopes_by_id(manifest)
    try:
        scope_configs = docs_source_config_settings.load_docs_scope_configs(repo_root)
    except FileNotFoundError:
        scope_configs = DOCS_SCOPE_CONFIGS
    for scope in sorted(scope_configs):
        config = scope_configs[scope]
        root = resolve_scope_path(repo_root, document_source_path(config))
        manifest_record = manifest_scopes.get(scope)
        generated_data_path = resolve_scope_path(repo_root, generated_documents_path(config)) / "index-tree.json"
        published_root = resolve_scope_path(repo_root, published_documents_path(config)).parent
        published_manifest_path = published_root / PUBLISH_MANIFEST_FILENAME
        published_available = published_manifest_path.is_file() and not published_manifest_path.is_symlink()
        publishable = is_public_readonly_scope(
            viewer_base_url=config.viewer_base_url,
            include_scope_param=config.include_scope_param,
        )
        transfer_capabilities = (
            docs_document_transfer.document_transfer_scope_capabilities(
                repo_root,
                config,
            )
        )
        transfer_capabilities["collections"] = (
            docs_document_transfer.document_transfer_collection_capability_records(
                repo_root,
                config,
            )
        )
        scopes[scope] = {
            "available": root.exists(),
            "scope_type": config.scope_type,
            "root": capability_scope_root_label(repo_root, scope, config),
            "generated_data_reads": generated_data_path.exists(),
            "generated_search_reads": resolve_scope_path(repo_root, generated_search_path(config)).exists(),
            "published_data_reads": published_available,
            "published_search_reads": published_available,
            "publishable": publishable,
            "document_transfer": transfer_capabilities,
            "scope_lifecycle": {
                "manifest_recorded": manifest_record is not None,
                "owner": str((manifest_record or {}).get("owner") or ""),
                "created_by_tool": (manifest_record or {}).get("created_by_tool") is True,
                "delete_eligible": docs_scope_manifest.scope_delete_eligible(manifest_record),
                "rename_eligible": docs_scope_rename.scope_rename_eligible(config, manifest_record),
            },
            "sub_scope_lifecycle": {
                "create_eligible": True,
                "delete_eligible": any(
                    sub_scope.lifecycle is not None
                    for sub_scope in config.sub_scopes
                ),
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
            "static_html_export": docs_static_html_export.scope_static_html_export_capability(
                repo_root,
                scope,
                config,
                workspace_available=static_html_export["preview"] and static_html_export["apply"],
            ),
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
            "document_transfer": {
                "preview": True,
                "apply": True,
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
            "scope_lifecycle": {
                "manifest": True,
                "create_preview": True,
                "create_apply": True,
                "rename_preview": True,
                "rename_apply": True,
                "delete_preview": True,
                "delete_apply": True,
                "sub_scope_create_preview": True,
                "sub_scope_create_apply": True,
                "sub_scope_delete_preview": True,
                "sub_scope_delete_apply": True,
                "publishing_modes": list(docs_scope_manifest.PUBLISHING_MODES),
                "manifest_path": docs_scope_manifest.MANIFEST_REL_PATH.as_posix(),
            },
            "publishing": {
                "status": True,
                "confirm": True,
                "apply": True,
            },
            "static_html_export": static_html_export,
            "scopes": scopes,
        },
    }
