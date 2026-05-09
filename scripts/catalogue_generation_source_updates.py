#!/usr/bin/env python3
"""Pure source-update planners for generated catalogue runs."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

try:
    from catalogue_generation_common import coerce_int, coerce_string, normalize_status
except ModuleNotFoundError:  # pragma: no cover - package import fallback
    from scripts.catalogue_generation_common import coerce_int, coerce_string, normalize_status


WORK_RECORD = "work"
WORK_DETAIL_RECORD = "work_detail"

NO_PROJECT_FOLDER_COLUMN = "no_project_folder_column"
MISSING_PROJECT_FOLDER = "missing_project_folder"


@dataclass(frozen=True)
class SourceUpdateWarning:
    """A structured warning emitted while planning source updates."""

    code: str
    record_kind: str
    record_id: str
    filename: Optional[str] = None
    source_path: Optional[Path] = None


@dataclass(frozen=True)
class SourceImagePathPlan:
    """Resolved source image path plus any warning needed to explain a miss."""

    source_path: Optional[Path]
    warning: Optional[SourceUpdateWarning] = None


@dataclass(frozen=True)
class SourceRecordUpdatePlan:
    """Mutable canonical source updates planned for one record."""

    record_kind: str
    record_id: str
    updates: Dict[str, Any]
    transition: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class DimensionUpdatePlan:
    """Dimension values read from source media and any canonical updates needed."""

    record_kind: str
    record_id: str
    width_px: Optional[int]
    height_px: Optional[int]
    updates: Dict[str, int]


def is_actionable_status(status_value: Any, *, refresh_published: bool) -> bool:
    status = normalize_status(status_value)
    if status == "draft":
        return True
    if status == "published" and refresh_published:
        return True
    return False


def plan_work_image_source_path(
    *,
    work_id: str,
    project_filename: Any,
    project_folder: Optional[str],
    project_subfolder: Optional[str],
    projects_root: Path,
    has_project_folder_column: bool,
) -> SourceImagePathPlan:
    filename = coerce_string(project_filename)
    if not filename:
        return SourceImagePathPlan(source_path=None)
    filename_path = Path(filename)
    if filename_path.is_absolute():
        return SourceImagePathPlan(source_path=filename_path)
    if project_folder:
        source_path = projects_root / project_folder
        if project_subfolder:
            source_path = source_path / project_subfolder
        return SourceImagePathPlan(source_path=source_path / filename)
    code = MISSING_PROJECT_FOLDER if has_project_folder_column else NO_PROJECT_FOLDER_COLUMN
    return SourceImagePathPlan(
        source_path=None,
        warning=SourceUpdateWarning(code=code, record_kind=WORK_RECORD, record_id=work_id, filename=filename),
    )


def plan_detail_image_source_path(
    *,
    detail_uid: str,
    project_filename: Any,
    work_project_folder: Optional[str],
    details_subfolder: Optional[str],
    projects_root: Path,
    has_project_folder_column: bool,
) -> SourceImagePathPlan:
    filename = coerce_string(project_filename)
    if work_project_folder:
        if filename:
            source_path = projects_root / work_project_folder
            if details_subfolder:
                source_path = source_path / details_subfolder
            return SourceImagePathPlan(source_path=source_path / filename)
    code = MISSING_PROJECT_FOLDER if has_project_folder_column else NO_PROJECT_FOLDER_COLUMN
    return SourceImagePathPlan(
        source_path=None,
        warning=SourceUpdateWarning(code=code, record_kind=WORK_DETAIL_RECORD, record_id=detail_uid, filename=filename),
    )


def plan_dimension_update(
    *,
    record_kind: str,
    record_id: str,
    current_width_px: Any,
    current_height_px: Any,
    source_width_px: Optional[int],
    source_height_px: Optional[int],
) -> DimensionUpdatePlan:
    if source_width_px is None or source_height_px is None:
        return DimensionUpdatePlan(
            record_kind=record_kind,
            record_id=record_id,
            width_px=coerce_int(current_width_px),
            height_px=coerce_int(current_height_px),
            updates={},
        )

    current_width = coerce_int(current_width_px)
    current_height = coerce_int(current_height_px)
    updates: Dict[str, int] = {}
    if current_width != source_width_px:
        updates["width_px"] = source_width_px
    if current_height != source_height_px:
        updates["height_px"] = source_height_px
    return DimensionUpdatePlan(
        record_kind=record_kind,
        record_id=record_id,
        width_px=source_width_px,
        height_px=source_height_px,
        updates=updates,
    )


def plan_work_publication_update(
    *,
    work_id: str,
    status: Any,
    today: dt.date,
    work_meta: Mapping[str, Any],
    series_title_by_id: Mapping[str, str],
) -> SourceRecordUpdatePlan:
    if normalize_status(status) != "draft":
        return SourceRecordUpdatePlan(record_kind=WORK_RECORD, record_id=work_id, updates={})

    today_iso = today.isoformat()
    series_ids = work_meta.get("series_ids")
    primary_series_id = series_ids[0] if isinstance(series_ids, list) and series_ids else ""
    transition = {
        "work_id": work_id,
        "title": coerce_string(work_meta.get("title")),
        "primary_series_id": primary_series_id,
        "series_title": series_title_by_id.get(primary_series_id) if primary_series_id else None,
        "published_date": today_iso,
    }
    return SourceRecordUpdatePlan(
        record_kind=WORK_RECORD,
        record_id=work_id,
        updates={"status": "published", "published_date": today_iso},
        transition=transition,
    )


def plan_detail_publication_update(*, detail_uid: str, status: Any, today: dt.date) -> SourceRecordUpdatePlan:
    if normalize_status(status) != "draft":
        return SourceRecordUpdatePlan(record_kind=WORK_DETAIL_RECORD, record_id=detail_uid, updates={})
    return SourceRecordUpdatePlan(
        record_kind=WORK_DETAIL_RECORD,
        record_id=detail_uid,
        updates={"status": "published", "published_date": today.isoformat()},
    )
