"""Complete exact Catalogue media locally before generating Working reader JSON."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import tempfile
from typing import Any, Sequence

from catalogue import catalogue_build_media as media
from catalogue.catalogue_media_version import finalize_catalogue_media_versions
from catalogue.catalogue_output_paths import catalogue_workspace_config, output_path
from catalogue.catalogue_source import CatalogueSourceRecords, slug_id, validate_source_records
from catalogue_media_paths import configured_catalogue_media_workspace
from external_workspace_paths import resolve_workspace_path
from local_env import runtime_env


def _download_filename(value: str) -> str:
    if not value or value in {".", ".."} or "/" in value or "\\" in value:
        raise ValueError(f"Catalogue download must name one file: {value!r}")
    return value


def complete_catalogue_media(
    repo_root: Path, source_dir: Path, *, records: CatalogueSourceRecords,
    previous: CatalogueSourceRecords | None, work_ids: Sequence[str], write: bool,
) -> dict[str, Any]:
    """Prepare current images/downloads and their metadata, with no network dependency.

    A staged download is an explicit local input; an existing shared download is
    retained when no replacement is staged. Missing local downloads fail. Removed
    references leave bytes for manual cleanup. Dry runs inspect and plan only.
    """
    errors = validate_source_records(records)
    if errors:
        raise ValueError("Catalogue source validation failed: " + "; ".join(errors[:20]))
    work_ids = sorted({slug_id(wid) for wid in work_ids})
    if not work_ids:
        return {"status": "completed" if write else "planned", "targets": []}
    assets = catalogue_workspace_config(repo_root).assets
    env = runtime_env(repo_root=repo_root)
    downloads = {
        _download_filename(item["filename"]) for wid in work_ids
        for item in (records.works.get(wid, {}).get("downloads") or [])
    }
    download_files = {}
    staging = configured_catalogue_media_workspace(repo_root) if downloads else None
    for filename in sorted(downloads):
        destination = output_path(assets.work_files, filename)
        staged = resolve_workspace_path(staging, f"works/files/{filename}")
        if staged.is_file():
            data = staged.read_bytes()
            if not data:
                raise ValueError(f"Catalogue download is empty: {filename}")
            if not destination.is_file() or destination.read_bytes() != data:
                download_files[destination] = data
        elif not destination.is_file() or not destination.stat().st_size:
            raise ValueError(f"Required local Catalogue download is unavailable: {filename}")

    tasks = []
    source_fields = ("media_source_id", "project_folder", "project_subfolder", "project_filename")
    for item_id in work_ids:
        record = records.works.get(item_id)
        if not record or not record.get("project_filename"):
            continue
        old = previous.works.get(item_id) if previous else None
        source, reason, base, error = media.resolve_work_media_source(records, item_id, env=env)
        if error or reason or source is None or base is None or not source.is_file():
            raise ValueError(f"{item_id}: {error or reason or 'source media file is missing'}")
        force = old is not None and any(old.get(field) != record.get(field) for field in source_fields)
        tasks.append(media.build_local_media_task(
            repo_root=repo_root, kind="work", item_id=item_id, source_path=source,
            projects_base_dir=base, force=force,
        ))
    pending = [task["id"] for task in tasks if task["status"] == "pending"]
    if not write:
        return {"status": "planned", "pending_media": pending,
                "downloads": sorted(path.name for path in download_files), "targets": work_ids}

    changed_images = set()
    prepared = dict(download_files)
    with tempfile.TemporaryDirectory(prefix="catalogue-media-") as temporary:
        for task in tasks:
            files, changed = media.prepare_local_media_task(task, Path(temporary))
            prepared.update(files)
            if changed:
                changed_images.add(task["id"])
        finalized = finalize_catalogue_media_versions(
            source_dir, tasks, changed_images=changed_images, media_files=prepared,
        )
    return {"status": "completed", "targets": work_ids, "prepared_images": pending,
            "downloads": sorted(path.name for path in download_files),
            "media_versions": [asdict(item) for item in finalized]}
