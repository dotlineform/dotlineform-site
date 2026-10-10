"""Gallery definition mutations, independent of the selected Work draft."""

from __future__ import annotations

from typing import Any, Mapping

from catalogue.catalogue_galleries import (
    GALLERIES_FILE, MEMBERSHIPS_FILE, CatalogueGalleries, read_galleries,
    validate_galleries, validate_gallery_id,
)
from catalogue.catalogue_revisions import CatalogueRevisionConflict, record_hash, require_record_revision
from catalogue.catalogue_series_galleries import (
    SERIES_GALLERIES_FILE, CatalogueSeriesGalleries, read_series_galleries,
    related_series_ids, validate_series_galleries, with_gallery_relation, without_gallery,
)
from catalogue.catalogue_service_context import CatalogueWriteContext, load_series_payload, load_works_payload, log_event, utc_now
from catalogue.catalogue_transactions import execute_source_json_write
from catalogue.catalogue_shared_changes import empty_shared_changes, GALLERY_INDEX, RELATIONSHIP_INDEX, RELATIONSHIP_REPORT


def gallery_record_payload(
    data: CatalogueGalleries, pairs: CatalogueSeriesGalleries, gallery_id: str,
) -> dict[str, Any]:
    """Return the exact definition, members and saved Series associations."""
    validate_gallery_id(gallery_id)
    if gallery_id not in data.galleries:
        raise ValueError(f"gallery_id not found: {gallery_id}")
    record = data.galleries[gallery_id]
    return {
        "gallery_id": gallery_id, "record": record, "record_hash": record_hash(record),
        "member_work_ids": sorted(wid for wid, ids in data.works.items() if gallery_id in ids),
        "related_series_ids": related_series_ids(pairs, gallery_id),
    }


def mutate_gallery_payload(
    context: CatalogueWriteContext, operation: str, body: Mapping[str, Any],
) -> dict[str, Any]:
    """Persist a definition and its exact Series relevance in one source transaction.

    Delete retains the existing definition and complete-member confirmation checks.
    Work metadata is untouched; completion receives all former member identities.
    """
    if operation not in {"create", "save", "delete"}:
        raise ValueError("Unsupported Gallery operation")
    works = load_works_payload(context.works_path)["works"]
    series = load_series_payload(context.series_path)["series"]
    data = read_galleries(context.source_dir, works)
    pairs = read_series_galleries(context.source_dir, series, data.galleries)
    if operation == "create":
        gallery_id = f"{max((int(gid) for gid in data.galleries), default=0) + 1:03d}"
        members = []
    else:
        gallery_id = body.get("gallery_id")
        current = gallery_record_payload(data, pairs, gallery_id)
        require_record_revision(current["record"], body.get("expected_record_hash"))
        members = current["member_work_ids"]

    definitions = dict(data.galleries)
    memberships = dict(data.works)
    updated_pairs = pairs
    if operation == "delete":
        expected = body.get("expected_member_work_ids")
        if not isinstance(expected, list) or any(not isinstance(wid, str) for wid in expected):
            raise ValueError("expected_member_work_ids must be an array of Work IDs")
        if sorted(expected) != members:
            raise CatalogueRevisionConflict("Gallery membership changed; reopen the Gallery before deleting.")
        del definitions[gallery_id]
        updated_pairs = without_gallery(pairs, gallery_id)
        for wid in members:
            remaining = [gid for gid in memberships[wid] if gid != gallery_id]
            if remaining:
                memberships[wid] = remaining
            else:
                del memberships[wid]
    else:
        if "series_id" not in body or "related_to_series" not in body:
            raise ValueError("series_id and related_to_series are required")
        series_id, related = body["series_id"], body["related_to_series"]
        if type(related) is not bool:
            raise ValueError("related_to_series must be a boolean")
        if series_id is not None:
            series_record = series.get(series_id) if isinstance(series_id, str) else None
            if not isinstance(series_record, dict) or series_record.get("series_id") != series_id:
                raise ValueError(f"Unknown exact Series context: {series_id!r}")
        elif related:
            raise ValueError("A Gallery cannot relate to an unavailable Series")
        title = body.get("title")
        if not isinstance(title, str) or not title.strip():
            raise ValueError("Gallery title is required")
        definitions[gallery_id] = {"gallery_id": gallery_id, "title": title.strip()}
        if series_id is not None:
            updated_pairs = with_gallery_relation(pairs, series_id, gallery_id, related)

    updated = CatalogueGalleries(definitions, memberships)
    validate_galleries(updated, works)
    validate_series_galleries(updated_pairs, series, definitions)
    payloads = updated.payloads()
    writes = {}
    if definitions != data.galleries:
        writes[(context.source_dir / GALLERIES_FILE).resolve()] = payloads[GALLERIES_FILE]
    if memberships != data.works:
        writes[(context.source_dir / MEMBERSHIPS_FILE).resolve()] = payloads[MEMBERSHIPS_FILE]
    if updated_pairs.pairs_by_series != pairs.pairs_by_series:
        writes[(context.source_dir / SERIES_GALLERIES_FILE).resolve()] = updated_pairs.payload()
    if not set(writes).issubset(context.allowed_write_paths):
        raise ValueError("write target not allowlisted")
    if writes:
        execute_source_json_write(writes, dry_run=context.dry_run, repo_root=context.repo_root)
    affected_series = set(related_series_ids(pairs, gallery_id)) | set(related_series_ids(updated_pairs, gallery_id))
    affected_works = set(members) | {wid for wid, record in works.items() if record.get("series_id") in affected_series}
    shared = empty_shared_changes()
    if writes:
        shared["deleted_galleries" if operation == "delete" else "current_galleries"] = [gallery_id]
        shared["current_series"] = sorted(affected_series)
        outputs = {RELATIONSHIP_REPORT}
        if definitions != data.galleries:
            outputs.add(GALLERY_INDEX)
        if updated_pairs.pairs_by_series != pairs.pairs_by_series or (definitions != data.galleries and affected_series):
            outputs.add(RELATIONSHIP_INDEX)
        shared["shared_outputs"] = sorted(outputs)
    response = {
        "ok": True, "gallery_id": gallery_id, "changed": bool(writes),
        "created": operation == "create", "deleted": operation == "delete",
        "affected_work_ids": sorted(affected_works), "affected_gallery_ids": [gallery_id],
        "_shared_changes": shared,
    }
    if operation != "delete":
        response.update(gallery_record_payload(updated, updated_pairs, gallery_id))
    if context.dry_run:
        response.update(dry_run=True, would_write=bool(writes))
    elif writes:
        response["saved_at_utc"] = utc_now()
    log_event(context.repo_root, f"catalogue_gallery_{operation}", {
        "gallery_id": gallery_id, "affected_work_ids": members,
        "changed": bool(writes), "dry_run": context.dry_run,
    })
    return response
