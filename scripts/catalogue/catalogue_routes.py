#!/usr/bin/env python3
"""Catalogue local-service endpoint path constants."""

HEALTH_PATH = "/health"
WORK_SAVE_PATH = "/catalogue/work/save"
WORK_CREATE_PATH = "/catalogue/work/create"
DETAIL_SAVE_PATH = "/catalogue/work-detail/save"
DETAIL_CREATE_PATH = "/catalogue/work-detail/create"
WORK_FILE_SAVE_PATH = "/catalogue/work-file/save"
WORK_FILE_CREATE_PATH = "/catalogue/work-file/create"
WORK_FILE_DELETE_PATH = "/catalogue/work-file/delete"
WORK_LINK_SAVE_PATH = "/catalogue/work-link/save"
WORK_LINK_CREATE_PATH = "/catalogue/work-link/create"
WORK_LINK_DELETE_PATH = "/catalogue/work-link/delete"
CATALOGUE_READ_PATH = "/catalogue/read"
IMPORT_PREVIEW_PATH = "/catalogue/import-preview"
IMPORT_APPLY_PATH = "/catalogue/import-apply"
SERIES_SAVE_PATH = "/catalogue/series/save"
SERIES_CREATE_PATH = "/catalogue/series/create"
BUILD_PREVIEW_PATH = "/catalogue/build-preview"
BUILD_APPLY_PATH = "/catalogue/build-apply"
PROSE_IMPORT_PREVIEW_PATH = "/catalogue/prose/import-preview"
PROSE_IMPORT_APPLY_PATH = "/catalogue/prose/import-apply"
MOMENT_IMPORT_PREVIEW_PATH = "/catalogue/moment/import-preview"
MOMENT_IMPORT_APPLY_PATH = "/catalogue/moment/import-apply"
MOMENT_PREVIEW_PATH = "/catalogue/moment/preview"
MOMENT_SAVE_PATH = "/catalogue/moment/save"
BULK_SAVE_PATH = "/catalogue/bulk-save"
DELETE_PREVIEW_PATH = "/catalogue/delete-preview"
DELETE_APPLY_PATH = "/catalogue/delete-apply"
PUBLICATION_PREVIEW_PATH = "/catalogue/publication-preview"
PUBLICATION_APPLY_PATH = "/catalogue/publication-apply"
PROJECT_STATE_REPORT_PATH = "/catalogue/project-state-report"
THUMBNAIL_QUALITY_PREVIEW_PATH = "/catalogue/thumbnail-quality-preview"

POST_PATHS = (
    WORK_CREATE_PATH,
    BULK_SAVE_PATH,
    DELETE_PREVIEW_PATH,
    DELETE_APPLY_PATH,
    PUBLICATION_PREVIEW_PATH,
    PUBLICATION_APPLY_PATH,
    WORK_SAVE_PATH,
    DETAIL_CREATE_PATH,
    DETAIL_SAVE_PATH,
    WORK_FILE_CREATE_PATH,
    WORK_FILE_SAVE_PATH,
    WORK_FILE_DELETE_PATH,
    WORK_LINK_CREATE_PATH,
    WORK_LINK_SAVE_PATH,
    WORK_LINK_DELETE_PATH,
    IMPORT_PREVIEW_PATH,
    IMPORT_APPLY_PATH,
    SERIES_SAVE_PATH,
    SERIES_CREATE_PATH,
    BUILD_PREVIEW_PATH,
    BUILD_APPLY_PATH,
    PROSE_IMPORT_PREVIEW_PATH,
    PROSE_IMPORT_APPLY_PATH,
    MOMENT_IMPORT_PREVIEW_PATH,
    MOMENT_IMPORT_APPLY_PATH,
    MOMENT_PREVIEW_PATH,
    MOMENT_SAVE_PATH,
    PROJECT_STATE_REPORT_PATH,
    THUMBNAIL_QUALITY_PREVIEW_PATH,
)

OPTIONS_PATHS = (*POST_PATHS, CATALOGUE_READ_PATH)
