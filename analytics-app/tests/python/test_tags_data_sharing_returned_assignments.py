#!/usr/bin/env python3
"""Analytics tags returned assignment tests."""

from __future__ import annotations

import json
from pathlib import Path

from adapters.tags import returned

from tags_data_sharing_adapter_test_support import dependencies, make_repo, read_json, resolve_tags_adapter, write_json

def test_assignments_review_reports_applicable_conflict_invalid_and_missing() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_json(
            root / "var/analytics/data-sharing/import-staging/assignments.json",
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

        review = returned.review_returned_package(
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
            root / "var/analytics/data-sharing/import-staging/assignments.json",
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

        preflight = returned.apply_returned_changes(
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
        applied = returned.apply_returned_changes(
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
                    "route": "/analytics/data-sharing/review/",
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
