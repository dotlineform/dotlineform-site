"""Docs Viewer document-package API routes."""

CONFIG_PATH = "/docs/packages/config"
DOCUMENTS_PATH = "/docs/packages/documents"
RETURNED_PATH = "/docs/packages/returned"
PREPARE_PATH = "/docs/packages/prepare"
CONTEXT_PATH = "/docs/packages/context"
RETURNED_INSPECT_PATH = "/docs/packages/returned/inspect"
RETURNED_REVIEW_PATH = "/docs/packages/returned/review"

GET_PATHS = (CONFIG_PATH, DOCUMENTS_PATH, RETURNED_PATH)
POST_PATHS = (
    PREPARE_PATH,
    CONTEXT_PATH,
    RETURNED_INSPECT_PATH,
    RETURNED_REVIEW_PATH,
)
OPTIONS_PATHS = (*GET_PATHS, *POST_PATHS)
