"""Shared fixtures for Analytics tags Data Sharing adapter tests."""

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

from adapters.tags import adapter, context, prepare, returned  # noqa: E402
import data_sharing_service  # noqa: E402


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def make_registry_payload() -> dict[str, object]:
    return {
        "schema_version": "data_sharing_adapters_v2",
        "paths": {
            "outbound_package_root": "var/analytics/data-sharing/exports",
            "returned_package_staging_root": "var/analytics/data-sharing/import-staging",
            "review_output_root": "var/analytics/data-sharing/import-preview",
        },
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
                        "selection_model": "records",
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
                                "selection": {"mode": "explicit_record_ids"},
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
                    "route": "/analytics/data-sharing/prepare/",
                    "actions": {
                        "prepare-share-package": {
                            "label": "prepare share package",
                            "endpoint": "/data-sharing/prepare",
                            "route": "/analytics/data-sharing/prepare/",
                            "control_id": "dataSharingPrepareRun",
                            "control_selector": "#dataSharingPrepareRun",
                            "record_id_field": "export_id",
                        }
                    },
                },
                "data-sharing-review": {
                    "label": "data sharing review",
                    "route": "/analytics/data-sharing/review/",
                    "actions": {
                        "apply-returned-tag-assignments": {
                            "label": "apply returned tag assignments",
                            "endpoint": "/data-sharing/apply",
                            "route": "/analytics/data-sharing/review/",
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
                {"tag_id": "subject:trees", "group": "subject", "label": "trees", "description": "Trees"},
                {"tag_id": "subject:water", "group": "subject", "label": "water", "description": "Water"},
                {"tag_id": "subject:stone", "group": "subject", "label": "stone", "description": "Stone"},
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
    (root / "var/analytics/data-sharing/import-staging").mkdir(parents=True, exist_ok=True)
    return temp_dir


def dependencies() -> context.TagsDataSharingDependencies:
    events: list[tuple[Path, str, dict[str, object]]] = []

    def log_event(repo_root: Path, event: str, details: dict[str, object]) -> None:
        events.append((repo_root, event, details))

    return context.TagsDataSharingDependencies(log_event=log_event)


def resolve_tags_adapter(root: Path, operation: str = "prepare"):
    return data_sharing_service.resolve_for_service(root, "tags", operation)
