"""Reconcile Catalogue reader output and record completed local freshness."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

from catalogue.catalogue_source import DEFAULT_SOURCE_DIR, SOURCE_FILES, records_from_json_source
from catalogue.catalogue_works_metadata import update_catalogue_works_metadata
from catalogue.catalogue_pending_updates import read_pending_updates, write_pending_updates
from catalogue.catalogue_pending_state import pending_counts
from catalogue.generate_work_pages import catalogue_payloads, same_generated_content
from catalogue.catalogue_galleries import read_galleries
from catalogue.catalogue_series_galleries import read_series_galleries
from catalogue.catalogue_output_paths import catalogue_workspace_config, output_path
from catalogue.catalogue_staged_media import catalogue_staging_assets, work_image_paths
from catalogue.catalogue_source import payload_for_map
from catalogue.catalogue_revisions import record_hash


def catalogue_refresh_status(repo_root: Path) -> dict[str, Any]:
    """Read Work/shared readiness and last successful time from the updates queue."""
    try:
        pending = read_pending_updates(repo_root)
    except (OSError, ValueError) as error:
        raise RuntimeError(f"Catalogue Refresh status is unavailable: {error}") from error
    header = pending["header"]
    needed = header["shared_refresh_pending"] or any(
        not entry["refreshed"] for family in ("current_works", "deleted_works")
        for entry in pending[family].values()
    )
    status = {"ok": True, "needed": needed}
    if header["last_refreshed_at_utc"] is not None:
        status["refreshed_at_utc"] = header["last_refreshed_at_utc"]
    return status


def refresh_catalogue(repo_root: Path) -> dict[str, Any]:
    """Handoff queued Works, preserve completed readiness and return final editor records.

    Mutation owners supply selection. Shared output retains unchanged content;
    Work metadata/media and canonical flag clears complete before readiness.
    Failure retains completed effects and shared pending state. Only full
    completion clears shared readiness and advances the last successful time.
    """
    work_id = ""
    phase = "queue"
    try:
        pending = read_pending_updates(repo_root)
        if not pending["header"]["shared_refresh_pending"]:
            pending["header"]["shared_refresh_pending"] = True
            write_pending_updates(repo_root, pending)
        source_dir = repo_root / DEFAULT_SOURCE_DIR
        records = records_from_json_source(source_dir)
        galleries = read_galleries(source_dir, records.works)
        pairs = read_series_galleries(source_dir, records.series, galleries.galleries)
        workspace = catalogue_workspace_config(repo_root)
        working, staging = workspace.assets, catalogue_staging_assets(repo_root)
        selected = {
            family: {wid: entry for wid, entry in pending[family].items() if not entry["refreshed"]}
            for family in ("current_works", "deleted_works")
        }
        phase = "shared output"
        payloads = catalogue_payloads(
            repo_root, records, galleries, pairs, timestamp=utc_timestamp(),
            work_ids=set(selected["current_works"]),
        )
        output = {"status": "completed", "written": [], "deleted": []}
        for identity, payload in payloads.items():
            if identity.startswith("works/index/"):
                continue
            path = output_path(workspace.catalogue.working, identity)
            try:
                previous = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                previous = None
            if same_generated_content(previous, payload):
                continue
            _write_payload(path, payload)
            output["written"].append(identity)
        gallery_root = output_path(workspace.catalogue.working, "galleries/index")
        for path in sorted(gallery_root.glob("*.json")):
            identity = path.relative_to(workspace.catalogue.working.path).as_posix()
            if identity not in payloads:
                output_path(workspace.catalogue.working, identity).unlink()
                output["deleted"].append(identity)
        report = update_catalogue_works_metadata(
            repo_root, records, work_ids=sorted(selected["current_works"]),
            deleted_work_ids=sorted(selected["deleted_works"]), write=True,
        )
        editor_records = []
        for family in ("current_works", "deleted_works"):
            for work_id, entry in sorted(selected[family].items()):
                phase = "media handoff"
                path = output_path(workspace.catalogue.working, f"works/index/{work_id}.json")
                if family == "deleted_works":
                    path.unlink(missing_ok=True)
                    if entry["image"]:
                        for image in work_image_paths(repo_root, work_id, working):
                            image.unlink(missing_ok=True)
                    for name in entry["file_names"]:
                        output_path(working.work_files, name).unlink(missing_ok=True)
                    output["deleted"].append(f"works/index/{work_id}.json")
                else:
                    record = records.works[work_id]
                    if entry["image"]:
                        destinations = work_image_paths(repo_root, work_id, working)
                        sources = work_image_paths(repo_root, work_id, staging if record["image_staged"] else working)
                        for source, destination in zip(sources, destinations, strict=True):
                            _handoff_file(source, destination)
                    downloads = {item["filename"]: item for item in record.get("downloads") or []}
                    for name in entry["file_names"]:
                        download = downloads[name]
                        source = output_path((staging if download["staged"] else working).work_files, name)
                        _handoff_file(source, output_path(working.work_files, name))
                    phase = "metadata handoff"
                    _write_payload(path, payloads[f"works/index/{work_id}.json"])
                    output["written"].append(f"works/index/{work_id}.json")
                    phase = "staging flags"
                    flags_changed = entry["image"] and record["image_staged"]
                    if entry["image"]:
                        record["image_staged"] = False
                    for name in entry["file_names"]:
                        flags_changed = flags_changed or downloads[name]["staged"]
                        downloads[name]["staged"] = False
                    if flags_changed:
                        _write_payload(source_dir / SOURCE_FILES["works"], payload_for_map("works", records.works))
                    editor_records.append({"work_id": work_id, "record": dict(record),
                                           "record_hash": record_hash(record), "gallery_ids": galleries.works.get(work_id, [])})
                phase = "readiness"
                entry["refreshed"] = True
                write_pending_updates(repo_root, pending)
        work_id, phase = "", "completion"
        pending["header"].update(last_refreshed_at_utc=utc_timestamp(), shared_refresh_pending=False)
        write_pending_updates(repo_root, pending)
        status = {"ok": True, "needed": False, "refreshed_at_utc": pending["header"]["last_refreshed_at_utc"]}
        return {"ok": True, "output": output, "report_metadata": report,
                "pending_updates": pending_counts(pending), "refresh_status": status, "records": editor_records}
    except Exception as error:
        raise RuntimeError(f"Refresh Catalogue incomplete ({work_id or 'shared output'}, {phase}): {error}") from error


def utc_timestamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_payload(path: Path, payload: dict[str, Any]) -> None:
    if path.is_symlink():
        raise ValueError("Catalogue handoff must not target a symlink")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _handoff_file(source: Path, destination: Path) -> None:
    if source.is_symlink() or not source.is_file() or not source.stat().st_size:
        raise FileNotFoundError(f"Prepared Catalogue media is unavailable: {source.name}")
    if source == destination:
        return
    if destination.is_symlink():
        raise ValueError("Working media must not target a symlink")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(source.read_bytes())
