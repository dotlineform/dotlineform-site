#!/usr/bin/env python3
"""Tag local-service endpoint path constants."""

HEALTH_PATH = "/health"
SAVE_TAGS_PATH = "/save-tags"
BUILD_DOCS_PATH = "/build-docs"
IMPORT_ASSIGNMENTS_PREVIEW_PATH = "/import-tag-assignments-preview"
IMPORT_ASSIGNMENTS_APPLY_PATH = "/import-tag-assignments"
IMPORT_REGISTRY_PATH = "/import-tag-registry"
IMPORT_ALIASES_PATH = "/import-tag-aliases"
DELETE_ALIAS_PATH = "/delete-tag-alias"
MUTATE_ALIAS_PREVIEW_PATH = "/mutate-tag-alias-preview"
MUTATE_ALIAS_APPLY_PATH = "/mutate-tag-alias"
PROMOTE_ALIAS_PREVIEW_PATH = "/promote-tag-alias-preview"
PROMOTE_ALIAS_APPLY_PATH = "/promote-tag-alias"
DEMOTE_TAG_PREVIEW_PATH = "/demote-tag-preview"
DEMOTE_TAG_APPLY_PATH = "/demote-tag"
MUTATE_TAG_PREVIEW_PATH = "/mutate-tag-preview"
MUTATE_TAG_APPLY_PATH = "/mutate-tag"

POST_PATHS = (
    SAVE_TAGS_PATH,
    BUILD_DOCS_PATH,
    IMPORT_ASSIGNMENTS_PREVIEW_PATH,
    IMPORT_ASSIGNMENTS_APPLY_PATH,
    IMPORT_REGISTRY_PATH,
    IMPORT_ALIASES_PATH,
    DELETE_ALIAS_PATH,
    MUTATE_ALIAS_PREVIEW_PATH,
    MUTATE_ALIAS_APPLY_PATH,
    PROMOTE_ALIAS_PREVIEW_PATH,
    PROMOTE_ALIAS_APPLY_PATH,
    DEMOTE_TAG_PREVIEW_PATH,
    DEMOTE_TAG_APPLY_PATH,
    MUTATE_TAG_PREVIEW_PATH,
    MUTATE_TAG_APPLY_PATH,
)

OPTIONS_PATHS = POST_PATHS
