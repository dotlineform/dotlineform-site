"""Catalogue service route dispatcher for Local Studio."""

from __future__ import annotations

from http import HTTPStatus
from pathlib import Path
from typing import Any, Mapping

from catalogue.catalogue_bulk_service import bulk_save_payload
from catalogue.catalogue_build_service import build_apply_payload, build_preview_payload
from catalogue.catalogue_detail_section_service import create_detail_section_payload, save_detail_section_payload
from catalogue.catalogue_delete_service import delete_apply_response, delete_preview_payload
from catalogue.catalogue_media_publish_service import media_publish_apply_response, media_publish_preview_response
from catalogue.catalogue_publication_service import publication_apply_response, publication_preview_payload
from catalogue.catalogue_series_service import series_create_payload, series_save_payload
from catalogue.catalogue_service_context import CatalogueWriteContext, build_catalogue_write_context
from catalogue.catalogue_work_service import work_create_payload, work_save_payload


SERVICE_POST_PATHS = {
    "/bulk-save",
    "/work-detail-section/create",
    "/work-detail-section/save",
    "/work/create",
    "/work/save",
    "/series/create",
    "/series/save",
    "/delete-preview",
    "/delete-apply",
    "/publication-preview",
    "/publication-apply",
    "/media-publish-preview",
    "/media-publish-apply",
    "/build-preview",
    "/build-apply",
}


def handle_catalogue_post(
    repo_root: Path,
    api_path: str,
    body: Mapping[str, Any],
    *,
    dry_run: bool = False,
) -> tuple[HTTPStatus, dict[str, Any]]:
    context = build_catalogue_write_context(repo_root, dry_run=dry_run)
    if api_path == "/work/create":
        return HTTPStatus.OK, work_create_payload(context, body)
    if api_path == "/bulk-save":
        return HTTPStatus.OK, bulk_save_payload(context, body)
    if api_path == "/work-detail-section/create":
        return HTTPStatus.OK, create_detail_section_payload(context, body)
    if api_path == "/work-detail-section/save":
        return HTTPStatus.OK, save_detail_section_payload(context, body)
    if api_path == "/work/save":
        return HTTPStatus.OK, work_save_payload(context, body)
    if api_path == "/series/create":
        return HTTPStatus.OK, series_create_payload(context, body)
    if api_path == "/series/save":
        return HTTPStatus.OK, series_save_payload(context, body)
    if api_path == "/delete-preview":
        return HTTPStatus.OK, delete_preview_payload(context, body)
    if api_path == "/delete-apply":
        return delete_apply_response(context, body)
    if api_path == "/publication-preview":
        return HTTPStatus.OK, publication_preview_payload(context, body)
    if api_path == "/publication-apply":
        return publication_apply_response(context, body)
    if api_path == "/media-publish-preview":
        return media_publish_preview_response(context, body)
    if api_path == "/media-publish-apply":
        return media_publish_apply_response(context, body)
    if api_path == "/build-preview":
        return HTTPStatus.OK, build_preview_payload(context, body)
    if api_path == "/build-apply":
        success, payload = build_apply_payload(context, body)
        return HTTPStatus.OK if success else HTTPStatus.INTERNAL_SERVER_ERROR, payload
    raise FileNotFoundError(f"Unknown catalogue service route: {api_path}")
