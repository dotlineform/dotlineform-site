"""Create confirmed folder images together, then hand off normal Save completion."""

from __future__ import annotations

from dataclasses import replace
import math
from pathlib import Path
from typing import Any, Mapping

from catalogue.catalogue_galleries import MEMBERSHIPS_FILE, read_galleries, with_work_memberships
from catalogue.catalogue_shared_changes import work_shared_changes
from catalogue.catalogue_media_files import IMAGE_EXTENSIONS
from catalogue.catalogue_revisions import record_hash
from catalogue.catalogue_service_context import CatalogueWriteContext, load_works_payload, log_event, utc_now
from catalogue.catalogue_source import (
    WORK_FIELDS, CatalogueSourceRecords, load_json_file, payload_for_map, validate_source_records,
)
from catalogue.catalogue_source_mutation import normalize_work_update
from catalogue.catalogue_transactions import execute_source_json_write
from catalogue.catalogue_work_service import extract_work_update
from pipeline_config import work_media_source_ids
from catalogue.catalogue_build_media import PIPELINE_CONFIG


PER_IMAGE_FIELDS = frozenset({
    "work_id", "title", "media_source_id", "project_folder", "project_subfolder", "project_filename",
    "media_version", "width_px", "height_px",
})


def _source_segment(value: Any, field: str) -> str:
    if (
        not isinstance(value, str) or not value or value.startswith(".")
        or "/" in value or "\\" in value
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise ValueError(f"{field} must be one visible source path segment")
    return value


def work_batch_create_payload(
    context: CatalogueWriteContext, body: Mapping[str, Any],
) -> tuple[dict[str, Any], CatalogueSourceRecords, CatalogueSourceRecords]:
    """Validate the entire confirmed batch and write Works/memberships once.

    Filenames are supplied by the picker, never rediscovered by enumeration.
    This validates source identities lexically; normal media completion resolves
    and reads every exact image after canonical persistence. Its failures retain
    all created Works. Reimport deliberately creates another independent batch.
    IDs advance above the highest canonical ID; lower gaps may be reserved and
    are never filled by this operation.
    """
    if set(body) - {"record", "gallery_ids", "folder_selection"}:
        raise ValueError("Unsupported batch creation fields")
    shared = extract_work_update(body)
    if set(shared) & PER_IMAGE_FIELDS:
        raise ValueError("Batch record must contain only shared Work metadata")
    if not isinstance(shared.get("series_id"), str) or not shared["series_id"].strip():
        raise ValueError("Series is required")
    year = shared.get("year")
    if isinstance(year, bool) or not isinstance(year, int):
        raise ValueError("Year must be a whole year")
    if not isinstance(shared.get("year_display"), str) or not shared["year_display"].strip():
        raise ValueError("Year display is required")
    for field in ("height_cm", "width_cm", "depth_cm"):
        value = shared.get(field)
        if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)):
            raise ValueError(f"{field} must be a finite number or empty")

    selection = body.get("folder_selection")
    if not isinstance(selection, dict) or set(selection) != {"media_source_id", "project_folder", "project_subfolder", "filenames"}:
        raise ValueError("A complete confirmed folder selection is required")
    source_id = selection["media_source_id"]
    if not isinstance(source_id, str) or source_id not in work_media_source_ids(PIPELINE_CONFIG):
        raise ValueError("An exact configured media source is required")
    folder = _source_segment(selection["project_folder"], "project_folder")
    subfolder = _source_segment(selection["project_subfolder"], "project_subfolder")
    filenames = selection["filenames"]
    if not isinstance(filenames, list) or not filenames:
        raise ValueError("Confirmed filenames must be a non-empty array")
    for filename in filenames:
        _source_segment(filename, "filename")
        if Path(filename).suffix.lower() not in IMAGE_EXTENSIONS:
            raise ValueError(f"Unsupported image filename: {filename}")
    if len(set(filenames)) != len(filenames):
        raise ValueError("Confirmed filenames must be distinct")
    filenames = sorted(filenames, key=lambda name: (name.casefold(), name))

    # Read each authority once; no per-image create requests or Catalogue rewrites.
    works = load_works_payload(context.works_path)["works"]
    series = load_json_file(context.series_path).get("series")
    if not isinstance(series, dict):
        raise ValueError("Series source must contain a series object")
    previous = CatalogueSourceRecords(works=works, series=series, work_detail_sections={}, work_details={})
    galleries = read_galleries(context.source_dir)
    next_work_number = max((int(work_id) for work_id in works), default=0) + 1
    if next_work_number + len(filenames) - 1 > 99999:
        raise ValueError("Not enough five-digit Work IDs above the highest current Work ID for this batch")
    additions = {}
    for number, filename in enumerate(filenames, start=next_work_number):
        work_id = f"{number:05d}"
        record = normalize_work_update(work_id, {field: None for field in WORK_FIELDS}, {
            **shared, "work_id": work_id, "title": Path(filename).stem,
            "media_source_id": source_id, "project_folder": folder,
            "project_subfolder": subfolder, "project_filename": filename,
        })
        # Exact source names and filename-stem titles are batch-owned values.
        record["title"] = Path(filename).stem
        additions[work_id] = record
    current = replace(previous, works={**works, **additions})
    errors = validate_source_records(current)
    if errors:
        raise ValueError("source validation failed: " + "; ".join(errors[:20]))
    updated_galleries = with_work_memberships(
        galleries, current.works, {work_id: body.get("gallery_ids", []) for work_id in additions},
    )
    writes = {context.works_path.resolve(): payload_for_map("works", current.works)}
    if galleries.works != updated_galleries.works:
        writes[(context.source_dir / MEMBERSHIPS_FILE).resolve()] = updated_galleries.payloads()[MEMBERSHIPS_FILE]
    if not set(writes).issubset(context.allowed_write_paths):
        raise ValueError("write target not allowlisted")
    execute_source_json_write(writes, dry_run=context.dry_run, repo_root=context.repo_root)
    created_ids = list(additions)
    response: dict[str, Any] = {
        "ok": True, "created": True, "changed": True,
        "created_ids": created_ids, "created_count": len(created_ids), "changed_work_ids": created_ids,
        "records": [{
            "work_id": work_id, "record": record, "record_hash": record_hash(record),
            "gallery_ids": updated_galleries.works.get(work_id, []),
        } for work_id, record in additions.items()],
        "affected_gallery_ids": sorted(body.get("gallery_ids", [])),
        "_shared_changes": work_shared_changes(
            previous.works, current.works, galleries.works, updated_galleries.works, additions,
        ),
    }
    if context.dry_run:
        response.update(dry_run=True, would_write=True)
    else:
        response["saved_at_utc"] = utc_now()
    log_event(context.repo_root, "catalogue_work_batch_create", {"created_ids": created_ids, "dry_run": context.dry_run})
    return response, previous, current
