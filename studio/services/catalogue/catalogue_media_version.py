"""Complete local images and their canonical dimensions/versions before JSON generation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from catalogue import catalogue_transactions as transactions
from catalogue.catalogue_source import CatalogueSourceRecords, SOURCE_FILES, payload_for_map, work_resource_entries


@dataclass(frozen=True)
class MediaVersionFinalization:
    kind: str
    item_id: str
    work_id: str
    previous_version: int
    media_version: int
    advanced: bool
    output_json_path: str


def finalize_catalogue_media_versions(
    source_dir: Path, tasks: Sequence[Mapping[str, Any]], *, records: CatalogueSourceRecords, changed_images: set[str],
    media_files: Mapping[Path, bytes], staged_downloads_by_work: Mapping[str, set[str]],
) -> list[MediaVersionFinalization]:
    """Commit prepared bytes/metadata, then update the caller's saved Work map.

    Proposed record copies keep the supplied map at its persisted state if the
    transaction fails. No canonical reread or transfer-owned update occurs here.
    """
    works = dict(records.works)
    finalized = []
    changed_records = {}
    for task in tasks:
        item_id = task["id"]
        advance = item_id in changed_images
        record = works.get(item_id)
        if not record or not record.get("project_filename"):
            raise ValueError(f"Work {item_id}: source image is required before local completion")
        previous_version = record.get("media_version")
        if type(previous_version) is not int or previous_version < 1:
            raise ValueError(f"Work {item_id}: media_version must be a positive whole number")
        work_id = item_id
        version = previous_version + int(advance)
        updates = {"media_version": version, "width_px": task["source_width_px"], "height_px": task["source_height_px"]}
        if task["status"] == "pending":
            updates["image_staged"] = True
        if any(record.get(key) != value for key, value in updates.items()):
            record = {**record, **updates}
            works[item_id] = record
            changed_records[item_id] = record
        finalized.append(MediaVersionFinalization("works", item_id, work_id, previous_version, version, advance, f"works/index/{work_id}.json"))
    for work_id, names in staged_downloads_by_work.items():
        if not names:
            continue
        record = works[work_id]
        downloads = [dict(item) for item in work_resource_entries(record, "downloads")]
        changed_downloads = False
        for download in downloads:
            if download["filename"] in names and download["staged"] is not True:
                download["staged"] = True
                changed_downloads = True
        if changed_downloads:
            record = {**record, "downloads": downloads}
            works[work_id] = record
            changed_records[work_id] = record
    payloads = {}
    if changed_records:
        payloads[source_dir / SOURCE_FILES["works"]] = payload_for_map("works", works)
    if payloads or media_files:
        transactions.atomic_write_many(payloads, media_files=media_files)
    records.works.update(changed_records)
    return finalized
