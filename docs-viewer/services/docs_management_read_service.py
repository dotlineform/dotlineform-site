"""Docs management generated-read and GET route dispatcher."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import docs_generated_reads
import docs_import_source_service as import_source_service
import docs_management_routes as routes
import docs_publish_gate
import docs_review_sessions
from docs_scope_config import load_docs_scope_configs
import docs_source_config_report
import docs_source_config_settings
import docs_staged_media_service
from docs_management_capabilities_service import capabilities_payload
from docs_management_source_service import read_source_body


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
    if path == routes.GENERATED_PAYLOAD_PATH:
        doc_id = docs_api_query_value(params, "doc_id") or docs_api_query_value(params, "doc")
        if not doc_id:
            raise ValueError("doc_id is required")
        return docs_generated_reads.read_generated_doc_payload(repo_root, scope, doc_id)
    if path == routes.GENERATED_REFERENCES_PATH:
        return docs_generated_reads.read_generated_references_index(repo_root, scope)
    if path == routes.GENERATED_REFERENCE_TARGET_PATH:
        target_kind = docs_api_query_value(params, "target_kind")
        target_slug = docs_api_query_value(params, "target_slug")
        if not target_kind or not target_slug:
            raise ValueError("target_kind and target_slug are required")
        return docs_generated_reads.read_generated_reference_target(repo_root, scope, target_kind, target_slug)
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
        routes.GENERATED_REFERENCES_PATH,
        routes.GENERATED_REFERENCE_TARGET_PATH,
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
    if path == routes.IMPORT_SOURCE_FILES_PATH:
        return import_source_service.handle_import_source_files(repo_root)
    if path == routes.STAGED_MEDIA_FILES_PATH:
        return docs_staged_media_service.list_staged_media_files(
            repo_root,
            docs_api_query_value(params, "media_kind"),
        )
    if path == routes.REVIEW_SESSIONS_PATH:
        return docs_review_sessions.list_review_sessions(repo_root)
    if path == routes.REVIEW_SESSION_INDEX_TREE_PATH:
        return docs_review_sessions.read_review_session_index_tree(
            repo_root,
            docs_api_query_value(params, "session_id"),
        )
    if path == routes.REVIEW_SESSION_PAYLOAD_PATH:
        return docs_review_sessions.read_review_session_payload(
            repo_root,
            docs_api_query_value(params, "session_id"),
            docs_api_query_value(params, "doc_id") or docs_api_query_value(params, "doc"),
        )
    if path == routes.PUBLISH_STATUS_PATH:
        return docs_publish_gate.publish_status(
            repo_root,
            {"scope": docs_api_query_value(params, "scope")},
        )
    if docs_api_query_value(params, "scope"):
        normalize_scope(repo_root, docs_api_query_value(params, "scope"))
    raise FileNotFoundError("Not found")
