#!/usr/bin/env python3
"""Build the local folder-centred Project State report."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.parse import quote

_BOOTSTRAP_START = Path(__file__).resolve()
for _candidate in (_BOOTSTRAP_START.parent, *_BOOTSTRAP_START.parents):
    if (_candidate / "site-tools/config/site-tools.json").exists():
        if str(_candidate) not in sys.path:
            sys.path.insert(0, str(_candidate))
        break

from studio.shared.python.studio_python_paths import ensure_studio_python_paths  # noqa: E402

ensure_studio_python_paths(__file__)

from docs_document_identity import is_immutable_doc_id  # noqa: E402
from docs_document_subjects import subject_from_record  # noqa: E402
from docs_document_location import canonical_document_viewer_url, management_document_viewer_url  # noqa: E402
from docs_local_links import encode_relative_target  # noqa: E402
from docs_workspace_config import generated_documents_path, load_docs_working_config, resolve_workspace_path  # noqa: E402
from catalogue.catalogue_source import normalize_text  # noqa: E402
from catalogue.catalogue_output_paths import catalogue_output_workspace  # noqa: E402
from catalogue.catalogue_report_inputs import WORK_SOURCES_PATH, SERIES_PATH, read_catalogue_report_input  # noqa: E402
from docs_artifact_locations import ArtifactLocation  # noqa: E402
from studio.shared.python.projects_directories import (  # noqa: E402
    PROJECTS_BASE_DIR_ENV,
    configured_projects_base,
    list_projects_directory,
    normalize_projects_directory_marker,
)

REPORT_SCHEMA_VERSION = "docs_project_state_report_v4"
WORKS_COLLECTION = "works"
GENERATION_PATTERN = re.compile(r"\Asha256:[0-9a-f]{64}\Z")


@dataclass(frozen=True)
class ProjectStatePaths:
    projects_base_dir: Path
    manage_manifest_path: Path
    collection_viewer_url: str
    catalogue_workspace: ArtifactLocation


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def default_project_state_paths(repo_root: Path) -> ProjectStatePaths:
    """Read document projections from the exact configured Working Works collection."""
    root = repo_root.resolve()
    scope = load_docs_working_config(root)
    collection = next((item for item in scope.collections if item.collection == WORKS_COLLECTION), None)
    if collection is None:
        raise ValueError(f"Docs Viewer collection is not configured: {WORKS_COLLECTION}")
    generated_root = resolve_workspace_path(root, generated_documents_path(collection))
    return ProjectStatePaths(
        projects_base_dir=configured_projects_base(),
        manage_manifest_path=generated_root / "manage-manifest.json",
        collection_viewer_url=canonical_document_viewer_url(collection.report_host_doc_id),
        catalogue_workspace=catalogue_output_workspace(root),
    )


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"{label} is unavailable") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must contain one JSON object")
    return payload


def _folder_keys(projects_base_dir: Path) -> list[str]:
    listing = list_projects_directory(
        "projects", environ={PROJECTS_BASE_DIR_ENV: str(projects_base_dir.resolve())}
    )
    records = listing.get("directories")
    if not isinstance(records, list):
        raise ValueError("Projects directory scan returned an invalid directory collection")
    keys: list[str] = []
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Projects directory scan returned an invalid directory record")
        key = normalize_projects_directory_marker(record.get("source_directory"))
        if len(key.split("/")) != 2 or not key.startswith("projects/"):
            raise ValueError("Project State scan must return immediate projects/ children only")
        if not key.removeprefix("projects/").startswith("."):
            keys.append(key)
    if len(keys) != len(set(keys)):
        raise ValueError("Project State scan returned duplicate folder keys")
    return sorted(keys, key=lambda value: (value.casefold(), value))


def _subject_documents(
    manifest: Mapping[str, Any], collection_viewer_url: str
) -> tuple[str, dict[tuple[str, str], list[dict[str, Any]]], int]:
    """Group valid Works subjects directly from private rows with configured links.

    Keep every document for a subject; unassigned documents contribute only to
    the document count, not report placement.
    """
    generation = str(manifest.get("subject_generation") or "").strip()
    manifest_rows = manifest.get("docs")
    if not GENERATION_PATTERN.fullmatch(generation) or not isinstance(manifest_rows, list):
        raise ValueError("Projects Manage manifest has an invalid subject projection")
    seen_doc_ids: set[str] = set()
    by_subject: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for raw_row in manifest_rows:
        if not isinstance(raw_row, dict):
            raise ValueError("Projects Manage manifest contains an invalid document record")
        row = dict(raw_row)
        doc_id = str(row.get("doc_id") or "").strip()
        if not is_immutable_doc_id(doc_id) or doc_id in seen_doc_ids:
            raise ValueError("Projects Manage manifest contains an invalid or duplicate doc_id")
        seen_doc_ids.add(doc_id)
        subject = subject_from_record(row, folder_supported=True)
        if subject["kind"] == "none":
            continue
        kind, key = subject["kind"], subject["key"]
        title = str(row.get("title") or "").strip()
        if not title:
            raise ValueError("Project document has invalid presentation")
        by_subject[(kind, key)].append(
            {
                "target": {"collection": WORKS_COLLECTION, "doc_id": doc_id},
                "title": title,
                "last_updated": str(row.get("last_updated") or "").strip(),
                "href": management_document_viewer_url(collection_viewer_url, doc_id, collection=True, collection_id=WORKS_COLLECTION),
                "declared_subject": {"kind": kind, "key": key},
            }
        )
    for values in by_subject.values():
        values.sort(key=lambda value: (value["title"].casefold(), value["title"], value["target"]["doc_id"]))
    return generation, dict(by_subject), len(seen_doc_ids)


def _catalogue_indexes(workspace: ArtifactLocation) -> tuple[
    dict[str, dict[str, str]],
    dict[str, list[dict[str, Any]]],
    dict[str, dict[str, Any]],
    dict[str, list[str]],
    int,
]:
    works = read_catalogue_report_input(workspace, WORK_SOURCES_PATH)
    series = read_catalogue_report_input(workspace, SERIES_PATH)
    series_by_id: dict[str, dict[str, str]] = {}
    for series_id, record in series.items():
        title = normalize_text(record["title"])
        series_by_id[series_id] = {"series_id": series_id, "title": title}

    works_by_folder: dict[str, list[dict[str, Any]]] = defaultdict(list)
    work_placement_by_id: dict[str, dict[str, Any]] = {}
    folder_keys_by_series: dict[str, set[str]] = defaultdict(set)
    for work_id, work in works.items():
        try:
            folder_key = normalize_projects_directory_marker(
                f"projects/{normalize_text(work.get('project_folder'))}"
            )
        except ValueError as exc:
            raise ValueError(f"Refreshed Work {work_id} has an invalid project_folder") from exc
        if len(folder_key.split("/")) != 2:
            raise ValueError(f"Refreshed Work {work_id} project_folder must identify one first-level project")
        series_ids = [work["series_id"]] if "series_id" in work else []
        report_work = {
            "target": {"family": "catalogue", "target_type": "work", "target_id": work_id},
            "series_ids": series_ids,
        }
        works_by_folder[folder_key].append(report_work)
        applicable_series_ids = [series_id for series_id in series_ids if series_id in series_by_id]
        work_placement_by_id[work_id] = {
            "folder_key": folder_key,
            "applicable_series_ids": applicable_series_ids,
        }
        for series_id in applicable_series_ids:
            folder_keys_by_series[series_id].add(folder_key)
    for values in works_by_folder.values():
        values.sort(key=lambda value: value["target"]["target_id"])
    return (
        series_by_id,
        dict(works_by_folder),
        work_placement_by_id,
        {
            series_id: sorted(folder_keys, key=lambda value: (value.casefold(), value))
            for series_id, folder_keys in folder_keys_by_series.items()
        },
        len(works),
    )


def _place_documents(
    folder_keys: list[str],
    documents_by_subject: Mapping[tuple[str, str], list[dict[str, Any]]],
    work_placement_by_id: Mapping[str, Mapping[str, Any]],
    folder_keys_by_series: Mapping[str, list[str]],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, int]]:
    scanned_folders = set(folder_keys)
    series_ids_by_folder: dict[str, set[str]] = defaultdict(set)
    for series_id, series_folder_keys in folder_keys_by_series.items():
        for folder_key in series_folder_keys:
            series_ids_by_folder[folder_key].add(series_id)

    placed_by_folder: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    matched_document_ids: set[str] = set()
    unmatched_document_ids: set[str] = set()
    recorded_only_folder_subjects: set[str] = set()

    for (kind, key), documents in sorted(documents_by_subject.items()):
        placements: list[tuple[str, list[str]]] = []
        if kind == "folder":
            if key in scanned_folders:
                placements.append((key, sorted(series_ids_by_folder.get(key, set()))))
            else:
                recorded_only_folder_subjects.add(key)
        elif kind == "work":
            work_placement = work_placement_by_id.get(key)
            folder_key = str(work_placement.get("folder_key") or "") if work_placement else ""
            if folder_key in scanned_folders:
                placements.append(
                    (folder_key, list(work_placement.get("applicable_series_ids") or []))
                )

        if not placements:
            unmatched_document_ids.update(document["target"]["doc_id"] for document in documents)
            continue

        for document in documents:
            doc_id = document["target"]["doc_id"]
            matched_document_ids.add(doc_id)
            for folder_key, applicable_series_ids in placements:
                placed_document = dict(document)
                placed_document["declared_subject"] = dict(document["declared_subject"])
                placed_document["applicable_series_ids"] = list(applicable_series_ids)
                existing = placed_by_folder[folder_key].get(doc_id)
                if existing is not None and existing != placed_document:
                    raise ValueError("Project document produced conflicting Folder placements")
                placed_by_folder[folder_key][doc_id] = placed_document

    documents_by_folder: dict[str, list[dict[str, Any]]] = {}
    for folder_key, documents in placed_by_folder.items():
        documents_by_folder[folder_key] = sorted(
            documents.values(),
            key=lambda value: (value["title"].casefold(), value["title"], value["target"]["doc_id"]),
        )
    return documents_by_folder, {
        "matched_document_count": len(matched_document_ids),
        "document_placement_count": sum(len(documents) for documents in documents_by_folder.values()),
        "unmatched_document_count": len(unmatched_document_ids),
        "recorded_only_document_folder_count": len(recorded_only_folder_subjects),
    }


def _state(document_count: int, work_count: int) -> str:
    if document_count and work_count:
        return "reconciled"
    if document_count:
        return "documents_only"
    if work_count:
        return "works_only"
    return "folder_only"


def _rows(
    folder_keys: list[str],
    documents_by_folder: Mapping[str, list[dict[str, Any]]],
    works_by_folder: Mapping[str, list[dict[str, Any]]],
    series_by_id: Mapping[str, Mapping[str, str]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for folder_key in folder_keys:
        documents = [dict(value) for value in documents_by_folder.get(folder_key, [])]
        works = [dict(value) for value in works_by_folder.get(folder_key, [])]
        work_ids_by_series: dict[str, set[str]] = defaultdict(set)
        issues: list[dict[str, Any]] = []
        for work in works:
            work_id = work["target"]["target_id"]
            for series_id in work["series_ids"]:
                if series_id in series_by_id:
                    work_ids_by_series[series_id].add(work_id)
                else:
                    issues.append({"state": "unknown_series", "work_id": work_id, "series_id": series_id})
        series = []
        for series_id in sorted(work_ids_by_series):
            work_ids = sorted(work_ids_by_series[series_id])
            series.append(
                {
                    "target": {"family": "catalogue", "target_type": "series", "target_id": series_id},
                    "title": series_by_id[series_id]["title"],
                    "href": f"/series/?series={quote(series_id)}",
                    "work_count": len(work_ids),
                    "work_ids": work_ids,
                }
            )
        issues.sort(key=lambda value: (value.get("work_id", ""), value.get("series_id", ""), value["state"]))
        rows.append(
            {
                "folder": {
                    "key": folder_key,
                    "label": f"/{folder_key.removeprefix('projects/')}",
                    "href": f"dlf-local:{encode_relative_target(folder_key)}",
                    "present": True,
                },
                "documents": documents,
                "works": works,
                "series": series,
                "series_issues": issues,
                "matched_document_count": len(documents),
                "matched_work_count": len(works),
                "states": {
                    "reconciliation": _state(len(documents), len(works)),
                    "documents": "multiple" if len(documents) > 1 else "one" if documents else "none",
                    "series": "incomplete" if issues else "complete" if works else "none",
                },
            }
        )
    return rows


def _generation(subject_generation: str, rows: list[dict[str, Any]]) -> str:
    source = json.dumps(
        {"subject_generation": subject_generation, "rows": rows},
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(source).hexdigest()


def validate_report(report: Mapping[str, Any]) -> None:
    rows = report.get("rows")
    summary = report.get("summary")
    inputs = report.get("inputs")
    if (
        report.get("schema_version") != REPORT_SCHEMA_VERSION
        or not GENERATION_PATTERN.fullmatch(str(report.get("generation") or ""))
        or not str(report.get("generated_at") or "").strip()
        or not isinstance(inputs, dict)
        or "scope" in inputs
        or "stage" in inputs
        or inputs.get("collection") != WORKS_COLLECTION
        or not GENERATION_PATTERN.fullmatch(str(inputs.get("subject_generation") or ""))
        or inputs.get("folder_scan") != {"root": "projects", "depth": "immediate_children"}
        or not isinstance(rows, list)
        or not isinstance(summary, dict)
    ):
        raise ValueError("Project State report failed envelope validation")
    row_keys = [row.get("folder", {}).get("key") for row in rows if isinstance(row, dict)]
    if len(row_keys) != len(rows) or len(row_keys) != len(set(row_keys)):
        raise ValueError("Project State report contains invalid or duplicate Folder rows")
    matched_document_ids: set[str] = set()
    document_placement_count = 0
    for row in rows:
        documents = row.get("documents")
        works = row.get("works")
        series = row.get("series")
        if not isinstance(documents, list) or not isinstance(works, list) or not isinstance(series, list):
            raise ValueError("Project State row contains invalid relationship collections")
        if (
            row["folder"].get("present") is not True
            or row.get("matched_document_count") != len(documents)
            or row.get("matched_work_count") != len(works)
        ):
            raise ValueError("Project State row failed relationship-count validation")
        if any(series_record["work_count"] != len(series_record["work_ids"]) for series_record in series):
            raise ValueError("Project State row failed Series-count validation")
        folder_key = row["folder"]["key"]
        series_ids = [series_record["target"]["target_id"] for series_record in series]
        work_by_id = {work["target"]["target_id"]: work for work in works}
        document_ids: set[str] = set()
        for document in documents:
            target = document.get("target")
            subject = document.get("declared_subject")
            applicable_series_ids = document.get("applicable_series_ids")
            doc_id = str(target.get("doc_id") or "") if isinstance(target, dict) else ""
            kind = str(subject.get("kind") or "") if isinstance(subject, dict) else ""
            key = str(subject.get("key") or "") if isinstance(subject, dict) else ""
            if (
                not doc_id
                or not is_immutable_doc_id(doc_id)
                or "scope" in target
                or "stage" in target
                or target.get("collection") != WORKS_COLLECTION
                or not str(document.get("title") or "").strip()
                or not str(document.get("href") or "").strip()
                or doc_id in document_ids
                or kind not in {"folder", "work"}
                or not key
                or not isinstance(applicable_series_ids, list)
                or any(not isinstance(series_id, str) or not series_id for series_id in applicable_series_ids)
                or len(applicable_series_ids) != len(set(applicable_series_ids))
                or any(series_id not in series_ids for series_id in applicable_series_ids)
            ):
                raise ValueError("Project State row failed document-placement validation")
            if kind == "folder":
                expected_series_ids = series_ids if key == folder_key else None
            else:
                work = work_by_id.get(key)
                expected_series_ids = (
                    [series_id for series_id in work["series_ids"] if series_id in series_ids]
                    if work is not None
                    else None
                )
            if expected_series_ids is None or applicable_series_ids != expected_series_ids:
                raise ValueError("Project State document provenance does not match its Folder row")
            document_ids.add(doc_id)
            matched_document_ids.add(doc_id)
        document_placement_count += len(documents)
    if (
        summary.get("matched_document_count") != len(matched_document_ids)
        or summary.get("document_placement_count") != document_placement_count
    ):
        raise ValueError("Project State summary failed document-count validation")


class ProjectStateProducer:
    def __init__(
        self,
        *,
        repo_root: Path,
        paths: ProjectStatePaths | None = None,
        clock: Callable[[], str] = utc_timestamp,
    ) -> None:
        self.repo_root = repo_root.resolve()
        self.paths = paths or default_project_state_paths(self.repo_root)
        self.clock = clock

    def build(self, *, generated_at: str) -> tuple[dict[str, Any], dict[str, Any]]:
        folder_keys = _folder_keys(self.paths.projects_base_dir)
        subject_generation, documents_by_subject, manifest_count = _subject_documents(
            _read_json(self.paths.manage_manifest_path, "Projects Manage manifest"),
            self.paths.collection_viewer_url,
        )
        (
            series_by_id,
            works_by_folder,
            work_placement_by_id,
            folder_keys_by_series,
            work_count,
        ) = _catalogue_indexes(self.paths.catalogue_workspace)
        documents_by_folder, document_diagnostics = _place_documents(
            folder_keys,
            documents_by_subject,
            work_placement_by_id,
            folder_keys_by_series,
        )
        rows = _rows(folder_keys, documents_by_folder, works_by_folder, series_by_id)
        generation = _generation(subject_generation, rows)
        diagnostics = {
            "scanned_folder_count": len(folder_keys),
            **document_diagnostics,
            "matched_work_count": sum(len(row["works"]) for row in rows),
            "series_membership_count": sum(series["work_count"] for row in rows for series in row["series"]),
            "series_issue_count": sum(len(row["series_issues"]) for row in rows),
            "recorded_only_work_folder_count": len(set(works_by_folder) - set(folder_keys)),
            "manifest_document_count": manifest_count,
            "canonical_work_count": work_count,
            "canonical_series_count": len(series_by_id),
        }
        report = {
            "schema_version": REPORT_SCHEMA_VERSION,
            "generation": generation,
            "generated_at": generated_at,
            "inputs": {
                "collection": WORKS_COLLECTION,
                "subject_generation": subject_generation,
                "folder_scan": {"root": "projects", "depth": "immediate_children"},
            },
            "summary": dict(diagnostics),
            "rows": rows,
        }
        validate_report(report)
        return report, diagnostics

    def run(self) -> dict[str, Any]:
        generated_at = self.clock()
        report, diagnostics = self.build(generated_at=generated_at)
        return {
            "report": report,
            "diagnostics": diagnostics,
        }


__all__ = [
    "WORKS_COLLECTION",
    "ProjectStatePaths",
    "ProjectStateProducer",
    "REPORT_SCHEMA_VERSION",
    "default_project_state_paths",
    "validate_report",
]
