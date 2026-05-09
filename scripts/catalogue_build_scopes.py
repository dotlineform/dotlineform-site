"""Scoped catalogue build planning helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Sequence

import catalogue_build_media as build_media
from catalogue_source import DEFAULT_SOURCE_DIR, normalize_status, records_from_json_source, slug_id
from moment_sources import (
    CATALOGUE_MOMENT_PROSE_REL_DIR,
    MOMENT_METADATA_FILENAME,
    load_moment_metadata_records,
    normalize_moment_filename,
    normalize_moment_metadata_record,
    validate_moment_metadata_record,
)
from pipeline_config import load_pipeline_config, source_moments_images_subdir
from series_ids import normalize_series_id


PIPELINE_CONFIG = load_pipeline_config(Path(__file__))
DEFAULT_ARTIFACTS = [
    "work-pages",
    "work-json",
    "series-pages",
    "series-index-json",
    "works-index-json",
    "recent-index-json",
]
DEFAULT_MOMENT_ARTIFACTS = ["moments"]

ReadinessBuilder = Callable[..., Dict[str, Any]]
MomentPreviewBuilder = Callable[..., Dict[str, Any]]
MomentMetadataBuilder = Callable[..., Dict[str, Any]]


def _default_work_readiness_builder() -> ReadinessBuilder:
    return build_media.build_work_readiness


def _default_detail_readiness_builder() -> ReadinessBuilder:
    return build_media.build_detail_readiness


def _default_series_readiness_builder() -> ReadinessBuilder:
    return build_media.build_series_readiness


def _default_moment_readiness_builder() -> ReadinessBuilder:
    return build_media.build_moment_readiness


def _default_moment_preview_builder() -> MomentPreviewBuilder:
    return preview_moment_source


def _default_moment_metadata_builder() -> MomentMetadataBuilder:
    return build_moment_import_metadata


def normalize_series_ids(values: Iterable[Any]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in values:
        text = str(raw or "").strip()
        if not text:
            continue
        for part in text.split(","):
            token = str(part or "").strip()
            if not token:
                continue
            series_id = normalize_series_id(token)
            if series_id in seen:
                continue
            seen.add(series_id)
            out.append(series_id)
    return out


def normalize_work_ids(values: Iterable[Any]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in values:
        text = str(raw or "").strip()
        if not text:
            continue
        for part in text.split(","):
            token = str(part or "").strip()
            if not token:
                continue
            work_id = slug_id(token)
            if work_id in seen:
                continue
            seen.add(work_id)
            out.append(work_id)
    return out


def validate_buildable_series_scope(records: Any, series_ids: Sequence[str]) -> None:
    work_series_ids_by_work_id: dict[str, list[str]] = {}
    for work_id, work_record in records.works.items():
        raw_series_ids = work_record.get("series_ids", [])
        if isinstance(raw_series_ids, list):
            work_series_ids_by_work_id[work_id] = normalize_series_ids(raw_series_ids)
        else:
            work_series_ids_by_work_id[work_id] = []

    errors: list[str] = []
    for series_id in series_ids:
        series_record = records.series.get(series_id)
        if not isinstance(series_record, dict):
            errors.append(f"series {series_id}: not found in source records")
            continue
        status = normalize_status(series_record.get("status"))
        if status != "published":
            errors.append(f"series {series_id}: status must be published for runtime build")
            continue
        raw_primary_work_id = str(series_record.get("primary_work_id") or "").strip()
        if not raw_primary_work_id:
            errors.append(f"series {series_id}: missing primary_work_id for runtime build")
            continue
        primary_work_id = slug_id(raw_primary_work_id)
        primary_work_record = records.works.get(primary_work_id)
        if not isinstance(primary_work_record, dict):
            errors.append(f"series {series_id}: primary_work_id {primary_work_id!r} not found in works")
            continue
        if normalize_status(primary_work_record.get("status")) != "published":
            errors.append(f"series {series_id}: primary_work_id {primary_work_id!r} is not a published work")
            continue
        if series_id not in work_series_ids_by_work_id.get(primary_work_id, []):
            errors.append(f"series {series_id}: primary_work_id {primary_work_id!r} is not in that work's series_ids")

    if errors:
        raise ValueError("series build precondition failed: " + "; ".join(errors[:20]))


def build_scope_for_work(
    source_dir: Path,
    work_id: str,
    extra_series_ids: Sequence[Any] | None = None,
    *,
    detail_uid: str = "",
    env: Dict[str, str] | None = None,
    work_readiness_builder: ReadinessBuilder | None = None,
    detail_readiness_builder: ReadinessBuilder | None = None,
) -> Dict[str, Any]:
    normalized_work_id = slug_id(work_id)
    records = records_from_json_source(source_dir)
    work_record = records.works.get(normalized_work_id)
    if not isinstance(work_record, dict):
        raise ValueError(f"work_id not found: {normalized_work_id}")
    if normalize_status(work_record.get("status")) != "published":
        raise ValueError(f"work {normalized_work_id}: status must be published for runtime build")

    current_series_ids: list[str] = []
    for series_id in normalize_series_ids(work_record.get("series_ids", [])):
        series_record = records.series.get(series_id)
        if isinstance(series_record, dict) and normalize_status(series_record.get("status")) == "published":
            current_series_ids.append(series_id)
    requested_extra_series_ids = normalize_series_ids(extra_series_ids or [])
    series_ids = normalize_series_ids([*current_series_ids, *requested_extra_series_ids])
    validate_buildable_series_scope(records, series_ids)
    scope = {
        "work_ids": [normalized_work_id],
        "series_ids": series_ids,
        "current_series_ids": current_series_ids,
        "extra_series_ids": [series_id for series_id in requested_extra_series_ids if series_id not in current_series_ids],
        "generate_only": list(DEFAULT_ARTIFACTS),
        "rebuild_search": True,
        "search_scope": "catalogue",
        "source_mode": "json",
        "source_dir": str(source_dir),
        "refresh_published": True,
        "summary": summarize_scope([normalized_work_id], series_ids),
    }
    work_readiness = work_readiness_builder or _default_work_readiness_builder()
    readiness = work_readiness(records, normalized_work_id, env=env)
    if detail_uid:
        normalized_detail_uid = str(detail_uid or "").strip()
        detail_readiness = detail_readiness_builder or _default_detail_readiness_builder()
        readiness["items"].extend(detail_readiness(records, normalized_detail_uid, env=env).get("items", []))
        scope["detail_uid"] = normalized_detail_uid
    scope["readiness"] = readiness
    return scope


def build_scope_for_series(
    source_dir: Path,
    series_id: str,
    extra_work_ids: Sequence[Any] | None = None,
    *,
    env: Dict[str, str] | None = None,
    series_readiness_builder: ReadinessBuilder | None = None,
) -> Dict[str, Any]:
    normalized_series_id = normalize_series_id(series_id)
    records = records_from_json_source(source_dir)
    series_record = records.series.get(normalized_series_id)
    if not isinstance(series_record, dict):
        raise ValueError(f"series_id not found: {normalized_series_id}")
    if normalize_status(series_record.get("status")) != "published":
        raise ValueError(f"series {normalized_series_id}: status must be published for runtime build")

    current_work_ids: list[str] = []
    for work_id, work_record in records.works.items():
        if normalize_status(work_record.get("status")) != "published":
            continue
        series_ids = work_record.get("series_ids", [])
        if isinstance(series_ids, list) and normalized_series_id in normalize_series_ids(series_ids):
            current_work_ids.append(work_id)
    current_work_ids = sorted(current_work_ids)

    requested_extra_work_ids = normalize_work_ids(extra_work_ids or [])
    work_ids = sorted({*current_work_ids, *requested_extra_work_ids})
    validate_buildable_series_scope(records, [normalized_series_id])
    scope = {
        "kind": "series",
        "work_ids": work_ids,
        "series_ids": [normalized_series_id],
        "current_work_ids": current_work_ids,
        "extra_work_ids": [work_id for work_id in requested_extra_work_ids if work_id not in current_work_ids],
        "generate_only": list(DEFAULT_ARTIFACTS),
        "rebuild_search": True,
        "search_scope": "catalogue",
        "source_mode": "json",
        "source_dir": str(source_dir),
        "refresh_published": True,
        "summary": summarize_scope(work_ids, [normalized_series_id]),
    }
    readiness = series_readiness_builder or _default_series_readiness_builder()
    scope["readiness"] = readiness(records, normalized_series_id, env=env)
    return scope


def build_scope_for_moment(
    repo_root: Path,
    moment_file: str,
    *,
    metadata: Dict[str, Any] | None = None,
    force: bool = False,
    env: Dict[str, str] | None = None,
    moment_preview_builder: MomentPreviewBuilder | None = None,
    moment_metadata_builder: MomentMetadataBuilder | None = None,
    moment_readiness_builder: ReadinessBuilder | None = None,
) -> Dict[str, Any]:
    preview_builder = moment_preview_builder or _default_moment_preview_builder()
    metadata_builder = moment_metadata_builder or _default_moment_metadata_builder()
    preview = preview_builder(repo_root, moment_file, metadata=metadata, env=env)
    if not preview.get("valid"):
        errors = preview.get("errors") or []
        raise ValueError("; ".join(str(error) for error in errors) or "moment source preview failed")
    moment_id = str(preview.get("moment_id") or "").strip().lower()
    moment_metadata = metadata_builder(repo_root / DEFAULT_SOURCE_DIR, moment_id, metadata)
    readiness_builder = moment_readiness_builder or _default_moment_readiness_builder()
    return {
        "kind": "moment",
        "moment_ids": [moment_id],
        "moment_file": str(preview.get("moment_file") or ""),
        "moment_metadata": moment_metadata,
        "work_ids": [],
        "series_ids": [],
        "generate_only": list(DEFAULT_MOMENT_ARTIFACTS),
        "rebuild_search": True,
        "search_scope": "catalogue",
        "source_mode": "moment-source",
        "summary": summarize_moment_scope([moment_id]),
        "effective_force": bool(force),
        "refresh_published": True,
        "preview": preview,
        "readiness": readiness_builder(repo_root, moment_file, metadata=moment_metadata, env=env),
    }


def summarize_scope(work_ids: Sequence[str], series_ids: Sequence[str]) -> str:
    work_text = ", ".join(work_ids) if work_ids else "none"
    series_text = ", ".join(series_ids) if series_ids else "none"
    return f"Build works [{work_text}], series [{series_text}], aggregate indexes, and catalogue search."


def summarize_moment_scope(moment_ids: Sequence[str]) -> str:
    moment_text = ", ".join(moment_ids) if moment_ids else "none"
    return f"Build moments [{moment_text}], rebuild the moments index, and rebuild catalogue search."


def build_moment_import_metadata(
    source_dir: Path,
    moment_id: str,
    metadata: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    records = load_moment_metadata_records(source_dir)
    existing = records.get(moment_id, {})
    merged = {**existing, **(metadata or {}), "moment_id": moment_id}
    return normalize_moment_metadata_record(moment_id, merged)


def preview_moment_source(
    repo_root: Path,
    moment_file: str,
    *,
    metadata: Dict[str, Any] | None = None,
    staged: bool = False,
    env: Dict[str, str] | None = None,
) -> Dict[str, Any]:
    filename = normalize_moment_filename(moment_file)
    moment_id = filename[:-3]
    source_dir = repo_root / DEFAULT_SOURCE_DIR
    staging_path = repo_root / build_media.MOMENT_PROSE_STAGING_REL_DIR / filename
    target_path = repo_root / CATALOGUE_MOMENT_PROSE_REL_DIR / filename
    source_path = staging_path if staged else target_path
    source_rel_path = (build_media.MOMENT_PROSE_STAGING_REL_DIR if staged else CATALOGUE_MOMENT_PROSE_REL_DIR) / filename
    metadata_record = build_moment_import_metadata(source_dir, moment_id, metadata)
    preview: Dict[str, Any] = {
        "kind": "moment",
        "moment_id": moment_id,
        "moment_file": filename,
        "source_path": str(source_rel_path),
        "staging_path": str(build_media.MOMENT_PROSE_STAGING_REL_DIR / filename),
        "target_path": str(CATALOGUE_MOMENT_PROSE_REL_DIR / filename),
        "metadata_path": str(DEFAULT_SOURCE_DIR / MOMENT_METADATA_FILENAME),
        "public_url": f"/moments/{moment_id}/",
        "generated_page_path": str(Path("_moments") / f"{moment_id}.md"),
        "generated_json_path": str(Path("assets/moments/index") / f"{moment_id}.json"),
        "moments_index_path": "assets/data/moments_index.json",
        "search_scope": "catalogue",
        "source_exists": source_path.exists(),
        "target_exists": target_path.exists(),
        "errors": [],
        "valid": False,
        "title": metadata_record.get("title") or "",
        "status": metadata_record.get("status") or "",
        "date": metadata_record.get("date") or "",
        "date_display": metadata_record.get("date_display") or "",
        "published_date": metadata_record.get("published_date") or "",
        "image_file": metadata_record.get("source_image_file") or f"{moment_id}.jpg",
        "image_alt": metadata_record.get("image_alt") or "",
    }

    if not source_path.exists():
        preview["errors"] = [f"Missing {'staged ' if staged else ''}moment prose file: {source_rel_path}"]
        return preview

    projects_base_dir, _availability_error = build_media.detect_projects_base_dir_optional(env)
    source_image_file = str(metadata_record.get("source_image_file") or f"{moment_id}.jpg")
    source_image_path = (projects_base_dir / source_moments_images_subdir(PIPELINE_CONFIG) / source_image_file) if projects_base_dir else None
    preview["source_image_path"] = str(Path("moments") / "images" / Path(source_image_file).name)
    preview["source_image_exists"] = bool(source_image_path and source_image_path.exists())
    preview["generated_page_exists"] = (repo_root / "_moments" / f"{moment_id}.md").exists()
    preview["generated_json_exists"] = (repo_root / "assets/moments/index" / f"{moment_id}.json").exists()
    preview["in_moments_index"] = False

    moments_index_path = repo_root / "assets/data/moments_index.json"
    if moments_index_path.exists():
        try:
            moments_index_text = moments_index_path.read_text(encoding="utf-8")
            payload = json.loads(moments_index_text)
            moments_map = payload.get("moments") if isinstance(payload, dict) else {}
            moment_index_ids = (
                {str(key).strip().lower() for key in moments_map.keys()}
                if isinstance(moments_map, dict)
                else set()
            )
            preview["in_moments_index"] = moment_id in moment_index_ids
            if not preview["in_moments_index"]:
                preview["in_moments_index"] = f'"{moment_id}":' in moments_index_text
        except Exception:
            preview["in_moments_index"] = False

    errors = validate_moment_metadata_record(metadata_record)
    preview["errors"] = errors
    preview["valid"] = not errors
    preview["effective_force"] = False
    preview["refresh_published"] = bool(metadata_record.get("status") == "published")
    source_label = build_media.MOMENT_PROSE_STAGING_REL_DIR / filename if staged else CATALOGUE_MOMENT_PROSE_REL_DIR / filename
    action = "Import" if staged else "Build"
    preview["summary"] = f"{action} moment {moment_id} from {source_label}, rebuild the moment payloads, and rebuild catalogue search."
    return preview
