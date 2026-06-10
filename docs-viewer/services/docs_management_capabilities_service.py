"""Docs management capability and source-config read helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import docs_scope_manifest
import docs_source_config_settings
import docs_source_model as source_model
from docs_management_context import relative_path
from docs_scope_config import DOCS_SCOPE_CONFIGS, SCOPE_ROOTS, is_public_readonly_scope


def capability_scope_docs(repo_root: Path, scope: str, root: Path) -> list[Any]:
    if not root.exists():
        return []
    if scope in SCOPE_ROOTS:
        return source_model.load_scope_docs(repo_root, scope)

    docs = []
    for path in source_model.scope_markdown_paths(root, scope):
        front_matter, body = source_model.parse_source(path)
        doc_id = str(front_matter.get("doc_id") or path.stem).strip()
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


def capabilities_payload(repo_root: Path) -> Dict[str, Any]:
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
        root = repo_root / config.source
        scope_docs = capability_scope_docs(repo_root, scope, root)
        manifest_record = manifest_scopes.get(scope)
        generated_data_path = repo_root / config.output / "index-tree.json"
        publishable = is_public_readonly_scope(
            viewer_base_url=config.viewer_base_url,
            include_scope_param=config.include_scope_param,
        )
        scopes[scope] = {
            "available": root.exists(),
            "root": relative_path(repo_root, root),
            "generated_data_reads": generated_data_path.exists(),
            "generated_search_reads": (repo_root / config.search_output).exists(),
            "publishable": publishable,
            "count": len(scope_docs),
            "scope_lifecycle": {
                "manifest_recorded": manifest_record is not None,
                "owner": str((manifest_record or {}).get("owner") or ""),
                "created_by_tool": (manifest_record or {}).get("created_by_tool") is True,
                "delete_eligible": docs_scope_manifest.scope_delete_eligible(manifest_record),
            },
            "publishing": {
                "status": publishable,
                "confirm": publishable,
                "apply": publishable,
                "published_docs_root": config.publish_output.as_posix(),
                "published_search_index": config.publish_search_output.as_posix(),
            },
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
            "html_import": True,
            "docs_export": True,
            "library_import": True,
            "scope_lifecycle": {
                "manifest": True,
                "create_preview": True,
                "create_apply": True,
                "delete_preview": True,
                "delete_apply": True,
                "publishing_modes": list(docs_scope_manifest.PUBLISHING_MODES),
                "manifest_path": docs_scope_manifest.MANIFEST_REL_PATH.as_posix(),
            },
            "publishing": {
                "status": True,
                "confirm": True,
                "apply": True,
            },
            "scopes": scopes,
        },
    }
