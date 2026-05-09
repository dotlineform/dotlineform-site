"""Field-aware scoped catalogue build planning helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping, Sequence

from catalogue_field_registry import (
    apply_field_build_plan_to_scope as apply_registry_field_build_plan_to_scope,
    field_aware_build_plan,
    load_catalogue_field_registry,
)
from catalogue_source import records_from_json_source


RECORD_FAMILIES = {"work", "work_detail", "series", "moment"}


def parse_csv_tokens(value: Any) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    if value is None:
        return out
    raw_values = value if isinstance(value, list) else [value]
    for raw in raw_values:
        for part in str(raw or "").split(","):
            item = part.strip()
            if not item or item in seen:
                continue
            seen.add(item)
            out.append(item)
    return out


def infer_record_family_for_scope(scope: Mapping[str, Any], explicit_family: str = "") -> str:
    family = str(explicit_family or "").strip().lower().replace("-", "_")
    if family:
        if family not in RECORD_FAMILIES:
            raise ValueError("--record-family must be work, work_detail, series, or moment")
        return family
    if str(scope.get("kind") or "") == "moment":
        return "moment"
    if scope.get("detail_uid"):
        return "work_detail"
    if scope.get("series_ids") and not scope.get("work_ids"):
        return "series"
    return "work"


def build_field_plan_for_scope(
    repo_root: Path,
    source_dir: Path,
    scope: Mapping[str, Any],
    *,
    changed_fields: Sequence[str],
    record_family: str = "",
) -> Dict[str, Any]:
    fields = [str(field).strip() for field in changed_fields if str(field).strip()]
    if not fields:
        return {}
    family = infer_record_family_for_scope(scope, record_family)
    registry = load_catalogue_field_registry(repo_root)
    context: Dict[str, Any] = {}
    if family in {"work", "work_detail", "series"}:
        records = records_from_json_source(source_dir)
        context["source_records"] = records
        if family == "work":
            work_ids = [str(item) for item in scope.get("work_ids", []) if str(item)]
            if work_ids:
                record = records.works.get(work_ids[0])
                if isinstance(record, dict):
                    context["current_record"] = record
                    context["updated_record"] = record
        elif family == "work_detail":
            detail_uid = str(scope.get("detail_uid") or "").strip()
            if detail_uid:
                record = records.work_details.get(detail_uid)
                if isinstance(record, dict):
                    context["current_record"] = record
                    context["updated_record"] = record
        else:
            series_ids = [str(item) for item in scope.get("series_ids", []) if str(item)]
            if series_ids:
                record = records.series.get(series_ids[0])
                if isinstance(record, dict):
                    context["current_record"] = record
                    context["updated_record"] = record
    return field_aware_build_plan(
        registry,
        record_family=family,
        operation="metadata_update",
        changed_field_names=fields,
        context=context,
    )


def apply_field_build_plan_to_scope(scope: Dict[str, Any], build_plan: Mapping[str, Any]) -> None:
    apply_registry_field_build_plan_to_scope(scope, build_plan)


def field_plan_explanation_lines(field_plan: Mapping[str, Any]) -> list[str]:
    explanations = field_plan.get("explanations") if isinstance(field_plan.get("explanations"), list) else []
    grouped: dict[tuple[str, str, str], list[str]] = {}
    for row in explanations:
        if not isinstance(row, Mapping):
            continue
        artifact = str(row.get("artifact") or "").strip()
        if not artifact:
            continue
        fields = ", ".join(str(field) for field in row.get("fields") or [] if str(field).strip()) or "field-aware plan"
        reason = str(row.get("reason") or "").strip() or "Selected by the field registry."
        fallback = str(row.get("fallback_reason") or "").strip() if row.get("fallback") else ""
        grouped.setdefault((fields, reason, fallback), []).append(artifact)
    lines: list[str] = []
    for (fields, reason, fallback), artifacts in grouped.items():
        prefix = "fallback " if fallback else ""
        lines.append(f"{', '.join(sorted(set(artifacts)))}: {prefix}{fields} -> {reason}")
    return lines
