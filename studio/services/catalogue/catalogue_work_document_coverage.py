"""Own Refresh's private Series/member-Work input for documentation coverage."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any, Iterable, Mapping


MANIFEST_PATH = "reports/work-document-coverage/manifest.json"
MANIFEST_SCHEMA = "catalogue_work_document_coverage_v1"


def _record_id(value: Any, *, work: bool = False) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{5}" if work else r"[0-9]{3}", value):
        raise ValueError("Invalid Work Document Coverage identity")
    return value


def _validate_row(row: Any, *, memberships: dict[str, str] | None = None) -> None:
    if (not isinstance(row, dict) or set(row) != {"series_id", "title", "work_ids"}
            or not isinstance(row["title"], str) or not row["title"].strip()
            or not isinstance(row["work_ids"], list)):
        raise ValueError("Invalid saved Work Document Coverage Series")
    _record_id(row["series_id"])
    previous = ""
    for work_id in row["work_ids"]:
        if (_record_id(work_id, work=True) <= previous
                or (memberships is not None and work_id in memberships)):
            raise ValueError("Invalid saved Work Document Coverage membership")
        previous = work_id
        if memberships is not None:
            memberships[work_id] = row["series_id"]


def _series_row(series_id: str, record: Mapping[str, Any], work_ids: Iterable[str]) -> dict[str, Any]:
    return {"series_id": series_id, "title": record["title"], "work_ids": sorted(work_ids)}


def _payload(rows: Mapping[str, Any], timestamp: str) -> dict[str, Any]:
    return {"header": {"schema": MANIFEST_SCHEMA, "generated_at_utc": timestamp},
            "series": [rows[series_id] for series_id in sorted(rows)]}


def work_document_coverage_manifest(
    series: Mapping[str, Any], works: Mapping[str, Any], *, timestamp: str,
) -> dict[str, Any]:
    """Project validated Catalogue inputs, including Series without member Works.

    Only Series labels and membership are persisted. Context document coverage
    remains a browser join against its independently generated management manifest.
    """
    members: dict[str, list[str]] = {series_id: [] for series_id in series}
    for work_id, record in works.items():
        series_id = record.get("series_id")
        if series_id is not None:
            members[series_id].append(work_id)
    rows = {series_id: _series_row(series_id, record, members[series_id]) for series_id, record in series.items()}
    return _payload(rows, timestamp)


def _validated_rows(payload: Any) -> tuple[dict[str, Any], dict[str, str]]:
    """Key saved rows and Work membership during their single validation pass."""
    if not isinstance(payload, dict) or set(payload) != {"header", "series"}:
        raise ValueError("Invalid saved Work Document Coverage manifest")
    header, rows = payload["header"], payload["series"]
    if (not isinstance(header, dict) or set(header) != {"schema", "generated_at_utc"}
            or header["schema"] != MANIFEST_SCHEMA or not isinstance(rows, list)
            or not isinstance(header["generated_at_utc"], str) or not header["generated_at_utc"]):
        raise ValueError("Invalid saved Work Document Coverage manifest header")
    previous_series = ""
    keyed_rows, memberships = {}, {}
    for row in rows:
        _validate_row(row, memberships=memberships)
        if row["series_id"] <= previous_series:
            raise ValueError("Invalid saved Work Document Coverage Series order")
        previous_series = row["series_id"]
        keyed_rows[previous_series] = row
    return keyed_rows, memberships


def validate_work_document_coverage_manifest(payload: Any) -> dict[str, Any]:
    """Validate saved minimal input without consulting canonical or public data."""
    _validated_rows(payload)
    return payload


def merge_work_document_coverage_manifest(
    path: Path, series: Mapping[str, Any], works: Mapping[str, Any], *,
    current_series: Iterable[str], deleted_series: Iterable[str],
    current_work_ids: Iterable[str], deleted_work_ids: Iterable[str], timestamp: str,
) -> dict[str, Any] | None:
    """Merge queued Series endpoints and Work memberships, preserving other rows.

    Parse and key saved membership once without validating its contents or the
    queued endpoints; never rebuild membership from canonical Works. Retained
    candidates include ready Works. None preserves bytes/time.
    """
    current, deleted = set(current_series), set(deleted_series)
    current_works, deleted_works = set(current_work_ids), set(deleted_work_ids)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows = {row["series_id"]: row for row in payload["series"]}
        previous_memberships = {wid: sid for sid, row in rows.items() for wid in row["work_ids"]}
    except (OSError, UnicodeError, ValueError) as error:
        raise ValueError(
            f"Work Document Coverage is unavailable or invalid; run explicit Work Document Coverage maintenance: {error}"
        ) from error
    members = {key: set(rows[key]["work_ids"]) if key in rows else set() for key in current}
    for work_id in sorted(current_works | deleted_works):
        old = previous_memberships.get(work_id)
        new = works[work_id].get("series_id") if work_id in current_works else None
        if old in members:
            members[old].discard(work_id)
        if new in members:
            members[new].add(work_id)
    changed = False
    for key in sorted(current):
        row = _series_row(key, series[key], members[key])
        if rows.get(key) != row:
            rows[key] = row
            changed = True
    for key in sorted(deleted):
        if key in rows:
            del rows[key]
            changed = True
    return _payload(rows, timestamp) if changed else None
