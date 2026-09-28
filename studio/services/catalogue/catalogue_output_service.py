"""Complete local Catalogue media and editor responses after a canonical mutation."""

from __future__ import annotations

from typing import Any

from catalogue.catalogue_output_media import MEDIA_SOURCE_FIELDS, complete_catalogue_media
from catalogue.catalogue_refresh_service import invalidate_refresh_receipt
from catalogue.catalogue_revisions import record_hash
from catalogue.catalogue_service_context import CatalogueWriteContext
from catalogue.catalogue_source import CatalogueSourceRecords, records_from_json_source


def download_filenames(record: dict[str, Any]) -> set[str]:
    return {item["filename"] for item in record.get("downloads") or []}


def changed_work_media_ids(
    previous: CatalogueSourceRecords, current: CatalogueSourceRecords, candidate_ids: set[str],
) -> tuple[list[str], list[str]]:
    """Select current Works with changed image sources or download references."""
    image_ids = []
    download_ids = []
    for key in sorted(candidate_ids & current.works.keys()):
        record = current.works[key]
        old = previous.works.get(key)
        if old is None or any(old.get(field) != record.get(field) for field in MEDIA_SOURCE_FIELDS):
            image_ids.append(key)
        if old is None or download_filenames(old) != download_filenames(record):
            download_ids.append(key)
    return sorted(image_ids), sorted(download_ids)


def complete_saved_catalogue_edit(
    context: CatalogueWriteContext, response: dict[str, Any], previous: CatalogueSourceRecords,
) -> None:
    """Preserve canonical success when local media or response completion fails."""
    if context.dry_run or not response.get("ok"):
        return
    response["saved"] = True
    failures: list[str] = []
    current: CatalogueSourceRecords | None = None
    media_attempted = False
    try:
        current = records_from_json_source(context.source_dir)
        candidate_ids = {
            key for key in (
                response.get("work_id"), *response.get("selected_ids", ()), *response.get("changed_work_ids", ()),
            ) if key in current.works
        }
        image_ids, download_ids = changed_work_media_ids(previous, current, candidate_ids)
        # A staged replacement can reuse an existing download filename.
        download_ids = sorted(set(download_ids) | {
            key for key in candidate_ids if download_filenames(current.works[key])
        })
        work_ids = sorted(set(image_ids) | set(download_ids))
        if work_ids:
            media_attempted = True
            response["media"] = complete_catalogue_media(
                context.repo_root, context.source_dir, records=current, previous=previous,
                work_ids=work_ids, image_work_ids=image_ids, write=True,
            )
    except (Exception, SystemExit) as error:
        failures.append(f"Local Save preparation: {error}")
    try:
        # Reuse the loaded source unless media promotion may have changed revisions.
        if current is None or media_attempted:
            current = records_from_json_source(context.source_dir)
        if "record" in response and "gallery_id" not in response:
            record = current.series.get(response.get("series_id")) if response.get("series_id") else current.works.get(response.get("work_id"))
            if record:
                response.update(record=record, record_hash=record_hash(record))
        # Bulk mutation responses already include every selected Work and its saved memberships.
        for key in ("records", "work_records"):
            for entry in response.get(key, []):
                record = current.works.get(entry.get("work_id"))
                if record:
                    entry.update(record=record, record_hash=record_hash(record))
    except Exception as error:
        failures.append(f"Editor response: {error}")
    if response.get("changed") or response.get("created") or response.get("deleted") or response.get("media", {}).get("downloads") or failures:
        try:
            invalidate_refresh_receipt(context.repo_root)
            response["refresh_needed"] = True
        except (OSError, ValueError) as error:
            failures.append(f"Refresh status: {error}")
    if failures:
        response["save_completion"] = {
            "status": "failed", "error": "; ".join(failures),
            "message": "Data saved, but local Save completion did not finish.",
        }
