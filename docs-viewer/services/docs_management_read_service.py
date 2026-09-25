"""Docs management generated-read and GET route dispatcher."""

from __future__ import annotations

from pathlib import Path

import docs_generated_reads
import docs_catalogue_media
import docs_diagram_source_service
import docs_import_source_service as import_source_service
import docs_management_routes as routes
import docs_preview_reads
import docs_source_config_report
import docs_series_works_report
import docs_unpublishable_report
import docs_source_config_settings
import docs_staged_media_service
from docs_management_capabilities_service import capabilities_payload
from docs_management_document_target import managed_document_metadata
from docs_management_source_service import read_source_body
from docs_document_link_targets import read_document_link_targets
from studio.shared.python.projects_directories import list_projects_directory


def docs_api_query_value(params: dict[str, list[str]], key: str) -> str:
    values = params.get(key, [""])
    if len(values) != 1:
        raise ValueError(f"{key} must have exactly one value")
    return values[0]


def docs_generated_read_payload(repo_root: Path, path: str, params: dict[str, list[str]]) -> dict[str, object]:
    if "sub_scope" in params:
        raise ValueError("sub_scope is retired; use collection")
    if "scope" in params:
        raise ValueError("scope is retired")
    if "collection" in params and path != routes.GENERATED_LINKS_PATH:
        raise ValueError("Use the configured collection artifact route for child payloads")

    stage = docs_api_query_value(params, "stage") if "stage" in params else None

    if path == routes.GENERATED_INDEX_TREE_PATH:
        return docs_generated_reads.read_generated_docs_index_tree(repo_root, stage)
    if path == routes.GENERATED_RECENT_PATH:
        return docs_generated_reads.read_generated_recent(repo_root, stage)
    if path == routes.GENERATED_BACKLINKS_PATH:
        return docs_generated_reads.read_generated_backlinks(repo_root, stage)
    if path == routes.GENERATED_SEARCH_PATH:
        return docs_generated_reads.read_generated_search_index(repo_root, stage)
    if path == routes.GENERATED_SEMANTIC_TOKENS_PATH:
        return docs_generated_reads.read_generated_semantic_tokens_index(repo_root, stage)
    if path == routes.GENERATED_LINKS_PATH:
        return docs_generated_reads.read_generated_doc_links(
            repo_root, docs_api_query_value(params, "doc_id"),
            docs_api_query_value(params, "collection"), stage,
        )
    if path == routes.GENERATED_WORKSPACE_LINKS_PATH:
        return docs_generated_reads.read_generated_workspace_links(repo_root, stage)
    if path == routes.GENERATED_PAYLOAD_PATH:
        doc_id = docs_api_query_value(params, "doc_id")
        if not doc_id:
            raise ValueError("doc_id is required")
        return docs_generated_reads.read_generated_doc_payload(repo_root, doc_id, stage)
    raise FileNotFoundError("Not found")


def docs_preview_read_payload(
    repo_root: Path,
    path: str,
    params: dict[str, list[str]],
) -> dict[str, object]:
    if "sub_scope" in params:
        raise ValueError("sub_scope is retired; use collection")
    if "scope" in params:
        raise ValueError("scope is retired")
    if "stage" in params and docs_api_query_value(params, "stage") != "preview":
        raise ValueError("Preview reads cannot address a source/generated stage")
    if "collection" in params:
        raise ValueError("Use the configured Preview collection artifact route for child payloads")
    if path == routes.PREVIEW_INDEX_TREE_PATH:
        return docs_preview_reads.read_preview_docs_index_tree(repo_root)
    if path == routes.PREVIEW_RECENT_PATH:
        return docs_preview_reads.read_preview_recent(repo_root)
    if path == routes.PREVIEW_BACKLINKS_PATH:
        return docs_preview_reads.read_preview_backlinks(repo_root)
    if path == routes.PREVIEW_SEARCH_PATH:
        return docs_preview_reads.read_preview_search_index(repo_root)
    if path == routes.PREVIEW_SEMANTIC_TOKENS_PATH:
        return docs_preview_reads.read_preview_semantic_tokens_index(repo_root)
    if path == routes.PREVIEW_PAYLOAD_PATH:
        doc_id = docs_api_query_value(params, "doc_id")
        if not doc_id:
            raise ValueError("doc_id is required")
        return docs_preview_reads.read_preview_doc_payload(
            repo_root,
            doc_id,
        )
    raise FileNotFoundError("Not found")


