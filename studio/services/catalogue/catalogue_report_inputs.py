"""Own private Refresh projections shared by local Catalogue report services."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any, Mapping

from catalogue.catalogue_output_paths import catalogue_output_workspace, output_path
from catalogue.catalogue_work_attachments import safe_download_filename
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
    return {
        "work_id": record["work_id"], "title": record["title"],
        "links": [{"label": item["label"], "url": item["url"]} for item in record.get("links") or []],
        "download_filenames": [item["filename"] for item in record.get("downloads") or []],
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
    """Project already loaded Catalogue records without inspecting physical files.

    Keep every Work, declared sources even when missing, and empty Series.
    These inputs are independent of final report rows and public Work payloads.
    Generation time supports Refresh's existing unchanged-content comparison.
    """
    payloads = {}
    for relative in sorted(selected):
        if relative not in INPUT_SCHEMAS:
            raise ValueError("Unknown private Catalogue report input")
        if relative == SERIES_PATH:
            family = "series"
            rows = {sid: {"series_id": sid, "title": record["title"]} for sid, record in sorted(series.items())}
        else:
            family = "works"
            project = _source_row if relative == WORK_SOURCES_PATH else _resource_row
            rows = {wid: project(record) for wid, record in sorted(works.items())}
        payload = {"header": {"schema": INPUT_SCHEMAS[relative], "generated_at_utc": timestamp}, family: rows}
        validate_catalogue_report_input(relative, payload)
        payloads[relative] = payload
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


def validate_catalogue_report_input(relative: str, payload: Any) -> dict[str, Any]:
    """Validate only this projection's exact identities and consumed facts.

    No canonical/editor record, document output or filesystem existence is a
    prerequisite. Runtime media configuration still owns source-root resolution.
    """
    family = "series" if relative == SERIES_PATH else "works"
    if relative not in INPUT_SCHEMAS or not isinstance(payload, dict) or set(payload) != {"header", family}:
        raise ValueError("Invalid private Catalogue input shape")
    header, rows = payload["header"], payload[family]
    if (not isinstance(header, dict) or set(header) != {"schema", "generated_at_utc"}
            or header["schema"] != INPUT_SCHEMAS[relative] or not isinstance(rows, dict)):
        raise ValueError("Invalid private Catalogue input header or records")
    _text(header["generated_at_utc"], "Catalogue input generation time")
    identity = "series_id" if family == "series" else "work_id"
    pattern = r"[0-9]{3}" if family == "series" else r"[0-9]{5}"
    required = {identity, "title"}
    optional = set(SOURCE_FIELDS) if relative == WORK_SOURCES_PATH else set()
    if relative == WORK_RESOURCES_PATH:
        required |= {"links", "download_filenames"}
    for key, row in rows.items():
        if (not isinstance(key, str) or not re.fullmatch(pattern, key)
                or not isinstance(row, dict) or row.get(identity) != key
                or not required <= set(row) or set(row) - required - optional):
            raise ValueError("Invalid private Catalogue identity or fields")
        _text(row["title"], f"Catalogue {key} title")
        if relative == WORK_SOURCES_PATH:
            if "series_id" in row and (not isinstance(row["series_id"], str) or not re.fullmatch(r"[0-9]{3}", row["series_id"])):
                raise ValueError(f"Work {key} requires an exact Series ID")
            if "media_source_id" in row:
                _text(row["media_source_id"], f"Work {key} media source")
            for field in ("project_folder", "project_subfolder", "project_filename"):
                if field in row:
                    _source_declaration(row[field], field)
        elif relative == WORK_RESOURCES_PATH:
            if not isinstance(row["links"], list) or not isinstance(row["download_filenames"], list):
                raise ValueError(f"Work {key} resources must be arrays")
            for link in row["links"]:
                if not isinstance(link, dict) or set(link) != {"label", "url"}:
                    raise ValueError(f"Work {key} has an invalid link")
                _text(link["label"], f"Work {key} link label")
                _text(link["url"], f"Work {key} link URL")
            for filename in row["download_filenames"]:
                safe_download_filename(filename)
    return payload


def read_catalogue_report_input(workspace: ArtifactLocation, relative: str) -> dict[str, dict[str, Any]]:
    """Read saved Working facts once; missing/invalid input requires Studio Refresh."""
    try:
        path = output_path(workspace, relative)
        payload = validate_catalogue_report_input(relative, json.loads(path.read_text(encoding="utf-8")))
    except (OSError, UnicodeError, ValueError) as error:
        raise ValueError(
            f"Catalogue report input {relative} is unavailable or invalid; run Refresh Catalogue in Studio. "
            "Unselected missing or invalid inputs require explicit Catalogue report-input maintenance."
        ) from error
    return payload["series" if relative == SERIES_PATH else "works"]


def read_work_sources(repo_root: Path) -> dict[str, dict[str, Any]]:
    """Resolve and read the Catalogue-owned Working source/placement aggregate."""
    return read_catalogue_report_input(catalogue_output_workspace(repo_root), WORK_SOURCES_PATH)


def read_work_resources(repo_root: Path) -> dict[str, dict[str, Any]]:
    """Resolve and read refreshed titles, authored links and exact download names."""
    return read_catalogue_report_input(catalogue_output_workspace(repo_root), WORK_RESOURCES_PATH)
