"""Complete local Catalogue media and editor responses after a canonical mutation."""

from __future__ import annotations

from typing import Any, Mapping

from catalogue.catalogue_output_media import MEDIA_SOURCE_FIELDS, complete_catalogue_media
from catalogue.catalogue_revisions import record_hash
from catalogue.catalogue_service_context import CatalogueWriteContext
from catalogue.catalogue_source import CatalogueSourceRecords, work_resource_entries
from catalogue.catalogue_pending_updates import accumulate_work_changes
from catalogue.catalogue_staged_media import clear_staged_works
from catalogue.catalogue_lookup import work_medium_values


def download_filenames(record: dict[str, Any]) -> set[str]:
    return {item["filename"] for item in work_resource_entries(record, "downloads")}


def changed_work_media(
    previous: CatalogueSourceRecords, current: CatalogueSourceRecords, candidate_ids: set[str],
    attachment_names: set[str],
) -> tuple[list[str], dict[str, set[str]]]:
    """Select changed image sources, added downloads and supplied replacement bytes.

    Unchanged downloads are assumed to remain available. Removed references do
    not select remaining files for validation or media completion.
    """
    image_ids = []
    file_changes = {}
    for key in sorted(candidate_ids & current.works.keys()):
        record = current.works[key]
        old = previous.works.get(key)
        if record.get("project_filename") and (
            old is None or any(old.get(field) != record.get(field) for field in MEDIA_SOURCE_FIELDS)
        ):
            image_ids.append(key)
        names = download_filenames(record)
        changed_names = (names - download_filenames(old or {})) | (names & attachment_names)
        if changed_names:
            file_changes[key] = changed_names
    return image_ids, file_changes


def complete_saved_catalogue_edit(
    context: CatalogueWriteContext, response: dict[str, Any], previous: CatalogueSourceRecords,
    *, attachment_files: Mapping[str, bytes] | None = None, regenerate_image: bool = False,
    current_records: CatalogueSourceRecords,
    deleted_media: Mapping[str, Mapping[str, Any]] | None = None,
) -> None:
    """Preserve canonical success when local media or response completion fails.

    Mutation owners carry before/after records through completion. Media
    persistence updates the supplied current map only after its write succeeds,
    so final editor records and queues use that same completed state. Bulk Save
    supplies final records, including relinked source folders, and preserves all
    prepared media; only single/batch Work actions select media candidates and
    require editor-record completion after media.
    """
    shared = response.pop("_shared_changes", None)
    if context.dry_run or not response.get("ok"):
        return
    response["saved"] = True
    failures: list[str] = []
    current = current_records
    refresh_needed = False
    image_ids: list[str] = []
    candidate_ids: set[str] = set()
    media_work_ids: set[str] = set()
    file_changes: dict[str, set[str]] = {}
    try:
        candidate_ids = {
            key for key in (
                response.get("work_id"), *response.get("changed_work_ids", ()),
            ) if key in current.works
        }
        if candidate_ids:
            image_ids, file_changes = changed_work_media(previous, current, candidate_ids, set(attachment_files or {}))
        if regenerate_image:
            image_ids = sorted(set(image_ids) | {response["work_id"]})
        media_work_ids = set(image_ids) | set(file_changes)
        if media_work_ids:
            response["media"] = complete_catalogue_media(
                context.repo_root, context.source_dir, records=current, previous=previous,
                work_ids=sorted(media_work_ids), image_work_ids=image_ids, download_names_by_work=file_changes, write=True,
                attachment_files=attachment_files,
                force_image_ids=[response["work_id"]] if regenerate_image else [],
            )
    except (Exception, SystemExit) as error:
        failures.append(f"Local Save preparation: {error}")
    try:
        # Definition records are already final; only Work media can change a record.
        if "record" in response and response.get("work_id"):
            record = current.works.get(response["work_id"])
            if record:
                response.update(record=record, record_hash=record_hash(record))
        # Reuse supplied bulk/batch records unless media completion could change them.
        for entry in response.get("records", []):
            if entry["work_id"] not in media_work_ids:
                continue
            record = current.works.get(entry.get("work_id"))
            if record:
                entry.update(record=record, record_hash=record_hash(record))
        work_response = "work_id" in response or "records" in response or response.get("kind") == "works"
        if work_response and (
            response.get("created") or response.get("created_ids") or response.get("deleted")
            or "medium" in response.get("changed_fields", ())
        ):
            response["medium_values"] = work_medium_values(current.works)
    except Exception as error:
        failures.append(f"Editor response: {error}")
    try:
        if shared is None:
            raise ValueError("Canonical mutation did not supply its shared Catalogue effects")
        changed_ids = set()
        if response.get("changed") or response.get("created"):
            for field in ("changed_work_ids", "changed_ids", "affected_work_ids", "created_ids"):
                changed_ids.update(response.get(field, []))
            if response.get("work_id"):
                changed_ids.add(response["work_id"])
        image_changes = {wid for wid in image_ids if current.works[wid].get("project_filename")}
        targets = (changed_ids | image_changes | set(file_changes)) & current.works.keys()
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
        clear_staged_works(context.repo_root, deleted_media or {})
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
