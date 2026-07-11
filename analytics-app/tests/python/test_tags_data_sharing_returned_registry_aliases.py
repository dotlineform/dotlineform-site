#!/usr/bin/env python3
"""Analytics tags returned registry and aliases tests."""

from __future__ import annotations

from pathlib import Path

from adapters.tags import returned

from tags_data_sharing_adapter_test_support import (
    data_sharing_workspace_path,
    dependencies,
    make_repo,
    read_json,
    resolve_tags_adapter,
    write_json,
)

def test_list_returned_packages_finds_json_files() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_json(data_sharing_workspace_path("import-staging/registry.json"), {"import_registry": {"tags": []}})
        data_sharing_workspace_path("import-staging/documents-document-content-20260627-120000.jsonl").write_text(
            '{"doc_id":"alpha","title":"Alpha","source_text":"Document body."}\n',
            encoding="utf-8",
        )

        payload = returned.list_returned_packages(
            root,
            "tags",
            adapter=resolve_tags_adapter(root, "list_returned"),
            dependencies=dependencies(),
        )

    assert payload["ok"] is True
    assert [item["filename"] for item in payload["files"]] == ["registry.json"]

def test_registry_review_and_confirmed_apply_writes_source() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_json(
            data_sharing_workspace_path("import-staging/registry.json"),
            {
                "mode": "merge",
                "import_registry": {
                    "tags": [
                        {"tag_id": "subject:trees", "group": "subject", "description": "Forest"},
                        {"tag_id": "subject:sky", "group": "subject", "description": "Sky"},
                    ]
                },
            },
        )

        review = returned.review_returned_package(
            root,
            {"data_domain": "tags", "operation": "review", "staged_filename": "registry.json"},
            dry_run=True,
            adapter=resolve_tags_adapter(root, "review"),
            dependencies=dependencies(),
        )
        preflight = returned.apply_returned_changes(
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
        applied = returned.apply_returned_changes(
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
            data_sharing_workspace_path("import-staging/aliases.json"),
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

        review = returned.review_returned_package(
            root,
            {"data_domain": "tags", "operation": "review", "staged_filename": "aliases.json"},
            dry_run=True,
            adapter=resolve_tags_adapter(root, "review"),
            dependencies=dependencies(),
        )
        preflight = returned.apply_returned_changes(
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
