"""Own private Refresh projections shared by local Catalogue report services."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any, Iterable, Mapping

from studio.services.catalogue.catalogue_output_paths import catalogue_output_workspace, output_path
from docs_artifact_locations import ArtifactLocation


WORK_SOURCES_PATH = "private/work-sources.json"
WORK_RESOURCES_PATH = "private/work-resources.json"
SERIES_PATH = "private/series.json"
INPUT_SCHEMAS = {
    WORK_SOURCES_PATH: "catalogue_work_sources_v1",
    WORK_RESOURCES_PATH: "catalogue_work_resources_v1",
    SERIES_PATH: "catalogue_series_definitions_v1",
}
SOURCE_FIELDS = ("series_id", "media_source_id", "project_folder", "project_subfolder", "project_filename")


def _source_row(record: Mapping[str, Any]) -> dict[str, Any]:
    return {key: record[key] for key in ("work_id", "title", *SOURCE_FIELDS) if key in record}


def _resource_row(record: Mapping[str, Any]) -> dict[str, Any]:
    """Project resource references with the UI-authored labels unchanged."""
    return {
        "work_id": record["work_id"], "title": record["title"],
        "links": [{"label": item["label"], "url": item["url"]} for item in record.get("links", [])],
        "download_filenames": [item["filename"] for item in record.get("downloads", [])],
    }


def changed_work_report_inputs(
    previous: Mapping[str, Any] | None, current: Mapping[str, Any] | None,
) -> set[str]:
    """Select only consumed old/new facts; deletion is captured before removal.

    Download labels, staging flags, media revisions, year and Gallery membership
    do not affect these inputs. Creation/deletion selects both Work aggregates.
    """
    if previous is None or current is None:
        return {WORK_SOURCES_PATH, WORK_RESOURCES_PATH}
    selected = set()
    if _source_row(previous) != _source_row(current):
        selected.add(WORK_SOURCES_PATH)
    if _resource_row(previous) != _resource_row(current):
        selected.add(WORK_RESOURCES_PATH)
    return selected


def catalogue_report_input_payloads(
    works: Mapping[str, Any], series: Mapping[str, Any], *, timestamp: str, selected: set[str],
) -> dict[str, dict[str, Any]]:
    """Explicit full projection, sharing row builders with normal Refresh.

    Keep every Work, declared sources even when missing, and empty Series.
    These inputs are independent of final report rows and public Work payloads.
    Generation time supports Refresh's existing unchanged-content comparison.
    """
    payloads = {}
    for relative in sorted(selected):
        if relative not in INPUT_SCHEMAS:
            raise ValueError("Unknown private Catalogue report input")
        sources = series if relative == SERIES_PATH else works
        rows = {key: _project_row(relative, key, record) for key, record in sources.items()}
        payloads[relative] = _payload(relative, rows, timestamp)
    return payloads


def _text(value: Any, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be nonempty text")


def _source_declaration(value: Any, field: str) -> None:
    if value is None or value == "":
        return
    _text(value, field)
    parts = value.split("/")
    if ("\\" in value or any(part in {"", ".", ".."} for part in parts)
            or any(ord(char) < 32 or ord(char) == 127 for char in value)
            or (field != "project_subfolder" and len(parts) != 1)):
        raise ValueError(f"{field} must be a portable relative source declaration")


def _record_id(relative: str, value: Any) -> str:
    pattern = r"[0-9]{3}" if relative == SERIES_PATH else r"[0-9]{5}"
    if not isinstance(value, str) or not re.fullmatch(pattern, value):
        raise ValueError("Invalid private Catalogue identity")
    return value


def _validate_row(relative: str, key: str, row: Any) -> None:
    _record_id(relative, key)
    identity = "series_id" if relative == SERIES_PATH else "work_id"
    required = {identity, "title"}
    optional = set(SOURCE_FIELDS) if relative == WORK_SOURCES_PATH else set()
    if (not isinstance(row, dict) or row.get(identity) != key
            or not required <= set(row) or set(row) - required - optional
            or not isinstance(row["title"], str)):
        raise ValueError("Invalid private Catalogue identity or fields")
    if relative == SERIES_PATH:
        _text(row["title"], f"Catalogue {key} title")
    if relative == WORK_SOURCES_PATH:
        if "series_id" in row and (not isinstance(row["series_id"], str) or not re.fullmatch(r"[0-9]{3}", row["series_id"])):
            raise ValueError(f"Work {key} requires an exact Series ID")
        if "media_source_id" in row:
            _text(row["media_source_id"], f"Work {key} media source")
        for field in ("project_folder", "project_subfolder", "project_filename"):
            if field in row:
                _source_declaration(row[field], field)


def _project_row(relative: str, key: str, source: Mapping[str, Any]) -> dict[str, Any]:
    if relative == SERIES_PATH:
        row = {"series_id": key, "title": source["title"]}
    else:
        row = _source_row(source) if relative == WORK_SOURCES_PATH else _resource_row(source)
    return row


def _payload(relative: str, rows: dict[str, Any], timestamp: str) -> dict[str, Any]:
    family = "series" if relative == SERIES_PATH else "works"
    return {"header": {"schema": INPUT_SCHEMAS[relative], "generated_at_utc": timestamp},
            family: dict(sorted(rows.items()))}


def validate_catalogue_report_input(relative: str, payload: Any) -> dict[str, Any]:
    """Validate source/Series identities and consumed facts for their readers.

    No canonical/editor record, document output or filesystem existence is a
    prerequisite. Runtime media configuration still owns source-root resolution.
    """
    family = "series" if relative == SERIES_PATH else "works"
    if relative not in {WORK_SOURCES_PATH, SERIES_PATH} or not isinstance(payload, dict) or set(payload) != {"header", family}:
        raise ValueError("Invalid private Catalogue input shape")
    header, rows = payload["header"], payload[family]
    if (not isinstance(header, dict) or set(header) != {"schema", "generated_at_utc"}
            or header["schema"] != INPUT_SCHEMAS[relative] or not isinstance(rows, dict)):
        raise ValueError("Invalid private Catalogue input header or records")
    _text(header["generated_at_utc"], "Catalogue input generation time")
    for key, row in rows.items():
        _validate_row(relative, key, row)
    return payload


def merge_catalogue_report_input(
    path: Path, *, relative: str, sources: Mapping[str, Any], current_ids: Iterable[str],
    deleted_ids: Iterable[str], timestamp: str,
) -> dict[str, Any] | None:
    """Read once, project supplied rows and remove only explicit deletions.

    Trust queued identities and saved contents without row/schema validation.
    Unaffected rows do not join canonical records. None preserves bytes/time;
    unreadable output never triggers a complete projection or filesystem scan.
    """
    if relative not in INPUT_SCHEMAS:
        raise ValueError("Unknown private Catalogue report input")
    current, deleted = set(current_ids), set(deleted_ids)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as error:
        raise ValueError(
            f"Catalogue report input {relative} is unavailable or invalid; run explicit private report-input maintenance: {error}"
        ) from error
    rows = payload["series" if relative == SERIES_PATH else "works"]
    changed = False
    for key in sorted(current):
        row = _project_row(relative, key, sources[key])
        if rows.get(key) != row:
            rows[key] = row
            changed = True
    for key in sorted(deleted):
        if key in rows:
            del rows[key]
            changed = True
    return _payload(relative, rows, timestamp) if changed else None


def read_catalogue_report_input(workspace: ArtifactLocation, relative: str) -> dict[str, dict[str, Any]]:
    """Read saved Working facts once; missing/invalid input requires explicit maintenance."""
    try:
        path = output_path(workspace, relative)
        payload = validate_catalogue_report_input(relative, json.loads(path.read_text(encoding="utf-8")))
    except (OSError, UnicodeError, ValueError) as error:
        raise ValueError(
            f"Catalogue report input {relative} is unavailable or invalid; run explicit Catalogue private report-input maintenance."
        ) from error
    return payload["series" if relative == SERIES_PATH else "works"]


def read_work_sources(repo_root: Path) -> dict[str, dict[str, Any]]:
    """Resolve and read the Catalogue-owned Working source/placement aggregate."""
    return read_catalogue_report_input(catalogue_output_workspace(repo_root), WORK_SOURCES_PATH)


def read_work_resources(workspace: ArtifactLocation) -> dict[str, dict[str, Any]]:
    """Parse one confined saved input, trusting Refresh-owned resource facts.

    Callers supply the resolved Working Catalogue owner. No schema, identity,
    label, URL or download audit and no canonical fallback is performed here.
    """
    path = output_path(workspace, WORK_RESOURCES_PATH)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as error:
        raise ValueError(
            "Catalogue Work resources are unavailable or invalid; run explicit Catalogue private report-input maintenance."
        ) from error
    if not isinstance(payload, dict):
        raise ValueError("Catalogue Work resources must contain a JSON object.")
    return payload["works"]
