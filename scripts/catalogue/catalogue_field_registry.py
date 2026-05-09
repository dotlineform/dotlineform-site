"""Catalogue field-to-artifact build planning helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

from catalogue.catalogue_source import CatalogueSourceRecords, load_json_file
from catalogue.series_ids import normalize_series_id, parse_series_ids


STUDIO_CONFIG_REL_PATH = Path("assets/studio/data/studio_config.json")
FALLBACK_CATALOGUE_FIELD_REGISTRY_REL_PATH = Path("assets/studio/data/catalogue_field_registry.json")

REGISTRY_ARTIFACT_TO_GENERATE_ONLY = {
    "work-page": "work-pages",
    "work-details-page": "work-details-pages",
    "series-page": "series-pages",
    "work-json": "work-json",
    "works-index-json": "works-index-json",
    "work-storage-index-json": "work-json",
    "series-json": "series-pages",
    "series-index-json": "series-index-json",
    "recent-index-json": "recent-index-json",
    "moment-page": "moments",
    "moment-json": "moments",
    "moments-index-json": "moments-index-json",
}

BUILD_ARTIFACT_ORDER = [
    "work-pages",
    "work-json",
    "work-details-pages",
    "series-pages",
    "series-index-json",
    "works-index-json",
    "recent-index-json",
    "moments",
    "moments-index-json",
]

def normalize_series_ids_value(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        out: list[str] = []
        seen: set[str] = set()
        for raw in value:
            series_id = normalize_series_id(raw)
            if series_id in seen:
                continue
            seen.add(series_id)
            out.append(series_id)
        return out
    return parse_series_ids(value)


def load_catalogue_field_registry(repo_root: Path) -> Dict[str, Any]:
    path = resolve_catalogue_field_registry_path(repo_root)
    payload = load_json_file(path)
    if not isinstance(payload, dict):
        raise ValueError(f"catalogue field registry must be a JSON object: {path}")
    if payload.get("schema") != "catalogue_field_registry_v1":
        raise ValueError("unsupported catalogue field registry schema")
    return payload


def resolve_catalogue_field_registry_path(repo_root: Path) -> Path:
    config_path = repo_root / STUDIO_CONFIG_REL_PATH
    if config_path.exists():
        config = load_json_file(config_path)
        data_paths = (((config.get("paths") or {}).get("data") or {}).get("studio") or {}) if isinstance(config, dict) else {}
        configured = str(data_paths.get("catalogue_field_registry") or "").strip()
        if configured:
            rel = configured.lstrip("/")
            return (repo_root / rel).resolve()
    return (repo_root / FALLBACK_CATALOGUE_FIELD_REGISTRY_REL_PATH).resolve()


def registry_rules_for(
    registry: Mapping[str, Any],
    *,
    record_family: str,
    operation: str,
) -> list[Mapping[str, Any]]:
    rules = registry.get("rules")
    if not isinstance(rules, list):
        raise ValueError("catalogue field registry missing rules[]")
    return [
        rule
        for rule in rules
        if isinstance(rule, Mapping)
        and str(rule.get("record_family") or "") == record_family
        and str(rule.get("operation") or "") == operation
    ]


def rule_fields(rule: Mapping[str, Any]) -> list[str]:
    return [str(field).strip() for field in rule.get("fields") or [] if str(field).strip()]


def build_rule_index(
    registry: Mapping[str, Any],
    *,
    record_family: str,
    operation: str,
) -> dict[str, Mapping[str, Any]]:
    index: dict[str, Mapping[str, Any]] = {}
    for rule in registry_rules_for(registry, record_family=record_family, operation=operation):
        rule_id = str(rule.get("id") or "").strip()
        for field in rule_fields(rule):
            if field in index:
                raise ValueError(f"catalogue field registry has duplicate {record_family}.{operation} field: {field}")
            if not rule_id:
                raise ValueError(f"catalogue field registry rule for {field} is missing id")
            index[field] = rule
    return index


def registry_default_reason(registry: Mapping[str, Any], key: str, fallback: str) -> str:
    target = registry_default_target(registry, key)
    return str(target.get("reason") or fallback)


def registry_default_target(registry: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    defaults = registry.get("defaults") if isinstance(registry.get("defaults"), Mapping) else {}
    default_row = defaults.get(key) if isinstance(defaults, Mapping) else {}
    return default_row.get("target") if isinstance(default_row, Mapping) and isinstance(default_row.get("target"), Mapping) else {}


def ordered_generate_artifacts(artifacts: Iterable[str]) -> list[str]:
    selected = {str(artifact) for artifact in artifacts if str(artifact)}
    return [artifact for artifact in BUILD_ARTIFACT_ORDER if artifact in selected]


def registry_artifacts_to_generate_only(artifacts: Iterable[str]) -> list[str]:
    mapped: set[str] = set()
    for artifact in artifacts:
        generate_artifact = REGISTRY_ARTIFACT_TO_GENERATE_ONLY.get(str(artifact))
        if generate_artifact:
            mapped.add(generate_artifact)
    return ordered_generate_artifacts(mapped)


def fallback_registry_artifacts_for_record_family(
    registry: Mapping[str, Any],
    *,
    default_key: str,
    record_family: str,
) -> list[str]:
    target = registry_default_target(registry, default_key)
    by_family = target.get("artifacts_by_record_family")
    if isinstance(by_family, Mapping):
        raw_artifacts = by_family.get(record_family)
        if raw_artifacts is None:
            raw_artifacts = by_family.get("work")
        if isinstance(raw_artifacts, list):
            return [str(artifact) for artifact in raw_artifacts if str(artifact).strip()]
    raw_artifacts = target.get("artifacts")
    if isinstance(raw_artifacts, list):
        return [str(artifact) for artifact in raw_artifacts if str(artifact).strip()]
    raise ValueError(f"catalogue field registry default {default_key} is missing fallback artifacts for {record_family}")


def series_sort_fields_for_work(records: CatalogueSourceRecords, work_record: Mapping[str, Any]) -> set[str]:
    fields: set[str] = set()
    for series_id in normalize_series_ids_value(work_record.get("series_ids")):
        series_record = records.series.get(series_id)
        if not isinstance(series_record, Mapping):
            continue
        raw_sort_fields = str(series_record.get("sort_fields") or "").strip()
        for raw_field in raw_sort_fields.split(","):
            field = raw_field.strip()
            if field:
                fields.add(field)
    return fields


def conditional_artifact_applies(
    artifact: str,
    *,
    rule_id: str,
    record_family: str,
    changed_field_names: set[str],
    context: Mapping[str, Any],
) -> bool:
    if artifact == "series-index-json" and record_family == "work" and rule_id == "work_display_core":
        source_records = context.get("source_records")
        current_record = context.get("current_record")
        updated_record = context.get("updated_record")
        if not isinstance(source_records, CatalogueSourceRecords):
            return False
        sort_fields: set[str] = set()
        if isinstance(current_record, Mapping):
            sort_fields.update(series_sort_fields_for_work(source_records, current_record))
        if isinstance(updated_record, Mapping):
            sort_fields.update(series_sort_fields_for_work(source_records, updated_record))
        return bool(sort_fields.intersection(changed_field_names))
    return False


def registry_artifact_description(registry: Mapping[str, Any], artifact: str) -> str:
    families = registry.get("artifact_families")
    if isinstance(families, Mapping):
        return str(families.get(artifact) or "")
    return ""


def build_artifact_explanations(
    registry: Mapping[str, Any],
    *,
    fields: list[str],
    rule_ids: list[str],
    artifacts: Iterable[str],
    reason: str,
    fallback: bool,
    fallback_reason: str = "",
) -> list[Dict[str, Any]]:
    explanation = str(reason or "").strip()
    rows: list[Dict[str, Any]] = []
    for artifact in sorted({str(item).strip() for item in artifacts if str(item).strip()}):
        rows.append(
            {
                "artifact": artifact,
                "fields": list(fields),
                "rule_ids": list(rule_ids),
                "fallback": bool(fallback),
                "fallback_reason": fallback_reason,
                "reason": explanation,
                "description": registry_artifact_description(registry, artifact),
            }
        )
    return rows


def field_aware_build_plan(
    registry: Mapping[str, Any],
    *,
    record_family: str,
    operation: str,
    changed_field_names: list[str],
    context: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    context = context or {}
    changed = sorted({str(field).strip() for field in changed_field_names if str(field).strip()})
    if not changed:
        return {
            "mode": "none",
            "fallback": False,
            "fields": [],
            "rule_ids": [],
            "artifacts": [],
            "generate_only": [],
            "rebuild_search": False,
            "generate_local_media": False,
            "build_required": False,
            "reason": "No source fields changed.",
            "explanations": [],
        }

    rule_index = build_rule_index(registry, record_family=record_family, operation=operation)
    unknown_fields = [field for field in changed if field not in rule_index]
    if unknown_fields:
        artifacts = fallback_registry_artifacts_for_record_family(
            registry,
            default_key="unknown_field",
            record_family=record_family,
        )
        reason = registry_default_reason(
            registry,
            "unknown_field",
            "Unknown source fields use conservative fallback until explicitly classified.",
        )
        generate_only = registry_artifacts_to_generate_only(artifacts)
        return {
            "mode": "full-fallback",
            "fallback": True,
            "fallback_reason": "unknown_field",
            "fields": changed,
            "rule_ids": [],
            "artifacts": artifacts,
            "generate_only": generate_only,
            "rebuild_search": "catalogue-search" in artifacts,
            "generate_local_media": "local-media" in artifacts,
            "build_required": bool(generate_only or "catalogue-search" in artifacts or "local-media" in artifacts),
            "unknown_fields": unknown_fields,
            "reason": reason,
            "explanations": build_artifact_explanations(
                registry,
                fields=changed,
                rule_ids=[],
                artifacts=artifacts,
                reason=reason,
                fallback=True,
                fallback_reason="unknown_field",
            ),
        }

    matched_rules: dict[str, Mapping[str, Any]] = {}
    for field in changed:
        rule = rule_index[field]
        matched_rules[str(rule.get("id") or "")] = rule

    if len(matched_rules) != 1:
        artifacts = fallback_registry_artifacts_for_record_family(
            registry,
            default_key="mixed_dependency_classes",
            record_family=record_family,
        )
        reason = registry_default_reason(
            registry,
            "mixed_dependency_classes",
            "Mixed edits spanning dependency classes use conservative fallback.",
        )
        generate_only = registry_artifacts_to_generate_only(artifacts)
        return {
            "mode": "full-fallback",
            "fallback": True,
            "fallback_reason": "mixed_dependency_classes",
            "fields": changed,
            "rule_ids": sorted(matched_rules),
            "artifacts": artifacts,
            "generate_only": generate_only,
            "rebuild_search": "catalogue-search" in artifacts,
            "generate_local_media": "local-media" in artifacts,
            "build_required": bool(generate_only or "catalogue-search" in artifacts or "local-media" in artifacts),
            "unknown_fields": [],
            "reason": reason,
            "explanations": build_artifact_explanations(
                registry,
                fields=changed,
                rule_ids=sorted(matched_rules),
                artifacts=artifacts,
                reason=reason,
                fallback=True,
                fallback_reason="mixed_dependency_classes",
            ),
        }

    rule_id, rule = next(iter(matched_rules.items()))
    target = rule.get("target") if isinstance(rule.get("target"), Mapping) else {}
    if bool(target.get("fallback")):
        raw_artifacts = target.get("artifacts")
        artifacts = (
            [str(artifact) for artifact in raw_artifacts if str(artifact).strip()]
            if isinstance(raw_artifacts, list)
            else fallback_registry_artifacts_for_record_family(
                registry,
                default_key="unknown_field",
                record_family=record_family,
            )
        )
        reason = str(target.get("reason") or "Registry rule requires conservative fallback.")
        generate_only = registry_artifacts_to_generate_only(artifacts)
        return {
            "mode": "full-fallback",
            "fallback": True,
            "fallback_reason": "rule_fallback",
            "fields": changed,
            "rule_ids": [rule_id],
            "artifacts": artifacts,
            "generate_only": generate_only,
            "rebuild_search": "catalogue-search" in artifacts,
            "generate_local_media": "local-media" in artifacts,
            "build_required": bool(generate_only or "catalogue-search" in artifacts or "local-media" in artifacts),
            "unknown_fields": [],
            "reason": reason,
            "explanations": build_artifact_explanations(
                registry,
                fields=changed,
                rule_ids=[rule_id],
                artifacts=artifacts,
                reason=reason,
                fallback=True,
                fallback_reason="rule_fallback",
            ),
        }

    artifacts = {str(artifact) for artifact in target.get("artifacts") or [] if str(artifact)}
    changed_set = set(changed)
    applied_conditional_artifacts: list[str] = []
    omitted_conditional_artifacts: list[str] = []
    for conditional in target.get("conditional_artifacts") or []:
        if not isinstance(conditional, Mapping):
            continue
        artifact = str(conditional.get("artifact") or "").strip()
        if not artifact:
            continue
        if conditional_artifact_applies(
            artifact,
            rule_id=rule_id,
            record_family=record_family,
            changed_field_names=changed_set,
            context=context,
        ):
            artifacts.add(artifact)
            applied_conditional_artifacts.append(artifact)
        else:
            omitted_conditional_artifacts.append(artifact)

    generate_only = registry_artifacts_to_generate_only(artifacts)
    rebuild_search = "catalogue-search" in artifacts
    generate_local_media = "local-media" in artifacts
    build_required = bool(generate_only or rebuild_search or generate_local_media)
    reason = str(target.get("reason") or "")
    return {
        "mode": "field-aware",
        "fallback": False,
        "fields": changed,
        "rule_ids": [rule_id],
        "artifacts": sorted(artifacts),
        "generate_only": generate_only,
        "rebuild_search": rebuild_search,
        "generate_local_media": generate_local_media,
        "build_required": build_required,
        "unknown_fields": [],
        "conditional_artifacts": {
            "applied": sorted(set(applied_conditional_artifacts)),
            "omitted": sorted(set(omitted_conditional_artifacts)),
        },
        "reason": reason,
        "explanations": build_artifact_explanations(
            registry,
            fields=changed,
            rule_ids=[rule_id],
            artifacts=artifacts,
            reason=reason,
            fallback=False,
        ),
    }


def full_fallback_build_plan(
    registry: Mapping[str, Any],
    *,
    fields: Iterable[str],
    reason: str,
    fallback_reason: str,
    record_family: str,
    default_key: str = "mixed_dependency_classes",
) -> Dict[str, Any]:
    fallback_reason_text = str(reason or "Conservative fallback selected this artifact family.")
    artifacts = fallback_registry_artifacts_for_record_family(
        registry,
        default_key=default_key,
        record_family=record_family,
    )
    generate_only = registry_artifacts_to_generate_only(artifacts)
    return {
        "mode": "full-fallback",
        "fallback": True,
        "fallback_reason": fallback_reason,
        "fields": sorted({str(field).strip() for field in fields if str(field).strip()}),
        "rule_ids": [],
        "artifacts": artifacts,
        "generate_only": generate_only,
        "rebuild_search": "catalogue-search" in artifacts,
        "generate_local_media": "local-media" in artifacts,
        "build_required": bool(generate_only or "catalogue-search" in artifacts or "local-media" in artifacts),
        "unknown_fields": [],
        "reason": fallback_reason_text,
        "explanations": [
            {
                "artifact": artifact,
                "fields": sorted({str(field).strip() for field in fields if str(field).strip()}),
                "rule_ids": [],
                "fallback": True,
                "fallback_reason": fallback_reason,
                "reason": fallback_reason_text,
                "description": "",
            }
            for artifact in artifacts
        ],
    }


def apply_field_build_plan_to_scope(scope: Dict[str, Any], build_plan: Mapping[str, Any]) -> None:
    scope["field_plan"] = {
        "mode": build_plan.get("mode"),
        "fallback": bool(build_plan.get("fallback")),
        "fallback_reason": build_plan.get("fallback_reason"),
        "fields": list(build_plan.get("fields") or []),
        "rule_ids": list(build_plan.get("rule_ids") or []),
        "artifacts": list(build_plan.get("artifacts") or []),
        "unknown_fields": list(build_plan.get("unknown_fields") or []),
        "conditional_artifacts": dict(build_plan.get("conditional_artifacts") or {}),
        "explanations": list(build_plan.get("explanations") or []),
        "reason": str(build_plan.get("reason") or ""),
    }
    scope["generate_only"] = list(build_plan.get("generate_only") or [])
    scope["rebuild_search"] = bool(build_plan.get("rebuild_search"))
    scope["generate_local_media"] = bool(build_plan.get("generate_local_media"))
    if "summary" not in scope:
        return
    mode = str(build_plan.get("mode") or "field-aware")
    artifacts = ", ".join(scope["generate_only"]) if scope["generate_only"] else "none"
    search = "yes" if scope["rebuild_search"] else "no"
    media = "yes" if scope["generate_local_media"] else "no"
    if str(scope.get("kind") or "work") == "moment":
        ids = ", ".join(str(item) for item in scope.get("moment_ids", [])) or "none"
        scope["summary"] = f"Field-aware build moments [{ids}]; mode {mode}; generate [{artifacts}], search {search}, local media {media}."
    else:
        work_ids = ", ".join(str(item) for item in scope.get("work_ids", [])) or "none"
        series_ids = ", ".join(str(item) for item in scope.get("series_ids", [])) or "none"
        scope["summary"] = f"Field-aware build works [{work_ids}], series [{series_ids}]; mode {mode}; generate [{artifacts}], search {search}, local media {media}."
