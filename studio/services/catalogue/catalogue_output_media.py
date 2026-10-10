"""Complete exact Catalogue media locally after a canonical edit."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import tempfile
from typing import Any, Mapping, Sequence

from catalogue import catalogue_build_media as media
from catalogue.catalogue_media_version import finalize_catalogue_media_versions
from catalogue.catalogue_output_paths import catalogue_workspace_config, output_path
from catalogue.catalogue_source import CatalogueSourceRecords, slug_id, validate_source_records
from catalogue.catalogue_work_attachments import safe_download_filename
from catalogue.catalogue_staged_media import catalogue_staging_assets
from local_env import runtime_env


MEDIA_SOURCE_FIELDS = ("media_source_id", "project_folder", "project_subfolder", "project_filename")


def complete_catalogue_media(
    repo_root: Path, source_dir: Path, *, records: CatalogueSourceRecords,
    previous: CatalogueSourceRecords | None, work_ids: Sequence[str], image_work_ids: Sequence[str], write: bool,
    attachment_files: Mapping[str, bytes] | None = None, force_image_ids: Sequence[str] = (),
) -> dict[str, Any]:
    """Prepare current images/downloads and their metadata, with no network dependency.

    Pending native bytes replace exact download identities; otherwise the existing
    download stays in its flag-selected staging or Working location. Missing
    downloads fail. Removed references leave bytes for manual cleanup.
    """
    errors = validate_source_records(records)
    if errors:
        raise ValueError("Catalogue source validation failed: " + "; ".join(errors[:20]))
    work_ids = sorted({slug_id(wid) for wid in work_ids})
    image_work_ids = sorted({slug_id(wid) for wid in image_work_ids})
    if not set(image_work_ids).issubset(work_ids):
        raise ValueError("Image work IDs must be included in media work IDs")
    if not set(force_image_ids).issubset(image_work_ids):
        raise ValueError("Forced image IDs must be included in image work IDs")
    if not work_ids:
        return {"status": "completed" if write else "planned", "targets": []}
    working = catalogue_workspace_config(repo_root).assets
    staging = catalogue_staging_assets(repo_root)
    env = runtime_env(repo_root=repo_root)
    downloads = {
        safe_download_filename(item["filename"]): item for wid in work_ids
        for item in (records.works.get(wid, {}).get("downloads") or [])
    }
    download_files = {}
    if not set(attachment_files or {}).issubset(downloads):
        raise ValueError("Attachment bytes must match the selected Work downloads")
    for filename in sorted(downloads):
        destination = output_path(staging.work_files, filename)
        if filename in (attachment_files or {}):
            data = attachment_files[filename]
            if not data:
                raise ValueError(f"Catalogue download is empty: {filename}")
            download_files[destination] = data
        else:
            selected = staging if downloads[filename]["staged"] else working
            existing = output_path(selected.work_files, filename)
            if not existing.is_file() or not existing.stat().st_size:
                raise ValueError(f"Required local Catalogue download is unavailable: {filename}")

    tasks = []
    for item_id in image_work_ids:
        record = records.works.get(item_id)
        if not record or not record.get("project_filename"):
            continue
        old = previous.works.get(item_id) if previous else None
        source, reason, base, error = media.resolve_work_media_source(records, item_id, env=env)
        if error or reason or source is None or base is None or not source.is_file():
            raise ValueError(f"{item_id}: {error or reason or 'source media file is missing'}")
        force = old is None or item_id in force_image_ids or (
            old is not None and any(old.get(field) != record.get(field) for field in MEDIA_SOURCE_FIELDS)
        )
        tasks.append(media.build_local_media_task(
            repo_root=repo_root, kind="work", item_id=item_id, source_path=source,
            projects_base_dir=base, force=force,
            destination_assets=staging, comparison_assets=staging if record["image_staged"] else working,
        ))
    pending = [task["id"] for task in tasks if task["status"] == "pending"]
    if not write:
        return {"status": "planned", "pending_media": pending,
                "downloads": sorted(path.name for path in download_files), "targets": work_ids}

    changed_images = set()
    dimensions_changed = any(
        records.works[task["id"]].get("width_px") != task["source_width_px"]
        or records.works[task["id"]].get("height_px") != task["source_height_px"] for task in tasks
    )
    prepared = dict(download_files)
    with tempfile.TemporaryDirectory(prefix="catalogue-media-") as temporary:
        for task in tasks:
            files, changed = media.prepare_local_media_task(task, Path(temporary))
            prepared.update(files)
            if changed:
                changed_images.add(task["id"])
        finalized = finalize_catalogue_media_versions(
            source_dir, tasks, changed_images=changed_images, media_files=prepared,
            staged_downloads_by_work={
                wid: {item["filename"] for item in records.works[wid].get("downloads") or []} & set(attachment_files or {})
                for wid in work_ids
            },
        )
    return {"status": "completed", "targets": work_ids, "prepared_images": pending,
            "changed": bool(download_files or changed_images or dimensions_changed),
            "downloads": sorted(path.name for path in download_files),
            "media_versions": [asdict(item) for item in finalized]}
