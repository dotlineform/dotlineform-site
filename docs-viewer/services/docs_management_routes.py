#!/usr/bin/env python3
"""Docs Management local-service endpoint path constants."""

HEALTH_PATH = "/health"
CAPABILITIES_PATH = "/capabilities"

GENERATED_INDEX_TREE_PATH = "/docs/index-tree"
GENERATED_RECENT_PATH = "/docs/recent"
GENERATED_BACKLINKS_PATH = "/docs/backlinks"
GENERATED_PAYLOAD_PATH = "/docs/doc"
GENERATED_LINKS_PATH = "/docs/links"
GENERATED_WORKSPACE_LINKS_PATH = "/docs/workspace-links"
GENERATED_SEARCH_PATH = "/docs/search"
GENERATED_SEMANTIC_TOKENS_PATH = "/docs/semantic-tokens"
PREVIEW_INDEX_TREE_PATH = "/docs/preview/index-tree"
PREVIEW_RECENT_PATH = "/docs/preview/recent"
PREVIEW_BACKLINKS_PATH = "/docs/preview/backlinks"
PREVIEW_PAYLOAD_PATH = "/docs/preview/doc"
PREVIEW_SEARCH_PATH = "/docs/preview/search"
PREVIEW_SEMANTIC_TOKENS_PATH = "/docs/preview/semantic-tokens"
SERIES_WORKS_REPORT_PATH = "/docs/series-works-report"
UNPUBLISHABLE_REPORT_PATH = "/docs/unpublishable-report"
SERIES_WORK_MEDIA_PATH = "/docs/series-work-media"
CATALOGUE_MEDIA_TARGETS_PATH = "/docs/catalogue-media-targets"
CATALOGUE_MEDIA_CONFIG_PATH = "/docs/catalogue-media-config"
CATALOGUE_WORK_PATH = "/docs/catalogue-work"
CATALOGUE_SERIES_PATH = "/docs/catalogue-series"
CATALOGUE_GALLERY_PATH = "/docs/catalogue-gallery"
CATALOGUE_REGENERATE_PREVIEW_PATH = "/docs/catalogue/regenerate-preview"
CATALOGUE_REGENERATE_APPLY_PATH = "/docs/catalogue/regenerate-apply"
SOURCE_CONFIG_SETTINGS_PATH = "/docs/source-config-settings"
IMPORT_SOURCE_DIRECTORIES_PATH = "/docs/import-source-directories"
IMPORT_SOURCE_FILES_PATH = "/docs/import-source-files"
STAGED_MEDIA_FILES_PATH = "/docs/staged-media-files"
DIAGRAM_SOURCES_PATH = "/docs/diagram-sources"

SOURCE_BODY_PATH = "/docs/source"
DOCUMENT_LINK_TARGETS_PATH = "/docs/document-link-targets"
METADATA_PATH = "/docs/metadata"
SOURCE_SAVE_PATH = "/docs/source/save"
OPEN_SOURCE_PATH = "/docs/open-source"
OPEN_PUBLICATION_IGNORE_PATH = "/docs/open-publication-ignore"
OPEN_DIAGRAM_SOURCE_PATH = "/docs/open-diagram-source"
OPEN_LOCAL_TARGET_PATH = "/docs/open-local-target"
BROKEN_LINKS_PATH = "/docs/broken-links"
PROJECT_STATE_PATH = "/docs/project-state"
DOCS_MEDIA_REPORT_PATH = "/docs/media-report"
OPEN_MEDIA_SOURCE_PATH = "/docs/open-media-source"
UNCATALOGED_FILES_PATH = "/docs/uncataloged-files"
MISSING_SOURCE_FILES_PATH = "/docs/missing-source-files"
IMPORT_SOURCE_PATH = "/docs/import-source"
STAGED_MEDIA_PREVIEW_PATH = "/docs/staged-media-preview"
STAGED_MEDIA_APPLY_PATH = "/docs/staged-media-apply"
SET_DRAFT_PATH = "/docs/set-draft"
ASSIGN_FIELD_GROUP_PATH = "/docs/assign-field-group"
CREATE_PATH = "/docs/create"
REBUILD_PATH = "/docs/rebuild"
PREPARE_PREVIEW_PLAN_PATH = "/docs/prepare-preview/plan"
PREPARE_PREVIEW_APPLY_PATH = "/docs/prepare-preview/apply"
MOVE_PATH = "/docs/move"
DELETE_PREVIEW_PATH = "/docs/delete-preview"
DELETE_APPLY_PATH = "/docs/delete-apply"
COLLECTION_CREATE_PREVIEW_PATH = "/docs/collections/create-preview"
COLLECTION_CREATE_APPLY_PATH = "/docs/collections/create-apply"
COLLECTION_DELETE_PREVIEW_PATH = "/docs/collections/delete-preview"
COLLECTION_DELETE_APPLY_PATH = "/docs/collections/delete-apply"
DEPLOY_REPO_PREVIEW_PATH = "/docs/deploy-repo/preview"
DEPLOY_REPO_APPLY_PATH = "/docs/deploy-repo/apply"
STATIC_HTML_EXPORT_PREVIEW_PATH = "/docs/export/static-html/preview"
STATIC_HTML_EXPORT_APPLY_PATH = "/docs/export/static-html/apply"

