"""Docs management generated-read and GET route dispatcher."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import docs_generated_reads
import docs_diagram_source_service
import docs_import_source_service as import_source_service
import docs_management_routes as routes
import docs_publish_gate
from docs_scope_config import load_docs_scope_configs
import docs_source_config_report
import docs_source_config_settings
import docs_staged_media_service
from docs_management_capabilities_service import capabilities_payload
from docs_management_document_target import managed_document_metadata
from docs_management_source_service import read_source_body
from studio.shared.python.projects_directories import list_projects_directory


def docs_api_query_value(params: dict[str, list[str]], key: str) -> str:
    return (params.get(key) or [""])[0]


def normalize_scope(repo_root: Path, value: Any) -> str:
    scope = str(value or "").strip().lower()
    configs = load_docs_scope_configs(repo_root)
    if scope not in configs:
        raise ValueError(f"scope must be one of: {', '.join(sorted(configs))}")
    return scope


def docs_generated_read_payload(repo_root: Path, path: str, params: dict[str, list[str]]) -> dict[str, object]:
    scope = normalize_scope(repo_root, docs_api_query_value(params, "scope"))

    if path == routes.GENERATED_INDEX_TREE_PATH:
        return docs_generated_reads.read_generated_docs_index_tree(repo_root, scope)
    if path == routes.GENERATED_RECENT_PATH:
        return docs_generated_reads.read_generated_recent(repo_root, scope)
    if path == routes.GENERATED_SEARCH_PATH:
        return docs_generated_reads.read_generated_search_index(repo_root, scope)
    if path == routes.GENERATED_SEMANTIC_TOKENS_PATH:
        return docs_generated_reads.read_generated_semantic_tokens_index(repo_root, scope)
    if path == routes.GENERATED_PAYLOAD_PATH:
        doc_id = docs_api_query_value(params, "doc_id") or docs_api_query_value(params, "doc")
        if not doc_id:
            raise ValueError("doc_id is required")
        return docs_generated_reads.read_generated_doc_payload(repo_root, scope, doc_id)
    raise FileNotFoundError("Not found")


def docs_management_get_payload(repo_root: Path, path: str, params: dict[str, list[str]], *, dry_run: bool = False) -> dict[str, object]:
    if path == routes.HEALTH_PATH:
        return {"ok": True, "service": "docs_management", "dry_run": dry_run}
    if path == routes.CAPABILITIES_PATH:
        return capabilities_payload(repo_root)
    if path in {
        routes.GENERATED_INDEX_TREE_PATH,
        routes.GENERATED_RECENT_PATH,
        routes.GENERATED_PAYLOAD_PATH,
        routes.GENERATED_SEARCH_PATH,
        routes.GENERATED_SEMANTIC_TOKENS_PATH,
    }:
        return docs_generated_read_payload(repo_root, path, params)
    if path == routes.SOURCE_CONFIG_PATH:
        return docs_source_config_report.build_source_config_report(repo_root)
    if path == routes.SOURCE_CONFIG_SETTINGS_PATH:
        return docs_source_config_settings.build_settings_contract(
            repo_root,
            docs_api_query_value(params, "scope"),
        )
    if path == routes.SOURCE_BODY_PATH:
        return read_source_body(repo_root, params)
    if path == routes.METADATA_PATH:
        target = {
            "scope": docs_api_query_value(params, "scope"),
            "doc_id": docs_api_query_value(params, "doc_id"),
        }
        if "sub_scope" in params:
            target["sub_scope"] = docs_api_query_value(params, "sub_scope")
        return managed_document_metadata(repo_root, target)
    if path in {
        routes.IMPORT_SOURCE_DIRECTORIES_PATH,
        routes.IMPORT_SOURCE_FILES_PATH,
    }:
        source_directory = docs_api_query_value(params, "source_directory")
        if not source_directory:
            raise ValueError("source_directory is required")
        if path == routes.IMPORT_SOURCE_DIRECTORIES_PATH:
            return list_projects_directory(source_directory)
        return import_source_service.handle_import_source_files(
            repo_root,
            source_directory=source_directory,
        )
    if path == routes.STAGED_MEDIA_FILES_PATH:
        return docs_staged_media_service.list_staged_media_files(
            repo_root,
            docs_api_query_value(params, "scope"),
            docs_api_query_value(params, "media_kind"),
            docs_api_query_value(params, "source_directory"),
        )
    if path == routes.DIAGRAM_SOURCES_PATH:
        return docs_diagram_source_service.list_diagram_sources(repo_root, params)
    if path == routes.PUBLISH_STATUS_PATH:
        return docs_publish_gate.publish_status(
            repo_root,
            {"scope": docs_api_query_value(params, "scope")},
        )
    if docs_api_query_value(params, "scope"):
        normalize_scope(repo_root, docs_api_query_value(params, "scope"))
    raise FileNotFoundError("Not found")
