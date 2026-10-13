"""Catalogue service route dispatcher for Local Studio."""

from __future__ import annotations

from http import HTTPStatus
from pathlib import Path
from typing import Any, Mapping, Sequence

from catalogue.catalogue_bulk_service import bulk_save_payload
from catalogue.catalogue_delete_service import delete_apply_response
from catalogue.catalogue_series_service import series_create_payload, series_save_payload
from catalogue.catalogue_gallery_service import mutate_gallery_payload
from catalogue.catalogue_service_context import build_catalogue_write_context
from catalogue.catalogue_work_service import work_create_payload, work_save_payload
from catalogue.catalogue_work_batch_service import work_batch_create_payload
from catalogue.catalogue_output_service import complete_saved_catalogue_edit
from catalogue.catalogue_work_attachments import WorkAttachment, bind_work_attachments


SERVICE_POST_PATHS = {
    "/bulk-save",
    "/work/create",
    "/work/create-batch",
    "/work/save",
    "/series/create",
    "/series/save",
    "/gallery/create",
    "/gallery/save",
    "/gallery/delete",
    "/delete-apply",
}


def handle_catalogue_post(
    repo_root: Path,
    api_path: str,
    body: Mapping[str, Any],
    *,
    dry_run: bool = False,
    attachments: Sequence[WorkAttachment] = (),
) -> tuple[HTTPStatus, dict[str, Any]]:
    attachment_files = {}
    regenerate_image = False
    if api_path in {"/work/create", "/work/save"}:
        attachment_files = bind_work_attachments(body, attachments)
        regenerate_image = body.get("regenerate_image", False)
    elif attachments or "regenerate_image" in body:
        raise ValueError("Media requests belong to single Work create/Save")
    context = build_catalogue_write_context(repo_root, dry_run=dry_run)
    if api_path == "/delete-apply":
        return delete_apply_response(context, body)
    mutations = {
        "/work/create": work_create_payload,
        "/work/save": work_save_payload,
        "/work/create-batch": work_batch_create_payload,
        "/series/create": series_create_payload,
        "/series/save": series_save_payload,
        "/bulk-save": bulk_save_payload,
    }
    if api_path in mutations:
        payload, previous, current = mutations[api_path](context, body)
    elif api_path in {"/gallery/create", "/gallery/save", "/gallery/delete"}:
        payload, previous, current = mutate_gallery_payload(context, api_path.rsplit("/", 1)[1], body)
    else:
        raise FileNotFoundError(f"Unknown catalogue service route: {api_path}")
    complete_saved_catalogue_edit(
        context, payload, previous, current_records=current, attachment_files=attachment_files,
        regenerate_image=regenerate_image,
    )
    return HTTPStatus.OK, payload
