#!/usr/bin/env python3
"""Catalogue local-service endpoint path constants."""

HEALTH_PATH = "/health"
WORK_SAVE_PATH = "/catalogue/work/save"
WORK_CREATE_PATH = "/catalogue/work/create"
CATALOGUE_READ_PATH = "/catalogue/read"
SERIES_SAVE_PATH = "/catalogue/series/save"
SERIES_CREATE_PATH = "/catalogue/series/create"
BULK_SAVE_PATH = "/catalogue/bulk-save"
DELETE_PREVIEW_PATH = "/catalogue/delete-preview"
DELETE_APPLY_PATH = "/catalogue/delete-apply"

POST_PATHS = (
    WORK_CREATE_PATH,
    BULK_SAVE_PATH,
    DELETE_PREVIEW_PATH,
    DELETE_APPLY_PATH,
    WORK_SAVE_PATH,
    SERIES_SAVE_PATH,
    SERIES_CREATE_PATH,
)

OPTIONS_PATHS = (*POST_PATHS, CATALOGUE_READ_PATH)
