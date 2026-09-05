"""Plan canonical Catalogue deletion without touching media or public output."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from catalogue.catalogue_source import (
    CatalogueSourceRecords,
    SOURCE_FILES,
    payload_for_map,
    records_from_json_source,
    validate_source_records,
    work_details_payload_for_maps,
)


@dataclass(frozen=True)
class DeleteApplyPlan:
    """Exact source writes and affected identities for one validated deletion."""

    kind: str
    record_id: str
    payloads: dict[Path, dict[str, Any]]
    affected: dict[str, list[str]]


def _delete_records(
    source_dir: Path, kind: str, record_id: str,
) -> tuple[CatalogueSourceRecords, dict[str, Any], dict[str, list[str]]]:
    source = records_from_json_source(source_dir)
    families = {"work": source.works, "series": source.series,
                "work_detail": source.work_details, "work_detail_section": source.work_detail_sections}
    if kind not in families:
        raise ValueError("delete kind must be work, series, work_detail, or work_detail_section")
    original = families[kind].get(record_id)
    if original is None:
        raise ValueError(f"{kind} not found: {record_id}")
    affected: dict[str, list[str]] = {"works": [], "series": [], "work_details": []}
    if kind == "series":
        del source.series[record_id]
        affected["series"] = [record_id]
        for work_id, work in source.works.items():
            if work.get("series_id") == record_id:
                work.pop("series_id")
                affected["works"].append(work_id)
    elif kind == "work":
        affected["works"] = [record_id]
        affected["series"] = [original["series_id"]] if original.get("series_id") else []
        del source.works[record_id]
        for section_id, section in list(source.work_detail_sections.items()):
            if section["work_id"] == record_id:
                del source.work_detail_sections[section_id]
        for detail_uid, detail in list(source.work_details.items()):
            if detail["work_id"] == record_id:
                affected["work_details"].append(detail_uid)
                del source.work_details[detail_uid]
    elif kind == "work_detail_section":
        affected["works"] = [original["work_id"]]
        del source.work_detail_sections[record_id]
        for detail_uid, detail in list(source.work_details.items()):
            if detail["section_id"] == record_id:
                affected["work_details"].append(detail_uid)
                del source.work_details[detail_uid]
    else:
        affected["works"] = [original["work_id"]]
        affected["work_details"] = [record_id]
        del source.work_details[record_id]
        section_id = original["section_id"]
        if not any(detail["section_id"] == section_id for detail in source.work_details.values()):
            del source.work_detail_sections[section_id]
    return source, dict(original), {key: sorted(values) for key, values in affected.items()}


def build_delete_preview(
    source_dir: Path, kind: str, record_id: str,
) -> dict[str, Any]:
    """Describe the exact canonical deletion; output and media remain paused."""
    source, original, affected = _delete_records(source_dir, kind, record_id)
    errors = validate_source_records(source)
    summary = f"Delete {kind} {record_id} from canonical Catalogue data."
    if kind == "series" and affected["works"]:
        summary += f" Clear the Series assignment on {len(affected['works'])} Work(s), keeping those Works."
    if affected["work_details"]:
        summary += f" Delete {len(affected['work_details'])} dependent Detail(s)."
    summary += " Media and output are unchanged."
    return {
        "kind": kind, "id": record_id, "record": original, "affected": affected,
        "blockers": [], "validation_errors": errors, "blocked": bool(errors),
        "summary": summary,
        "cleanup": {},
    }


def build_delete_apply_plan(
    source_dir: Path, kind: str, record_id: str,
) -> DeleteApplyPlan:
    """Recompute and validate source writes instead of trusting the preview payload."""
    source, _original, affected = _delete_records(source_dir, kind, record_id)
    errors = validate_source_records(source)
    if errors:
        raise ValueError("source validation failed: " + "; ".join(errors[:20]))
    payloads: dict[Path, dict[str, Any]] = {}
    if kind in {"work", "series"}:
        payloads[(source_dir / SOURCE_FILES["works"]).resolve()] = payload_for_map("works", source.works)
    if kind == "series":
        payloads[(source_dir / SOURCE_FILES["series"]).resolve()] = payload_for_map("series", source.series)
    if kind != "series":
        payloads[(source_dir / SOURCE_FILES["work_details"]).resolve()] = work_details_payload_for_maps(
            source.work_detail_sections, source.work_details,
        )
    return DeleteApplyPlan(kind, record_id, payloads, affected)
