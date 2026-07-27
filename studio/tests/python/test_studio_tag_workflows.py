#!/usr/bin/env python3
"""Focused checks for Studio tag workflow API contracts."""

from __future__ import annotations

from http import HTTPStatus
import json
from pathlib import Path
import sys
import tempfile

REPO_ROOT = Path(__file__).resolve().parents[3]
STUDIO_SERVER_DIR = REPO_ROOT / "studio" / "app" / "server" / "studio"
for path in (REPO_ROOT, STUDIO_SERVER_DIR):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

from studio_tags_api import tags_get_payload, tags_post_response  # noqa: E402


def test_studio_tag_reads_return_existing_payloads() -> None:
    groups_payload = tags_get_payload(REPO_ROOT, "/tag-groups")
    registry_payload = tags_get_payload(REPO_ROOT, "/tag-registry")
    aliases_payload = tags_get_payload(REPO_ROOT, "/tag-aliases")
    assignments_payload = tags_get_payload(REPO_ROOT, "/tag-assignments")

    assert groups_payload["ok"] is True
    assert groups_payload["tag_groups_version"] == "tag_groups_v1"
    assert {group["group_id"] for group in groups_payload["groups"]} >= {"subject", "domain", "form", "theme"}
    assert registry_payload["ok"] is True
    assert registry_payload["tag_registry_version"] == "tag_registry_v1"
    assert any(tag["tag_id"] == "subject:flower" for tag in registry_payload["tags"])
    assert aliases_payload["ok"] is True
    assert aliases_payload["tag_aliases_version"] == "tag_aliases_v1"
    assert "floral" in aliases_payload["aliases"]
    assert assignments_payload["ok"] is True
    assert assignments_payload["tag_assignments_version"] == "tag_assignments_v1"
    assert "001" in assignments_payload["series"]


def test_studio_save_tags_dry_run_uses_assignment_contract() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir)
        assignments_path = repo_root / "studio" / "data" / "canonical" / "tags" / "tag-assignments.json"
        assignments_path.parent.mkdir(parents=True)
        assignments_path.write_text(
            """{
  "tag_assignments_version": "tag_assignments_v1",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "series": {}
}
""",
            encoding="utf-8",
        )

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

        persisted = assignments_path.read_text(encoding="utf-8")
        assert status == HTTPStatus.OK
        assert payload["ok"] is True
        assert payload["series_id"] == "series-a"
        assert payload["tag_count"] == 1
        assert payload["dry_run"] is True
        assert payload["would_write"]["tags"] == [{"tag_id": "subject:trees", "w_manual": 0.9}]
        assert "subject:trees" not in persisted


def test_studio_import_tag_assignments_dry_run_uses_assignment_contract() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir)
        assignments_path = repo_root / "studio" / "data" / "canonical" / "tags" / "tag-assignments.json"
        series_index_path = repo_root / "site" / "assets" / "data" / "series_index.json"
        assignments_path.parent.mkdir(parents=True)
        series_index_path.parent.mkdir(parents=True)
        assignments_path.write_text(
            """{
  "tag_assignments_version": "tag_assignments_v1",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "series": {
    "series-a": {
      "tags": []
    }
  }
}
""",
            encoding="utf-8",
        )
        series_index_path.write_text(
            """{
  "series": {
    "series-a": {
      "works": []
    }
  }
}
""",
            encoding="utf-8",
        )
        import_assignments = {
            "version": "tag_assignments_export_v1",
            "series": {
                "series-a": {
                    "base_row_snapshot": {"tags": []},
                    "staged_row": {"tags": [{"tag_id": "theme:growth", "w_manual": 0.6}]},
                }
            },
        }

        preview_status, preview_payload = tags_post_response(
            repo_root,
            "/import-tag-assignments-preview",
            {
                "import_assignments": import_assignments,
                "import_filename": "import.json",
                "client_time_utc": "2026-05-22T00:00:00Z",
            },
            dry_run=True,
        )
        apply_status, apply_payload = tags_post_response(
            repo_root,
            "/import-tag-assignments",
            {
                "import_assignments": import_assignments,
                "import_filename": "import.json",
                "resolutions": {},
                "client_time_utc": "2026-05-22T00:00:00Z",
            },
            dry_run=True,
        )

        persisted = assignments_path.read_text(encoding="utf-8")
        assert preview_status == HTTPStatus.OK
        assert preview_payload["ok"] is True
        assert preview_payload["applicable_count"] == 1
        assert apply_status == HTTPStatus.OK
        assert apply_payload["ok"] is True
        assert apply_payload["applied_series"] == 1
        assert apply_payload["dry_run"] is True
        assert apply_payload["would_write"]["applied_series"] == 1
        assert "theme:growth" not in persisted


