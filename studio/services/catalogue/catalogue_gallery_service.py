"""Gallery definition mutations, independent of the selected Work draft."""

from __future__ import annotations

from typing import Any, Mapping

from catalogue.catalogue_galleries import (
    GALLERIES_FILE, MEMBERSHIPS_FILE, CatalogueGalleries, read_galleries,
    validate_gallery_id,
)
from catalogue.catalogue_series_galleries import (
    SERIES_GALLERIES_FILE, CatalogueSeriesGalleries, read_series_galleries,
    related_series_ids, with_gallery_relation, without_gallery,
)
from catalogue.catalogue_service_context import CatalogueWriteContext, load_works_payload, log_event, utc_now
from catalogue.catalogue_transactions import execute_source_json_write
from catalogue.catalogue_source import CatalogueSourceRecords
from catalogue.catalogue_shared_changes import empty_shared_changes, GALLERY_INDEX, RELATIONSHIP_INDEX, RELATIONSHIP_REPORT


def gallery_record_payload(
    definitions: Mapping[str, dict[str, str]], pairs: CatalogueSeriesGalleries, gallery_id: str,
) -> dict[str, Any]:
    """Return the exact definition and saved Series associations."""
    validate_gallery_id(gallery_id)
    if gallery_id not in definitions:
        raise ValueError(f"gallery_id not found: {gallery_id}")
    record = definitions[gallery_id]
    return {
        "gallery_id": gallery_id, "record": record,
        "related_series_ids": related_series_ids(pairs, gallery_id),
    }


def mutate_gallery_payload(
    context: CatalogueWriteContext, operation: str, body: Mapping[str, Any],
) -> tuple[dict[str, Any], CatalogueSourceRecords, CatalogueSourceRecords]:
    """Persist the UI-authored definition/relevance with create/save integrity checks.

    Create uses the supplied exact ID and cannot replace a saved definition.
    Save addresses an existing identity without repeating authoring validation or
    auditing the Catalogue. The UI owns title completion, Series selection and
    the relationship checkbox's boolean/available-Series validation.
    Delete trusts the UI's saved-ID selection, requires its exact existing target
    and removes current references without spelling/revision/member preconditions
    or a complete canonical audit. Removal captures its changed stores and former
    relevance endpoints without complete-map comparisons or relation rescans.
    Work metadata is untouched; completion receives all former member identities.
    """
    if operation not in {"create", "save", "delete"}:
        raise ValueError("Unsupported Gallery operation")
    if operation == "delete" and set(body) != {"gallery_id"}:
        raise ValueError("Gallery Delete requires only gallery_id")
    if operation != "delete" and set(body) != {"gallery_id", "title", "series_id", "related_to_series"}:
        raise ValueError("Gallery Create/Save requires gallery_id, title, series_id and related_to_series")
    gallery_id = body["gallery_id"]
    if operation == "delete":
        if not isinstance(gallery_id, str):
            raise ValueError("Gallery Delete requires an exact Gallery ID string")
    else:
        validate_gallery_id(gallery_id)
    works = load_works_payload(context.works_path)["works"]
    data = read_galleries(context.source_dir)
    pairs = read_series_galleries(context.source_dir)
    if operation == "create":
        if gallery_id in data.galleries:
            raise ValueError(f"gallery_id already exists: {gallery_id}")
        members = []
    else:
        if gallery_id not in data.galleries:
            raise ValueError(f"gallery_id not found: {gallery_id}")
        members = sorted(wid for wid, ids in data.works.items() if gallery_id in ids)

    definitions = dict(data.galleries)
    memberships = data.works
    updated_pairs = pairs
    if operation == "delete":
        memberships = dict(data.works)
        del definitions[gallery_id]
        updated_pairs, previous_related_series = without_gallery(pairs, gallery_id)
        for wid in members:
            remaining = [gid for gid in memberships[wid] if gid != gallery_id]
            if remaining:
                memberships[wid] = remaining
            else:
                del memberships[wid]
        definitions_changed = True
        memberships_changed = bool(members)
        relations_changed = bool(previous_related_series)
        saved_related_series = []
    else:
        series_id, related = body["series_id"], body["related_to_series"]
        title = body["title"]
        definitions[gallery_id] = {"gallery_id": gallery_id, "title": title}
        if series_id is not None:
            updated_pairs = with_gallery_relation(pairs, series_id, gallery_id, related)
        definitions_changed = definitions != data.galleries
        memberships_changed = False
        relations_changed = updated_pairs.pairs_by_series != pairs.pairs_by_series
        previous_related_series = related_series_ids(pairs, gallery_id)
        saved_related_series = related_series_ids(updated_pairs, gallery_id) if relations_changed else previous_related_series

    updated = CatalogueGalleries(definitions, memberships)
    writes = {}
    if definitions_changed:
        writes[(context.source_dir / GALLERIES_FILE).resolve()] = updated.definitions_payload()
    if memberships_changed:
        writes[(context.source_dir / MEMBERSHIPS_FILE).resolve()] = updated.memberships_payload()
    if relations_changed:
        writes[(context.source_dir / SERIES_GALLERIES_FILE).resolve()] = updated_pairs.payload()
    if not set(writes).issubset(context.allowed_write_paths):
        raise ValueError("write target not allowlisted")
    if writes:
        execute_source_json_write(writes, dry_run=context.dry_run, repo_root=context.repo_root)
    affected_series = set(previous_related_series) | set(saved_related_series)
    affected_works = set(members) | {wid for wid, record in works.items() if record.get("series_id") in affected_series}
    shared = empty_shared_changes()
    if writes:
        shared["deleted_galleries" if operation == "delete" else "current_galleries"] = [gallery_id]
        if operation == "create":
            shared["created_galleries"] = [gallery_id]
        shared["current_series"] = sorted(affected_series)
        outputs = {RELATIONSHIP_REPORT}
        if definitions_changed:
            outputs.add(GALLERY_INDEX)
        if relations_changed or (definitions_changed and affected_series):
            outputs.add(RELATIONSHIP_INDEX)
        shared["shared_outputs"] = sorted(outputs)
    response = {
        "ok": True, "gallery_id": gallery_id, "changed": bool(writes),
        "created": operation == "create", "deleted": operation == "delete",
        "affected_work_ids": sorted(affected_works), "affected_gallery_ids": [gallery_id],
        "_shared_changes": shared,
    }
    if operation != "delete":
        response.update(record=definitions[gallery_id], related_series_ids=saved_related_series)
    if context.dry_run:
        response.update(dry_run=True, would_write=bool(writes))
    elif writes:
        response["saved_at_utc"] = utc_now()
    log_event(context.repo_root, f"catalogue_gallery_{operation}", {
        "gallery_id": gallery_id, "affected_work_ids": members,
        "changed": bool(writes), "dry_run": context.dry_run,
    })
    records = CatalogueSourceRecords(works=works, series={})
    return response, records, records
