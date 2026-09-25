"""Complete local images and their canonical dimensions/versions before JSON generation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from catalogue import catalogue_transactions as transactions
from catalogue.catalogue_source import SOURCE_FILES, payload_for_map, records_from_json_source, validate_source_records


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
    source_dir: Path, tasks: Sequence[Mapping[str, Any]], *, changed_images: set[str],
    media_files: Mapping[Path, bytes],
) -> list[MediaVersionFinalization]:
    """Commit prepared local bytes and their metadata together; transfers never call this."""
    records = records_from_json_source(source_dir)
    finalized = []
    changed_works = False
    for task in tasks:
        item_id = task["id"]
        advance = item_id in changed_images
        record = records.works.get(item_id)
        if not record or not record.get("project_filename"):
            raise ValueError(f"Work {item_id}: source image is required before local completion")
        previous_version = record.get("media_version")
        if type(previous_version) is not int or previous_version < 1:
            raise ValueError(f"Work {item_id}: media_version must be a positive whole number")
        work_id = item_id
        version = previous_version + int(advance)
        updates = {"media_version": version, "width_px": task["source_width_px"], "height_px": task["source_height_px"]}
        if any(record.get(key) != value for key, value in updates.items()):
            record.update(updates)
            changed_works = True
        finalized.append(MediaVersionFinalization("works", item_id, work_id, previous_version, version, advance, f"works/index/{work_id}.json"))
    errors = validate_source_records(records)
    if errors:
        raise ValueError("Catalogue source validation failed: " + "; ".join(errors[:20]))
    payloads = {}
    if changed_works:
        payloads[source_dir / SOURCE_FILES["works"]] = payload_for_map("works", records.works)
    if payloads or media_files:
        transactions.atomic_write_many(payloads, media_files=media_files)
    return finalized