def test_studio_tag_registry_dry_run_uses_registry_contract() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir)
        registry_path = repo_root / "studio" / "data" / "canonical" / "tags" / "tag-registry.json"
        aliases_path = repo_root / "studio" / "data" / "canonical" / "tags" / "tag-aliases.json"
        assignments_path = repo_root / "studio" / "data" / "canonical" / "tags" / "tag-assignments.json"
        registry_path.parent.mkdir(parents=True)
        registry_path.write_text(
            """{
  "tag_registry_version": "tag_registry_v1",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "policy": {"allowed_groups": ["subject", "theme"]},
  "tags": [{"tag_id": "subject:trees", "group": "subject", "label": "trees", "description": "Old trees"}]
}
""",
            encoding="utf-8",
        )
        aliases_path.write_text(
            """{
  "tag_aliases_version": "tag_aliases_v1",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "aliases": {"woodland": {"description": "Woodland", "tags": ["subject:trees"]}}
}
""",
            encoding="utf-8",
        )
        assignments_path.write_text(
            """{
  "tag_assignments_version": "tag_assignments_v1",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "series": {"series-a": {"tags": [{"tag_id": "subject:trees", "w_manual": 0.6}]}}
}
""",
            encoding="utf-8",
        )
        import_status, import_payload = tags_post_response(
            repo_root,
            "/import-tag-registry",
            {
                "mode": "add",
                "import_registry": {
                    "tags": [
                        {"tag_id": "theme:growth", "group": "theme", "label": "growth", "description": "Growth"}
                    ]
                },
                "import_filename": "registry.json",
                "client_time_utc": "2026-05-22T00:00:00Z",
            },
            dry_run=True,
        )
        preview_status, preview_payload = tags_post_response(
            repo_root,
            "/mutate-tag-preview",
            {"action": "delete", "tag_id": "subject:trees", "client_time_utc": "2026-05-22T00:00:00Z"},
            dry_run=True,
        )

        persisted = registry_path.read_text(encoding="utf-8")
        assert import_status == HTTPStatus.OK
        assert import_payload["ok"] is True
        assert import_payload["added"] == 1
        assert import_payload["dry_run"] is True
        assert preview_status == HTTPStatus.OK
        assert preview_payload["ok"] is True
        assert preview_payload["preview"] is True
        assert preview_payload["action"] == "delete"
        assert preview_payload["series_tag_refs_rewritten"] == 1
        assert "theme:growth" not in persisted


