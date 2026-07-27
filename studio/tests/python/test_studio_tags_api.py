#!/usr/bin/env python3
"""Focused Studio tag API and policy ownership tests."""

from __future__ import annotations

import hashlib
from http import HTTPStatus
from pathlib import Path
import tempfile

from studio_tags_api import tags_get_payload, tags_health_payload, tags_post_response
from tags.tag_management_config import load_tag_management_config, tag_analysis_policy
from tags.tag_source_paths import TAG_ASSIGNMENTS_REL_PATH


REPO_ROOT = Path(__file__).resolve().parents[3]

EXPECTED_CANONICAL_FILES = {
    "tag-registry.json": ("c52fa354bf41570c0a1e29ce78e298b945a1cc8f5a81bad1dd4986881698ec20", 99743),
    "tag-aliases.json": ("579757259edf6c53c363b8ba35f098eb63a2e2325e40f03a64da8f562cb60393", 8165),
    "tag-assignments.json": ("5b337ce9c09b7c31bf6582f9c3b4a1269db74b1739573368805e75a92d43504d", 13317),
    "tag-groups.json": ("9883b239143045684e05d2888f4ce73ea0d0a865e20c0a238206de972e90f529", 2866),
}


def test_canonical_tag_files_preserve_frozen_bytes() -> None:
    source_dir = REPO_ROOT / "studio" / "data" / "canonical" / "tags"
    for filename, (expected_digest, expected_size) in EXPECTED_CANONICAL_FILES.items():
        data = (source_dir / filename).read_bytes()
        assert len(data) == expected_size
        assert hashlib.sha256(data).hexdigest() == expected_digest


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
    aliases = tags_get_payload(REPO_ROOT, "/tag-aliases")
    assignments = tags_get_payload(REPO_ROOT, "/tag-assignments")

    assert groups["ok"] is True and len(groups["groups"]) == 4
    assert registry["ok"] is True and len(registry["tags"]) == 275
    assert aliases["ok"] is True and len(aliases["aliases"]) == 82
    assert assignments["ok"] is True and len(assignments["series"]) == 140
    health = tags_health_payload()
    assert health["service"] == "studio_tags"
    assert health["writes"]["create_tag"] is True


def test_studio_tag_api_dry_run_preserves_assignment_source() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        path = repo_root / TAG_ASSIGNMENTS_REL_PATH
        path.parent.mkdir(parents=True)
        path.write_text(
            """{
  "tag_assignments_version": "tag_assignments_v1",
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
                "tags": [{"tag_id": "subject:trees", "w_manual": 0.9}],
                "client_time_utc": "2026-05-22T00:00:00Z",
            },
            dry_run=True,
        )

        assert status == HTTPStatus.OK
        assert payload["ok"] is True
        assert payload["dry_run"] is True
        assert path.read_bytes() == before
