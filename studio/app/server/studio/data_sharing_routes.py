#!/usr/bin/env python3
"""Studio Data Sharing local-service endpoint path constants."""

PREPARE_PATH = "/data-sharing/prepare"
RETURNED_PACKAGES_PATH = "/data-sharing/returned-packages"
REVIEW_PATH = "/data-sharing/review"
APPLY_PATH = "/data-sharing/apply"

GET_PATHS = (
    RETURNED_PACKAGES_PATH,
)

POST_PATHS = (
    PREPARE_PATH,
    REVIEW_PATH,
    APPLY_PATH,
)

OPTIONS_PATHS = (*GET_PATHS, *POST_PATHS)
