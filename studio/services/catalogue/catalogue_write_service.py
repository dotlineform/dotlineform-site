"""Catalogue service route dispatcher for Local Studio."""

from __future__ import annotations

from http import HTTPStatus
from pathlib import Path
from typing import Any, Mapping

from catalogue.catalogue_bulk_service import bulk_save_payload
from catalogue.catalogue_detail_section_service import create_detail_section_payload, save_detail_section_payload
from catalogue.catalogue_delete_service import delete_apply_response, delete_preview_payload
from catalogue.catalogue_series_service import series_create_payload, series_save_payload
from catalogue.catalogue_service_context import CatalogueWriteContext, build_catalogue_write_context
from catalogue.catalogue_work_service import work_create_payload, work_save_payload
from catalogue.catalogue_output_service import complete_saved_catalogue_output
from catalogue.catalogue_source import records_from_json_source


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
}


def handle_catalogue_post(
    repo_root: Path,
    api_path: str,
    body: Mapping[str, Any],
    *,
    dry_run: bool = False,
) -> tuple[HTTPStatus, dict[str, Any]]:
    context = build_catalogue_write_context(repo_root, dry_run=dry_run)
    previous = records_from_json_source(context.source_dir) if api_path != "/delete-preview" else None
    status, payload = _dispatch_mutation(context, api_path, body)
    if previous is not None:
        complete_saved_catalogue_output(context, payload, previous)
    return status, payload


def _dispatch_mutation(context: CatalogueWriteContext, api_path: str, body: Mapping[str, Any]) -> tuple[HTTPStatus, dict[str, Any]]:
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
    raise FileNotFoundError(f"Unknown catalogue service route: {api_path}")