def test_studio_create_tag_dry_run_validates_before_write() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir)
        registry_path = repo_root / "studio" / "data" / "canonical" / "tags" / "tag-registry.json"
        registry_path.parent.mkdir(parents=True)
        registry_path.write_text(
            """{
  "tag_registry_version": "tag_registry_v1",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "policy": {"allowed_groups": ["subject", "theme"]},
  "tags": [{"tag_id": "subject:trees", "group": "subject", "label": "trees", "description": "Trees"}]
}
""",
            encoding="utf-8",
        )
        before = registry_path.read_bytes()

        status, payload = tags_post_response(
            repo_root,
            "/create-tag",
            {
                "group": "theme",
                "slug": "renewal",
                "description": " Renewal ",
                "client_time_utc": "2026-05-22T00:00:00Z",
            },
            dry_run=True,
        )

        assert status == HTTPStatus.OK
        assert payload["ok"] is True
        assert payload["action"] == "create"
        assert payload["tag_id"] == "theme:renewal"
        assert payload["added"] == 1
        assert payload["final_total"] == 2
        assert payload["dry_run"] is True
        assert payload["would_write"]["tag_id"] == "theme:renewal"
        assert registry_path.read_bytes() == before

        invalid_requests = (
            {"group": "domain", "slug": "studio", "description": ""},
            {"group": "theme", "slug": "Bad Slug", "description": ""},
            {"group": "subject", "slug": "trees", "description": ""},
            {"group": "theme", "slug": "renewal", "description": {"bad": True}},
        )
        for invalid_body in invalid_requests:
            try:
                tags_post_response(repo_root, "/create-tag", invalid_body, dry_run=False)
            except ValueError:
                pass
            else:
                raise AssertionError(f"invalid create request was accepted: {invalid_body!r}")
            assert registry_path.read_bytes() == before


def test_studio_tag_alias_dry_run_uses_alias_contract() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir)
        aliases_path = repo_root / "studio" / "data" / "canonical" / "tags" / "tag-aliases.json"
        registry_path = repo_root / "studio" / "data" / "canonical" / "tags" / "tag-registry.json"
        aliases_path.parent.mkdir(parents=True)
        aliases_path.write_text(
            """{
  "tag_aliases_version": "tag_aliases_v1",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "aliases": {"foliage": {"description": "Old foliage", "tags": ["subject:trees"]}}
}
""",
            encoding="utf-8",
        )
        registry_path.write_text(
            """{
  "tag_registry_version": "tag_registry_v1",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "policy": {"allowed_groups": ["subject", "theme"]},
  "tags": [
    {"tag_id": "subject:trees", "group": "subject", "label": "trees", "description": "Trees"},
    {"tag_id": "theme:growth", "group": "theme", "label": "growth", "description": "Growth"}
  ]
}
""",
            encoding="utf-8",
        )
        before = aliases_path.read_bytes()

        create_status, create_payload = tags_post_response(
            repo_root,
            "/create-tag-alias",
            {
                "alias": "canopy",
                "description": " Canopy ",
                "tags": ["subject:trees", "theme:growth"],
                "client_time_utc": "2026-05-22T00:00:00Z",
            },
            dry_run=True,
        )

        import_status, import_payload = tags_post_response(
            repo_root,
            "/import-tag-aliases",
            {
                "mode": "add",
                "import_aliases": {"aliases": {"growth": {"description": "Growth", "tags": ["theme:growth"]}}},
                "import_filename": "aliases.json",
                "client_time_utc": "2026-05-22T00:00:00Z",
            },
            dry_run=True,
        )
        delete_status, delete_payload = tags_post_response(
            repo_root,
            "/delete-tag-alias",
            {"alias": "foliage", "client_time_utc": "2026-05-22T00:00:00Z"},
            dry_run=True,
        )
        preview_status, preview_payload = tags_post_response(
            repo_root,
            "/mutate-tag-alias-preview",
            {
                "alias": "foliage",
                "new_alias": "canopy",
                "description": "Canopy",
                "tags": ["subject:trees", "theme:growth"],
                "client_time_utc": "2026-05-22T00:00:00Z",
            },
            dry_run=True,
        )

        persisted = aliases_path.read_text(encoding="utf-8")
        assert create_status == HTTPStatus.OK
        assert create_payload["ok"] is True
        assert create_payload["action"] == "create_alias"
        assert create_payload["alias"] == "canopy"
        assert create_payload["tags"] == ["subject:trees", "theme:growth"]
        assert create_payload["added"] == 1
        assert create_payload["dry_run"] is True
        assert create_payload["would_write"]["alias"] == "canopy"
        assert import_status == HTTPStatus.OK
        assert import_payload["ok"] is True
        assert import_payload["added"] == 1
        assert import_payload["dry_run"] is True
        assert delete_status == HTTPStatus.OK
        assert delete_payload["ok"] is True
        assert delete_payload["alias"] == "foliage"
        assert delete_payload["dry_run"] is True
        assert preview_status == HTTPStatus.OK
        assert preview_payload["ok"] is True
        assert preview_payload["preview"] is True
        assert preview_payload["renamed"] is True
        assert "canopy" not in persisted
        assert aliases_path.read_bytes() == before

        invalid_requests = (
            {"alias": "Bad Alias", "description": "", "tags": ["subject:trees"]},
            {"alias": "foliage", "description": "", "tags": ["subject:trees"]},
            {"alias": "canopy", "description": "", "tags": []},
            {"alias": "canopy", "description": "", "tags": ["subject:missing"]},
            {"alias": "canopy", "description": "", "tags": ["subject:trees", "subject:trees"]},
            {"alias": "canopy", "description": "", "tags": ["subject:trees", "subject:other"]},
        )
        for invalid_body in invalid_requests:
            try:
                tags_post_response(repo_root, "/create-tag-alias", invalid_body, dry_run=False)
            except ValueError:
                pass
            else:
                raise AssertionError(f"invalid alias create request was accepted: {invalid_body!r}")
            assert aliases_path.read_bytes() == before


