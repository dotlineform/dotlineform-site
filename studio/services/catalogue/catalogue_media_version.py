"""Promote confirmed Catalogue media versions once per completed upload batch."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from catalogue import catalogue_transactions as transactions
from catalogue.catalogue_source import DEFAULT_SOURCE_DIR, SOURCE_FILES, payload_for_map, records_from_json_source
from catalogue.generate_work_pages import generate_catalogue_json


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
    repo_root: Path, targets: Mapping[tuple[str, str], bool], *, refresh_output: bool,
) -> list[MediaVersionFinalization]:
    """Persist confirmed versions coherently; callers include only complete remote sets."""
    source_dir = repo_root / DEFAULT_SOURCE_DIR
    records = records_from_json_source(source_dir)
    finalized = []
    changed_works = False
    for (kind, item_id), advance in targets.items():
        if kind != "works":
            raise ValueError(f"unsupported Catalogue media kind: {kind}")
        record = records.works.get(item_id)
        if not record or not record.get("project_filename"):
            raise ValueError(f"{kind} {item_id}: source image is required before promotion")
        previous_version = record.get("media_version")
        if not isinstance(previous_version, int) or previous_version < 1:
            raise ValueError(f"{kind} {item_id}: media_version must be a positive whole number")
        work_id = item_id
        version = previous_version + int(advance)
        if advance:
            record["media_version"] = version
            changed_works = True
        finalized.append(MediaVersionFinalization(kind, item_id, work_id, previous_version, version, advance, f"works/index/{work_id}.json"))
    payloads = {}
    if changed_works:
        payloads[source_dir / SOURCE_FILES["works"]] = payload_for_map("works", records.works)
    if payloads:
        transactions.execute_source_json_write(payloads, dry_run=False, repo_root=repo_root)
    if refresh_output and finalized:
        generate_catalogue_json(repo_root, source_dir, write=True, work_ids=sorted({item.work_id for item in finalized}))
    return finalized
