#!/usr/bin/env python3
"""Source record projection for Docs Data Sharing document workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from docs_scope_config import path_label


@dataclass(frozen=True)
class DataSharingDocsSourceRecord:
    doc_id: str
    scope: str
    title: str
    published: bool
    summary: str
    added_date: str
    last_updated: str
    parent_id: str
    parent_title: str
    viewable: bool
    ui_status: str
    source_path: str
    viewer_url: str
    content_text_length: int


def front_matter_bool(front_matter: dict[str, Any], key: str, default: bool) -> bool:
    if key not in front_matter:
        return default
    value = front_matter[key]
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() not in {"false", "0", "no", "off"}


def source_path_for_record(repo_root: Path, source_root: Path, doc: Any) -> str:
    path = (source_root / doc.source_path).resolve()
    return path_label(repo_root, path)


def source_record_from_doc(
    *,
    repo_root: Path,
    source_root: Path,
    scope: str,
    doc: Any,
    parent_title: str,
    published: bool,
    content_text_length: int,
) -> DataSharingDocsSourceRecord:
    return DataSharingDocsSourceRecord(
        doc_id=doc.doc_id,
        scope=scope,
        title=doc.title,
        published=published,
        summary=doc.summary,
        added_date=doc.added_date,
        last_updated=doc.last_updated,
        parent_id=doc.parent_id,
        parent_title=parent_title,
        viewable=doc.viewable,
        ui_status=doc.ui_status,
        source_path=source_path_for_record(repo_root, source_root, doc),
        viewer_url=doc.viewer_url,
        content_text_length=content_text_length,
    )
