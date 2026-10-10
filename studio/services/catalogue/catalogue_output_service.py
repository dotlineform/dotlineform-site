"""Complete local Catalogue media and editor responses after a canonical mutation."""

from __future__ import annotations

from typing import Any, Mapping

from catalogue.catalogue_output_media import MEDIA_SOURCE_FIELDS, complete_catalogue_media
from catalogue.catalogue_revisions import record_hash
from catalogue.catalogue_service_context import CatalogueWriteContext
from catalogue.catalogue_source import CatalogueSourceRecords, records_from_json_source
from catalogue.catalogue_pending_updates import accumulate_work_changes
from catalogue.catalogue_staged_media import clear_staged_work


def download_filenames(record: dict[str, Any]) -> set[str]:
    return {item["filename"] for item in record.get("downloads") or []}


def changed_work_media_ids(
    previous: CatalogueSourceRecords, current: CatalogueSourceRecords, candidate_ids: set[str],
) -> tuple[list[str], list[str]]:
    """Select current Works with changed image sources or download references."""
    image_ids = []
    download_ids = []
    for key in sorted(candidate_ids & current.works.keys()):
        record = current.works[key]
        old = previous.works.get(key)
        if old is None or any(old.get(field) != record.get(field) for field in MEDIA_SOURCE_FIELDS):
            image_ids.append(key)
        if old is None or download_filenames(old) != download_filenames(record):
            download_ids.append(key)
    return sorted(image_ids), sorted(download_ids)


def complete_saved_catalogue_edit(
    context: CatalogueWriteContext, response: dict[str, Any], previous: CatalogueSourceRecords,
    *, attachment_files: Mapping[str, bytes] | None = None, regenerate_image: bool = False,
    current_records: CatalogueSourceRecords | None = None,
    deleted_media: Mapping[str, Mapping[str, Any]] | None = None,
) -> None:
    """Preserve canonical success when local media or response completion fails.

    Creation and deletion owners may pass validated current records to avoid an
    initial reread. Media promotion still owns dimensions/revisions, so editor
    completion reads their final canonical state after media has been attempted.
    """
    shared = response.pop("_shared_changes", None)
    if context.dry_run or not response.get("ok"):
        return
    response["saved"] = True
    failures: list[str] = []
    current = current_records
    media_attempted = False
    refresh_needed = False
    image_ids: list[str] = []
    candidate_ids: set[str] = set()
    try:
        if current is None:
            current = records_from_json_source(context.source_dir)
        candidate_ids = {
            key for key in (
                response.get("work_id"), *response.get("selected_ids", ()), *response.get("changed_work_ids", ()),
            ) if key in current.works
        }
        image_ids, download_ids = changed_work_media_ids(previous, current, candidate_ids)
        if regenerate_image:
            image_ids = sorted(set(image_ids) | {response["work_id"]})
        # Retain validation of ready downloads; pending native bytes replace exact identities.
        download_ids = sorted(set(download_ids) | {
            key for key in candidate_ids if download_filenames(current.works[key])
        })
        work_ids = sorted(set(image_ids) | set(download_ids))
        if work_ids:
            media_attempted = True
            response["media"] = complete_catalogue_media(
                context.repo_root, context.source_dir, records=current, previous=previous,
                work_ids=work_ids, image_work_ids=image_ids, write=True,
                attachment_files=attachment_files,
                force_image_ids=[response["work_id"]] if regenerate_image else [],
            )
    except (Exception, SystemExit) as error:
        failures.append(f"Local Save preparation: {error}")
    try:
        # Reuse the loaded source unless media promotion may have changed revisions.
        if current is None or media_attempted:
            current = records_from_json_source(context.source_dir)
        if "record" in response and "gallery_id" not in response:
            record = current.series.get(response.get("series_id")) if response.get("series_id") else current.works.get(response.get("work_id"))
            if record:
                response.update(record=record, record_hash=record_hash(record))
        # Bulk mutation responses already include every selected Work and its saved memberships.
        for key in ("records", "work_records"):
            for entry in response.get(key, []):
                record = current.works.get(entry.get("work_id"))
                if record:
                    entry.update(record=record, record_hash=record_hash(record))
    except Exception as error:
        failures.append(f"Editor response: {error}")
    try:
        if current is None:
            raise ValueError("Saved canonical records are unavailable for queue completion")
        if shared is None:
            raise ValueError("Canonical mutation did not supply its shared Catalogue effects")
        changed_ids = set()
        if response.get("changed") or response.get("created"):
            for field in ("changed_work_ids", "changed_ids", "affected_work_ids", "created_ids"):
                changed_ids.update(response.get(field, []))
            if response.get("work_id"):
                changed_ids.add(response["work_id"])
        image_changes = {wid for wid in image_ids if current.works[wid].get("project_filename")}
        file_changes = {
            wid: (download_filenames(current.works[wid]) - download_filenames(previous.works.get(wid, {})))
                 | (download_filenames(current.works[wid]) & set(attachment_files or {}))
            for wid in candidate_ids
        }
        targets = (changed_ids | image_changes | {wid for wid, names in file_changes.items() if names}) & current.works.keys()
        selections = {
            wid: {"metadata": wid in changed_ids or wid in image_changes,
                  "image": wid in image_changes, "file_names": sorted(file_changes.get(wid, set()))}
            for wid in targets
        }
        refresh_needed = bool(selections or deleted_media or any(shared.values()) or failures)
        accumulate_work_changes(
            context.repo_root, selections, deleted_media or {},
            downloads_by_work={wid: download_filenames(current.works[wid]) for wid in targets},
            shared=shared,
        )
        for wid, selection in (deleted_media or {}).items():
            clear_staged_work(context.repo_root, wid, dict(selection))
    except Exception as error:
        identities = sorted(set(deleted_media or {}) | set(response.get("affected_work_ids", [])))
        failures.append(f"Catalogue queue/staging completion ({', '.join(identities)}): {error}")
    if refresh_needed or failures:
        response["refresh_needed"] = True
    if failures:
        response["save_completion"] = {
            "status": "failed", "error": "; ".join(failures),
            "message": "Data saved, but local Save completion did not finish.",
        }
        if response.get("created_ids"):
            response["save_completion"]["message"] = (
                "Works created (" + ", ".join(response["created_ids"]) + "), but local Save completion did not finish."
            )