GET_PATHS = (
    HEALTH_PATH,
    CAPABILITIES_PATH,
    GENERATED_INDEX_TREE_PATH,
    GENERATED_RECENT_PATH,
    GENERATED_BACKLINKS_PATH,
    GENERATED_PAYLOAD_PATH,
    GENERATED_LINKS_PATH,
    GENERATED_WORKSPACE_LINKS_PATH,
    GENERATED_SEARCH_PATH,
    GENERATED_SEMANTIC_TOKENS_PATH,
    PREVIEW_INDEX_TREE_PATH,
    PREVIEW_RECENT_PATH,
    PREVIEW_BACKLINKS_PATH,
    PREVIEW_PAYLOAD_PATH,
    PREVIEW_SEARCH_PATH,
    PREVIEW_SEMANTIC_TOKENS_PATH,
    SERIES_WORKS_REPORT_PATH,
    UNPUBLISHABLE_REPORT_PATH,
    SERIES_WORK_MEDIA_PATH,
    CATALOGUE_MEDIA_TARGETS_PATH,
    CATALOGUE_WORK_PATH,
    CATALOGUE_MEDIA_CONFIG_PATH,
    CATALOGUE_SERIES_PATH,
    CATALOGUE_GALLERY_PATH,
    SOURCE_CONFIG_SETTINGS_PATH,
    SOURCE_BODY_PATH,
    DOCUMENT_LINK_TARGETS_PATH,
    METADATA_PATH,
    IMPORT_SOURCE_DIRECTORIES_PATH,
    IMPORT_SOURCE_FILES_PATH,
    STAGED_MEDIA_FILES_PATH,
    DIAGRAM_SOURCES_PATH,
)

POST_PATHS = (
    CATALOGUE_REGENERATE_PREVIEW_PATH,
    CATALOGUE_REGENERATE_APPLY_PATH,
    SOURCE_SAVE_PATH,
    OPEN_SOURCE_PATH,
    OPEN_PUBLICATION_IGNORE_PATH,
    OPEN_DIAGRAM_SOURCE_PATH,
    OPEN_LOCAL_TARGET_PATH,
    BROKEN_LINKS_PATH,
    PROJECT_STATE_PATH,
    DOCS_MEDIA_REPORT_PATH,
    OPEN_MEDIA_SOURCE_PATH,
    UNCATALOGED_FILES_PATH,
    MISSING_SOURCE_FILES_PATH,
    SOURCE_CONFIG_SETTINGS_PATH,
    IMPORT_SOURCE_PATH,
    STAGED_MEDIA_PREVIEW_PATH,
    STAGED_MEDIA_APPLY_PATH,
    SET_DRAFT_PATH,
    ASSIGN_FIELD_GROUP_PATH,
    CREATE_PATH,
    REBUILD_PATH,
    PREPARE_PREVIEW_PLAN_PATH,
    PREPARE_PREVIEW_APPLY_PATH,
    MOVE_PATH,
    DELETE_PREVIEW_PATH,
    DELETE_APPLY_PATH,
    COLLECTION_CREATE_PREVIEW_PATH,
    COLLECTION_CREATE_APPLY_PATH,
    COLLECTION_DELETE_PREVIEW_PATH,
    COLLECTION_DELETE_APPLY_PATH,
    DEPLOY_REPO_PREVIEW_PATH,
    DEPLOY_REPO_APPLY_PATH,
    STATIC_HTML_EXPORT_PREVIEW_PATH,
    STATIC_HTML_EXPORT_APPLY_PATH,
)

OPTIONS_PATHS = tuple(dict.fromkeys((*POST_PATHS, *GET_PATHS)))
