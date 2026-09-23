"""Plan the one-time conversion of canonical Details to independent Works."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from catalogue.catalogue_galleries import CatalogueGalleries, validate_galleries
from catalogue.catalogue_source import (
    CatalogueSourceRecords, WORK_FIELDS, payload_for_map, load_json_file, load_work_details_flat_payload,
    validate_source_records,
)


def source_fingerprints(source_dir: Path) -> dict[str, str]:
    paths = [source_dir / "works.json", source_dir / "series.json",
             *sorted((source_dir / "work_details").glob("*.json"))]
    return {str(path.relative_to(source_dir)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}


def plan_gallery_conversion(source_dir: Path) -> dict[str, Any]:
    """Allocate globally, in exact Detail/section ID order; write nothing."""
    for name in ("galleries.json", "galleries-by-work.json"):
        if (source_dir / name).exists():
            raise ValueError(f"Gallery conversion already has a destination: {name}")
    fingerprints = source_fingerprints(source_dir)
    # The old Detail model is read only here, never as a runtime fallback.
    detail_payload = load_work_details_flat_payload(source_dir / "work_details")
    source = CatalogueSourceRecords(
        works=load_json_file(source_dir / "works.json")["works"],
        series={sid: {key: value for key, value in record.items() if key != "sort_fields"}
                for sid, record in load_json_file(source_dir / "series.json")["series"].items()},
        work_details=detail_payload["work_details"],
        work_detail_sections=detail_payload["work_detail_sections"],
    )
    errors = validate_source_records(source)
    if errors:
        raise ValueError("Invalid conversion source: " + "; ".join(errors[:20]))
    if not source.work_details or not source.work_detail_sections:
        raise ValueError("Conversion requires canonical Details and sections")
    for wid, work in source.works.items():
        if work.get("series_id") not in source.series:
            raise ValueError(f"Work {wid} requires exactly one known Series")
    galleries = {sid: {"gallery_id": sid, "title": series["title"]} for sid, series in source.series.items()}
    memberships = {wid: [work["series_id"]] for wid, work in source.works.items()}
    next_gallery = max(int(gid) for gid in galleries) + 1
    sections = {}
    for offset, (section_id, section) in enumerate(sorted(source.work_detail_sections.items())):
        gid = f"{next_gallery + offset:03d}"
        parent = source.works[section["work_id"]]
        galleries[gid] = {"gallery_id": gid, "title": f"{parent['title']} ({section['section_title']})"}
        sections[section_id] = gid
    next_work = max(int(wid) for wid in source.works) + 1
    if next_work + len(source.work_details) - 1 > 99999:
        raise ValueError("Conversion would exhaust five-digit Work IDs")
    works = dict(source.works)
    conversions = {}
    for offset, (uid, detail) in enumerate(sorted(source.work_details.items())):
        wid = f"{next_work + offset:05d}"
        parent = source.works[detail["work_id"]]
        section = source.work_detail_sections[detail["section_id"]]
        work = {key: None for key in WORK_FIELDS}
        work["work_id"] = wid
        for key in ("series_id", "media_source_id", "project_folder", "year", "year_display", "medium_type", "medium_caption"):
            if key in parent:
                work[key] = parent[key]
            else:
                work.pop(key, None)
        work["project_subfolder"] = section.get("details_subfolder")
        for key in ("project_filename", "media_version", "title", "width_px", "height_px"):
            work[key] = detail.get(key)
        for key in ("media_version", "width_px", "height_px"):
            if type(work[key]) is not int or work[key] <= 0:
                raise ValueError(f"Detail {uid} has no valid {key}")
        if not work["project_filename"]:
            raise ValueError(f"Detail {uid} has no project filename")
        works[wid] = work
        memberships[wid] = [sections[detail["section_id"]]]
        conversions[uid] = {"work_id": wid, "gallery_id": memberships[wid][0]}
    series = {sid: {key: value for key, value in record.items() if key != "sort_fields"}
              for sid, record in source.series.items()}
    converted = CatalogueSourceRecords(works=works, series=series, work_details={}, work_detail_sections={})
    errors = validate_source_records(converted)
    if errors:
        raise ValueError("Invalid converted source: " + "; ".join(errors[:20]))
    gallery_data = CatalogueGalleries(galleries=galleries, works=memberships)
    validate_galleries(gallery_data, works)
    if fingerprints != source_fingerprints(source_dir):
        raise ValueError("Canonical source changed during conversion planning")
    return {
        "schema": "catalogue_gallery_conversion_v1",
        "source_sha256": fingerprints,
        "counts": {"original_works": len(source.works), "converted_details": len(conversions),
                   "works": len(works), "series": len(series), "galleries": len(galleries)},
        "details_to_works": conversions,
        "sections_to_galleries": sections,
        "canonical": {"works.json": payload_for_map("works", works),
                      "series.json": payload_for_map("series", series), **gallery_data.payloads()},
        "retire_source_files": [name for name in fingerprints if name.startswith("work_details/")],
    }


def write_conversion_plan(plan: dict[str, Any], destination: Path) -> None:
    """Write review material only, outside the canonical source directory."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
