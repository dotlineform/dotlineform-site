#!/usr/bin/env python3
"""Docs Management local-service endpoint path constants."""

HEALTH_PATH = "/health"
CAPABILITIES_PATH = "/capabilities"

GENERATED_INDEX_TREE_PATH = "/docs/index-tree"
GENERATED_RECENT_PATH = "/docs/recent"
SELECTED_PATH = "/docs/selected"
GENERATED_BACKLINKS_PATH = "/docs/backlinks"
GENERATED_PAYLOAD_PATH = "/docs/doc"
GENERATED_WORKSPACE_LINKS_PATH = "/docs/workspace-links"
GENERATED_SEARCH_PATH = "/docs/search"
UNPUBLISHABLE_REPORT_PATH = "/docs/unpublishable-report"
CATALOGUE_MEDIA_TARGETS_PATH = "/docs/catalogue-media-targets"
CATALOGUE_MEDIA_CONFIG_PATH = "/docs/catalogue-media-config"
CATALOGUE_WORK_PATH = "/docs/catalogue-work"
CATALOGUE_GALLERY_PATH = "/docs/catalogue-gallery"
CATALOGUE_SERIES_GALLERIES_PATH = "/docs/catalogue-series-galleries"
CATALOGUE_REGENERATE_PATH = "/docs/catalogue/regenerate"
SOURCE_CONFIG_SETTINGS_PATH = "/docs/source-config-settings"
IMPORT_SOURCE_DIRECTORIES_PATH = "/docs/import-source-directories"
IMPORT_SOURCE_FILES_PATH = "/docs/import-source-files"
SOURCE_MEDIA_OPTIONS_PATH = "/docs/source/media/options"
DIAGRAM_SOURCES_PATH = "/docs/diagram-sources"

SOURCE_PATH = "/docs/source"
SOURCE_CONTEXT_PATH = "/docs/source/context"
DOCUMENT_LINK_TARGETS_PATH = "/docs/document-link-targets"
METADATA_PATH = "/docs/metadata"
SOURCE_SAVE_PATH = "/docs/source/save"
OPEN_SOURCE_PATH = "/docs/open-source"
OPEN_PUBLICATION_IGNORE_PATH = "/docs/open-publication-ignore"
OPEN_DIAGRAM_SOURCE_PATH = "/docs/open-diagram-source"
OPEN_LOCAL_TARGET_PATH = "/docs/open-local-target"
BROKEN_LINKS_PATH = "/docs/broken-links"
PROJECT_STATE_PATH = "/docs/project-state"
MEDIA_METADATA_PATH = "/docs/media-metadata"
MEDIA_REFRESH_PATH = "/docs/media-refresh"
OPEN_MEDIA_SOURCE_PATH = "/docs/open-media-source"
UNCATALOGED_FILES_PATH = "/docs/uncataloged-files"
MISSING_SOURCE_FILES_PATH = "/docs/missing-source-files"
WORK_DOWNLOADS_PATH = "/docs/work-downloads"
WORK_LINKS_PATH = "/docs/work-links"
OPEN_WORK_DOWNLOAD_PATH = "/docs/open-work-download"
IMPORT_SOURCE_PATH = "/docs/import-source"
SOURCE_MEDIA_APPLY_PATH = "/docs/source/media"
SET_DRAFT_PATH = "/docs/set-draft"
SET_SELECTED_PATH = "/docs/set-selected"
ASSIGN_FIELD_GROUP_PATH = "/docs/assign-field-group"
CREATE_PATH = "/docs/create"
REBUILD_PATH = "/docs/rebuild"
PUBLISH_PATH = "/docs/publish"
MOVE_PATH = "/docs/move"
DELETE_PREVIEW_PATH = "/docs/delete-preview"
DELETE_APPLY_PATH = "/docs/delete-apply"
STATIC_HTML_EXPORT_PREVIEW_PATH = "/docs/export/static-html/preview"
STATIC_HTML_EXPORT_APPLY_PATH = "/docs/export/static-html/apply"

GET_PATHS = (
    HEALTH_PATH,
    CAPABILITIES_PATH,
    GENERATED_INDEX_TREE_PATH,
    GENERATED_RECENT_PATH,
    SELECTED_PATH,
    GENERATED_BACKLINKS_PATH,
    GENERATED_PAYLOAD_PATH,
    GENERATED_WORKSPACE_LINKS_PATH,
    GENERATED_SEARCH_PATH,
    UNPUBLISHABLE_REPORT_PATH,
    CATALOGUE_MEDIA_TARGETS_PATH,
    CATALOGUE_WORK_PATH,
    CATALOGUE_MEDIA_CONFIG_PATH,
    CATALOGUE_GALLERY_PATH,
    CATALOGUE_SERIES_GALLERIES_PATH,
    SOURCE_CONFIG_SETTINGS_PATH,
    SOURCE_PATH,
    DOCUMENT_LINK_TARGETS_PATH,
    METADATA_PATH,
    IMPORT_SOURCE_DIRECTORIES_PATH,
    IMPORT_SOURCE_FILES_PATH,
    SOURCE_MEDIA_OPTIONS_PATH,
    DIAGRAM_SOURCES_PATH,
    MEDIA_METADATA_PATH,
    BROKEN_LINKS_PATH,
)

POST_PATHS = (
    CATALOGUE_REGENERATE_PATH,
    SOURCE_SAVE_PATH,
    SOURCE_CONTEXT_PATH,
    OPEN_SOURCE_PATH,
    OPEN_PUBLICATION_IGNORE_PATH,
    OPEN_DIAGRAM_SOURCE_PATH,
    OPEN_LOCAL_TARGET_PATH,
    BROKEN_LINKS_PATH,
    PROJECT_STATE_PATH,
    OPEN_MEDIA_SOURCE_PATH,
    MEDIA_REFRESH_PATH,
    UNCATALOGED_FILES_PATH,
    MISSING_SOURCE_FILES_PATH,
    WORK_DOWNLOADS_PATH,
    WORK_LINKS_PATH,
    OPEN_WORK_DOWNLOAD_PATH,
    SOURCE_CONFIG_SETTINGS_PATH,
    IMPORT_SOURCE_PATH,
    SOURCE_MEDIA_APPLY_PATH,
    SET_DRAFT_PATH,
    SET_SELECTED_PATH,
    ASSIGN_FIELD_GROUP_PATH,
    CREATE_PATH,
    REBUILD_PATH,
    PUBLISH_PATH,
    MOVE_PATH,
    DELETE_PREVIEW_PATH,
    DELETE_APPLY_PATH,
    STATIC_HTML_EXPORT_PREVIEW_PATH,
    STATIC_HTML_EXPORT_APPLY_PATH,
)

OPTIONS_PATHS = tuple(dict.fromkeys((*POST_PATHS, *GET_PATHS)))
