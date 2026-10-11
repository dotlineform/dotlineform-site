"""Generate replaceable Catalogue JSON; canonical records and public sites are never written."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import quote

from catalogue import catalogue_generation_indexes as indexes
from catalogue import catalogue_generation_records as projection
from catalogue.catalogue_compact_indexes import build_compact_index
from catalogue.catalogue_galleries import CatalogueGalleries
from catalogue.catalogue_generation_common import compact_json_object
from catalogue.catalogue_media_policy import catalogue_media_policy
from catalogue.catalogue_series_galleries import CatalogueSeriesGalleries
from catalogue.catalogue_series_galleries_index import series_gallery_links, series_galleries_index_payload
from catalogue.catalogue_series_galleries_report import METADATA_PATH as SERIES_GALLERIES_REPORT_PATH, series_galleries_report_payload
from catalogue.catalogue_source import CatalogueSourceRecords
from catalogue.catalogue_shared_changes import WORK_INDEX, GALLERY_INDEX, RELATIONSHIP_INDEX, RELATIONSHIP_REPORT, WORK_DOCUMENT_COVERAGE_MANIFEST
from catalogue.catalogue_work_document_coverage import work_document_coverage_manifest
from catalogue.catalogue_report_inputs import INPUT_SCHEMAS, catalogue_report_input_payloads


def catalogue_payloads(
    repo_root: Path, records: CatalogueSourceRecords, galleries: CatalogueGalleries,
    pairs: CatalogueSeriesGalleries, *, timestamp: str, work_ids: set[str] | None = None,
    gallery_ids: set[str] | None = None, shared_outputs: set[str] | None = None,
) -> dict[str, dict[str, Any]]:
    """Project selected loaded inputs; Save and complete maintenance own audits."""
    supported_shared = {"media-config.json", WORK_INDEX, GALLERY_INDEX, RELATIONSHIP_INDEX, RELATIONSHIP_REPORT, WORK_DOCUMENT_COVERAGE_MANIFEST, *INPUT_SCHEMAS}
    shared = supported_shared if shared_outputs is None else shared_outputs
    if shared - supported_shared:
        raise ValueError("Catalogue generation selected an output without a builder")
    selected_galleries = set(galleries.galleries) if gallery_ids is None else gallery_ids
    if selected_galleries - galleries.galleries.keys() or (work_ids is not None and work_ids - records.works.keys()):
        raise ValueError("Catalogue generation selected an unavailable current identity")
    works_by_gallery: dict[str, list[str]] = {gid: [] for gid in selected_galleries}
    if selected_galleries:
        for wid, ids in galleries.works.items():
            for gid in ids:
                if gid in works_by_gallery:
                    works_by_gallery[gid].append(wid)
    payloads: dict[str, dict[str, Any]] = {}
    media_config = None
    if "media-config.json" in shared:
        payloads["media-config.json"] = catalogue_media_policy(repo_root, timestamp=timestamp)
    projection_ids = records.works.keys() if work_ids is None else sorted(work_ids)
    for wid in projection_ids:
        source = records.works[wid]
        work = compact_json_object({"work_id": wid, **projection.build_work_record_projection(source)})
        if source.get("series_id"):
            work["series_id"] = source["series_id"]
        if source.get("links"):
            work["links"] = source["links"]
        if source.get("downloads"):
            if media_config is None:
                media_config = json.loads((repo_root / "site-tools/config/site-tools.json").read_text())["media"]
            work["downloads"] = [
                {"filename": download["filename"], "label": download["label"],
                 "url": f"{media_config['base'].rstrip('/')}/{media_config['files_works'].strip('/')}/{quote(download['filename'], safe='')}"}
                for download in source["downloads"]
            ]
        work["galleries"] = [dict(galleries.galleries[gid]) for gid in sorted(galleries.works.get(wid, []))]
        payloads[f"works/index/{wid}.json"] = projection.build_work_json_payload(
            work_record=work, generated_at_utc=timestamp,
        )
    for gid in sorted(selected_galleries):
        source = galleries.galleries[gid]
        payloads[f"galleries/index/{gid}.json"] = projection.build_gallery_json_payload(
            gallery_id=gid, gallery_record=source,
            member_works=indexes.build_member_work_records(work_records=records.works, work_ids=works_by_gallery[gid]), generated_at_utc=timestamp,
        )
    if WORK_INDEX in shared:
        payloads[WORK_INDEX] = build_compact_index("works", records.works, timestamp=timestamp)
    if GALLERY_INDEX in shared:
        payloads[GALLERY_INDEX] = build_compact_index("galleries", galleries.galleries, timestamp=timestamp)
    series_galleries = {
        sid: series_gallery_links(sid, records.series, galleries.galleries, pairs)
        for sid in sorted(records.series)
    } if {RELATIONSHIP_INDEX, RELATIONSHIP_REPORT} & shared else {}
    if RELATIONSHIP_INDEX in shared:
        payloads[RELATIONSHIP_INDEX] = series_galleries_index_payload(series_galleries, timestamp=timestamp)
    if RELATIONSHIP_REPORT in shared:
        payloads[SERIES_GALLERIES_REPORT_PATH] = series_galleries_report_payload(
            records.series, galleries.galleries, series_galleries, timestamp=timestamp,
        )
    if WORK_DOCUMENT_COVERAGE_MANIFEST in shared:
        payloads[WORK_DOCUMENT_COVERAGE_MANIFEST] = work_document_coverage_manifest(
            records.series, records.works, timestamp=timestamp,
        )
    payloads.update(catalogue_report_input_payloads(
        records.works, records.series, timestamp=timestamp, selected=shared & INPUT_SCHEMAS.keys(),
    ))
    return payloads


def same_generated_content(actual: Any, expected: dict[str, Any]) -> bool:
    """Ignore only the generation timestamp when comparing complete output."""
    if (not isinstance(actual, dict) or not isinstance(actual.get("header"), dict)
            or not isinstance(actual["header"].get("generated_at_utc"), str)
            or not actual["header"]["generated_at_utc"]):
        return False
    actual_content = {**actual, "header": {key: value for key, value in actual["header"].items() if key != "generated_at_utc"}}
    expected_content = {**expected, "header": {key: value for key, value in expected["header"].items() if key != "generated_at_utc"}}
    return actual_content == expected_content
