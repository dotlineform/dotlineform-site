#!/usr/bin/env python3
"""Focused Studio tag API and policy ownership tests."""

from __future__ import annotations

from http import HTTPStatus
from pathlib import Path
import tempfile

from studio_tags_api import tags_get_payload, tags_health_payload, tags_post_response
from tags.tag_management_config import load_tag_management_config, tag_analysis_policy
from tags.tag_source_paths import TAG_ASSIGNMENTS_REL_PATH


REPO_ROOT = Path(__file__).resolve().parents[3]

def test_studio_tag_policy_preserves_retained_analysis_contract() -> None:
    payload = load_tag_management_config(REPO_ROOT)
    analysis = tag_analysis_policy(REPO_ROOT)

    assert payload["tag_management_config_version"] == "tag_management_config_v1"
    assert analysis["groups"]["ordered"] == ["subject", "domain", "form", "theme"]
    assert analysis["groups"]["coverage_groups"] == ["subject", "domain", "form", "theme"]
    assert analysis["rag"]["completeness"]["group_coverage_denominator"] == 4
    assert analysis["rag"]["rules"]["amber"]["if_missing_all_groups"] == ["form", "theme"]


def test_studio_tag_api_reads_each_canonical_payload() -> None:
    groups = tags_get_payload(REPO_ROOT, "/tag-groups")
    registry = tags_get_payload(REPO_ROOT, "/tag-registry")
    associations = tags_get_payload(REPO_ROOT, "/tag-associations")
    aliases = tags_get_payload(REPO_ROOT, "/tag-aliases")
    assignments = tags_get_payload(REPO_ROOT, "/tag-assignments")

    assert groups["ok"] is True and groups["groups"]
    assert registry["tag_registry_version"] == "tag_registry_v6"
    assert registry["ok"] is True and registry["tags"]
    assert associations["schema_version"] == "docs_tag_associations_v1"
    assert associations["ok"] is True and associations["associations"]
    assert aliases["tag_aliases_version"] == "tag_aliases_v2"
    assert aliases["ok"] is True and aliases["aliases"]
    assert assignments["tag_assignments_version"] == "tag_assignments_v2"
    assert assignments["ok"] is True and assignments["series"]
    health = tags_health_payload()
    assert health["service"] == "studio_tags"
    assert health["writes"]["create_tag"] is True
    assert health["writes"]["create_tag_alias"] is True
    assert "import_tag_assignments" not in health["writes"]
    assert "import_tag_assignments_preview" not in health["writes"]
    assert "import_tag_registry" not in health["writes"]
    assert "import_tag_aliases" not in health["writes"]


def test_studio_tag_api_dry_run_preserves_assignment_source() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        path = repo_root / TAG_ASSIGNMENTS_REL_PATH
        path.parent.mkdir(parents=True)
        path.write_text(
            """{
  "tag_assignments_version": "tag_assignments_v2",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "series": {}
}
""",
            encoding="utf-8",
        )
        before = path.read_bytes()
        status, payload = tags_post_response(
            repo_root,
            "/save-tags",
            {
                "series_id": "series-a",
                "tags": [{"tag_id": "trees", "w_manual": 0.9}],
                "client_time_utc": "2026-05-22T00:00:00Z",
            },
            dry_run=True,
        )

        assert status == HTTPStatus.OK
        assert payload["ok"] is True
        assert payload["dry_run"] is True
        assert path.read_bytes() == before
