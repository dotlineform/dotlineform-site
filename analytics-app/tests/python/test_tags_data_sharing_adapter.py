#!/usr/bin/env python3
"""Focused checks for the Analytics tags Data Sharing adapter."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = REPO_ROOT / "scripts"
ANALYTICS_SERVER_DIR = REPO_ROOT / "analytics-app" / "app" / "server"
ANALYTICS_PACKAGE_DIR = ANALYTICS_SERVER_DIR / "analytics_app"
for path in (SCRIPTS_DIR, ANALYTICS_SERVER_DIR, ANALYTICS_PACKAGE_DIR):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

from data_sharing.adapters.tags import adapter  # noqa: E402
import data_sharing_service  # noqa: E402


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def make_registry_payload() -> dict[str, object]:
    return {
        "schema_version": "data_sharing_adapters_v2",
        "dispatch": [
            {"data_domain": "tags", "operation": "prepare", "adapter_id": "analytics-tags"},
            {"data_domain": "tags", "operation": "list_returned", "adapter_id": "analytics-tags"},
            {"data_domain": "tags", "operation": "review", "adapter_id": "analytics-tags"},
            {"data_domain": "tags", "operation": "apply", "adapter_id": "analytics-tags"},
        ],
        "adapters": [
            {
                "id": "analytics-tags",
                "module": "analytics.tags",
                "label": "Tags",
                "status": "active",
                "portability": {"package": "analytics-tags-data-sharing"},
                "data_domains": {
                    "tags": {
                        "app": "analytics",
                        "label": "Tags",
                        "status": "active",
                        "selection_model": "records",
                        "paths": {
                            "outbound_package_root": "var/analytics/data-sharing/tags/exports",
                            "returned_package_staging_root": "var/analytics/data-sharing/tags/import-staging",
                            "review_output_root": "var/analytics/data-sharing/tags/import-preview",
                            "source_root": "analytics-app/data/canonical",
                        },
                        "source_write_targets": {
                            "tag_registry": "analytics-app/data/canonical/tag-registry.json",
                            "tag_aliases": "analytics-app/data/canonical/tag-aliases.json",
                            "tag_assignments": "analytics-app/data/canonical/tag-assignments.json",
                        },
                        "sources": {
                            "tag_registry": "analytics-app/data/canonical/tag-registry.json",
                            "tag_aliases": "analytics-app/data/canonical/tag-aliases.json",
                            "tag_assignments": "analytics-app/data/canonical/tag-assignments.json",
                            "series": "site/assets/data/series_index.json",
                            "works": "site/assets/data/works_index.json",
                        },
                        "config": {},
                    }
                },
                "capabilities": [
                    {
                        "operation": "prepare",
                        "status": "active",
                        "selection_model": "none",
                        "input_formats": [],
                        "output_formats": ["json"],
                        "sharing_profiles": [
                            {
                                "id": "tag-registry",
                                "label": "Tag registry",
                                "enabled": True,
                                "data_domains": ["tags"],
                                "family": "registry",
                                "target": {"format": "json", "supported_formats": ["json"]},
                                "selection": {"mode": "none"},
                            },
                            {
                                "id": "tags-bundle",
                                "label": "Combined tags bundle",
                                "enabled": True,
                                "data_domains": ["tags"],
                                "family": "bundle",
                                "target": {"format": "json", "supported_formats": ["json"]},
                                "selection": {"mode": "none"},
                            },
                        ],
                        "path_contract": {"output_root": "outbound_package_root"},
                        "activity": {
                            "script_purpose": "data-sharing-prepare",
                            "record_groups": ["tags", "aliases", "series", "works", "files"],
                        },
                    },
                    {
                        "operation": "list_returned",
                        "status": "active",
                        "selection_model": "none",
                        "input_formats": ["json", "jsonl"],
                        "output_formats": [],
                        "path_contract": {"staging_root": "returned_package_staging_root"},
                        "activity": {"script_purpose": "data-sharing-list-returned", "record_groups": ["files"]},
                    },
                    {
                        "operation": "review",
                        "status": "active",
                        "selection_model": "file_only",
                        "input_formats": ["json", "jsonl"],
                        "output_formats": ["json"],
                        "path_contract": {
                            "staging_root": "returned_package_staging_root",
                            "review_output_root": "review_output_root",
                        },
                        "review_rows": {
                            "fields": ["id", "type", "title", "meta", "record_index", "selectable", "record_groups", "issues"]
                        },
                        "activity": {"script_purpose": "data-sharing-review", "record_groups": ["tags", "aliases", "series", "works", "files"]},
                    },
                    {
                        "operation": "apply",
                        "status": "active",
                        "selection_model": "records",
                        "input_formats": ["json", "jsonl"],
                        "output_formats": [],
                        "path_contract": {
                            "staging_root": "returned_package_staging_root",
                            "source_root": "source_root",
                        },
                        "requires_confirmation": True,
                        "apply_actions": [
                            {
                                "id": "registry_apply",
                                "label": "Apply tag registry changes",
                                "status": "active",
                                "confirmation": {"title": "Apply tag registry changes?", "body": "Update registry."},
                                "activity": {"script_purpose": "save-tag-data", "record_groups": ["tags", "files"]},
                            },
                            {
                                "id": "aliases_apply",
                                "label": "Apply tag alias changes",
                                "status": "active",
                                "confirmation": {"title": "Apply tag alias changes?", "body": "Update aliases."},
                                "activity": {"script_purpose": "save-tag-data", "record_groups": ["aliases", "tags", "files"]},
                            },
                            {
                                "id": "assignments_apply",
                                "label": "Apply tag assignment changes",
                                "status": "active",
                                "confirmation": {"title": "Apply tag assignment changes?", "body": "Update assignments."},
                                "activity": {"script_purpose": "save-tag-data", "record_groups": ["series", "works", "tags", "files"]},
                            },
                        ],
                        "activity": {"script_purpose": "save-tag-data", "record_groups": ["tags", "aliases", "series", "works", "files"]},
                    },
                ],
            }
        ],
    }


def write_activity_contract(root: Path) -> None:
    write_json(
        root / "studio/data/config/runtime/activity-contract.json",
        {
            "pages": {
                "data-sharing-prepare": {
                    "label": "data sharing prepare",
                    "route": "/analytics/data-sharing/prepare/?mode=manage",
                    "actions": {
                        "prepare-share-package": {
                            "label": "prepare share package",
                            "endpoint": "/data-sharing/prepare",
                            "route": "/analytics/data-sharing/prepare/?mode=manage",
                            "control_id": "dataSharingPrepareRun",
                            "control_selector": "#dataSharingPrepareRun",
                            "record_id_field": "export_id",
                        }
                    },
                },
                "data-sharing-review": {
                    "label": "data sharing review",
                    "route": "/analytics/data-sharing/review/?mode=manage",
                    "actions": {
                        "apply-returned-tag-assignments": {
                            "label": "apply returned tag assignments",
                            "endpoint": "/data-sharing/apply",
                            "route": "/analytics/data-sharing/review/?mode=manage",
                            "control_id": "dataSharingReviewApplyTagAssignments",
                            "control_selector": "#dataSharingReviewApplyTagAssignments",
                            "record_id_field": "staged_filename",
                        }
                    },
                }
            },
            "script_purposes": {
                "prepare-share-package": {"label": "prepare share package"},
                "save-tag-data": {"label": "save tag data"},
            },
        },
    )


def make_repo() -> tempfile.TemporaryDirectory[str]:
    temp_dir: tempfile.TemporaryDirectory[str] = tempfile.TemporaryDirectory()
    root = Path(temp_dir.name)
    (root / "site-tools/config").mkdir(parents=True, exist_ok=True); (root / "site-tools/config/site-tools.json").write_text("{\"schema_version\":\"site_tools_config_v1\"}\n", encoding="utf-8")
    write_json(root / "data-sharing/config/adapters.json", make_registry_payload())
    write_json(
        root / "analytics-app/data/canonical/tag-registry.json",
        {
            "tag_registry_version": "tag_registry_v1",
            "policy": {"allowed_groups": ["subject", "domain", "form", "theme"]},
            "tags": [
                {"tag_id": "subject:trees", "group": "subject", "label": "trees", "status": "active", "description": "Trees"},
                {"tag_id": "subject:water", "group": "subject", "label": "water", "status": "active", "description": "Water"},
                {"tag_id": "subject:stone", "group": "subject", "label": "stone", "status": "active", "description": "Stone"},
            ],
        },
    )
    write_json(
        root / "analytics-app/data/canonical/tag-aliases.json",
        {
            "tag_aliases_version": "tag_aliases_v1",
            "aliases": {"woods": {"description": "", "tags": ["subject:trees"]}},
        },
    )
    write_json(
        root / "analytics-app/data/canonical/tag-assignments.json",
        {
            "tag_assignments_version": "tag_assignments_v1",
            "series": {
                "series-a": {
                    "tags": [{"tag_id": "subject:trees", "w_manual": 0.6}],
                    "updated_at_utc": "2026-01-01T00:00:00Z",
                },
                "series-b": {
                    "tags": [{"tag_id": "subject:water", "w_manual": 0.6}],
                    "updated_at_utc": "2026-01-02T00:00:00Z",
                },
                "series-c": {"tags": [], "updated_at_utc": "2026-01-03T00:00:00Z"},
            },
        },
    )
    write_json(
        root / "site/assets/data/series_index.json",
        {
            "series": {
                "series-a": {"works": ["00001"]},
                "series-b": {"works": ["00002"]},
                "series-c": {"works": ["00003"]},
            }
        },
    )
    write_activity_contract(root)
    (root / "var/analytics/data-sharing/tags/import-staging").mkdir(parents=True, exist_ok=True)
    return temp_dir


def dependencies() -> adapter.TagsDataSharingDependencies:
    events: list[tuple[Path, str, dict[str, object]]] = []

    def log_event(repo_root: Path, event: str, details: dict[str, object]) -> None:
        events.append((repo_root, event, details))

    return adapter.TagsDataSharingDependencies(log_event=log_event)


def resolve_tags_adapter(root: Path, operation: str = "prepare"):
    return data_sharing_service.resolve_for_service(root, "tags", operation)


def test_list_returned_packages_finds_json_files() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_json(root / "var/analytics/data-sharing/tags/import-staging/registry.json", {"import_registry": {"tags": []}})

        payload = adapter.list_returned_packages(
            root,
            "tags",
            adapter=resolve_tags_adapter(root, "list_returned"),
            dependencies=dependencies(),
        )

    assert payload["ok"] is True
    assert [item["filename"] for item in payload["files"]] == ["registry.json"]


def test_prepare_registry_package_dry_run_does_not_write() -> None:
    with make_repo() as temp:
        root = Path(temp)

        payload = adapter.prepare_package(
            root,
            {"data_domain": "tags", "config_id": "tag-registry", "target_format": "json"},
            dry_run=True,
            adapter=resolve_tags_adapter(root, "prepare"),
            dependencies=dependencies(),
        )

        output_path = root / payload["output_file"]

    assert payload["ok"] is True
    assert payload["output_written"] is False
    assert payload["tag_family"] == "registry"
    assert payload["counts"]["tags"] == 3
    assert not output_path.exists()


def test_tags_handlers_dispatch_through_data_sharing_workflow() -> None:
    with make_repo() as temp:
        root = Path(temp)
        handlers = {"analytics.tags": adapter.handlers_for(dependencies)}

        selectable = data_sharing_service.selectable_records(root, "tags", {}, handlers)
        payload = data_sharing_service.prepare_package(
            root,
            {"data_domain": "tags", "config_id": "tag-registry", "target_format": "json"},
            True,
            handlers,
        )

    assert selectable["ok"] is True
    assert selectable["adapter_id"] == "analytics-tags"
    assert selectable["source"]["source"] == "profile_only"
    assert payload["ok"] is True
    assert payload["adapter_id"] == "analytics-tags"
    assert payload["tag_family"] == "registry"


def test_prepare_bundle_package_writes_under_outbound_root_and_activity() -> None:
    with make_repo() as temp:
        root = Path(temp)

        payload = adapter.prepare_package(
            root,
            {
                "data_domain": "tags",
                "config_id": "tags-bundle",
                "target_format": "json",
                "activity_context": {
                    "correlation_id": "test-tags-prepare",
                    "page_id": "data-sharing-prepare",
                    "action_id": "prepare-share-package",
                    "route": "/analytics/data-sharing/prepare/?mode=manage",
                    "control_id": "dataSharingPrepareRun",
                    "control_selector": "#dataSharingPrepareRun",
                    "export_id": "tags:tags-bundle",
                },
            },
            dry_run=False,
            adapter=resolve_tags_adapter(root, "prepare"),
            dependencies=dependencies(),
        )
        output_path = root / payload["output_file"]
        package = read_json(output_path)
        activity_line = (root / "var/admin/activity/activity_log.jsonl").read_text(encoding="utf-8").splitlines()[-1]
        activity = json.loads(activity_line)

    assert payload["ok"] is True
    assert payload["output_written"] is True
    assert payload["output_file"].startswith("var/analytics/data-sharing/tags/exports/tags-bundle-")
    assert package["package_metadata"]["package_family"] == "bundle"
    assert set(package["families"]) == {"registry", "aliases", "assignments"}
    assert activity["record_groups"]["files"]["sample_ids"] == [payload["output_file"]]
    assert activity["record_groups"]["tags"]["sample_ids"] == ["subject:stone", "subject:trees", "subject:water"]


def test_registry_review_and_confirmed_apply_writes_source() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_json(
            root / "var/analytics/data-sharing/tags/import-staging/registry.json",
            {
                "mode": "merge",
                "import_registry": {
                    "tags": [
                        {"tag_id": "subject:trees", "group": "subject", "status": "active", "description": "Forest"},
                        {"tag_id": "subject:sky", "group": "subject", "status": "active", "description": "Sky"},
                    ]
                },
            },
        )

        review = adapter.review_returned_package(
            root,
            {"data_domain": "tags", "operation": "review", "staged_filename": "registry.json"},
            dry_run=True,
            adapter=resolve_tags_adapter(root, "review"),
            dependencies=dependencies(),
        )
        preflight = adapter.apply_returned_changes(
            root,
            {
                "data_domain": "tags",
                "operation": "apply",
                "apply_action": "registry_apply",
                "staged_filename": "registry.json",
                "record_indices": [0, 1],
                "confirm": False,
            },
            dry_run=False,
            adapter=resolve_tags_adapter(root, "apply"),
            dependencies=dependencies(),
        )
        applied = adapter.apply_returned_changes(
            root,
            {
                "data_domain": "tags",
                "operation": "apply",
                "apply_action": "registry_apply",
                "staged_filename": "registry.json",
                "record_indices": [0, 1],
                "confirm": True,
            },
            dry_run=False,
            adapter=resolve_tags_adapter(root, "apply"),
            dependencies=dependencies(),
        )
        registry = read_json(root / "analytics-app/data/canonical/tag-registry.json")

    assert review["ok"] is True
    assert [row["title"] for row in review["review_rows"]] == ["subject:trees", "subject:sky"]
    assert preflight["requires_confirmation"] is True
    assert preflight["written"] is False
    assert applied["written"] is True
    assert "backup_files" not in applied
    assert {item["tag_id"] for item in registry["tags"]} == {"subject:trees", "subject:water", "subject:stone", "subject:sky"}


def test_aliases_review_and_preflight_validate_without_writing() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_json(
            root / "var/analytics/data-sharing/tags/import-staging/aliases.json",
            {
                "mode": "merge",
                "import_aliases": {
                    "aliases": {
                        "forest": {"description": "Forest", "tags": ["subject:trees"]},
                        "river": {"description": "River", "tags": ["subject:water"]},
                    }
                },
            },
        )

        review = adapter.review_returned_package(
            root,
            {"data_domain": "tags", "operation": "review", "staged_filename": "aliases.json"},
            dry_run=True,
            adapter=resolve_tags_adapter(root, "review"),
            dependencies=dependencies(),
        )
        preflight = adapter.apply_returned_changes(
            root,
            {
                "data_domain": "tags",
                "operation": "apply",
                "apply_action": "aliases_apply",
                "staged_filename": "aliases.json",
                "record_indices": [0, 1],
                "confirm": False,
            },
            dry_run=False,
            adapter=resolve_tags_adapter(root, "apply"),
            dependencies=dependencies(),
        )
        aliases = read_json(root / "analytics-app/data/canonical/tag-aliases.json")

    assert review["counts"]["records"] == 2
    assert [row["type"] for row in review["review_rows"]] == ["alias", "alias"]
    assert preflight["requires_confirmation"] is True
    assert aliases["aliases"] == {"woods": {"description": "", "tags": ["subject:trees"]}}


def test_assignments_review_reports_applicable_conflict_invalid_and_missing() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_json(
            root / "var/analytics/data-sharing/tags/import-staging/assignments.json",
            {
                "import_assignments": {
                    "series": {
                        "series-a": {
                            "base_row_snapshot": {"tags": [{"tag_id": "subject:trees", "w_manual": 0.6}]},
                            "staged_row": {"tags": [{"tag_id": "subject:sky", "w_manual": 0.6}]},
                        },
                        "series-b": {
                            "base_row_snapshot": {"tags": []},
                            "staged_row": {"tags": [{"tag_id": "subject:stone", "w_manual": 0.6}]},
                        },
                        "series-c": {
                            "base_row_snapshot": {"tags": []},
                            "staged_row": {
                                "tags": [],
                                "works": {"99999": {"tags": [{"tag_id": "subject:stone", "w_manual": 0.6}]}},
                            },
                        },
                        "series-missing": {
                            "base_row_snapshot": {"tags": []},
                            "staged_row": {"tags": [{"tag_id": "subject:stone", "w_manual": 0.6}]},
                        },
                    }
                }
            },
        )

        review = adapter.review_returned_package(
            root,
            {"data_domain": "tags", "operation": "review", "staged_filename": "assignments.json"},
            dry_run=True,
            adapter=resolve_tags_adapter(root, "review"),
            dependencies=dependencies(),
        )

    assert review["counts"]["applicable"] == 1
    assert review["counts"]["conflicts"] == 1
    assert review["counts"]["invalid"] == 1
    assert review["counts"]["missing"] == 1
    assert [(row["title"], row["meta"], row["selectable"]) for row in review["review_rows"]] == [
        ("series-a", "apply", True),
        ("series-b", "conflict", False),
        ("series-c", "invalid", False),
        ("series-missing", "missing", False),
    ]


def test_assignments_confirmed_apply_writes_source_and_activity_groups() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_json(
            root / "var/analytics/data-sharing/tags/import-staging/assignments.json",
            {
                "import_assignments": {
                    "series": {
                        "series-a": {
                            "base_row_snapshot": {"tags": [{"tag_id": "subject:trees", "w_manual": 0.6}]},
                            "staged_row": {
                                "tags": [{"tag_id": "subject:sky", "w_manual": 0.6}],
                                "works": {"00001": {"tags": [{"tag_id": "subject:stone", "w_manual": 0.6}]}},
                            },
                        }
                    }
                }
            },
        )

        preflight = adapter.apply_returned_changes(
            root,
            {
                "data_domain": "tags",
                "operation": "apply",
                "apply_action": "assignments_apply",
                "staged_filename": "assignments.json",
                "record_indices": [0],
                "confirm": False,
            },
            dry_run=False,
            adapter=resolve_tags_adapter(root, "apply"),
            dependencies=dependencies(),
        )
        applied = adapter.apply_returned_changes(
            root,
            {
                "data_domain": "tags",
                "operation": "apply",
                "apply_action": "assignments_apply",
                "staged_filename": "assignments.json",
                "record_indices": [0],
                "confirm": True,
                "activity_context": {
                    "correlation_id": "test-tags-assignments",
                    "page_id": "data-sharing-review",
                    "action_id": "apply-returned-tag-assignments",
                    "route": "/analytics/data-sharing/review/?mode=manage",
                    "control_id": "dataSharingReviewApplyTagAssignments",
                    "control_selector": "#dataSharingReviewApplyTagAssignments",
                    "staged_filename": "assignments.json",
                },
            },
            dry_run=False,
            adapter=resolve_tags_adapter(root, "apply"),
            dependencies=dependencies(),
        )
        assignments = read_json(root / "analytics-app/data/canonical/tag-assignments.json")
        activity_line = (root / "var/admin/activity/activity_log.jsonl").read_text(encoding="utf-8").splitlines()[-1]
        activity = json.loads(activity_line)

    assert preflight["requires_confirmation"] is True
    assert applied["written"] is True
    assert "backup_files" not in applied
    assert assignments["series"]["series-a"]["tags"] == [{"tag_id": "subject:sky", "w_manual": 0.6}]
    assert activity["record_groups"]["series"]["sample_ids"] == ["series-a"]
    assert activity["record_groups"]["works"]["sample_ids"] == ["00001"]
    assert activity["record_groups"]["tags"]["sample_ids"] == ["subject:sky", "subject:stone"]


def main() -> None:
    tests = [
        test_list_returned_packages_finds_json_files,
        test_prepare_registry_package_dry_run_does_not_write,
        test_tags_handlers_dispatch_through_data_sharing_workflow,
        test_prepare_bundle_package_writes_under_outbound_root_and_activity,
        test_registry_review_and_confirmed_apply_writes_source,
        test_aliases_review_and_preflight_validate_without_writing,
        test_assignments_review_reports_applicable_conflict_invalid_and_missing,
        test_assignments_confirmed_apply_writes_source_and_activity_groups,
    ]
    for test in tests:
        test()


if __name__ == "__main__":
    main()
