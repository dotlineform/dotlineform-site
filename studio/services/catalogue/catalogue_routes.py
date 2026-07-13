#!/usr/bin/env python3
"""Catalogue local-service endpoint path constants."""

HEALTH_PATH = "/health"
WORK_SAVE_PATH = "/catalogue/work/save"
WORK_CREATE_PATH = "/catalogue/work/create"
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
BULK_SAVE_PATH = "/catalogue/bulk-save"
DELETE_PREVIEW_PATH = "/catalogue/delete-preview"
DELETE_APPLY_PATH = "/catalogue/delete-apply"
PUBLICATION_PREVIEW_PATH = "/catalogue/publication-preview"
PUBLICATION_APPLY_PATH = "/catalogue/publication-apply"
MEDIA_PUBLISH_PREVIEW_PATH = "/catalogue/media-publish-preview"
MEDIA_PUBLISH_APPLY_PATH = "/catalogue/media-publish-apply"
PROJECT_STATE_REPORT_PATH = "/catalogue/project-state-report"
THUMBNAIL_QUALITY_PREVIEW_PATH = "/catalogue/thumbnail-quality-preview"

POST_PATHS = (
    WORK_CREATE_PATH,
    BULK_SAVE_PATH,
    DELETE_PREVIEW_PATH,
    DELETE_APPLY_PATH,
    PUBLICATION_PREVIEW_PATH,
    PUBLICATION_APPLY_PATH,
    MEDIA_PUBLISH_PREVIEW_PATH,
    MEDIA_PUBLISH_APPLY_PATH,
    WORK_SAVE_PATH,
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
    PROJECT_STATE_REPORT_PATH,
    THUMBNAIL_QUALITY_PREVIEW_PATH,
)

OPTIONS_PATHS = (*POST_PATHS, CATALOGUE_READ_PATH)
