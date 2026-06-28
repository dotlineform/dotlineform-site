#!/usr/bin/env python3
"""Returned document record normalization."""

from __future__ import annotations

import copy
from typing import Any

from docs_returned_import_common import (
    KNOWN_RECORD_FIELDS,
    issue,
    normalize_id_title_pairs,
    normalize_string_list,
    normalize_text,
)

def normalize_record(row: dict[str, Any], record_index: int, line: int | None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    doc_id = normalize_text(row.get("doc_id"))
    title = normalize_text(row.get("title"))
    issues: list[dict[str, Any]] = []
    if not doc_id:
        issues.append(issue("warning", "missing_doc_id", "record is missing doc_id", record_index=record_index, line=line))
    if not title:
        issues.append(issue("warning", "missing_title", "record is missing title", record_index=record_index, line=line, doc_id=doc_id))

    normalized: dict[str, Any] = {
        "record_index": record_index,
        "doc_id": doc_id,
        "title": title,
        "parent_id": normalize_text(row.get("parent_id")),
        "metadata": {},
        "relationships": {},
        "unknown_metadata": {},
    }
    if line is not None:
        normalized["line"] = line

    for key in ["parent_title", "last_updated"]:
        if key in row:
            normalized["metadata"][key] = normalize_text(row.get(key))
    for key in ["summary", "current_summary"]:
        if key in row:
            normalized["metadata"][key] = str(row.get(key) or "")
    for key in ["viewable"]:
        if key in row:
            normalized["metadata"][key] = row.get(key)
    if "headings" in row:
        normalized["metadata"]["headings"] = normalize_string_list(row.get("headings"))
    if "source_text" in row:
        normalized["metadata"]["source_text"] = str(row.get("source_text") or "")

    for key in ["ancestors", "children"]:
        if key in row:
            normalized["relationships"][key] = normalize_id_title_pairs(row.get(key))

    unknown = {
        key: copy.deepcopy(value)
        for key, value in row.items()
        if key not in KNOWN_RECORD_FIELDS and key != "_source_line"
    }
    normalized["unknown_metadata"] = unknown
    return normalized, issues
