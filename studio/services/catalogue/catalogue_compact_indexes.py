"""Own compact Work/Gallery projection, saved validation and selected-row merging."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any, Iterable, Mapping

from studio.services.catalogue.catalogue_generation_indexes import build_work_index_row


INDEX_SCHEMAS = {"works": "catalogue_works_index_v3", "galleries": "catalogue_galleries_index_v3"}
IDENTITY_FIELDS = {"works": "work_id", "galleries": "gallery_id"}
IDENTITY_PATTERNS = {"works": r"[0-9]{5}", "galleries": r"(?:[0-9]{3}|[1-9][0-9]{3,})"}


def _identity(family: str, value: Any) -> str:
    if not isinstance(value, str) or not re.fullmatch(IDENTITY_PATTERNS[family], value):
        raise ValueError(f"Compact {family} index requires an exact identity")
    return value


def _validate_row(family: str, identity: str, row: Any) -> None:
    field = IDENTITY_FIELDS[family]
    _identity(family, identity)
    if (not isinstance(row, dict) or set(row) != {field, "title"} or row[field] != identity
            or not isinstance(row["title"], str) or not row["title"].strip()):
        raise ValueError(f"Invalid compact {family} index row: {identity}")


def validate_compact_index(payload: Any, *, family: str) -> dict[str, Any]:
    """Validate saved facts without joining canonical data or computing a hash."""
    if not isinstance(payload, dict) or set(payload) != {"header", family}:
        raise ValueError(f"Invalid compact {family} index envelope; run explicit compact-index maintenance")
    header, rows = payload["header"], payload[family]
    if (not isinstance(header, dict) or set(header) != {"schema", "generated_at_utc"}
            or header["schema"] != INDEX_SCHEMAS[family] or not isinstance(rows, dict)
            or not isinstance(header["generated_at_utc"], str) or not header["generated_at_utc"].strip()):
        raise ValueError(f"Invalid compact {family} index header; run explicit compact-index maintenance")
    previous = ""
    for identity, row in rows.items():
        _validate_row(family, identity, row)
        if identity <= previous:
            raise ValueError(f"Compact {family} index identities must be distinct and ordered")
        previous = identity
    return payload


def _project_row(family: str, identity: str, source: Mapping[str, Any]) -> dict[str, str]:
    field = IDENTITY_FIELDS[family]
    if source.get(field) != identity:
        raise ValueError(f"Compact {family} source identity is mismatched: {identity}")
    row = (build_work_index_row(work_id=identity, work_record=source) if family == "works"
           else {"gallery_id": identity, "title": source.get("title")})
    _validate_row(family, identity, row)
    return row


def _payload(family: str, rows: dict[str, Any], timestamp: str) -> dict[str, Any]:
    return {"header": {"schema": INDEX_SCHEMAS[family], "generated_at_utc": timestamp},
            family: dict(sorted(rows.items()))}


def build_compact_index(family: str, sources: Mapping[str, Any], *, timestamp: str) -> dict[str, Any]:
    """Explicit whole-index generation uses the same row projection as Refresh."""
    return _payload(family, {identity: _project_row(family, identity, source)
                             for identity, source in sources.items()}, timestamp)


def merge_compact_index(
    path: Path, *, family: str, sources: Mapping[str, Any], current_ids: Iterable[str],
    deleted_ids: Iterable[str], timestamp: str,
) -> dict[str, Any] | None:
    """Read once, project supplied current rows and remove explicit deletions.

    None means no write, preserving the saved bytes and generation time. Missing
    or invalid saved output fails without invoking complete generation.
    """
    current = {_identity(family, identity) for identity in current_ids}
    deleted = {_identity(family, identity) for identity in deleted_ids}
    if current & deleted or current - sources.keys() or deleted & sources.keys():
        raise ValueError(f"Compact {family} selection disagrees with canonical identities")
    try:
        payload = validate_compact_index(json.loads(path.read_text(encoding="utf-8")), family=family)
    except (OSError, ValueError) as error:
        raise ValueError(f"Compact {family} index is unavailable; run explicit compact-index maintenance: {error}") from error
    rows = payload[family]
    changed = False
    for identity in sorted(current):
        row = _project_row(family, identity, sources[identity])
        if rows.get(identity) != row:
            rows[identity] = row
            changed = True
    for identity in sorted(deleted):
        if identity in rows:
            del rows[identity]
            changed = True
    return _payload(family, rows, timestamp) if changed else None
