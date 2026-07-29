#!/usr/bin/env python3
"""Verify the one-time tag Registry document-link migration."""

from __future__ import annotations

import copy
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
STUDIO_SERVICES_DIR = REPO_ROOT / "studio" / "services"
if str(STUDIO_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(STUDIO_SERVICES_DIR))

from tags import tag_registry_v5_migration as migration  # noqa: E402


NOW = "2026-07-29T12:00:00Z"


def fixtures() -> tuple[dict, dict, dict]:
    registry = {
        "tag_registry_version": "tag_registry_v4",
        "updated_at_utc": "2026-07-28T12:00:00Z",
        "policy": {"allowed_groups": ["subject", "theme"]},
        "tags": [
            {
                "tag_id": "trees",
                "group": "subject",
                "description": "Trees",
                "doc_id": "d-20260728-120000-000001",
                "updated_at_utc": "2026-07-28T12:00:00Z",
            },
            {
                "tag_id": "growth",
                "group": "theme",
                "description": "",
                "doc_id": "",
                "updated_at_utc": "2026-07-28T13:00:00Z",
            },
        ],
    }
    aliases = {
        "tag_aliases_version": "tag_aliases_v2",
        "updated_at_utc": NOW,
        "aliases": {},
    }
    assignments = {
        "tag_assignments_version": "tag_assignments_v2",
        "updated_at_utc": NOW,
        "series": {},
    }
    return registry, aliases, assignments


def test_projection_replaces_scalar_links_and_removes_descriptions() -> None:
    registry, aliases, assignments = fixtures()
    original = copy.deepcopy(registry)
    projected, stats = migration.project_tag_registry_v5(
        registry,
        aliases,
        assignments,
        now_utc=NOW,
        document_url_for_id=lambda doc_id: (
            "/analysis/?doc=d-20260624-213316-478639"
            f"&subdoc={doc_id}"
        ),
    )

    assert registry == original
    assert projected["tag_registry_version"] == "tag_registry_v5"
    assert [row["tag_id"] for row in projected["tags"]] == ["trees", "growth"]
    assert projected["tags"][0] == {
        "tag_id": "trees",
        "group": "subject",
        "doc_url": [
            "/analysis/?doc=d-20260624-213316-478639"
            "&subdoc=d-20260728-120000-000001"
        ],
        "updated_at_utc": "2026-07-28T12:00:00Z",
    }
    assert projected["tags"][1]["doc_url"] == []
    assert stats["populated_doc_url_count"] == 1
    assert stats["empty_doc_url_count"] == 1
    assert stats["description_fields_removed"] == 2


def test_projection_rejects_wrong_version_and_malformed_rows() -> None:
    registry, aliases, assignments = fixtures()
    registry["tag_registry_version"] = "tag_registry_v5"
    with pytest.raises(ValueError, match="requires tag_registry_v4"):
        migration.project_tag_registry_v5(
            registry,
            aliases,
            assignments,
            now_utc=NOW,
            document_url_for_id=lambda _doc_id: "",
        )

    registry, aliases, assignments = fixtures()
    registry["tags"][0]["description"] = {}
    with pytest.raises(ValueError, match="description must be a string"):
        migration.project_tag_registry_v5(
            registry,
            aliases,
            assignments,
            now_utc=NOW,
            document_url_for_id=lambda _doc_id: "",
        )
