"""Complete exact Catalogue media targets using the retained converters and R2 transport."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Sequence

from catalogue import catalogue_build_media as media
from catalogue.catalogue_output_paths import catalogue_output_workspace, output_path
from catalogue.catalogue_source import CatalogueSourceRecords, records_from_json_source, payload_for_map, slug_id, validate_source_records
from catalogue.catalogue_transactions import execute_source_json_write
from catalogue_media_paths import configured_catalogue_media_workspace
from external_workspace_paths import resolve_workspace_path
from local_env import runtime_env
from studio.services.media import publish_media_to_r2 as transport


def _require_complete(report: dict[str, Any]) -> None:
    errors = [item for item in report.get("objects", []) if item.get("status") in {"failed", "not_attempted"} or str(item.get("status", "")).startswith("blocked")]
    errors.extend(item for item in report.get("media_versions", []) if item.get("status") in {"failed", "not_promoted"})
    if errors:
        first = errors[0]
        raise RuntimeError(f"{first.get('local_path') or first.get('item_id') or first.get('kind')}: {first.get('reason') or first['status']}")


def _download_filename(value: str) -> str:
    if not value or value in {".", ".."} or "/" in value or "\\" in value:
        raise ValueError(f"Catalogue download must name one file: {value!r}")
    return value


def _downloads(records: CatalogueSourceRecords, work_ids: Sequence[str]) -> set[str]:
    return {_download_filename(item["filename"]) for wid in work_ids for item in (records.works.get(wid, {}).get("downloads") or [])}


def _save_dimensions(repo_root: Path, source_dir: Path, tasks: list[dict[str, Any]]) -> None:
    current = records_from_json_source(source_dir)
    changed_works = False
    for task in tasks:
        dimensions = {key: task.get(key) for key in ("source_width_px", "source_height_px")}
        if not all(isinstance(value, int) and value > 0 for value in dimensions.values()):
            continue
        record = current.works[task["id"]]
        updated = {"width_px": dimensions["source_width_px"], "height_px": dimensions["source_height_px"]}
        if all(record.get(key) == value for key, value in updated.items()):
            continue
        record.update(updated)
        changed_works = True
    payloads = {}
    if changed_works:
        payloads[source_dir / "works.json"] = payload_for_map("works", current.works)
    if payloads:
        execute_source_json_write(payloads, dry_run=False, repo_root=repo_root)


def complete_catalogue_media(
    repo_root: Path, source_dir: Path, *, records: CatalogueSourceRecords,
    previous: CatalogueSourceRecords | None, work_ids: Sequence[str], write: bool,
    client: transport.RemoteClient | None = None,
) -> dict[str, Any]:
    """Prepare selected media, then upload complete sets and remove exact obsolete outputs.

    Dry runs compare remote objects without writes. Original project media and
    the frozen archive are never cleanup targets. A supplied client supports
    isolated service verification without remote writes. An unchanged download
    recorded in the Work's previous source and generated output may use its
    verified remote object when no local replacement is staged.
    """
    errors = validate_source_records(records)
    if errors:
        raise ValueError("Catalogue source validation failed: " + "; ".join(errors[:20]))
    work_ids = sorted({slug_id(wid) for wid in work_ids})
    workspace = catalogue_output_workspace(repo_root)
    staging = configured_catalogue_media_workspace(repo_root)
    env = runtime_env(repo_root=repo_root)
    targets: list[tuple[str, str]] = []
    removed: list[tuple[str, str]] = []
    generated_downloads: set[str] = set()
    downloads_requiring_local: set[str] = set()
    for wid in work_ids:
        path = output_path(workspace, f"works/index/{wid}.json")
        if not path.exists():
            downloads_requiring_local.update(_downloads(records, [wid]))
            continue
        payload = json.loads(path.read_text())
        if payload.get("work", {}).get("work_id") != wid:
            raise ValueError(f"Generated Work identity does not match {path}")
        if not records.works.get(wid, {}).get("project_filename"):
            removed.append(("works", wid))
        output_downloads = {_download_filename(item["filename"]) for item in payload["work"].get("downloads", [])}
        generated_downloads.update(output_downloads)
        previous_downloads = _downloads(previous, [wid]) if previous else set()
        downloads_requiring_local.update(_downloads(records, [wid]) - (output_downloads & previous_downloads))
    downloads = _downloads(records, work_ids)
    old_downloads = generated_downloads | (_downloads(previous, work_ids) if previous else set())
    removed_downloads = old_downloads - _downloads(records, list(records.works))
    tasks: list[dict[str, Any]] = []
    source_fields = ("media_source_id", "project_folder", "project_subfolder", "project_filename")
    for item_id in work_ids:
        record = records.works.get(item_id)
        old = previous.works.get(item_id) if previous else None
        if not record or not record.get("project_filename"):
            if old and old.get("project_filename"):
                removed.append(("works", item_id))
            continue
        if not staging.root.is_dir():
            raise ValueError(f"Catalogue staging is unavailable: {staging.marker}")
        source, reason, base, error = media.resolve_work_media_source(records, item_id, env=env)
        if error or reason or source is None or not source.is_file():
            raise ValueError(f"{source or item_id}: {error or reason or 'source media file is missing'}")
        force = old is not None and any(old.get(field) != record.get(field) for field in source_fields)
        staged_paths = [media.media_staging_input_path(staging.projects_base, "work", item_id, source),
                        *media.staged_primary_output_paths(staging.projects_base, "work", item_id),
                        *media.staged_thumb_output_paths(staging.projects_base, "work", item_id)]
        for staged_path in staged_paths:
            resolve_workspace_path(staging, staged_path.relative_to(staging.root))
        tasks.append(media.build_local_media_task(
            repo_root=repo_root, kind="work", item_id=item_id, source_path=source,
            projects_base_dir=base, force=force,
        ))
        targets.append(("works", item_id))
    result = media.execute_local_media_plan(
        repo_root, scope={"source_dir": str(source_dir)}, write=write, env=env,
        plan_builder=lambda *args, **kwargs: {"tasks": tasks},
    )
    if result["status"] == "failed" or any(result.get("blocked", {}).values()):
        raise RuntimeError(str(result.get("stderr_tail") or result.get("summary")))
    if write and tasks:
        _save_dimensions(repo_root, source_dir, tasks)
    # A dry run with pending derivatives cannot compare bytes which do not exist yet.
    pending = sum(task["status"] == "pending" for task in tasks)
    if not write and pending:
        return {"status": "planned", "pending_media": pending, "targets": targets, "removed": removed}
    if not targets and not removed and not downloads and not removed_downloads:
        return {"status": "completed", "targets": []}
    remote = client or transport.R2Client(transport.load_r2_credentials(env_files=[repo_root / ".env.local"], environ=env))
    report: dict[str, Any] = {"status": "completed", "targets": targets}
    if targets:
        report["primary"] = transport.run_catalogue_upload_targets(
            repo_root=repo_root, targets=targets, write=write, force=True,
            client=remote, environ=env, refresh_output=False,
        )
        _require_complete(report["primary"])
    config = json.loads((repo_root / "site-tools/config/site-tools.json").read_text())["media"]
    prefix = transport.normalize_remote_prefix(config["files_works"])
    if prefix.startswith("archive/"):
        raise ValueError("Catalogue downloads cannot target the archive")
    download_root = resolve_workspace_path(staging, "works/files")
    objects = []
    for filename in sorted(downloads):
        path = resolve_workspace_path(staging, f"works/files/{filename}")
        object_key = f"{prefix}/{filename}"
        if not path.exists() and filename not in downloads_requiring_local:
            if remote.head_object(object_key) is None:
                raise ValueError(f"download file is missing locally and in R2: {path} ({object_key})")
            continue
        if not path.is_file():
            raise ValueError(f"download file is missing: {path}")
        objects.append(transport.LocalMediaObject(
            scope="catalogue", kind="files", item_id=filename, width=0, local_path=path,
            source_root=download_root, object_key=object_key, size=path.stat().st_size, md5=transport.file_md5(path),
        ))
    if objects:
        uploaded = transport.plan_and_publish(objects=objects, client=remote, write=write, force=True)
        report["downloads"] = [asdict(item) for item in uploaded]
        failed = [item for item in uploaded if item.status == "failed"]
        if failed:
            raise RuntimeError(f"{failed[0].local_path}: {failed[0].reason}")
    if removed:
        removed = sorted(set(removed))
        deleted = transport.run_catalogue_remote_delete(repo_root=repo_root, targets=removed, write=write, client=remote)
        report["deleted_media"] = deleted
        _require_complete(deleted)
        for family, item_id in removed:
            paths = [*media.thumb_output_paths(repo_root, "work", item_id), *media.staged_primary_output_paths(staging.projects_base, "work", item_id)]
            paths.extend(resolve_workspace_path(staging, f"{family}/make_srcset_images").glob(f"{item_id}.*"))
            for path in paths:
                checked = output_path(workspace, path.relative_to(workspace.root)) if path.is_relative_to(workspace.root) else resolve_workspace_path(staging, path.relative_to(staging.root))
                if write and checked.is_file():
                    checked.unlink()
    if removed_downloads:
        deleted_files = transport.plan_and_delete(
            objects=[transport.RemoteMediaObject("catalogue", "files", filename, 0, f"{prefix}/{filename}") for filename in sorted(removed_downloads)],
            client=remote, write=write,
        )
        report["deleted_downloads"] = [asdict(item) for item in deleted_files]
        failed_files = [item for item in deleted_files if item.status == "failed"]
        if failed_files:
            raise RuntimeError(f"{failed_files[0].item_id}: {failed_files[0].reason}")
    return report
