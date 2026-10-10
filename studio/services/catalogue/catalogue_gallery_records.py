"""Validate saved Galleries and merge selected member rows without full projection."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any, Iterable, Mapping, Sequence

from studio.services.catalogue.catalogue_galleries import validate_gallery_id
from studio.services.catalogue.catalogue_generation_indexes import build_member_work_records
from studio.services.catalogue.catalogue_generation_records import GALLERY_RECORD_SCHEMA_VERSION, build_gallery_json_payload


def _validated_members(payload: Any, gallery_id: str) -> dict[str, dict[str, str]]:
    validate_gallery_id(gallery_id)
    if not isinstance(payload, dict) or set(payload) != {"header", "gallery", "member_works"}:
        raise ValueError("Generated Gallery requires its header, definition and members")
    header, gallery, members = payload["header"], payload["gallery"], payload["member_works"]
    if (not isinstance(header, dict) or set(header) != {"schema", "generated_at_utc", "gallery_id"}
            or header["schema"] != GALLERY_RECORD_SCHEMA_VERSION or header["gallery_id"] != gallery_id
            or not isinstance(header["generated_at_utc"], str) or not header["generated_at_utc"].strip()):
        raise ValueError("Generated Gallery header does not match the selected Gallery")
    if (not isinstance(gallery, dict) or set(gallery) != {"gallery_id", "title"}
            or gallery["gallery_id"] != gallery_id
            or not isinstance(gallery["title"], str) or not gallery["title"].strip()):
        raise ValueError("Generated Gallery definition is invalid")
    if not isinstance(members, list):
        raise ValueError("Generated Gallery membership must be a list")
    rows, previous = {}, ""
    for row in members:
        if (not isinstance(row, dict) or set(row) != {"work_id", "title"}
                or not isinstance(row["work_id"], str) or not re.fullmatch(r"[0-9]{5}", row["work_id"])
                or not isinstance(row["title"], str) or not row["title"].strip()):
            raise ValueError("Generated Gallery member requires an exact Work ID and title")
        identity = row["work_id"]
        if identity <= previous:
            raise ValueError("Generated Gallery Works must be distinct and in ascending ID order")
        rows[identity], previous = row, identity
    return rows


def validate_gallery_record(payload: Any, *, gallery_id: str) -> dict[str, Any]:
    """Validate a saved v3 record without canonical or member by-ID reads."""
    _validated_members(payload, gallery_id)
    return payload


def merge_gallery_record(
    path: Path, *, gallery_id: str, gallery_record: Mapping[str, Any],
    work_records: Mapping[str, Mapping[str, Any]], memberships: Mapping[str, list[str]],
    current_work_ids: Iterable[str], deleted_work_ids: Iterable[str], timestamp: str,
    initial_member_ids: Sequence[str] | None = None,
) -> dict[str, Any] | None:
    """Read once and merge only queued member candidates using final membership.

    Initial members are supplied only for explicit queued Gallery creation; a
    missing existing record fails and requires deliberate Gallery maintenance.
    Creation replaces any former incarnation's members. None preserves saved
    bytes and time. Unselected saved rows never join canonical Work data.
    """
    validate_gallery_id(gallery_id)
    current, deleted = set(current_work_ids), set(deleted_work_ids)
    if current & deleted or current - work_records.keys() or deleted & work_records.keys():
        raise ValueError("Gallery member selection disagrees with canonical Work identities")
    try:
        previous = json.loads(path.read_text(encoding="utf-8"))
        rows = _validated_members(previous, gallery_id)
    except FileNotFoundError as error:
        if initial_member_ids is None:
            raise ValueError(f"Gallery {gallery_id} is unavailable; run explicit Gallery-record maintenance") from error
        previous, rows = None, {}
    except (OSError, ValueError) as error:
        raise ValueError(f"Gallery {gallery_id} is invalid; run explicit Gallery-record maintenance: {error}") from error
    if initial_member_ids is not None:
        members = build_member_work_records(work_records=work_records, work_ids=initial_member_ids)
        if previous is not None and previous["gallery"] == gallery_record and previous["member_works"] == members:
            return None
    else:
        changed = previous["gallery"] != gallery_record
        retained = {wid for wid in current if gallery_id in memberships.get(wid, [])}
        for row in build_member_work_records(work_records=work_records, work_ids=sorted(retained)):
            if rows.get(row["work_id"]) != row:
                rows[row["work_id"]] = row
                changed = True
        for wid in deleted | (current - retained):
            if wid in rows:
                del rows[wid]
                changed = True
        if not changed:
            return None
        members = [rows[wid] for wid in sorted(rows)]
    return build_gallery_json_payload(
        gallery_id=gallery_id, gallery_record=gallery_record, member_works=members, generated_at_utc=timestamp,
    )
