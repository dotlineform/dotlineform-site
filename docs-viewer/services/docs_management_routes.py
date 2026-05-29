#!/usr/bin/env python3
"""Docs Management local-service endpoint path constants."""

HEALTH_PATH = "/health"
CAPABILITIES_PATH = "/capabilities"

GENERATED_INDEX_PATH = "/docs/index"
GENERATED_INDEX_ALT_PATH = "/docs/generated/index"
GENERATED_PAYLOAD_PATH = "/docs/doc"
GENERATED_PAYLOAD_ALT_PATH = "/docs/generated/payload"
GENERATED_SEARCH_PATH = "/docs/search"
GENERATED_SEARCH_ALT_PATH = "/docs/generated/search"
GENERATED_DOCS_LOG_PATH = "/docs/generated/docs-log"
GENERATED_REFERENCES_PATH = "/docs/references"
GENERATED_REFERENCES_ALT_PATH = "/docs/generated/references"
GENERATED_REFERENCE_TARGET_PATH = "/docs/reference-target"
GENERATED_REFERENCE_TARGET_ALT_PATH = "/docs/generated/reference-target"
SOURCE_CONFIG_PATH = "/docs/source-config"
SOURCE_CONFIG_SETTINGS_PATH = "/docs/source-config-settings"
IMPORT_SOURCE_FILES_PATH = "/docs/import-source-files"
IMPORT_HTML_FILES_PATH = "/docs/import-html-files"

OPEN_SOURCE_PATH = "/docs/open-source"
BROKEN_LINKS_PATH = "/docs/broken-links"
IMPORT_SOURCE_PATH = "/docs/import-source"
IMPORT_HTML_PATH = "/docs/import-html"
UPDATE_METADATA_PATH = "/docs/update-metadata"
UPDATE_VIEWABILITY_PATH = "/docs/update-viewability"
UPDATE_VIEWABILITY_BULK_PATH = "/docs/update-viewability-bulk"
CREATE_PATH = "/docs/create"
REBUILD_PATH = "/docs/rebuild"
MOVE_PATH = "/docs/move"
NORMALIZE_ORDER_PATH = "/docs/normalize-order"
DELETE_PREVIEW_PATH = "/docs/delete-preview"
DELETE_APPLY_PATH = "/docs/delete-apply"
SCOPE_CREATE_PREVIEW_PATH = "/docs/scopes/create-preview"
SCOPE_CREATE_APPLY_PATH = "/docs/scopes/create-apply"
SCOPE_DELETE_PREVIEW_PATH = "/docs/scopes/delete-preview"
SCOPE_DELETE_APPLY_PATH = "/docs/scopes/delete-apply"

GET_PATHS = (
    HEALTH_PATH,
    CAPABILITIES_PATH,
    GENERATED_INDEX_PATH,
    GENERATED_INDEX_ALT_PATH,
    GENERATED_PAYLOAD_PATH,
    GENERATED_PAYLOAD_ALT_PATH,
    GENERATED_SEARCH_PATH,
    GENERATED_SEARCH_ALT_PATH,
    GENERATED_DOCS_LOG_PATH,
    GENERATED_REFERENCES_PATH,
    GENERATED_REFERENCES_ALT_PATH,
    GENERATED_REFERENCE_TARGET_PATH,
    GENERATED_REFERENCE_TARGET_ALT_PATH,
    SOURCE_CONFIG_PATH,
    SOURCE_CONFIG_SETTINGS_PATH,
    IMPORT_SOURCE_FILES_PATH,
    IMPORT_HTML_FILES_PATH,
)

POST_PATHS = (
    OPEN_SOURCE_PATH,
    BROKEN_LINKS_PATH,
    SOURCE_CONFIG_SETTINGS_PATH,
    IMPORT_SOURCE_PATH,
    IMPORT_HTML_PATH,
    UPDATE_METADATA_PATH,
    UPDATE_VIEWABILITY_PATH,
    UPDATE_VIEWABILITY_BULK_PATH,
    CREATE_PATH,
    REBUILD_PATH,
    MOVE_PATH,
    NORMALIZE_ORDER_PATH,
    DELETE_PREVIEW_PATH,
    DELETE_APPLY_PATH,
    SCOPE_CREATE_PREVIEW_PATH,
    SCOPE_CREATE_APPLY_PATH,
    SCOPE_DELETE_PREVIEW_PATH,
    SCOPE_DELETE_APPLY_PATH,
)

OPTIONS_PATHS = tuple(dict.fromkeys((*POST_PATHS, *GET_PATHS)))
