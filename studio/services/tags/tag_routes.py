#!/usr/bin/env python3
"""Studio tag service endpoint path constants."""

HEALTH_PATH = "/health"
SAVE_TAGS_PATH = "/save-tags"
CREATE_TAG_PATH = "/create-tag"
CREATE_ALIAS_PATH = "/create-tag-alias"
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
    CREATE_TAG_PATH,
    CREATE_ALIAS_PATH,
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
