"""Generate replaceable Catalogue JSON; canonical records and public sites are never written."""

from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import quote

from catalogue import catalogue_generation_indexes as indexes
from catalogue import catalogue_generation_records as projection
from catalogue.catalogue_generation_common import compact_json_object, compute_payload_version
from catalogue.catalogue_output_paths import catalogue_output_workspace, output_path
from catalogue.catalogue_source import CatalogueSourceRecords, records_from_json_source, validate_source_records, slug_id, section_sort_key, detail_sort_key_for_section
from catalogue.series_ids import normalize_series_id
from pipeline_config import load_pipeline_config


def media_references(config: Mapping[str, Any], media: Mapping[str, Any], family: str, item_id: str, record: Mapping[str, Any]) -> dict[str, Any]:
    """Project explicit consumer references from checked media policy and exact identity."""
    if not record.get("project_filename"):
        return {}
    key = "image_works" if family == "works" else "image_work_details"
    prefix = str(media[key]).strip("/")
    if prefix == "archive" or prefix.startswith("archive/") or ".." in prefix.split("/"):
        raise ValueError(f"invalid active Catalogue media prefix: {prefix}")
    extension = config["encoding"]["format"]
    version = int(record.get("media_version") or 1)
    return {
        "thumbnails": [
            {"path": f"{family}/thumbs/{item_id}-{config['variants']['thumb']['suffix']}-{size}.{extension}", "size": size}
            for size in config["variants"]["thumb"]["sizes"]
        ],
        "primary": [
            {"url": f"{media['base'].rstrip('/')}/{prefix}/{item_id}-{config['variants']['primary']['suffix']}-{width}.{extension}?v={version}", "width": width}
            for width in config["variants"]["primary"]["widths"]
        ],
    }


def _index(family: str, items: Mapping[str, Any], timestamp: str) -> dict[str, Any]:
    schema = f"catalogue_{family}_index_v1"
    return {"header": {"schema": schema, "version": compute_payload_version({"schema": schema, family: items}),
                       "generated_at_utc": timestamp, "count": len(items)}, family: dict(items)}


def catalogue_payloads(repo_root: Path, records: CatalogueSourceRecords, *, timestamp: str) -> dict[str, dict[str, Any]]:
    """Build complete Work aggregates, independent Series and compact discovery indexes."""
    errors = validate_source_records(records)
    if errors:
        raise ValueError("Catalogue source validation failed: " + "; ".join(errors[:20]))
    context = indexes.build_series_work_index_context(series_records=records.series, work_records=records.works)
    payloads: dict[str, dict[str, Any]] = {}
    works_index: dict[str, Any] = {}
    details_index: dict[str, Any] = {}
    media_config = json.loads((repo_root / "site-tools/config/site-tools.json").read_text())["media"]
    pipeline = load_pipeline_config(repo_root=repo_root)
    details_by_section: dict[str, list[dict[str, Any]]] = {}
    for uid, source in records.work_details.items():
        detail = projection.build_canonical_detail_record(
            source["work_id"], source["detail_id"], source.get("title"), source.get("width_px"),
            source.get("height_px"), source.get("media_version"),
        )
        detail["media"] = media_references(pipeline, media_config, "work_details", uid, source)
        details_by_section.setdefault(source["section_id"], []).append(detail)
        details_index[uid] = {**detail, "section_id": source["section_id"]}
    sections_by_work: dict[str, list[dict[str, Any]]] = {}
    for section in records.work_detail_sections.values():
        details = details_by_section.get(section["section_id"], [])
        details.sort(key=lambda item: detail_sort_key_for_section(section, item))
        sections_by_work.setdefault(section["work_id"], []).append({
            **{key: section[key] for key in ("section_id", "section_title", "section_order", "detail_sort") if key in section},
            "details": details,
        })
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
        work["media"] = media_references(pipeline, media_config, "works", wid, source)
        sections = sorted(sections_by_work.get(wid, []), key=section_sort_key)
        payloads[f"works/index/{wid}.json"] = projection.build_work_json_payload(
            work_id=wid, work_record=work, sections=sections, generated_at_utc=timestamp,
            count=sum(len(section["details"]) for section in sections),
        )
        works_index[wid] = {key: work[key] for key in ("work_id", "title", "year", "year_display", "series_id", "media") if key in work}
    for sid, source in records.series.items():
        series = {**source, "documents": []}
        payloads[f"series/index/{sid}.json"] = projection.build_series_json_payload(
            series_id=sid, series_record=series,
            member_works=indexes.build_series_member_work_records(context=context, series_id=sid), generated_at_utc=timestamp,
        )
    payloads["works/works_index.json"] = _index("works", works_index, timestamp)
    payloads["series/series_index.json"] = _index("series", indexes.build_series_index_records(series_records=records.series, context=context), timestamp)
    payloads["work_details/work_details_index.json"] = _index("work_details", details_index, timestamp)
    return payloads


def generate_catalogue_json(
    repo_root: Path, source_dir: Path, *, write: bool,
    work_ids: Sequence[str] | None = None, series_ids: Sequence[str] = (),
) -> dict[str, Any]:
    """Refresh selected records and every index, or reconcile the complete owned JSON set.

    A missing selected ID means deletion. Previous Work membership is read only to
    refresh the former Series; identity always comes from the requested IDs.
    """
    workspace = catalogue_output_workspace(repo_root)
    records = records_from_json_source(source_dir)
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    payloads = catalogue_payloads(repo_root, records, timestamp=timestamp)
    full = work_ids is None
    selected_works = set(records.works if full else (slug_id(wid) for wid in work_ids))
    selected_series = set(records.series if full else (normalize_series_id(sid) for sid in series_ids))
    for wid in selected_works:
        previous_path = output_path(workspace, f"works/index/{wid}.json")
        if previous_path.exists():
            previous = json.loads(previous_path.read_text())
            if previous.get("work", {}).get("work_id") != wid:
                raise ValueError(f"Generated Work identity does not match {previous_path}")
            previous_series = previous.get("work", {}).get("series_id")
            if previous_series:
                selected_series.add(normalize_series_id(previous_series))
        current_series = records.works.get(wid, {}).get("series_id")
        if current_series:
            selected_series.add(current_series)
    selected = {f"works/index/{wid}.json" for wid in selected_works} | {f"series/index/{sid}.json" for sid in selected_series}
    selected.update(path for path in payloads if "/index/" not in path)
    if full:
        for family in ("works", "series"):
            selected.update(path.relative_to(workspace.root).as_posix() for path in output_path(workspace, f"{family}/index").glob("*.json"))
    written, deleted = [], []
    if full:
        expected_thumbs = {
            thumbnail["path"] for family in ("works", "work_details")
            for record in payloads[f"{family}/{family}_index.json"][family].values()
            for thumbnail in record.get("media", {}).get("thumbnails", [])
        }
        for family in ("works", "work_details"):
            for existing in output_path(workspace, f"{family}/thumbs").glob("*"):
                if not re.fullmatch(r"\d{5}(?:-\d+)?-thumb-\d+\.webp", existing.name):
                    continue
                relative = existing.relative_to(workspace.root).as_posix()
                if relative not in expected_thumbs:
                    checked = output_path(workspace, relative)
                    deleted.append(relative)
                    if write:
                        checked.unlink()
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
            old = json.loads(path.read_text())
            if old.get("header", {}).get("version") == payload["header"]["version"]:
                continue
        written.append(relative)
        if write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"status": "completed", "write": write, "written": written, "deleted": deleted,
            "counts": {"works": len(records.works), "series": len(records.series), "details": len(records.work_details)}}
