#!/usr/bin/env python3
"""Verify representative catalogue field-registry build plans."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from catalogue_field_registry import field_aware_build_plan, full_fallback_build_plan, load_catalogue_field_registry  # noqa: E402
from catalogue_source import CatalogueSourceRecords  # noqa: E402


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
            plan_for(registry, record_family="work", fields=["notes", "provenance"]),
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
            plan_for(registry, record_family="work_detail", fields=["status"]),
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
            "series notes metadata",
            plan_for(registry, record_family="series", fields=["notes"]),
            {
                "rule_id": "series_public_notes",
                "artifacts": ["source-json", "studio-lookup", "series-json", "series-index-json"],
                "generate_only": ["series-pages", "series-index-json"],
                "rebuild_search": False,
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
