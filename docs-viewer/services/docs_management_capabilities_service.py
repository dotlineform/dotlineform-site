"""Docs management capability and source-config read helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import docs_scope_manifest
import docs_scope_rename
import docs_source_config_settings
import docs_static_html_export
import docs_subtree_copy
import docs_source_model as source_model
from docs_scope_config import (
    DOCS_SCOPE_CONFIGS,
    DOCUMENT_SOURCE_ROOTS,
    LOCAL_EXTERNAL_SCOPE_TYPE,
    document_source_path,
    is_public_readonly_scope,
    path_label,
    publication_documents_path,
    publication_search_path,
    published_documents_path,
    published_search_path,
    resolve_scope_path,
)
from services.paths import workspace_status


def capability_scope_docs(repo_root: Path, scope: str, root: Path) -> list[Any]:
    if not root.exists():
        return []
    if scope in DOCUMENT_SOURCE_ROOTS:
        return source_model.load_scope_docs(repo_root, scope)

    docs = []
    for path in source_model.scope_markdown_paths(root, scope):
        front_matter, body = source_model.parse_source(path)
        doc_id = str(front_matter.get("doc_id") or "").strip()
        if not doc_id:
            raise ValueError(f"missing required doc_id in {path.relative_to(root).as_posix()}")
        title = str(front_matter.get("title") or source_model.humanize(doc_id or path.stem)).strip() or doc_id
        docs.append(
            source_model.ScopeDoc(
                scope=scope,
                path=path,
                source_text=path.read_text(encoding="utf-8"),
                front_matter=dict(front_matter),
                body=body,
                doc_id=doc_id,
                title=title,
                ui_status=source_model.normalize_ui_status(front_matter.get("ui_status")),
                parent_id=str(front_matter.get("parent_id") or "").strip(),
                viewable=source_model.doc_is_viewable(front_matter),
            )
        )
    return docs


def capability_scope_root_label(repo_root: Path, scope: str, config: Any) -> str:
    if config.scope_type == LOCAL_EXTERNAL_SCOPE_TYPE:
        return (Path("source") / scope).as_posix()
    return path_label(repo_root, document_source_path(config))


def copy_subtree_target_available(repo_root: Path, config: Any) -> bool:
    try:
        docs_subtree_copy.require_copy_source_root(
            repo_root,
            config,
            require_writable=True,
        )
    except (OSError, ValueError):
        return False
    return True


def capabilities_payload(repo_root: Path) -> Dict[str, Any]:
    data_sharing_workspace = workspace_status(repo_root)
    docs_import_workspace = workspace_status(repo_root, required_paths=("import_staging",))
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
        scope_docs = capability_scope_docs(repo_root, scope, root)
        manifest_record = manifest_scopes.get(scope)
        generated_data_path = resolve_scope_path(repo_root, published_documents_path(config)) / "index-tree.json"
        publishable = is_public_readonly_scope(
            viewer_base_url=config.viewer_base_url,
            include_scope_param=config.include_scope_param,
        )
        scopes[scope] = {
            "available": root.exists(),
            "scope_type": config.scope_type,
            "root": capability_scope_root_label(repo_root, scope, config),
            "generated_data_reads": generated_data_path.exists(),
            "generated_search_reads": resolve_scope_path(repo_root, published_search_path(config)).exists(),
            "publishable": publishable,
            "copy_subtree_target": copy_subtree_target_available(repo_root, config),
            "count": len(scope_docs),
            "scope_lifecycle": {
                "manifest_recorded": manifest_record is not None,
                "owner": str((manifest_record or {}).get("owner") or ""),
                "created_by_tool": (manifest_record or {}).get("created_by_tool") is True,
                "delete_eligible": docs_scope_manifest.scope_delete_eligible(manifest_record),
                "rename_eligible": docs_scope_rename.scope_rename_eligible(config, manifest_record),
            },
            "sub_scope_lifecycle": {
                "create_eligible": True,
                "delete_eligible": bool(config.sub_scopes),
                "sub_scopes": [
                    {
                        "sub_scope": sub_scope.sub_scope,
                        "title": sub_scope.title,
                        "source": path_label(repo_root, document_source_path(sub_scope)),
                        "output": path_label(repo_root, published_documents_path(sub_scope)),
                        "publish_output": path_label(repo_root, publication_documents_path(sub_scope)),
                    }
                    for sub_scope in config.sub_scopes
                ],
            },
            "publishing": {
                "status": publishable,
                "confirm": publishable,
                "apply": publishable,
                "published_docs_root": publication_documents_path(config).as_posix(),
                "published_search_index": publication_search_path(config).as_posix(),
            },
            "static_html_export": docs_static_html_export.scope_static_html_export_capability(repo_root, scope, config),
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
            "html_import": docs_import_workspace["available"],
            "docs_export": True,
            "copy_subtree": {
                "preview": True,
                "apply": True,
            },
            "library_import": docs_import_workspace["available"],
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
                "review_sessions": data_sharing_workspace["available"],
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
            "static_html_export": {
                "apply": True,
                "delete": True,
            },
            "scopes": scopes,
        },
    }
