#!/usr/bin/env python3
"""Focused checks for Admin site-consistency source resolution."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = REPO_ROOT / "admin-app" / "checks" / "audit_site_consistency.py"
SPEC = importlib.util.spec_from_file_location("audit_site_consistency", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def test_studio_source_paths_resolve_from_repo_root(tmp_path: Path) -> None:
    assignments_path = audit.resolve_repo_source_path(
        audit.tag_source_paths.TAG_ASSIGNMENTS_REL_PATH,
        tmp_path,
    )
    series_path = audit.resolve_repo_source_path(
        Path("studio/data/canonical/catalogue/series.json"),
        tmp_path,
    )
    series_path.parent.mkdir(parents=True)
    series_path.write_text(
        json.dumps(
            {
                "series": {
                    "009": {"status": "published"},
                    "010": {"status": "draft"},
                }
            }
        ),
        encoding="utf-8",
    )

    assert assignments_path == (
        tmp_path / "studio" / "data" / "canonical" / "tags" / "tag-assignments.json"
    ).resolve()
    assert audit.load_source_series_statuses(tmp_path) == {
        "009": "published",
        "010": "draft",
    }
