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


def _work_series(work_id: str, record: Mapping[str, Any], series: Mapping[str, Any]) -> str:
    _record_id(work_id, work=True)
    series_id = _record_id(record.get("series_id"))
    if record.get("work_id") != work_id or series_id not in series:
        raise ValueError(f"Work Document Coverage Work {work_id} has a mismatched identity or unavailable Series")
    return series_id


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
    if record.get("series_id") != series_id:
        raise ValueError(f"Work Document Coverage Series identity is mismatched: {series_id}")
    row = {"series_id": series_id, "title": record["title"], "work_ids": sorted(work_ids)}
    _validate_row(row)
    return row


def _payload(rows: Mapping[str, Any], timestamp: str) -> dict[str, Any]:
    if not isinstance(timestamp, str) or not timestamp.strip():
        raise ValueError("Work Document Coverage generation time must be nonempty text")
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
        members[_work_series(work_id, record, series)].append(work_id)
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

    Read/validate saved membership once; never scan canonical Works to rebuild
    affected Series. Retained candidates include already-refreshed Works. None
    preserves bytes/time; missing or invalid input requires explicit maintenance.
    """
    current = {_record_id(key) for key in current_series}
    deleted = {_record_id(key) for key in deleted_series}
    current_works = {_record_id(key, work=True) for key in current_work_ids}
    deleted_works = {_record_id(key, work=True) for key in deleted_work_ids}
    if (current & deleted or current - series.keys() or deleted & series.keys()
            or current_works & deleted_works or current_works - works.keys() or deleted_works & works.keys()):
        raise ValueError("Work Document Coverage selection disagrees with canonical identities")
    try:
        rows, previous_memberships = _validated_rows(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, UnicodeError, ValueError) as error:
        raise ValueError(
            f"Work Document Coverage is unavailable or invalid; run explicit Work Document Coverage maintenance: {error}"
        ) from error
    members = {key: set(rows[key]["work_ids"]) if key in rows else set() for key in current}
    endpoints = current | deleted
    for work_id in sorted(current_works | deleted_works):
        old = previous_memberships.get(work_id)
        new = _work_series(work_id, works[work_id], series) if work_id in current_works else None
        if old != new and ({key for key in (old, new) if key is not None} - endpoints):
            raise ValueError(f"Work Document Coverage membership endpoints are not queued for Work {work_id}")
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
