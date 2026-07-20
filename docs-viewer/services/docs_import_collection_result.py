#!/usr/bin/env python3
"""Grouped result shaping and Markdown reporting for Docs Import collections."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
import re
import sys
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[2]
SHARED_PYTHON_DIR = REPO_ROOT / "studio/shared/python"
if str(SHARED_PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_PYTHON_DIR))

from json_markdown_report import write_json_markdown_report  # noqa: E402
from docs_document_packages.workspace import marker_path  # noqa: E402


RESULT_STATUSES = ("created", "overwritten", "skipped", "failed", "not-attempted")
REPORT_SECTION_ORDER = (
    "package_identity",
    "target_scope",
    "timestamp",
    "source_mutation",
    "generation",
    "created",
    "overwritten",
    "skipped",
    "failed",
    "not_attempted",
    "warnings",
    "manual_copy_instructions",
)


def utc_timestamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _report_filename(timestamp: str, staged_filename: str) -> str:
    compact_timestamp = re.sub(r"[^0-9TZ]", "", timestamp)
    package_stem = re.sub(r"[^a-z0-9]+", "-", Path(staged_filename).stem.lower()).strip("-")
    return f"{compact_timestamp}-{package_stem or 'collection'}-import-result.md"


def group_collection_records(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups = {status: [] for status in RESULT_STATUSES}
    for record in records:
        status = str(record.get("status") or "").strip()
        if status in groups:
            groups[status].append(record)
    return groups


def collection_result_counts(groups: dict[str, list[dict[str, Any]]]) -> dict[str, int]:
    return {status.replace("-", "_"): len(groups.get(status) or []) for status in RESULT_STATUSES}


def safe_generation_result(generation: dict[str, Any]) -> dict[str, Any]:
    """Project generation status without commands, process output, or local paths."""

    rebuild = generation.get("rebuild") if isinstance(generation.get("rebuild"), dict) else None
    safe_rebuild = None
    if rebuild is not None:
        docs = rebuild.get("docs") if isinstance(rebuild.get("docs"), dict) else {}
        search = rebuild.get("search") if isinstance(rebuild.get("search"), dict) else {}
        safe_rebuild = {
            "ok": bool(rebuild.get("ok")),
            "docs": {
                "mode": str(docs.get("mode") or ""),
                "doc_ids": list(docs.get("doc_ids") or []),
            },
            "search": {
                "mode": str(search.get("mode") or ""),
                "doc_ids": list(search.get("doc_ids") or []),
            },
        }
    return {
        "status": str(generation.get("status") or "not-run"),
        "rebuild": safe_rebuild,
        "error": str(generation.get("error") or ""),
    }


def shape_collection_result(
    *,
    source_format: str,
    scope: str,
    staged_filename: str,
    package: dict[str, Any],
    records: list[dict[str, Any]],
    generation: dict[str, Any],
    warnings: list[dict[str, Any]],
    manual_copy_instructions: list[str],
    timestamp: str,
) -> dict[str, Any]:
    groups = group_collection_records(records)
    counts = collection_result_counts(groups)
    source_failed = bool(groups["failed"])
    applied_count = counts["created"] + counts["overwritten"]
    source_status = (
        "partial" if source_failed and applied_count
        else "failed" if source_failed
        else "completed"
    )
    safe_generation = safe_generation_result(generation)
    generation_status = safe_generation["status"]
    outcome = (
        "generation-failed" if generation_status == "failed"
        else "partial" if source_status == "partial"
        else "failed" if source_status == "failed"
        else "completed"
    )
    return {
        "ok": True,
        "collection": True,
        "source_format": source_format,
        "scope": scope,
        "staged_filename": staged_filename,
        "preview_only": False,
        "confirmed": True,
        "outcome": outcome,
        "timestamp": timestamp,
        "package": dict(package),
        "source_mutation": {
            "status": source_status,
            "applied": applied_count,
            "failed": counts["failed"],
            "not_attempted": counts["not_attempted"],
        },
        "generation": safe_generation,
        "records": records,
        "groups": groups,
        "counts": counts,
        "warnings": warnings,
        "manual_copy_instructions": manual_copy_instructions,
        "report_path": "",
    }


def collection_report_payload(result: dict[str, Any]) -> dict[str, Any]:
    groups = result.get("groups") if isinstance(result.get("groups"), dict) else {}
    payload: dict[str, Any] = {
        "package_identity": {
            "staged_filename": result.get("staged_filename", ""),
            "export_id": (result.get("package") or {}).get("export_id", ""),
            "source_sha256": (result.get("package") or {}).get("source_sha256", ""),
        },
        "target_scope": result.get("scope", ""),
        "timestamp": result.get("timestamp", ""),
        "source_mutation": result.get("source_mutation", {}),
        "generation": result.get("generation", {}),
    }
    for status in RESULT_STATUSES:
        records = groups.get(status) if isinstance(groups.get(status), list) else []
        if records:
            payload[status.replace("-", "_")] = records
    if result.get("warnings"):
        payload["warnings"] = result["warnings"]
    if result.get("manual_copy_instructions"):
        payload["manual_copy_instructions"] = result["manual_copy_instructions"]
    return payload


def write_collection_result_report(
    result: dict[str, Any],
    *,
    staging_root: Path,
    workspace_root: Path,
    writer: Callable[..., Path] = write_json_markdown_report,
) -> str:
    results_root = staging_root / "results"
    target = results_root / _report_filename(
        str(result.get("timestamp") or utc_timestamp()),
        str(result.get("staged_filename") or "collection.jsonl"),
    )
    written = writer(
        target,
        collection_report_payload(result),
        title="Docs Import collection result",
        section_order=REPORT_SECTION_ORDER,
    )
    return marker_path(written, workspace_root=workspace_root)


__all__ = [
    "REPORT_SECTION_ORDER",
    "RESULT_STATUSES",
    "collection_report_payload",
    "collection_result_counts",
    "group_collection_records",
    "shape_collection_result",
    "safe_generation_result",
    "utc_timestamp",
    "write_collection_result_report",
]
