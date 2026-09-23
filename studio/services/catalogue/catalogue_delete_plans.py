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
    load_json_file,
)
from catalogue.catalogue_galleries import read_galleries, validate_galleries, MEMBERSHIPS_FILE


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
    families = {"work": source.works, "series": source.series}
    if kind not in families:
        raise ValueError("delete kind must be work or series")
    original = families[kind].get(record_id)
    if original is None:
        raise ValueError(f"{kind} not found: {record_id}")
    affected: dict[str, list[str]] = {"works": [], "series": []}
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
    if kind == "work":
        galleries = read_galleries(source_dir, load_json_file(source_dir / "works.json")["works"])
        galleries.works.pop(record_id, None)
        validate_galleries(galleries, source.works)
        payloads[(source_dir / MEMBERSHIPS_FILE).resolve()] = galleries.payloads()[MEMBERSHIPS_FILE]
    return DeleteApplyPlan(kind, record_id, payloads, affected)
