"""Save/import/delete completion after the authoritative canonical transaction."""

from __future__ import annotations

from typing import Any

from catalogue.catalogue_output_media import complete_catalogue_media
from catalogue.catalogue_revisions import record_hash
from catalogue.catalogue_service_context import CatalogueWriteContext, refresh_lookup_payloads
from catalogue.catalogue_source import CatalogueSourceRecords, records_from_json_source
from catalogue.generate_work_pages import generate_catalogue_json


def changed_output_ids(previous: CatalogueSourceRecords, current: CatalogueSourceRecords) -> tuple[list[str], list[str]]:
    """Include changed children and both ends of a membership change."""
    works = {key for key in previous.works.keys() | current.works.keys() if previous.works.get(key) != current.works.get(key)}
    series = {key for key in previous.series.keys() | current.series.keys() if previous.series.get(key) != current.series.get(key)}
    for before, after in ((previous.work_details, current.work_details), (previous.work_detail_sections, current.work_detail_sections)):
        for key in before.keys() | after.keys():
            if before.get(key) != after.get(key):
                works.update(record["work_id"] for record in (before.get(key), after.get(key)) if record)
    for wid in works:
        series.update(record["series_id"] for record in (previous.works.get(wid), current.works.get(wid)) if record and record.get("series_id"))
    return sorted(works), sorted(series)


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
        elif response.get("kind") == "work_details":
            work_ids = sorted(set(work_ids) | {current.work_details[uid]["work_id"] for uid in selected})
        if not work_ids and not series_ids:
            return
        complete_catalogue_media(context.repo_root, context.source_dir, records=current, previous=previous, work_ids=work_ids, write=True)
        response["output"] = generate_catalogue_json(
            context.repo_root, context.source_dir, write=True, work_ids=work_ids, series_ids=series_ids,
        )
    except (Exception, SystemExit) as error:
        response["output"] = {"status": "failed", "error": str(error), "message": "Data saved, but output generation did not complete."}
    try:
        # Media promotion can change revisions, including before a later failure.
        current = records_from_json_source(context.source_dir)
        if "record" in response:
            record = current.series.get(response.get("series_id")) if response.get("series_id") else current.works.get(response.get("work_id"))
            if record:
                response.update(record=record, record_hash=record_hash(record))
        if response.get("selected_ids"):
            identity = "detail_uid" if response["kind"] == "work_details" else "work_id"
            response["records"] = [{identity: item_id} for item_id in response["selected_ids"]]
        for key in ("records", "work_records"):
            for entry in response.get(key, []):
                record = current.work_details.get(entry.get("detail_uid")) if entry.get("detail_uid") else current.works.get(entry.get("work_id"))
                if record:
                    entry.update(record=record, record_hash=record_hash(record))
        response["lookup_refresh"] = refresh_lookup_payloads(context)
    except Exception as error:
        response["output"] = {"status": "failed", "error": str(error), "message": "Data saved, but Studio lookup refresh did not complete."}