def docs_management_get_payload(repo_root: Path, path: str, params: dict[str, list[str]], *, dry_run: bool = False) -> dict[str, object]:
    if "sub_scope" in params:
        raise ValueError("sub_scope is retired; use collection")
    if "scope" in params:
        raise ValueError("scope is retired; supply an explicit stage and optional collection")
    if path == routes.HEALTH_PATH:
        return {"ok": True, "service": "docs_management", "dry_run": dry_run}
    if path == routes.CAPABILITIES_PATH:
        return capabilities_payload(repo_root)
    if path == routes.DOCUMENT_LINK_TARGETS_PATH:
        return read_document_link_targets(
            repo_root,
            stage=docs_api_query_value(params, "stage") if "stage" in params else None,
        )
    if path == routes.CATALOGUE_MEDIA_TARGETS_PATH:
        return docs_catalogue_media.read_catalogue_media_targets(repo_root, stage=docs_api_query_value(params, "stage"))
    if path == routes.CATALOGUE_MEDIA_CONFIG_PATH:
        return docs_catalogue_media.local_catalogue_media_config(repo_root, stage=docs_api_query_value(params, "stage"))
    if path == routes.CATALOGUE_WORK_PATH:
        return docs_catalogue_media.local_catalogue_work(
            repo_root, docs_api_query_value(params, "work_id"), stage=docs_api_query_value(params, "stage"),
        )
    if path == routes.CATALOGUE_SERIES_PATH:
        return docs_catalogue_media.read_catalogue_series(
            repo_root, docs_api_query_value(params, "series_id"), stage=docs_api_query_value(params, "stage"),
        )
    if path == routes.CATALOGUE_GALLERY_PATH:
        return docs_catalogue_media.read_catalogue_gallery(
            repo_root, docs_api_query_value(params, "gallery_id"), stage=docs_api_query_value(params, "stage"),
        )
    if path == routes.UNPUBLISHABLE_REPORT_PATH:
        return docs_unpublishable_report.build_unpublishable_report(
            repo_root,
            stage=docs_api_query_value(params, "stage"),
        )
    if path in {
        routes.GENERATED_INDEX_TREE_PATH,
        routes.GENERATED_RECENT_PATH,
        routes.GENERATED_BACKLINKS_PATH,
        routes.GENERATED_PAYLOAD_PATH,
        routes.GENERATED_LINKS_PATH,
        routes.GENERATED_WORKSPACE_LINKS_PATH,
        routes.GENERATED_SEARCH_PATH,
        routes.GENERATED_SEMANTIC_TOKENS_PATH,
    }:
        return docs_generated_read_payload(repo_root, path, params)
    if path in {
        routes.PREVIEW_INDEX_TREE_PATH,
        routes.PREVIEW_RECENT_PATH,
        routes.PREVIEW_BACKLINKS_PATH,
        routes.PREVIEW_PAYLOAD_PATH,
        routes.PREVIEW_SEARCH_PATH,
        routes.PREVIEW_SEMANTIC_TOKENS_PATH,
    }:
        return docs_preview_read_payload(repo_root, path, params)
    if path == routes.SOURCE_CONFIG_PATH:
        return docs_source_config_report.build_source_config_report(repo_root)
    if path == routes.SOURCE_CONFIG_SETTINGS_PATH:
        return docs_source_config_settings.build_settings_contract(
            repo_root,
            stage=docs_api_query_value(params, "stage") or None,
        )
    if path == routes.SOURCE_BODY_PATH:
        return read_source_body(repo_root, params)
    if path in {routes.METADATA_PATH, routes.SERIES_WORKS_REPORT_PATH, routes.SERIES_WORK_MEDIA_PATH}:
        target = {
            "stage": docs_api_query_value(params, "stage"),
            "doc_id": docs_api_query_value(params, "doc_id"),
        }
        if "collection" in params:
            target["collection"] = docs_api_query_value(params, "collection")
        if path == routes.SERIES_WORKS_REPORT_PATH:
            return docs_series_works_report.build_series_works_report(repo_root, target)
        if path == routes.SERIES_WORK_MEDIA_PATH:
            return docs_series_works_report.build_series_work_media(repo_root, target, docs_api_query_value(params, "work_id"))
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
            docs_api_query_value(params, "media_kind"),
            stage=docs_api_query_value(params, "stage"),
            collection=docs_api_query_value(params, "collection"),
        )
    if path == routes.DIAGRAM_SOURCES_PATH:
        return docs_diagram_source_service.list_diagram_sources(repo_root, params)
    raise FileNotFoundError("Not found")
