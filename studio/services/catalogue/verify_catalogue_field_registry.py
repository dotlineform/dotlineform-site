#!/usr/bin/env python3
"""Verify catalogue field-registry build plans and source-schema coverage."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = SCRIPT_DIR.parent
REPO_ROOT = SCRIPT_DIR.parents[2]
sys.path.insert(0, str(SCRIPTS_DIR))

from catalogue.catalogue_field_registry import field_aware_build_plan, full_fallback_build_plan, load_catalogue_field_registry  # noqa: E402
from catalogue.catalogue_source import (  # noqa: E402
    DETAIL_FIELDS,
    DETAIL_TEXT_FIELDS,
    OMIT_EMPTY_SOURCE_FIELDS,
    SERIES_FIELDS,
    SOURCE_DERIVED_FIELDS_BY_RECORD_FAMILY,
    SOURCE_FIELDS_BY_RECORD_FAMILY,
    SOURCE_IDENTITY_FIELDS_BY_RECORD_FAMILY,
    SOURCE_METADATA_FIELDS_BY_RECORD_FAMILY,
    WORK_FIELDS,
    WORK_TEXT_FIELDS,
    CatalogueSourceRecords,
    normalize_source_record,
)
from catalogue.moment_sources import (  # noqa: E402
    MOMENT_DERIVED_FIELDS,
    MOMENT_IDENTITY_FIELDS,
    MOMENT_METADATA_FIELDS,
    MOMENT_METADATA_UPDATE_FIELDS,
)


MOMENT_SOURCE_FIELDS = {
    "moment": tuple(MOMENT_METADATA_FIELDS),
}

MOMENT_SOURCE_IDENTITY_FIELDS = {
    "moment": tuple(MOMENT_IDENTITY_FIELDS),
}

MOMENT_SOURCE_DERIVED_FIELDS = {
    "moment": tuple(MOMENT_DERIVED_FIELDS),
}

MOMENT_SOURCE_METADATA_FIELDS = {
    "moment": tuple(MOMENT_METADATA_UPDATE_FIELDS),
}

REGISTRY_FIELD_EXEMPTIONS: dict[tuple[str, str], set[str]] = {}
SOURCE_FIELD_EXEMPTIONS: dict[tuple[str, str], set[str]] = {}


def fail(message: str) -> None:
    raise AssertionError(message)


def assert_equal(label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        fail(f"{label}: expected {expected!r}, got {actual!r}")


def assert_artifacts(label: str, plan: Mapping[str, Any], expected: Sequence[str]) -> None:
    assert_equal(f"{label} artifacts", sorted(plan.get("artifacts") or []), sorted(expected))


def assert_generate_only(label: str, plan: Mapping[str, Any], expected: Sequence[str]) -> None:
    assert_equal(f"{label} generate_only", list(plan.get("generate_only") or []), list(expected))


def assert_booleans(
    label: str,
    plan: Mapping[str, Any],
    *,
    rebuild_search: bool,
    generate_local_media: bool,
    fallback: bool = False,
    build_required: bool | None = None,
) -> None:
    assert_equal(f"{label} fallback", bool(plan.get("fallback")), fallback)
    assert_equal(f"{label} rebuild_search", bool(plan.get("rebuild_search")), rebuild_search)
    assert_equal(f"{label} generate_local_media", bool(plan.get("generate_local_media")), generate_local_media)
    if build_required is not None:
        assert_equal(f"{label} build_required", bool(plan.get("build_required")), build_required)


def assert_rule(label: str, plan: Mapping[str, Any], expected_rule_id: str) -> None:
    assert_equal(f"{label} rule_ids", list(plan.get("rule_ids") or []), [expected_rule_id])


def assert_explanations(label: str, plan: Mapping[str, Any]) -> None:
    explanations = plan.get("explanations") or []
    artifacts = plan.get("artifacts") or []
    assert_equal(f"{label} explanation count", len(explanations), len(artifacts))
    for row in explanations:
        if not isinstance(row, Mapping):
            fail(f"{label} explanation row is not an object: {row!r}")
        if not row.get("artifact"):
            fail(f"{label} explanation row missing artifact: {row!r}")
        if not row.get("reason"):
            fail(f"{label} explanation row missing reason: {row!r}")


def assert_plan(
    label: str,
    plan: Mapping[str, Any],
    *,
    rule_id: str | None,
    artifacts: Sequence[str],
    generate_only: Sequence[str],
    rebuild_search: bool,
    generate_local_media: bool,
    fallback: bool = False,
    fallback_reason: str = "",
    build_required: bool | None = None,
) -> None:
    if rule_id is not None:
        assert_rule(label, plan, rule_id)
    assert_artifacts(label, plan, artifacts)
    assert_generate_only(label, plan, generate_only)
    assert_booleans(
        label,
        plan,
        rebuild_search=rebuild_search,
        generate_local_media=generate_local_media,
        fallback=fallback,
        build_required=build_required,
    )
    if fallback_reason:
        assert_equal(f"{label} fallback_reason", str(plan.get("fallback_reason") or ""), fallback_reason)
    assert_explanations(label, plan)


def plan_for(
    registry: Mapping[str, Any],
    *,
    record_family: str,
    fields: Sequence[str],
    context: Mapping[str, Any] | None = None,
) -> Mapping[str, Any]:
    return field_aware_build_plan(
        registry,
        record_family=record_family,
        operation="metadata_update",
        changed_field_names=list(fields),
        context=context,
    )


def work_sort_context() -> dict[str, Any]:
    records = CatalogueSourceRecords(
        works={"00001": {"work_id": "00001", "series_ids": ["009"]}},
        work_details={},
        series={"009": {"series_id": "009", "sort_fields": "title"}},
    )
    record = records.works["00001"]
    return {"source_records": records, "current_record": record, "updated_record": record}


def source_fields_by_family() -> dict[str, set[str]]:
    return {
        **{family: set(fields) for family, fields in SOURCE_FIELDS_BY_RECORD_FAMILY.items()},
        **{family: set(fields) for family, fields in MOMENT_SOURCE_FIELDS.items()},
    }


def source_identity_fields_by_family() -> dict[str, set[str]]:
    return {
        **{family: set(fields) for family, fields in SOURCE_IDENTITY_FIELDS_BY_RECORD_FAMILY.items()},
        **{family: set(fields) for family, fields in MOMENT_SOURCE_IDENTITY_FIELDS.items()},
    }


def source_derived_fields_by_family() -> dict[str, set[str]]:
    return {
        **{family: set(fields) for family, fields in SOURCE_DERIVED_FIELDS_BY_RECORD_FAMILY.items()},
        **{family: set(fields) for family, fields in MOMENT_SOURCE_DERIVED_FIELDS.items()},
    }


def source_metadata_fields_by_family() -> dict[str, set[str]]:
    return {
        **{family: set(fields) for family, fields in SOURCE_METADATA_FIELDS_BY_RECORD_FAMILY.items()},
        **{family: set(fields) for family, fields in MOMENT_SOURCE_METADATA_FIELDS.items()},
    }


def iter_registry_field_rows(registry: Mapping[str, Any]) -> list[tuple[str, str, str, str]]:
    rows: list[tuple[str, str, str, str]] = []
    rules = registry.get("rules")
    if not isinstance(rules, list):
        fail("catalogue field registry missing rules[]")
    for index, rule in enumerate(rules):
        if not isinstance(rule, Mapping):
            fail(f"registry rule {index} is not an object")
        rule_id = str(rule.get("id") or "").strip()
        family = str(rule.get("record_family") or "").strip()
        operation = str(rule.get("operation") or "").strip()
        if not rule_id:
            fail(f"registry rule {index} is missing id")
        if not family:
            fail(f"registry rule {rule_id} is missing record_family")
        if not operation:
            fail(f"registry rule {rule_id} is missing operation")
        fields = rule.get("fields")
        if not isinstance(fields, list) or not fields:
            fail(f"registry rule {rule_id} is missing fields[]")
        for raw_field in fields:
            field = str(raw_field or "").strip()
            if not field:
                fail(f"registry rule {rule_id} has a blank field")
            rows.append((family, operation, field, rule_id))
    return rows


def verify_duplicate_rule_fields(registry: Mapping[str, Any]) -> int:
    seen: dict[tuple[str, str, str], str] = {}
    verified = 0
    for family, operation, field, rule_id in iter_registry_field_rows(registry):
        key = (family, operation, field)
        previous = seen.get(key)
        if previous is not None:
            fail(f"duplicate registry ownership for {family}.{operation}.{field}: {previous} and {rule_id}")
        seen[key] = rule_id
        verified += 1
    return verified


def verify_registry_fields_known_to_source(registry: Mapping[str, Any]) -> int:
    source_fields = source_fields_by_family()
    identity_fields = source_identity_fields_by_family()
    derived_fields = source_derived_fields_by_family()
    verified = 0

    for family, operation, field, _rule_id in iter_registry_field_rows(registry):
        allowed = source_fields.get(family)
        if allowed is None:
            fail(f"registry field {family}.{operation}.{field}: unknown record family")
        exemptions = REGISTRY_FIELD_EXEMPTIONS.get((family, operation), set())
        if field not in allowed and field not in exemptions:
            fail(f"registry field {family}.{operation}.{field}: field is not known to source schema")
        if operation == "metadata_update" and field in identity_fields.get(family, set()):
            fail(f"registry field {family}.{operation}.{field}: identity field cannot be metadata_update")
        if operation == "metadata_update" and field in derived_fields.get(family, set()):
            fail(f"registry field {family}.{operation}.{field}: derived field cannot be metadata_update")
        verified += 1
    return verified


def registry_fields_for_operation(registry: Mapping[str, Any], family: str, operation: str) -> set[str]:
    return {
        field
        for current_family, current_operation, field, _rule_id in iter_registry_field_rows(registry)
        if current_family == family and current_operation == operation
    }


def verify_source_metadata_fields_covered(registry: Mapping[str, Any]) -> int:
    verified = 0
    for family, source_fields in sorted(source_metadata_fields_by_family().items()):
        registry_fields = registry_fields_for_operation(registry, family, "metadata_update")
        exemptions = SOURCE_FIELD_EXEMPTIONS.get((family, "metadata_update"), set())
        missing = sorted(source_fields - registry_fields - exemptions)
        if missing:
            fail(f"{family}.metadata_update source fields missing registry coverage: {', '.join(missing)}")
        verified += len(source_fields)
    return verified


def assert_field_present(label: str, record: Mapping[str, Any], field: str, expected: Any) -> None:
    if field not in record:
        fail(f"{label}: expected {field} to be present")
    assert_equal(f"{label}.{field}", record.get(field), expected)


def assert_field_omitted(label: str, record: Mapping[str, Any], field: str) -> None:
    if field in record:
        fail(f"{label}: expected {field} to be omitted, got {record.get(field)!r}")


def verify_optional_source_serialization() -> int:
    if OMIT_EMPTY_SOURCE_FIELDS != {"project_subfolder", "details_subfolder", "sort_order"}:
        fail(f"unexpected omit-empty source fields: {sorted(OMIT_EMPTY_SOURCE_FIELDS)!r}")

    work_with_subfolder = normalize_source_record(
        {"work_id": "00001", "project_subfolder": "prints"},
        WORK_FIELDS,
        text_fields=WORK_TEXT_FIELDS,
    )
    assert_field_present("work project_subfolder non-empty", work_with_subfolder, "project_subfolder", "prints")
    for raw in (None, "", "   "):
        record = normalize_source_record(
            {"work_id": "00001", "project_subfolder": raw},
            WORK_FIELDS,
            text_fields=WORK_TEXT_FIELDS,
        )
        assert_field_omitted(f"work project_subfolder empty {raw!r}", record, "project_subfolder")

    detail_with_subfolder = normalize_source_record(
        {"detail_uid": "00001-001", "details_subfolder": "details"},
        DETAIL_FIELDS,
        text_fields=DETAIL_TEXT_FIELDS,
    )
    assert_field_present("detail details_subfolder non-empty", detail_with_subfolder, "details_subfolder", "details")
    for raw in (None, "", "   "):
        record = normalize_source_record(
            {"detail_uid": "00001-001", "details_subfolder": raw},
            DETAIL_FIELDS,
            text_fields=DETAIL_TEXT_FIELDS,
        )
        assert_field_omitted(f"detail details_subfolder empty {raw!r}", record, "details_subfolder")

    for raw, expected in ((0, 0), ("7", 7)):
        record = normalize_source_record(
            {"detail_uid": "00001-001", "sort_order": raw},
            DETAIL_FIELDS,
            text_fields=DETAIL_TEXT_FIELDS,
        )
        assert_field_present(f"detail sort_order non-empty {raw!r}", record, "sort_order", expected)
    for raw in (None, "", "   "):
        record = normalize_source_record(
            {"detail_uid": "00001-001", "sort_order": raw},
            DETAIL_FIELDS,
            text_fields=DETAIL_TEXT_FIELDS,
        )
        assert_field_omitted(f"detail sort_order empty {raw!r}", record, "sort_order")

    for field in ("section_id", "section_title"):
        blank_record = normalize_source_record(
            {"detail_uid": "00001-001", field: ""},
            DETAIL_FIELDS,
            text_fields=DETAIL_TEXT_FIELDS,
        )
        assert_field_present(f"detail required {field} blank", blank_record, field, None)
        non_blank_record = normalize_source_record(
            {"detail_uid": "00001-001", field: "value"},
            DETAIL_FIELDS,
            text_fields=DETAIL_TEXT_FIELDS,
        )
        assert_field_present(f"detail required {field} non-empty", non_blank_record, field, "value")

    return 14


def verify_registry_defaults(registry: Mapping[str, Any]) -> None:
    defaults = registry.get("defaults") if isinstance(registry.get("defaults"), Mapping) else {}
    for key in ("unknown_field", "mixed_dependency_classes"):
        target = (defaults.get(key) or {}).get("target") if isinstance(defaults.get(key), Mapping) else {}
        by_family = target.get("artifacts_by_record_family") if isinstance(target, Mapping) else {}
        for family in ("work", "work_detail", "series", "moment"):
            artifacts = by_family.get(family) if isinstance(by_family, Mapping) else None
            if not isinstance(artifacts, list) or not artifacts:
                fail(f"registry default {key} missing artifacts_by_record_family.{family}")


def main() -> None:
    registry = load_catalogue_field_registry(REPO_ROOT)
    verify_registry_defaults(registry)
    verified = 1
    verified += verify_duplicate_rule_fields(registry)
    verified += verify_registry_fields_known_to_source(registry)
    verified += verify_source_metadata_fields_covered(registry)
    verified += verify_optional_source_serialization()

    cases = [
        (
            "work local public metadata",
            plan_for(registry, record_family="work", fields=["downloads", "links"]),
            {
                "rule_id": "work_local_public_metadata",
                "artifacts": ["source-json", "studio-lookup", "work-json"],
                "generate_only": ["work-json"],
                "rebuild_search": False,
                "generate_local_media": False,
                "build_required": True,
            },
        ),
        (
            "work editor-only metadata",
            plan_for(registry, record_family="work", fields=["provenance"]),
            {
                "rule_id": "work_editor_only",
                "artifacts": ["source-json", "studio-lookup"],
                "generate_only": [],
                "rebuild_search": False,
                "generate_local_media": False,
                "build_required": False,
            },
        ),
        (
            "work media source metadata",
            plan_for(registry, record_family="work", fields=["project_subfolder", "project_filename"]),
            {
                "rule_id": "work_media_source",
                "artifacts": ["source-json", "studio-lookup", "local-media"],
                "generate_only": [],
                "rebuild_search": False,
                "generate_local_media": True,
                "build_required": True,
            },
        ),
        (
            "work search enrichment metadata",
            plan_for(registry, record_family="work", fields=["medium_type"]),
            {
                "rule_id": "work_search_enrichment",
                "artifacts": ["source-json", "studio-lookup", "work-json", "catalogue-search"],
                "generate_only": ["work-json"],
                "rebuild_search": True,
                "generate_local_media": False,
                "build_required": True,
            },
        ),
        (
            "work display metadata with series sort dependency",
            plan_for(registry, record_family="work", fields=["title"], context=work_sort_context()),
            {
                "rule_id": "work_display_core",
                "artifacts": [
                    "source-json",
                    "studio-lookup",
                    "work-json",
                    "works-index-json",
                    "recent-index-json",
                    "catalogue-search",
                    "series-index-json",
                ],
                "generate_only": ["work-json", "series-index-json", "works-index-json", "recent-index-json"],
                "rebuild_search": True,
                "generate_local_media": False,
                "build_required": True,
            },
        ),
        (
            "work publication membership metadata",
            plan_for(registry, record_family="work", fields=["series_ids"]),
            {
                "rule_id": "work_publish_membership",
                "artifacts": [
                    "source-json",
                    "studio-lookup",
                    "work-json",
                    "works-index-json",
                    "series-index-json",
                    "recent-index-json",
                    "catalogue-search",
                ],
                "generate_only": ["work-json", "series-index-json", "works-index-json", "recent-index-json"],
                "rebuild_search": True,
                "generate_local_media": False,
                "build_required": True,
            },
        ),
        (
            "work-detail public metadata",
            plan_for(registry, record_family="work_detail", fields=["title"]),
            {
                "rule_id": "work_detail_public_metadata",
                "artifacts": ["source-json", "studio-lookup", "work-json"],
                "generate_only": ["work-json"],
                "rebuild_search": False,
                "generate_local_media": False,
                "build_required": True,
            },
        ),
        (
            "work-detail media source metadata",
            plan_for(registry, record_family="work_detail", fields=["details_subfolder", "project_filename"]),
            {
                "rule_id": "work_detail_media_source",
                "artifacts": ["source-json", "studio-lookup", "local-media"],
                "generate_only": [],
                "rebuild_search": False,
                "generate_local_media": True,
                "build_required": True,
            },
        ),
        (
            "work-detail section metadata",
            plan_for(registry, record_family="work_detail", fields=["section_title", "sort_order"]),
            {
                "rule_id": "work_detail_section_metadata",
                "artifacts": ["source-json", "studio-lookup", "work-json"],
                "generate_only": ["work-json"],
                "rebuild_search": False,
                "generate_local_media": False,
                "build_required": True,
            },
        ),
        (
            "series publication metadata",
            plan_for(registry, record_family="series", fields=["status"]),
            {
                "rule_id": "series_publish_primary_order",
                "artifacts": [
                    "source-json",
                    "studio-lookup",
                    "series-json",
                    "series-index-json",
                    "recent-index-json",
                    "catalogue-search",
                ],
                "generate_only": ["series-pages", "series-index-json", "recent-index-json"],
                "rebuild_search": True,
                "generate_local_media": False,
                "build_required": True,
            },
        ),
        (
            "moment media source metadata",
            plan_for(registry, record_family="moment", fields=["source_image_file"]),
            {
                "rule_id": "moment_media_source",
                "artifacts": ["source-json", "local-media"],
                "generate_only": [],
                "rebuild_search": False,
                "generate_local_media": True,
                "build_required": True,
            },
        ),
        (
            "moment display metadata",
            plan_for(registry, record_family="moment", fields=["title"]),
            {
                "rule_id": "moment_display_search",
                "artifacts": ["source-json", "moment-json", "moments-index-json", "catalogue-search"],
                "generate_only": ["moments", "moments-index-json"],
                "rebuild_search": True,
                "generate_local_media": False,
                "build_required": True,
            },
        ),
    ]

    for label, current_plan, expected in cases:
        assert_plan(label, current_plan, **expected)
        verified += 1

    unknown_plan = plan_for(registry, record_family="work", fields=["made_up_field"])
    assert_plan(
        "unknown work field fallback",
        unknown_plan,
        rule_id=None,
        artifacts=[
            "source-json",
            "studio-lookup",
            "work-page",
            "work-json",
            "works-index-json",
            "series-page",
            "series-json",
            "series-index-json",
            "recent-index-json",
            "catalogue-search",
            "local-media",
        ],
        generate_only=["work-pages", "work-json", "series-pages", "series-index-json", "works-index-json", "recent-index-json"],
        rebuild_search=True,
        generate_local_media=True,
        fallback=True,
        fallback_reason="unknown_field",
        build_required=True,
    )
    verified += 1

    mixed_plan = plan_for(registry, record_family="work", fields=["duration", "title"])
    assert_plan(
        "mixed work dependency fallback",
        mixed_plan,
        rule_id=None,
        artifacts=[
            "source-json",
            "studio-lookup",
            "work-page",
            "work-json",
            "works-index-json",
            "series-page",
            "series-json",
            "series-index-json",
            "recent-index-json",
            "catalogue-search",
            "local-media",
        ],
        generate_only=["work-pages", "work-json", "series-pages", "series-index-json", "works-index-json", "recent-index-json"],
        rebuild_search=True,
        generate_local_media=True,
        fallback=True,
        fallback_reason="mixed_dependency_classes",
        build_required=True,
    )
    verified += 1

    series_cross_family_fallback = full_fallback_build_plan(
        registry,
        fields=["sort_fields", "work.series_ids"],
        fallback_reason="series_save_changed_member_works",
        reason="Series save also changed member work records; use conservative fallback until cross-family saves are scoped explicitly.",
        record_family="series",
    )
    assert_plan(
        "series save member-work fallback",
        series_cross_family_fallback,
        rule_id=None,
        artifacts=[
            "source-json",
            "studio-lookup",
            "series-page",
            "series-json",
            "series-index-json",
            "works-index-json",
            "recent-index-json",
            "catalogue-search",
        ],
        generate_only=["series-pages", "series-index-json", "works-index-json", "recent-index-json"],
        rebuild_search=True,
        generate_local_media=False,
        fallback=True,
        fallback_reason="series_save_changed_member_works",
        build_required=True,
    )
    verified += 1

    print(f"catalogue field registry verification passed ({verified} checks)")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as exc:
        print(f"catalogue field registry verification failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
