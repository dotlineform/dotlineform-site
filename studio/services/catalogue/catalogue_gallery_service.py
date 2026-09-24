"""Gallery definition mutations, independent of the selected Work draft."""

from __future__ import annotations

from typing import Any, Mapping

from catalogue.catalogue_galleries import (
    GALLERIES_FILE, MEMBERSHIPS_FILE, CatalogueGalleries, read_galleries,
    validate_galleries, validate_gallery_id,
)
from catalogue.catalogue_revisions import CatalogueRevisionConflict, record_hash, require_record_revision
from catalogue.catalogue_service_context import CatalogueWriteContext, load_works_payload, log_event, utc_now
from catalogue.catalogue_transactions import execute_source_json_write


def gallery_record_payload(data: CatalogueGalleries, gallery_id: str) -> dict[str, Any]:
    """Return an exact definition revision and its current canonical member IDs."""
    validate_gallery_id(gallery_id)
    if gallery_id not in data.galleries:
        raise ValueError(f"gallery_id not found: {gallery_id}")
    record = data.galleries[gallery_id]
    return {
        "gallery_id": gallery_id, "record": record, "record_hash": record_hash(record),
        "member_work_ids": sorted(wid for wid, ids in data.works.items() if gallery_id in ids),
    }


def mutate_gallery_payload(
    context: CatalogueWriteContext, operation: str, body: Mapping[str, Any],
) -> dict[str, Any]:
    """Persist a definition and any global membership removal in one source transaction.

    Delete checks the definition and complete member set shown for confirmation.
    Work metadata is untouched; completion receives all former member identities.
    """
    if operation not in {"create", "save", "delete"}:
        raise ValueError("Unsupported Gallery operation")
    works = load_works_payload(context.works_path)["works"]
    data = read_galleries(context.source_dir, works)
    if operation == "create":
        gallery_id = f"{max((int(gid) for gid in data.galleries), default=0) + 1:03d}"
        members = []
    else:
        gallery_id = body.get("gallery_id")
        current = gallery_record_payload(data, gallery_id)
        require_record_revision(current["record"], body.get("expected_record_hash"))
        members = current["member_work_ids"]

    definitions = dict(data.galleries)
    memberships = dict(data.works)
    if operation == "delete":
        expected = body.get("expected_member_work_ids")
        if not isinstance(expected, list) or any(not isinstance(wid, str) for wid in expected):
            raise ValueError("expected_member_work_ids must be an array of Work IDs")
        if sorted(expected) != members:
            raise CatalogueRevisionConflict("Gallery membership changed; reopen the Gallery before deleting.")
        del definitions[gallery_id]
        for wid in members:
            remaining = [gid for gid in memberships[wid] if gid != gallery_id]
            if remaining:
                memberships[wid] = remaining
            else:
                del memberships[wid]
    else:
        title = body.get("title")
        if not isinstance(title, str) or not title.strip():
            raise ValueError("Gallery title is required")
        definitions[gallery_id] = {"gallery_id": gallery_id, "title": title.strip()}

    updated = CatalogueGalleries(definitions, memberships)
    validate_galleries(updated, works)
    payloads = updated.payloads()
    writes = {}
    if definitions != data.galleries:
        writes[(context.source_dir / GALLERIES_FILE).resolve()] = payloads[GALLERIES_FILE]
    if memberships != data.works:
        writes[(context.source_dir / MEMBERSHIPS_FILE).resolve()] = payloads[MEMBERSHIPS_FILE]
    if not set(writes).issubset(context.allowed_write_paths):
        raise ValueError("write target not allowlisted")
    if writes:
        execute_source_json_write(writes, dry_run=context.dry_run, repo_root=context.repo_root)
    response = {
        "ok": True, "gallery_id": gallery_id, "changed": bool(writes),
        "created": operation == "create", "deleted": operation == "delete",
        "affected_work_ids": members, "affected_gallery_ids": [gallery_id],
    }
    if operation != "delete":
        response.update(gallery_record_payload(updated, gallery_id))
    if context.dry_run:
        response.update(dry_run=True, would_write=bool(writes))
    elif writes:
        response["saved_at_utc"] = utc_now()
    log_event(context.repo_root, f"catalogue_gallery_{operation}", {
        "gallery_id": gallery_id, "affected_work_ids": members,
        "changed": bool(writes), "dry_run": context.dry_run,
    })
    return response
