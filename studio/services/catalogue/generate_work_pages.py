"""Generate replaceable Catalogue JSON; canonical records and public sites are never written."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import quote

from catalogue import catalogue_generation_indexes as indexes
from catalogue import catalogue_generation_records as projection
from catalogue.catalogue_galleries import CatalogueGalleries, read_galleries, validate_galleries
from catalogue.catalogue_generation_common import compact_json_object, compute_payload_version
from catalogue.catalogue_media_policy import catalogue_media_policy
from catalogue.catalogue_output_paths import catalogue_output_workspace, output_path
from catalogue.catalogue_output_selection import selected_output_paths
from catalogue.catalogue_series_galleries import CatalogueSeriesGalleries, read_series_galleries, validate_series_galleries
from catalogue.catalogue_source import CatalogueSourceRecords, records_from_json_source, validate_source_records


def _index(family: str, items: Mapping[str, Any], timestamp: str) -> dict[str, Any]:
    schema = f"catalogue_{family}_index_v1"
    return {"header": {"schema": schema, "version": compute_payload_version({"schema": schema, family: items}),
                       "generated_at_utc": timestamp, "count": len(items)}, family: dict(items)}


def catalogue_payloads(
    repo_root: Path, records: CatalogueSourceRecords, galleries: CatalogueGalleries,
    pairs: CatalogueSeriesGalleries, *, timestamp: str,
) -> dict[str, dict[str, Any]]:
    """Build Work and Gallery records plus compact discovery indexes."""
    errors = validate_source_records(records)
    if errors:
        raise ValueError("Catalogue source validation failed: " + "; ".join(errors[:20]))
    validate_galleries(galleries, records.works)
    validate_series_galleries(pairs, records.series, galleries.galleries)
    context = indexes.build_series_work_index_context(series_records=records.series, work_records=records.works)
    works_by_gallery: dict[str, list[str]] = {gid: [] for gid in galleries.galleries}
    for wid, ids in galleries.works.items():
        for gid in ids:
            works_by_gallery[gid].append(wid)
    payloads: dict[str, dict[str, Any]] = {}
    works_index: dict[str, Any] = {}
    media_config = json.loads((repo_root / "site-tools/config/site-tools.json").read_text())["media"]
    payloads["media-config.json"] = catalogue_media_policy(repo_root, timestamp=timestamp)
    for wid, source in records.works.items():
        work = compact_json_object({"work_id": wid, **projection.build_work_record_projection(source)})
        if source.get("series_id"):
            work["series_id"] = source["series_id"]
        if source.get("links"):
            work["links"] = source["links"]
        if source.get("downloads"):
            work["downloads"] = [
                {**download, "url": f"{media_config['base'].rstrip('/')}/{media_config['files_works'].strip('/')}/{quote(download['filename'], safe='')}"}
                for download in source["downloads"]
            ]
        work["documents"] = []
        work["galleries"] = [dict(galleries.galleries[gid]) for gid in sorted(galleries.works.get(wid, []))]
        payloads[f"works/index/{wid}.json"] = projection.build_work_json_payload(
            work_id=wid, work_record=work, sections=[], generated_at_utc=timestamp, count=0,
        )
        works_index[wid] = {key: work[key] for key in ("work_id", "title", "year", "year_display", "series_id") if key in work}
    for gid, source in galleries.galleries.items():
        payloads[f"galleries/index/{gid}.json"] = projection.build_gallery_json_payload(
            gallery_id=gid, gallery_record=source,
            member_works=indexes.build_member_work_records(context=context, work_ids=works_by_gallery[gid]), generated_at_utc=timestamp,
        )
    payloads["works/works_index.json"] = _index("works", works_index, timestamp)
    payloads["galleries/galleries_index.json"] = _index("galleries", {
        gid: {"gallery_id": gid, "title": galleries.galleries[gid]["title"], "work_count": len(works_by_gallery[gid])}
        for gid in sorted(galleries.galleries)
    }, timestamp)
    payloads["series-galleries-index.json"] = _index("series_galleries", {
        sid: [
            {"gallery_id": gid, "title": galleries.galleries[gid]["title"]}
            for gid in pairs.pairs_by_series.get(sid, ())
        ]
        for sid in sorted(records.series)
    }, timestamp)
    return payloads


def _same_generated_content(actual: Any, expected: dict[str, Any]) -> bool:
    """Ignore only the generation timestamp when comparing complete output."""
    if (not isinstance(actual, dict) or not isinstance(actual.get("header"), dict)
            or not isinstance(actual["header"].get("generated_at_utc"), str)
            or not actual["header"]["generated_at_utc"]):
        return False
    actual_content = {**actual, "header": {key: value for key, value in actual["header"].items() if key != "generated_at_utc"}}
    expected_content = {**expected, "header": {key: value for key, value in expected["header"].items() if key != "generated_at_utc"}}
    return actual_content == expected_content


def generate_catalogue_json(
    repo_root: Path, source_dir: Path, *, write: bool,
    work_ids: Sequence[str] | None = None, gallery_ids: Sequence[str] = (),
) -> dict[str, Any]:
    """Refresh selected records and every index, or reconcile the complete owned JSON set.

    Pass work_ids=() for a Gallery-only refresh. Missing selected IDs mean deletion.
    Gallery edits refresh current and former members; Work edits refresh current
    and former Galleries. Canonical records always own the written content.
    """
    workspace = catalogue_output_workspace(repo_root)
    records = records_from_json_source(source_dir)
    galleries = read_galleries(source_dir, records.works)
    pairs = read_series_galleries(source_dir, records.series, galleries.galleries)
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    payloads = catalogue_payloads(repo_root, records, galleries, pairs, timestamp=timestamp)
    complete = work_ids is None
    selected = selected_output_paths(workspace, records, galleries, work_ids=work_ids, gallery_ids=gallery_ids)
    selected.update(path for path in payloads if "/index/" not in path)
    written, deleted = [], []
    for relative in sorted(selected):
        path = output_path(workspace, relative)
        payload = payloads.get(relative)
        if payload is None:
            if path.exists():
                deleted.append(relative)
                if write:
                    path.unlink()
            continue
        if path.exists():
            try:
                old = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                if not complete:
                    raise
                old = None
            if (complete and _same_generated_content(old, payload)) or (
                not complete and isinstance(old, dict) and old.get("header", {}).get("version") == payload["header"]["version"]
            ):
                continue
        written.append(relative)
        if write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"status": "completed", "write": write, "written": written, "deleted": deleted,
            "counts": {"works": len(records.works), "series": len(records.series), "galleries": len(galleries.galleries)}}
