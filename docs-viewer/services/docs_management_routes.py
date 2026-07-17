#!/usr/bin/env python3
"""Docs Management local-service endpoint path constants."""

HEALTH_PATH = "/health"
CAPABILITIES_PATH = "/capabilities"

GENERATED_INDEX_TREE_PATH = "/docs/index-tree"
GENERATED_RECENT_PATH = "/docs/recent"
GENERATED_PAYLOAD_PATH = "/docs/doc"
GENERATED_SEARCH_PATH = "/docs/search"
GENERATED_REFERENCES_PATH = "/docs/references"
GENERATED_REFERENCE_TARGET_PATH = "/docs/reference-target"
SOURCE_CONFIG_PATH = "/docs/source-config"
SOURCE_CONFIG_SETTINGS_PATH = "/docs/source-config-settings"
IMPORT_SOURCE_FILES_PATH = "/docs/import-source-files"
REVIEW_SESSIONS_PATH = "/docs/review-sessions"
REVIEW_SESSION_BUILD_PATH = "/docs/review-sessions/build"
REVIEW_SESSION_DELETE_PATH = "/docs/review-sessions/delete"
REVIEW_SESSION_INDEX_TREE_PATH = "/docs/review-sessions/index-tree"
REVIEW_SESSION_PAYLOAD_PATH = "/docs/review-sessions/payload"

SOURCE_BODY_PATH = "/docs/source"
SOURCE_REBUILD_PATH = "/docs/source/rebuild"
OPEN_SOURCE_PATH = "/docs/open-source"
BROKEN_LINKS_PATH = "/docs/broken-links"
IMPORT_SOURCE_PATH = "/docs/import-source"
UPDATE_METADATA_PATH = "/docs/update-metadata"
UPDATE_VIEWABILITY_PATH = "/docs/update-viewability"
UPDATE_VIEWABILITY_BULK_PATH = "/docs/update-viewability-bulk"
CREATE_PATH = "/docs/create"
REBUILD_PATH = "/docs/rebuild"
MOVE_PATH = "/docs/move"
COPY_SUBTREE_PREVIEW_PATH = "/docs/copy-subtree-preview"
COPY_SUBTREE_APPLY_PATH = "/docs/copy-subtree-apply"
DELETE_PREVIEW_PATH = "/docs/delete-preview"
DELETE_APPLY_PATH = "/docs/delete-apply"
SCOPE_CREATE_PREVIEW_PATH = "/docs/scopes/create-preview"
SCOPE_CREATE_APPLY_PATH = "/docs/scopes/create-apply"
SCOPE_RENAME_PREVIEW_PATH = "/docs/scopes/rename-preview"
SCOPE_RENAME_APPLY_PATH = "/docs/scopes/rename-apply"
SCOPE_DELETE_PREVIEW_PATH = "/docs/scopes/delete-preview"
SCOPE_DELETE_APPLY_PATH = "/docs/scopes/delete-apply"
SUB_SCOPE_CREATE_PREVIEW_PATH = "/docs/scopes/sub-scopes/create-preview"
SUB_SCOPE_CREATE_APPLY_PATH = "/docs/scopes/sub-scopes/create-apply"
SUB_SCOPE_DELETE_PREVIEW_PATH = "/docs/scopes/sub-scopes/delete-preview"
SUB_SCOPE_DELETE_APPLY_PATH = "/docs/scopes/sub-scopes/delete-apply"
PUBLISH_STATUS_PATH = "/docs/publish/status"
PUBLISH_CONFIRM_PATH = "/docs/publish/confirm"
PUBLISH_APPLY_PATH = "/docs/publish/apply"
STATIC_HTML_EXPORT_APPLY_PATH = "/docs/export/static-html/apply"
STATIC_HTML_EXPORT_DELETE_PATH = "/docs/export/static-html/delete"

GET_PATHS = (
    HEALTH_PATH,
    CAPABILITIES_PATH,
    GENERATED_INDEX_TREE_PATH,
    GENERATED_RECENT_PATH,
    GENERATED_PAYLOAD_PATH,
    GENERATED_SEARCH_PATH,
    GENERATED_REFERENCES_PATH,
    GENERATED_REFERENCE_TARGET_PATH,
    SOURCE_CONFIG_PATH,
    SOURCE_CONFIG_SETTINGS_PATH,
    SOURCE_BODY_PATH,
    IMPORT_SOURCE_FILES_PATH,
    REVIEW_SESSIONS_PATH,
    REVIEW_SESSION_INDEX_TREE_PATH,
    REVIEW_SESSION_PAYLOAD_PATH,
    PUBLISH_STATUS_PATH,
)

POST_PATHS = (
    SOURCE_REBUILD_PATH,
    OPEN_SOURCE_PATH,
    BROKEN_LINKS_PATH,
    SOURCE_CONFIG_SETTINGS_PATH,
    IMPORT_SOURCE_PATH,
    REVIEW_SESSION_BUILD_PATH,
    REVIEW_SESSION_DELETE_PATH,
    UPDATE_METADATA_PATH,
    UPDATE_VIEWABILITY_PATH,
    UPDATE_VIEWABILITY_BULK_PATH,
    CREATE_PATH,
    REBUILD_PATH,
    MOVE_PATH,
    COPY_SUBTREE_PREVIEW_PATH,
    COPY_SUBTREE_APPLY_PATH,
    DELETE_PREVIEW_PATH,
    DELETE_APPLY_PATH,
    SCOPE_CREATE_PREVIEW_PATH,
    SCOPE_CREATE_APPLY_PATH,
    SCOPE_RENAME_PREVIEW_PATH,
    SCOPE_RENAME_APPLY_PATH,
    SCOPE_DELETE_PREVIEW_PATH,
    SCOPE_DELETE_APPLY_PATH,
    SUB_SCOPE_CREATE_PREVIEW_PATH,
    SUB_SCOPE_CREATE_APPLY_PATH,
    SUB_SCOPE_DELETE_PREVIEW_PATH,
    SUB_SCOPE_DELETE_APPLY_PATH,
    PUBLISH_CONFIRM_PATH,
    PUBLISH_APPLY_PATH,
    STATIC_HTML_EXPORT_APPLY_PATH,
    STATIC_HTML_EXPORT_DELETE_PATH,
)

OPTIONS_PATHS = tuple(dict.fromkeys((*POST_PATHS, *GET_PATHS)))
