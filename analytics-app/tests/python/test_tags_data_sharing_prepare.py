#!/usr/bin/env python3
"""Analytics tags Data Sharing prepare tests."""

from __future__ import annotations

import json
from pathlib import Path

from adapters.tags import adapter, prepare
import data_sharing_service

from tags_data_sharing_adapter_test_support import (
    dependencies,
    make_repo,
    read_json,
    resolve_data_sharing_marker,
    resolve_tags_adapter,
)

def test_prepare_registry_package_dry_run_does_not_write() -> None:
    with make_repo() as temp:
        root = Path(temp)

        payload = prepare.prepare_package(
            root,
            {"data_domain": "tags", "config_id": "tag-registry", "target_format": "json"},
            dry_run=True,
            adapter=resolve_tags_adapter(root, "prepare"),
            dependencies=dependencies(),
        )

        output_path = resolve_data_sharing_marker(payload["output_file"])

    assert payload["ok"] is True
    assert payload["output_written"] is False
    assert payload["tag_family"] == "registry"
    assert payload["counts"]["tags"] == 3
    assert not output_path.exists()

def test_selectable_records_returns_tag_registry_records() -> None:
    with make_repo() as temp:
        root = Path(temp)

        payload = prepare.selectable_records(
            root,
            "tags",
            {"config_id": "tag-registry"},
            adapter=resolve_tags_adapter(root, "prepare"),
            dependencies=dependencies(),
        )

    assert payload["ok"] is True
    assert payload["selection_model"] == "records"
    assert payload["source"]["source"] == "tag_registry"
    assert [(record["id"], record["name"]) for record in payload["records"]] == [
        ("subject:stone", "stone"),
        ("subject:trees", "trees"),
        ("subject:water", "water"),
    ]

def test_prepare_registry_package_uses_selected_tag_records() -> None:
    with make_repo() as temp:
        root = Path(temp)

        payload = prepare.prepare_package(
            root,
            {
                "data_domain": "tags",
                "config_id": "tag-registry",
                "target_format": "json",
                "selection": {"record_ids": ["subject:water", "subject:stone", "subject:trees"], "select_all": False},
            },
            dry_run=False,
            adapter=resolve_tags_adapter(root, "prepare"),
            dependencies=dependencies(),
        )
        package = read_json(resolve_data_sharing_marker(payload["output_file"]))

    assert payload["ok"] is True
    assert payload["counts"]["selected"] == 3
    assert payload["counts"]["tags"] == 3
    assert [tag["tag_id"] for tag in package["tags"]] == ["subject:stone", "subject:trees", "subject:water"]

def test_tags_handlers_dispatch_through_data_sharing_workflow() -> None:
    with make_repo() as temp:
        root = Path(temp)
        handlers = {"analytics.tags": adapter.handlers_for(dependencies)}

        selectable = data_sharing_service.selectable_records(root, "tags", {"config_id": "tag-registry"}, handlers)
        payload = data_sharing_service.prepare_package(
            root,
            {"data_domain": "tags", "config_id": "tag-registry", "target_format": "json"},
            True,
            handlers,
        )

    assert selectable["ok"] is True
    assert selectable["adapter_id"] == "analytics-tags"
    assert selectable["source"]["source"] == "tag_registry"
    assert [record["id"] for record in selectable["records"]] == ["subject:stone", "subject:trees", "subject:water"]
    assert payload["ok"] is True
    assert payload["adapter_id"] == "analytics-tags"
    assert payload["tag_family"] == "registry"

def test_prepare_bundle_package_writes_under_outbound_root_and_activity() -> None:
    with make_repo() as temp:
        root = Path(temp)

        payload = prepare.prepare_package(
            root,
            {
                "data_domain": "tags",
                "config_id": "tags-bundle",
                "target_format": "json",
                "activity_context": {
                    "correlation_id": "test-tags-prepare",
                    "page_id": "data-sharing-prepare",
                    "action_id": "prepare-share-package",
                    "route": "/analytics/data-sharing/prepare/",
                    "control_id": "dataSharingPrepareRun",
                    "control_selector": "#dataSharingPrepareRun",
                    "export_id": "tags:tags-bundle",
                },
            },
            dry_run=False,
            adapter=resolve_tags_adapter(root, "prepare"),
            dependencies=dependencies(),
        )
        output_path = resolve_data_sharing_marker(payload["output_file"])
        package = read_json(output_path)
        activity_line = (root / "var/admin/activity/activity_log.jsonl").read_text(encoding="utf-8").splitlines()[-1]
        activity = json.loads(activity_line)

    assert payload["ok"] is True
    assert payload["output_written"] is True
    assert payload["output_file"].startswith("$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/exports/")
    assert payload["output_file"].endswith("-tags-bundle.json")
    assert package["package_metadata"]["package_family"] == "bundle"
    assert set(package["families"]) == {"registry", "aliases", "assignments"}
    assert activity["record_groups"]["files"]["sample_ids"] == [payload["output_file"]]
    assert activity["record_groups"]["tags"]["sample_ids"] == ["subject:stone", "subject:trees", "subject:water"]
