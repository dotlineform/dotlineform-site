"""Docs management generated-read and GET route dispatcher."""

from __future__ import annotations

from pathlib import Path

import docs_generated_reads
import docs_catalogue_media
from docs_series_galleries_report import read_series_galleries_report
from docs_work_document_coverage import read_work_document_coverage_manifest
import docs_diagram_source_service
import docs_import_source_service as import_source_service
import docs_management_routes as routes
import docs_media_metadata
from docs_management_broken_links_service import read_broken_links
import docs_unpublishable_report
from docs_selected_documents import read_selected
from docs_workspace_config import document_source_path, load_docs_working_config, resolve_workspace_path
from docs_publication_ignore import WorkingPublicationExclusions, read_publication_ignore_ids
import docs_source_config_settings
import docs_source_media_service
from docs_management_capabilities_service import capabilities_payload
from docs_management_document_target import managed_document_metadata
from docs_management_source_service import read_source_document
from docs_document_link_targets import read_document_link_targets
from studio.shared.python.projects_directories import list_projects_directory


def docs_api_query_value(params: dict[str, list[str]], key: str) -> str:
    values = params.get(key, [""])
    if len(values) != 1:
        raise ValueError(f"{key} must have exactly one value")
    return values[0]


def read_management_docs_index_tree(repo_root: Path) -> dict[str, object]:
    """Attach fresh inherited ignore policy to the local index response only.

    Generated/public files and authored draft values remain unchanged. The
    browser's existing index refresh also observes ignore-list and tree edits.
    """
    payload = docs_generated_reads.read_generated_docs_index_tree(repo_root)
    config = load_docs_working_config(repo_root)
    exclusions = WorkingPublicationExclusions(
        resolve_workspace_path(repo_root, document_source_path(config)),
        read_publication_ignore_ids(repo_root),
    )

    def project(nodes: object) -> None:
        if not isinstance(nodes, list):
            raise ValueError("Management index requires document arrays")
        for node in nodes:
            if not isinstance(node, dict):
                raise ValueError("Management index requires document objects")
            node["publication_ignored"] = exclusions.excludes(node.get("doc_id"))
            project(node.get("children", []))

    project(payload.get("docs"))
    return payload


def docs_generated_read_payload(repo_root: Path, path: str, params: dict[str, list[str]]) -> dict[str, object]:
    if "stage" in params:
        raise ValueError("stage is retired from Docs requests")
    if "sub_scope" in params:
        raise ValueError("sub_scope is retired; use collection")
    if "scope" in params:
        raise ValueError("scope is retired")
    if "collection" in params:
        raise ValueError("Use the configured collection artifact route for child payloads")


    if path == routes.GENERATED_INDEX_TREE_PATH:
        return read_management_docs_index_tree(repo_root)
    if path == routes.GENERATED_RECENT_PATH:
        return docs_generated_reads.read_generated_recent(repo_root)
    if path == routes.GENERATED_SEARCH_PATH:
        return docs_generated_reads.read_generated_search_index(repo_root)
    if path == routes.GENERATED_WORKSPACE_LINKS_PATH:
        return docs_generated_reads.read_generated_workspace_links(repo_root)
    if path == routes.GENERATED_PAYLOAD_PATH:
        doc_id = docs_api_query_value(params, "doc_id")
        if not doc_id:
            raise ValueError("doc_id is required")
        return docs_generated_reads.read_generated_doc_payload(repo_root, doc_id)
    raise FileNotFoundError("Not found")


def docs_management_get_payload(repo_root: Path, path: str, params: dict[str, list[str]], *, dry_run: bool = False) -> dict[str, object]:
    if "stage" in params:
        raise ValueError("stage is retired from Docs requests")
    if "sub_scope" in params:
        raise ValueError("sub_scope is retired; use collection")
    if "scope" in params:
        raise ValueError("scope is retired; use an optional collection")
    if path == routes.HEALTH_PATH:
        return {"ok": True, "service": "docs_management", "dry_run": dry_run}
    if path == routes.CAPABILITIES_PATH:
        return capabilities_payload(repo_root)
    if path == routes.SELECTED_PATH:
        if params:
            raise ValueError("Selected Documents reads do not accept parameters")
        return read_selected(load_docs_working_config(repo_root))
    if path == routes.MEDIA_METADATA_PATH:
        if params:
            raise ValueError("Docs Media metadata reads do not accept parameters")
        return docs_media_metadata.read_media_metadata(repo_root)
    if path == routes.BROKEN_LINKS_PATH:
        if params:
            raise ValueError("Broken Links reads do not accept parameters")
        return read_broken_links(repo_root)
    if path == routes.DOCUMENT_LINK_TARGETS_PATH:
        return read_document_link_targets(
            repo_root,
        )
    if path == routes.CATALOGUE_MEDIA_TARGETS_PATH:
        return docs_catalogue_media.read_catalogue_media_targets(repo_root)
    if path == routes.CATALOGUE_MEDIA_CONFIG_PATH:
        return docs_catalogue_media.local_catalogue_media_config(repo_root)
    if path == routes.CATALOGUE_WORK_PATH:
        return docs_catalogue_media.local_catalogue_work(
            repo_root, docs_api_query_value(params, "work_id"),
        )
    if path == routes.CATALOGUE_GALLERY_PATH:
        return docs_catalogue_media.read_catalogue_gallery(
            repo_root, docs_api_query_value(params, "gallery_id"),
        )
    if path == routes.CATALOGUE_SERIES_GALLERIES_PATH:
        return docs_catalogue_media.read_catalogue_series_galleries_index(repo_root)
    if path == routes.SERIES_GALLERIES_REPORT_PATH:
        if params:
            raise ValueError("Series and Galleries report reads do not accept parameters")
        return read_series_galleries_report(repo_root)
    if path == routes.WORK_DOCUMENT_COVERAGE_PATH:
        if params:
            raise ValueError("Work Document Coverage reads do not accept parameters")
        return read_work_document_coverage_manifest(repo_root)
    if path == routes.UNPUBLISHABLE_REPORT_PATH:
        return docs_unpublishable_report.build_unpublishable_report(
            repo_root,
        )
    if path in {
        routes.GENERATED_INDEX_TREE_PATH,
        routes.GENERATED_RECENT_PATH,
        routes.GENERATED_PAYLOAD_PATH,
        routes.GENERATED_WORKSPACE_LINKS_PATH,
        routes.GENERATED_SEARCH_PATH,
    }:
        return docs_generated_read_payload(repo_root, path, params)
    if path == routes.SOURCE_CONFIG_SETTINGS_PATH:
        return docs_source_config_settings.build_settings_contract(
            repo_root,
        )
    if path == routes.SOURCE_PATH:
        return read_source_document(repo_root, params)
    if path == routes.METADATA_PATH:
        target = {
            "doc_id": docs_api_query_value(params, "doc_id"),
        }
        if "collection" in params:
            target["collection"] = docs_api_query_value(params, "collection")
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
    if path == routes.SOURCE_MEDIA_OPTIONS_PATH:
        return docs_source_media_service.media_options(
            repo_root,
            docs_api_query_value(params, "media_kind"),
            collection=docs_api_query_value(params, "collection"),
        )
    if path == routes.DIAGRAM_SOURCES_PATH:
        return docs_diagram_source_service.list_diagram_sources(repo_root, params)
    raise FileNotFoundError("Not found")
