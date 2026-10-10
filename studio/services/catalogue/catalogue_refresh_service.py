"""Reconcile Catalogue reader output and record completed local freshness."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

from catalogue.catalogue_source import DEFAULT_SOURCE_DIR, SOURCE_FILES, records_from_json_source, validate_source_records
from catalogue.catalogue_compact_indexes import build_compact_index, merge_compact_index
from catalogue.catalogue_works_metadata import update_catalogue_works_metadata
from catalogue.catalogue_pending_updates import read_pending_updates, write_pending_updates
from catalogue.catalogue_pending_state import pending_counts
from catalogue.generate_work_pages import catalogue_payloads, same_generated_content
from catalogue.catalogue_galleries import read_galleries, validate_galleries
from catalogue.catalogue_refresh_inputs import read_refresh_inputs
from catalogue.catalogue_gallery_records import merge_gallery_record
from catalogue.catalogue_series_galleries import read_series_galleries, validate_series_galleries
from catalogue.catalogue_series_galleries_index import merge_series_galleries_index, series_gallery_links, series_galleries_index_payload
from catalogue.catalogue_series_galleries_report import merge_series_galleries_report, series_galleries_report_payload
from catalogue.catalogue_output_paths import catalogue_workspace_config, output_path
from catalogue.catalogue_staged_media import catalogue_staging_assets, work_image_paths
from catalogue.catalogue_source import payload_for_map
from catalogue.catalogue_revisions import record_hash
from catalogue.catalogue_shared_changes import REFRESH_FIELDS, WORK_INDEX, GALLERY_INDEX, RELATIONSHIP_INDEX, RELATIONSHIP_REPORT, empty_shared_changes, shared_changes
from catalogue.catalogue_pending_publication import merge_completed_shared
from catalogue.catalogue_report_inputs import INPUT_SCHEMAS, SERIES_PATH, catalogue_report_input_payloads, merge_catalogue_report_input
from catalogue.catalogue_work_document_coverage import MANIFEST_PATH as COVERAGE_MANIFEST, merge_work_document_coverage_manifest, work_document_coverage_manifest
from docs_artifact_locations import ArtifactLocation


def catalogue_refresh_status(repo_root: Path) -> dict[str, Any]:
    """Read Work/shared readiness and last successful time from the updates queue."""
    try:
        pending = read_pending_updates(repo_root)
    except (OSError, ValueError) as error:
        raise RuntimeError(f"Catalogue Refresh status is unavailable: {error}") from error
    header = pending["header"]
    needed = any(pending[field] for field in REFRESH_FIELDS) or any(
        not entry["refreshed"] for family in ("current_works", "deleted_works")
        for entry in pending[family].values()
    )
    status = {"ok": True, "needed": needed}
    if header["last_refreshed_at_utc"] is not None:
        status["refreshed_at_utc"] = header["last_refreshed_at_utc"]
    return status


def refresh_private_report_inputs(repo_root: Path) -> dict[str, Any]:
    """Explicit maintenance of the three private inputs, preserving unrelated work.

    Validate the updates queue and canonical inputs before projection. Complete
    only these private output selections; retain Work readiness, other selections
    and the last full Refresh timestamp. No media, documents or Publish handoff.
    Unrefreshed Works must complete normal Refresh first so staged references
    cannot precede their required metadata/media handoff.
    """
    pending = read_pending_updates(repo_root)
    if any(not entry["refreshed"] for family in ("current_works", "deleted_works") for entry in pending[family].values()):
        raise ValueError("Complete queued Work Refresh before private report-input maintenance.")
    records = records_from_json_source(repo_root / DEFAULT_SOURCE_DIR)
    errors = validate_source_records(records)
    if errors:
        raise ValueError("Catalogue source validation failed: " + "; ".join(errors[:20]))
    payloads = catalogue_report_input_payloads(
        records.works, records.series, timestamp=utc_timestamp(), selected=set(INPUT_SCHEMAS),
    )
    written = _write_shared_payloads(catalogue_workspace_config(repo_root).catalogue.working, payloads)
    if set(pending["shared_outputs"]) & INPUT_SCHEMAS.keys():
        pending["shared_outputs"] = [name for name in pending["shared_outputs"] if name not in INPUT_SCHEMAS]
        write_pending_updates(repo_root, pending)
    return {"ok": True, "output": {"status": "completed", "written": written, "deleted": []}}


def refresh_compact_indexes(repo_root: Path) -> dict[str, Any]:
    """Explicit whole-index baseline/repair; preserve unrelated lifecycle work.

    This maintenance authority is never invoked by normal Refresh or a reader.
    Forward the two completed public indexes before clearing their selections.
    Work readiness and both lifecycle timestamps retain their existing owners.
    """
    pending = read_pending_updates(repo_root)
    records = records_from_json_source(repo_root / DEFAULT_SOURCE_DIR)
    errors = validate_source_records(records)
    if errors:
        raise ValueError("Catalogue source validation failed: " + "; ".join(errors[:20]))
    galleries = read_galleries(repo_root / DEFAULT_SOURCE_DIR)
    validate_galleries(galleries, records.works)
    timestamp = utc_timestamp()
    payloads = {
        WORK_INDEX: build_compact_index("works", records.works, timestamp=timestamp),
        GALLERY_INDEX: build_compact_index("galleries", galleries.galleries, timestamp=timestamp),
    }
    written = _write_shared_payloads(catalogue_workspace_config(repo_root).catalogue.working, payloads)
    merge_completed_shared(repo_root, {**empty_shared_changes(), "shared_outputs": sorted(payloads)})
    if set(pending["shared_outputs"]) & payloads.keys():
        pending["shared_outputs"] = [name for name in pending["shared_outputs"] if name not in payloads]
        write_pending_updates(repo_root, pending)
    return {"ok": True, "output": {"status": "completed", "written": written, "deleted": []}}


def refresh_work_document_coverage(repo_root: Path) -> dict[str, Any]:
    """Explicit complete private coverage baseline/repair, preserving other work.

    Complete normal Work handoffs first. Clear only this output selection after
    success; retain candidates, shared endpoints, lifecycle times and Publish.
    Normal Refresh and saved readers never invoke this maintenance authority.
    """
    pending = read_pending_updates(repo_root)
    if any(not entry["refreshed"] for family in ("current_works", "deleted_works") for entry in pending[family].values()):
        raise ValueError("Complete queued Work Refresh before Work Document Coverage maintenance.")
    records = records_from_json_source(repo_root / DEFAULT_SOURCE_DIR)
    errors = validate_source_records(records)
    if errors:
        raise ValueError("Catalogue source validation failed: " + "; ".join(errors[:20]))
    payload = work_document_coverage_manifest(records.series, records.works, timestamp=utc_timestamp())
    written = _write_shared_payloads(catalogue_workspace_config(repo_root).catalogue.working, {COVERAGE_MANIFEST: payload})
    if COVERAGE_MANIFEST in pending["shared_outputs"]:
        pending["shared_outputs"].remove(COVERAGE_MANIFEST)
        write_pending_updates(repo_root, pending)
    return {"ok": True, "output": {"status": "completed", "written": written, "deleted": []}}


def refresh_series_galleries(repo_root: Path) -> dict[str, Any]:
    """Explicit relationship index/report baseline or repair, without other generation."""
    pending = read_pending_updates(repo_root)
    source_dir = repo_root / DEFAULT_SOURCE_DIR
    records = records_from_json_source(source_dir)
    errors = validate_source_records(records)
    if errors:
        raise ValueError("Catalogue source validation failed: " + "; ".join(errors[:20]))
    galleries = read_galleries(source_dir)
    pairs = read_series_galleries(source_dir)
    validate_galleries(galleries, records.works)
    validate_series_galleries(pairs, records.series, galleries.galleries)
    timestamp = utc_timestamp()
    mapping = {sid: series_gallery_links(sid, records.series, galleries.galleries, pairs)
               for sid in sorted(records.series)}
    payloads = {
        RELATIONSHIP_INDEX: series_galleries_index_payload(mapping, timestamp=timestamp),
        RELATIONSHIP_REPORT: series_galleries_report_payload(records.series, galleries.galleries, mapping, timestamp=timestamp),
    }
    written = _write_shared_payloads(catalogue_workspace_config(repo_root).catalogue.working, payloads)
    merge_completed_shared(repo_root, {**empty_shared_changes(), "shared_outputs": sorted(payloads)})
    if set(pending["shared_outputs"]) & payloads.keys():
        pending["shared_outputs"] = [name for name in pending["shared_outputs"] if name not in payloads]
        write_pending_updates(repo_root, pending)
    return {"ok": True, "output": {"status": "completed", "written": written, "deleted": []}}


def refresh_gallery_records(repo_root: Path) -> dict[str, Any]:
    """Explicit complete Gallery-record baseline/repair; preserve other output work.

    Complete queued Gallery deletions too, forward this family's public selection
    before clearing its creation/member candidates. Retain common Gallery IDs
    for other selected aggregates, Work readiness and both lifecycle times.
    Normal Refresh and readers never call this maintenance authority.
    """
    pending = read_pending_updates(repo_root)
    source_dir = repo_root / DEFAULT_SOURCE_DIR
    records = records_from_json_source(source_dir)
    galleries = read_galleries(source_dir)
    pairs = read_series_galleries(source_dir)
    errors = validate_source_records(records)
    if errors:
        raise ValueError("Catalogue source validation failed: " + "; ".join(errors[:20]))
    validate_galleries(galleries, records.works)
    validate_series_galleries(pairs, records.series, galleries.galleries)
    if set(pending["deleted_galleries"]) & galleries.galleries.keys():
        raise ValueError("Queued Gallery deletion still has a canonical definition")
    payloads = catalogue_payloads(
        repo_root, records, galleries, pairs, timestamp=utc_timestamp(), work_ids=set(), shared_outputs=set(),
    )
    working = catalogue_workspace_config(repo_root).catalogue.working
    written = _write_shared_payloads(working, payloads)
    deleted = []
    for gid in pending["deleted_galleries"]:
        identity = f"galleries/index/{gid}.json"
        path = output_path(working, identity)
        if path.exists():
            path.unlink()
            deleted.append(identity)
    merge_completed_shared(repo_root, {
        **empty_shared_changes(), "current_galleries": sorted(galleries.galleries),
        "deleted_galleries": pending["deleted_galleries"],
    })
    fields = ("created_galleries", "gallery_member_works")
    if any(pending[field] for field in fields):
        for field in fields:
            pending[field] = []
        write_pending_updates(repo_root, pending)
    return {"ok": True, "output": {"status": "completed", "written": written, "deleted": deleted}}


def refresh_catalogue(repo_root: Path) -> dict[str, Any]:
    """Handoff queued Works, preserve completed readiness and return final editor records.

    Mutation owners supply selection. Shared output retains unchanged content;
    Work metadata/media and canonical flag clears complete before readiness.
    Failure retains completed effects and exact shared selections. Only full
    completion advances the last successful time.
    """
    work_id = ""
    phase = "queue"
    try:
        pending = read_pending_updates(repo_root)
        shared = shared_changes(pending)
        source_dir = repo_root / DEFAULT_SOURCE_DIR
        records, galleries, pairs = read_refresh_inputs(source_dir, pending)
        workspace = catalogue_workspace_config(repo_root)
        working, staging = workspace.assets, catalogue_staging_assets(repo_root)
        selected = {
            family: {wid: entry for wid, entry in pending[family].items() if not entry["refreshed"]}
            for family in ("current_works", "deleted_works")
        }
        phase = "shared output"
        timestamp = utc_timestamp()
        row_payloads = {}
        metadata_work_ids = [wid for wid, entry in pending["current_works"].items() if entry["metadata"]]
        for identity, family, sources, current_ids, deleted_ids in (
            (WORK_INDEX, "works", records.works, metadata_work_ids, pending["deleted_works"]),
            (GALLERY_INDEX, "galleries", galleries.galleries, shared["current_galleries"], shared["deleted_galleries"]),
        ):
            if identity in shared["shared_outputs"]:
                payload = merge_compact_index(
                    output_path(workspace.catalogue.working, identity), family=family, sources=sources,
                    current_ids=current_ids, deleted_ids=deleted_ids, timestamp=timestamp,
                )
                if payload is not None:
                    row_payloads[identity] = payload
        if RELATIONSHIP_INDEX in shared["shared_outputs"]:
            payload = merge_series_galleries_index(
                output_path(workspace.catalogue.working, RELATIONSHIP_INDEX), records.series, galleries.galleries, pairs,
                current_ids=shared["current_series"], deleted_ids=shared["deleted_series"], timestamp=timestamp,
            )
            if payload is not None:
                row_payloads[RELATIONSHIP_INDEX] = payload
        if RELATIONSHIP_REPORT in shared["shared_outputs"]:
            payload = merge_series_galleries_report(
                output_path(workspace.catalogue.working, RELATIONSHIP_REPORT), records.series, galleries.galleries, pairs,
                current_series=shared["current_series"], deleted_series=shared["deleted_series"],
                current_galleries=shared["current_galleries"], deleted_galleries=shared["deleted_galleries"], timestamp=timestamp,
            )
            if payload is not None:
                row_payloads[RELATIONSHIP_REPORT] = payload
        if set(shared["current_galleries"]) - galleries.galleries.keys():
            raise ValueError("Queued current Gallery is unavailable")
        initial_members = {gid: [] for gid in shared["created_galleries"]}
        if initial_members:
            for wid, ids in galleries.works.items():
                for gid in ids:
                    if gid in initial_members:
                        initial_members[gid].append(wid)
        member_candidates = set(shared["gallery_member_works"])
        current_members = member_candidates & pending["current_works"].keys()
        deleted_members = member_candidates & pending["deleted_works"].keys()
        for gid in shared["current_galleries"]:
            identity = f"galleries/index/{gid}.json"
            payload = merge_gallery_record(
                output_path(workspace.catalogue.working, identity), gallery_id=gid, gallery_record=galleries.galleries[gid],
                work_records=records.works, memberships=galleries.works,
                current_work_ids=current_members, deleted_work_ids=deleted_members, timestamp=timestamp,
                initial_member_ids=initial_members.get(gid),
            )
            if payload is not None:
                row_payloads[identity] = payload
        payloads = catalogue_payloads(
            repo_root, records, galleries, pairs, timestamp=timestamp,
            work_ids=set(selected["current_works"]),
            gallery_ids=set(),
            shared_outputs=set(shared["shared_outputs"]) - {WORK_INDEX, GALLERY_INDEX, RELATIONSHIP_INDEX, RELATIONSHIP_REPORT, COVERAGE_MANIFEST, *INPUT_SCHEMAS},
        )
        if set(shared["deleted_galleries"]) & galleries.galleries.keys() or set(shared["deleted_series"]) & records.series.keys():
            raise ValueError("Queued shared deletion still has a canonical definition")
        if set(shared["current_series"]) - records.series.keys():
            raise ValueError("Queued current Series is unavailable")
        output = {"status": "completed", "written": [], "deleted": []}
        phase = "Work report handoff"
        report = update_catalogue_works_metadata(
            repo_root, records, work_ids=sorted(selected["current_works"]),
            deleted_work_ids=sorted(selected["deleted_works"]), write=True,
        ) if any(selected.values()) else None
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
        work_id, phase = "", "private report input handoff"
        for identity in sorted(set(shared["shared_outputs"]) & INPUT_SCHEMAS.keys()):
            is_series = identity == SERIES_PATH
            payload = merge_catalogue_report_input(
                output_path(workspace.catalogue.working, identity), relative=identity,
                sources=records.series if is_series else records.works,
                current_ids=shared["current_series"] if is_series else metadata_work_ids,
                deleted_ids=shared["deleted_series"] if is_series else pending["deleted_works"],
                timestamp=timestamp,
            )
            if payload is not None:
                row_payloads[identity] = payload
        if COVERAGE_MANIFEST in shared["shared_outputs"]:
            phase = "Work Document Coverage handoff"
            payload = merge_work_document_coverage_manifest(
                output_path(workspace.catalogue.working, COVERAGE_MANIFEST), records.series, records.works,
                current_series=shared["current_series"], deleted_series=shared["deleted_series"],
                current_work_ids=metadata_work_ids, deleted_work_ids=pending["deleted_works"], timestamp=timestamp,
            )
            if payload is not None:
                row_payloads[COVERAGE_MANIFEST] = payload
        phase = "shared output"
        output["written"].extend(_write_shared_payloads(workspace.catalogue.working, {
            identity: payload for identity, payload in payloads.items() if not identity.startswith("works/index/")
        }))
        for identity, payload in row_payloads.items():
            _write_payload(output_path(workspace.catalogue.working, identity), payload)
            output["written"].append(identity)
        for gallery_id in shared["deleted_galleries"]:
            identity = f"galleries/index/{gallery_id}.json"
            path = output_path(workspace.catalogue.working, identity)
            if path.exists():
                path.unlink()
                output["deleted"].append(identity)
        if any(shared.values()):
            phase = "shared publication queue"
            merge_completed_shared(repo_root, shared)
            phase = "shared updates queue"
            for field in REFRESH_FIELDS:
                pending[field] = []
            write_pending_updates(repo_root, pending)
        work_id, phase = "", "completion"
        pending["header"]["last_refreshed_at_utc"] = utc_timestamp()
        write_pending_updates(repo_root, pending)
        status = {"ok": True, "needed": False, "refreshed_at_utc": pending["header"]["last_refreshed_at_utc"]}
        return {"ok": True, "output": output, "report_metadata": report,
                "pending_updates": pending_counts(pending), "refresh_status": status, "records": editor_records}
    except Exception as error:
        raise RuntimeError(f"Refresh Catalogue incomplete ({work_id or 'shared output'}, {phase}): {error}") from error


def utc_timestamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_shared_payloads(workspace: ArtifactLocation, payloads: dict[str, dict[str, Any]]) -> list[str]:
    written = []
    for identity, payload in payloads.items():
        path = output_path(workspace, identity)
        try:
            previous = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            previous = None
        if same_generated_content(previous, payload):
            continue
        _write_payload(path, payload)
        written.append(identity)
    return written


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
