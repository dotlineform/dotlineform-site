#!/usr/bin/env python3
"""Verify the unified Studio activity feed writer."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import studio_activity  # noqa: E402


def write_contract(repo_root: Path) -> None:
    contract_path = repo_root / studio_activity.ACTIVITY_CONTRACT_REL_PATH
    contract_path.parent.mkdir(parents=True, exist_ok=True)
    contract_path.write_text(
        json.dumps(
            {
                "pages": {
                    "catalogue-work": {
                        "label": "catalogue work editor",
                        "actions": {
                            "save-work": {
                                "label": "save work",
                            }
                        },
                    }
                },
                "script_purposes": {
                    "save-canonical-data": {
                        "label": "save canonical data",
                    }
                },
            }
        ),
        encoding="utf-8",
    )


def write_context_contract(repo_root: Path) -> None:
    contract_path = repo_root / studio_activity.ACTIVITY_CONTRACT_REL_PATH
    contract_path.parent.mkdir(parents=True, exist_ok=True)
    contract_path.write_text(
        json.dumps(
            {
                "pages": {
                    "data-sharing-prepare": {
                        "label": "data sharing prepare",
                        "route": "/analytics/data-sharing/prepare/?mode=manage",
                        "actions": {
                            "prepare-share-package": {
                                "label": "prepare share package",
                                "control_id": "dataSharingPrepareRun",
                                "control_selector": "#dataSharingPrepareRun",
                                "endpoint": "/data-sharing/prepare",
                                "record_id_field": "export_id",
                            }
                        },
                    }
                },
                "script_purposes": {
                    "prepare-share-package": {
                        "label": "prepare share package",
                    }
                },
            }
        ),
        encoding="utf-8",
    )


def test_append_hydrates_registry_labels_and_writes_feed() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo_root = Path(tmp)
        write_contract(repo_root)
        _, feed_path = studio_activity.append_studio_activity(
            repo_root,
            {
                "id": "2026-05-08T16:50:00Z-save-1-save-canonical-data",
                "activity_id": "2026-05-08T16:50:00Z-save-1-save-canonical-data",
                "correlation_id": "save-1",
                "timestamp": "2026-05-08T16:50:00Z",
                "status": "completed",
                "page_id": "catalogue-work",
                "user_action_id": "save-work",
                "script_purpose_id": "save-canonical-data",
                "record_groups": {"works": ["00001"], "series": [], "work_details": [], "moments": []},
                "detail_items": ["Saved canonical work record 00001"],
                "source_refs": [{"kind": "log", "path": "var/studio/catalogue/logs/catalogue_service_context.log"}],
            },
        )
        if feed_path != repo_root.resolve() / "var/admin/activity/activity_log.json":
            raise AssertionError("feed path should stay under var/admin/activity/")
        payload = json.loads(feed_path.read_text(encoding="utf-8"))
        entry = payload["entries"][0]
        if payload["header"]["schema"] != "admin_activity_log_v1":
            raise AssertionError("unexpected feed schema")
        if entry["page_label"] != "catalogue work editor":
            raise AssertionError("page label was not hydrated from the activity contract")
        if entry["user_action_label"] != "save work":
            raise AssertionError("user action label was not hydrated from the activity contract")
        if entry["script_purpose_label"] != "save canonical data":
            raise AssertionError("script purpose label was not hydrated from the activity contract")
        if entry["record_groups"]["works"]["sample_ids"] != ["00001"]:
            raise AssertionError("work ids were not compacted")
        if entry["detail_items"] != ["Saved canonical work record 00001"]:
            raise AssertionError("detail items were not preserved")


def test_required_fields_are_validated() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo_root = Path(tmp)
        write_contract(repo_root)
        try:
            studio_activity.append_studio_activity(
                repo_root,
                {
                    "id": "missing-correlation",
                    "timestamp": "2026-05-08T16:50:00Z",
                    "page_id": "catalogue-work",
                    "user_action_id": "save-work",
                    "script_purpose_id": "save-canonical-data",
                },
            )
        except ValueError as exc:
            if "correlation_id" not in str(exc):
                raise AssertionError(f"unexpected validation error: {exc}") from exc
            return
        raise AssertionError("expected missing correlation_id to fail")


def test_context_normalizer_validates_contract_action() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo_root = Path(tmp)
        write_context_contract(repo_root)
        context = studio_activity.normalize_activity_context_from_contract(
            repo_root,
            {
                "page_id": "data-sharing-prepare",
                "action_id": "prepare-share-package",
                "route": "/analytics/data-sharing/prepare/?mode=manage",
                "control_id": "dataSharingPrepareRun",
                "control_selector": "#dataSharingPrepareRun",
                "correlation_id": "export:test",
                "export_id": "library:missing-summary",
            },
            endpoint="/data-sharing/prepare",
            record_id="library:missing-summary",
        )
        if context["action_id"] != "prepare-share-package":
            raise AssertionError("action id was not preserved")
        if context["export_id"] != "library:missing-summary":
            raise AssertionError("record id was not preserved")

        try:
            studio_activity.normalize_activity_context_from_contract(
                repo_root,
                {
                    "page_id": "data-sharing-prepare",
                    "action_id": "prepare-share-package",
                    "route": "/analytics/data-sharing/prepare/?mode=manage",
                    "control_id": "dataSharingPrepareRun",
                    "control_selector": "#dataSharingPrepareRun",
                    "correlation_id": "export:test",
                    "export_id": "library:missing-summary",
                },
                endpoint="/data-sharing/apply",
                record_id="library:missing-summary",
            )
        except ValueError as exc:
            if "endpoint" not in str(exc):
                raise AssertionError(f"unexpected validation error: {exc}") from exc
            return
        raise AssertionError("expected endpoint mismatch to fail")


def test_activity_entry_suffix_keeps_shared_action_rows_distinct() -> None:
    context = {
        "correlation_id": "save-series-tags:009",
        "page_id": "series-tag-editor",
        "action_id": "save-series-tags",
    }
    first = studio_activity.studio_activity_entry(
        context,
        script_purpose_id="save-tag-data",
        now_utc="2026-05-08T16:50:00Z",
        activity_id_suffix="series:009",
    )
    second = studio_activity.studio_activity_entry(
        context,
        script_purpose_id="save-tag-data",
        now_utc="2026-05-08T16:50:00Z",
        activity_id_suffix="work:00001",
    )
    if first["activity_id"] == second["activity_id"]:
        raise AssertionError("activity id suffix did not distinguish shared-action rows")
    if not first["activity_id"].endswith("-series:009"):
        raise AssertionError("series activity id suffix was not preserved")
    if not second["activity_id"].endswith("-work:00001"):
        raise AssertionError("work activity id suffix was not preserved")


def main() -> None:
    test_append_hydrates_registry_labels_and_writes_feed()
    test_required_fields_are_validated()
    test_context_normalizer_validates_contract_action()
    test_activity_entry_suffix_keeps_shared_action_rows_distinct()
    print("Studio activity feed tests OK")


if __name__ == "__main__":
    main()
