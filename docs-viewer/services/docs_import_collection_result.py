#!/usr/bin/env python3
"""Grouped result shaping for Docs Import collections."""

from __future__ import annotations

import datetime as dt
from typing import Any


RESULT_STATUSES = ("created", "overwritten", "failed", "not-attempted")


def utc_timestamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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
    }


__all__ = [
    "RESULT_STATUSES",
    "collection_result_counts",
    "group_collection_records",
    "shape_collection_result",
    "safe_generation_result",
    "utc_timestamp",
]