def test_studio_promotion_demotion_dry_run_uses_promotion_contract() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir)
        registry_path = repo_root / "studio" / "data" / "canonical" / "tags" / "tag-registry.json"
        aliases_path = repo_root / "studio" / "data" / "canonical" / "tags" / "tag-aliases.json"
        assignments_path = repo_root / "studio" / "data" / "canonical" / "tags" / "tag-assignments.json"
        registry_path.parent.mkdir(parents=True)
        registry_path.write_text(
            """{
  "tag_registry_version": "tag_registry_v1",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "policy": {"allowed_groups": ["subject", "theme"]},
  "tags": [
    {"tag_id": "subject:trees", "group": "subject", "label": "trees", "description": "Trees"},
    {"tag_id": "theme:growth", "group": "theme", "label": "growth", "description": "Growth"}
  ]
}
""",
            encoding="utf-8",
        )
        aliases_path.write_text(
            """{
  "tag_aliases_version": "tag_aliases_v1",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "aliases": {"foliage": {"description": "Foliage", "tags": ["subject:trees"]}}
}
""",
            encoding="utf-8",
        )
        assignments_path.write_text(
            """{
  "tag_assignments_version": "tag_assignments_v1",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "series": {"series-a": {"tags": [{"tag_id": "subject:trees", "w_manual": 0.6}]}}
}
""",
            encoding="utf-8",
        )

        promote_status, promote_payload = tags_post_response(
            repo_root,
            "/promote-tag-alias-preview",
            {"alias": "foliage", "group": "theme", "client_time_utc": "2026-05-22T00:00:00Z"},
            dry_run=True,
        )
        demote_status, demote_payload = tags_post_response(
            repo_root,
            "/demote-tag-preview",
            {"tag_id": "subject:trees", "alias_targets": ["theme:growth"], "client_time_utc": "2026-05-22T00:00:00Z"},
            dry_run=True,
        )

        registry_persisted = registry_path.read_text(encoding="utf-8")
        aliases_persisted = json.loads(aliases_path.read_text(encoding="utf-8"))
        assert promote_status == HTTPStatus.OK
        assert promote_payload["ok"] is True
        assert promote_payload["preview"] is True
        assert promote_payload["new_tag_id"] == "theme:foliage"
        assert demote_status == HTTPStatus.OK
        assert demote_payload["ok"] is True
        assert demote_payload["preview"] is True
        assert demote_payload["alias_key"] == "trees"
        assert demote_payload["series_tag_refs_rewritten"] == 1
        assert "theme:foliage" not in registry_persisted
        assert "trees" not in aliases_persisted["aliases"]
