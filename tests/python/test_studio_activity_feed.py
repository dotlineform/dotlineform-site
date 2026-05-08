#!/usr/bin/env python3
"""Verify the unified Studio activity feed writer."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
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
                "source_refs": [{"kind": "log", "path": "var/studio/catalogue/logs/catalogue_write_server.log"}],
            },
        )
        payload = json.loads(feed_path.read_text(encoding="utf-8"))
        entry = payload["entries"][0]
        if payload["header"]["schema"] != "studio_activity_log_v1":
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


def main() -> None:
    test_append_hydrates_registry_labels_and_writes_feed()
    test_required_fields_are_validated()
    print("Studio activity feed tests OK")


if __name__ == "__main__":
    main()
