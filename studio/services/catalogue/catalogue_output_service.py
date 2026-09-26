"""Save/import/delete completion after the authoritative canonical transaction."""

from __future__ import annotations

from typing import Any

from catalogue.catalogue_output_media import complete_catalogue_media
from catalogue.catalogue_revisions import record_hash
from catalogue.catalogue_service_context import CatalogueWriteContext, refresh_lookup_payloads
from catalogue.catalogue_source import CatalogueSourceRecords, records_from_json_source
from catalogue.generate_work_pages import generate_catalogue_json
from catalogue.catalogue_works_metadata import update_catalogue_works_metadata
from catalogue.works_collection_metadata import update_works_collection_metadata


def changed_output_ids(previous: CatalogueSourceRecords, current: CatalogueSourceRecords) -> tuple[list[str], list[str]]:
    """Include changed Works and both ends of a Series membership change."""
    works = {key for key in previous.works.keys() | current.works.keys() if previous.works.get(key) != current.works.get(key)}
    series = {key for key in previous.series.keys() | current.series.keys() if previous.series.get(key) != current.series.get(key)}
    for wid in works:
        series.update(record["series_id"] for record in (previous.works.get(wid), current.works.get(wid)) if record and record.get("series_id"))
    return sorted(works), sorted(series)


def _update_report_metadata(context: CatalogueWriteContext, response: dict[str, Any], records: CatalogueSourceRecords) -> None:
    """Use mutation identities, independent of wider media/Gallery invalidation."""
    work_ids: set[str] = set()
    deleted_work_ids: list[str] = []
    if "work_id" in response:
        work_ids.add(response["work_id"])
    elif response.get("kind") == "works":
        work_ids.update(response["selected_ids"])
    elif "series_id" in response:
        work_ids.update(response["changed_work_ids"])
        # Series titles are embedded in member rows, including unchanged Save retries.
        work_ids.update(wid for wid, record in records.works.items() if record.get("series_id") == response["series_id"])
    elif response.get("deleted") and response["kind"] == "work":
        deleted_work_ids.append(response["id"])
    if work_ids or deleted_work_ids:
        response["report_metadata"] = update_catalogue_works_metadata(
            context.repo_root, records, work_ids=sorted(work_ids), deleted_work_ids=deleted_work_ids, write=True,
        )


def complete_saved_catalogue_output(
    context: CatalogueWriteContext, response: dict[str, Any], previous: CatalogueSourceRecords,
) -> None:
    """Preserve the saved result and revisions even when output processing fails."""
    if context.dry_run or not response.get("ok"):
        return
    response["saved"] = True
    try:
        current = records_from_json_source(context.source_dir)
        work_ids, series_ids = changed_output_ids(previous, current)
        # Save also refreshes unchanged selections after the author fixes a media file.
        if not work_ids and response.get("work_id"):
            work_ids = [response["work_id"]]
        if not series_ids and response.get("series_id"):
            series_ids = [response["series_id"]]
        selected = response.get("selected_ids", [])
        if response.get("kind") == "works":
            work_ids = sorted(set(work_ids) | set(selected))
        gallery_ids = response.get("affected_gallery_ids", ())
        if not work_ids and not series_ids and not gallery_ids:
            return
        # Definition-only Gallery mutations change references, never Work media.
        if work_ids or series_ids:
            complete_catalogue_media(context.repo_root, context.source_dir, records=current, previous=previous, work_ids=work_ids, write=True)
        output_work_ids = sorted(set(work_ids) | set(response.get("affected_work_ids", ())))
        response["output"] = generate_catalogue_json(
            context.repo_root, context.source_dir, write=True, work_ids=output_work_ids, series_ids=series_ids,
            gallery_ids=gallery_ids,
        )
        _update_report_metadata(context, response, current)
        if work_ids or series_ids:
            response["works_collection_metadata"] = update_works_collection_metadata(
                context.repo_root, current,
                work_ids=[key for key in work_ids if key in current.works],
                series_ids=[key for key in series_ids if key in current.series],
                deleted_work_ids=[key for key in work_ids if key not in current.works],
                deleted_series_ids=[key for key in series_ids if key not in current.series],
                write=True,
            )
    except (Exception, SystemExit) as error:
        response["output"] = {"status": "failed", "error": str(error), "message": "Data saved, but output generation did not complete."}
    try:
        # Media promotion can change revisions, including before a later failure.
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
        response["lookup_refresh"] = refresh_lookup_payloads(context)
    except Exception as error:
        response["output"] = {"status": "failed", "error": str(error), "message": "Data saved, but Studio lookup refresh did not complete."}
