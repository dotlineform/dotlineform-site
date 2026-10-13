"""Docs Viewer document-package API routes."""

PREPARE_OPTIONS_PATH = "/docs/packages/prepare-options"
RETURNED_PATH = "/docs/packages/returned"
PREPARE_PATH = "/docs/packages/prepare"
RETURNED_REVIEW_PATH = "/docs/packages/returned/review"

GET_PATHS = (RETURNED_PATH,)
POST_PATHS = (
    PREPARE_OPTIONS_PATH,
    PREPARE_PATH,
    RETURNED_REVIEW_PATH,
)
OPTIONS_PATHS = (*GET_PATHS, *POST_PATHS)
