#!/usr/bin/env python3
"""Focused checks for Studio tag workflow API contracts."""

from __future__ import annotations

from http import HTTPStatus
import json
from pathlib import Path
import sys
import tempfile
from typing import Any, Callable

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
STUDIO_SERVER_DIR = REPO_ROOT / "studio" / "app" / "server" / "studio"
for path in (REPO_ROOT, STUDIO_SERVER_DIR):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

from studio_tags_api import tags_get_payload, tags_post_response  # noqa: E402
from tags import tag_document_creation  # noqa: E402


ANALYSIS_TAGS_REPORT_ID = "d-20260430-230000-000099"


def analysis_tag_url(doc_id: str) -> str:
    return (
        f"/docs/?scope=analysis&doc={ANALYSIS_TAGS_REPORT_ID}"
        f"&subdoc={doc_id}"
    )


def write_analysis_tags_fixture(repo_root: Path, doc_id: str) -> None:
    config_path = (
        repo_root / "docs-viewer/config/scopes/docs_scopes.json"
    )
    report_path = (
        repo_root
        / "docs-viewer/scopes/analysis/source/documents"
        / f"{ANALYSIS_TAGS_REPORT_ID}.md"
    )
    report_path.parent.mkdir(parents=True)
    report_path.write_text(
        f"""---
doc_id: {ANALYSIS_TAGS_REPORT_ID}
title: Tags
added_date: "2026-04-30 23:00:00"
last_updated: 2026-04-30
parent_id: ""
viewable: true
viewer_report: docs_subscope
viewer_report_subscope: tags
---
# Tags
""",
        encoding="utf-8",
    )
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        json.dumps(
            {
                "schema_version": "docs_scopes_v3",
                "scopes": [
                    {
                        "scope_id": "analysis",
                        "scope_type": "local",
                        "meta": "analysis",
                        "scope_root": {
                            "provider": "repository",
                            "path": "docs-viewer/scopes/analysis",
                        },
                        "source": {"build_media": {}},
                        "published": {
                            "media": {
                                "img": {
                                    "reference_prefix": "docs/analysis/img",
                                    "served_path_prefix": "/docs/media/analysis/img",
                                    "build_inputs": [],
                                }
                            }
                        },
                        "public_projection": None,
                        "viewer_base_url": "/docs/",
                        "include_scope_param": True,
                        "default_doc_id": "",
                        "non_loadable_doc_ids": [],
                        "manage_only_tree_root_ids": [],
                        "allow_unresolved_parent_ids": False,
                        "sub_scopes": [
                            {
                                "sub_scope": "tags",
                                "title": "Tags",
                                "ui_statuses": [],
                                "document_groups": [
                                    "subject",
                                    "theme",
                                ],
                                "public_projection": None,
                            }
                        ],
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    source_path = (
        repo_root
        / "docs-viewer/scopes/analysis/source/sub-scopes/tags/documents"
        / f"{doc_id}.md"
    )
    source_path.parent.mkdir(parents=True)
    source_path.write_text(
        f"""---
doc_id: {doc_id}
title: trees
added_date: "2026-05-01 00:00:00"
last_updated: 2026-05-01
group: subject
parent_id: ""
viewable: true
---
# trees

Trees
""",
        encoding="utf-8",
    )


def test_studio_tag_reads_return_existing_payloads() -> None:
    groups_payload = tags_get_payload(REPO_ROOT, "/tag-groups")
    registry_payload = tags_get_payload(REPO_ROOT, "/tag-registry")
    aliases_payload = tags_get_payload(REPO_ROOT, "/tag-aliases")
    assignments_payload = tags_get_payload(REPO_ROOT, "/tag-assignments")

    assert groups_payload["ok"] is True
    assert groups_payload["tag_groups_version"] == "tag_groups_v1"
    assert {group["group_id"] for group in groups_payload["groups"]} >= {"subject", "domain", "form", "theme"}
    assert registry_payload["ok"] is True
    assert registry_payload["tag_registry_version"] == "tag_registry_v5"
    assert any(tag["tag_id"] == "flower" for tag in registry_payload["tags"])
    assert aliases_payload["ok"] is True
    assert aliases_payload["tag_aliases_version"] == "tag_aliases_v2"
    assert "floral" in aliases_payload["aliases"]
    assert assignments_payload["ok"] is True
    assert assignments_payload["tag_assignments_version"] == "tag_assignments_v2"
    assert "001" in assignments_payload["series"]


def test_studio_save_tags_dry_run_uses_assignment_contract() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir)
        assignments_path = repo_root / "studio" / "data" / "canonical" / "tags" / "tag-assignments.json"
        assignments_path.parent.mkdir(parents=True)
        assignments_path.write_text(
            """{
  "tag_assignments_version": "tag_assignments_v2",
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
                "tags": [{"tag_id": "trees", "w_manual": 0.9}],
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
        assert payload["would_write"]["tags"] == [{"tag_id": "trees", "w_manual": 0.9}]
        assert "trees" not in persisted


def test_studio_tag_registry_dry_run_uses_registry_contract() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir)
        registry_path = repo_root / "studio" / "data" / "canonical" / "tags" / "tag-registry.json"
        aliases_path = repo_root / "studio" / "data" / "canonical" / "tags" / "tag-aliases.json"
        assignments_path = repo_root / "studio" / "data" / "canonical" / "tags" / "tag-assignments.json"
        registry_path.parent.mkdir(parents=True)
        registry_path.write_text(
            """{
  "tag_registry_version": "tag_registry_v5",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "policy": {"allowed_groups": ["subject", "theme"]},
  "tags": [{"tag_id": "trees", "group": "subject", "doc_url": [], "updated_at_utc": "2026-05-01T00:00:00Z"}]
}
""",
            encoding="utf-8",
        )
        aliases_path.write_text(
            """{
  "tag_aliases_version": "tag_aliases_v2",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "aliases": {"woodland": {"description": "Woodland", "tags": ["trees"]}}
}
""",
            encoding="utf-8",
        )
        assignments_path.write_text(
            """{
  "tag_assignments_version": "tag_assignments_v2",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "series": {"series-a": {"tags": [{"tag_id": "trees", "w_manual": 0.6}]}}
}
""",
            encoding="utf-8",
        )
        before = registry_path.read_bytes()
        preview_status, preview_payload = tags_post_response(
            repo_root,
            "/mutate-tag-preview",
            {"action": "delete", "tag_id": "trees", "client_time_utc": "2026-05-22T00:00:00Z"},
            dry_run=True,
        )

        assert preview_status == HTTPStatus.OK
        assert preview_payload["ok"] is True
        assert preview_payload["preview"] is True
        assert preview_payload["action"] == "delete"
        assert preview_payload["series_tag_refs_rewritten"] == 1
        assert registry_path.read_bytes() == before


def test_studio_create_tag_dry_run_validates_before_write() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir)
        existing_doc_id = "d-20260501-000000-000001"
        write_analysis_tags_fixture(repo_root, existing_doc_id)
        registry_path = repo_root / "studio" / "data" / "canonical" / "tags" / "tag-registry.json"
        registry_path.parent.mkdir(parents=True)
        registry_path.write_text(
            """{
  "tag_registry_version": "tag_registry_v5",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "policy": {"allowed_groups": ["subject", "theme"]},
  "tags": [{"tag_id": "trees", "group": "subject", "doc_url": ["/docs/?scope=analysis&doc=d-20260430-230000-000099&subdoc=d-20260501-000000-000001"], "updated_at_utc": "2026-05-01T00:00:00Z"}]
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
                "tag_id": "renewal",
                "client_time_utc": "2026-05-22T00:00:00Z",
            },
            dry_run=True,
        )

        assert status == HTTPStatus.OK
        assert payload["ok"] is True
        assert payload["action"] == "create"
        assert payload["tag_id"] == "renewal"
        assert payload["doc_id"].startswith("d-")
        assert payload["document_target"] == {
            "scope": "analysis",
            "sub_scope": "tags",
            "doc_id": payload["doc_id"],
        }
        assert payload["added"] == 1
        assert payload["final_total"] == 2
        assert payload["dry_run"] is True
        assert payload["would_write"]["tag_id"] == "renewal"
        assert payload["would_write"]["doc_id"] == payload["doc_id"]
        assert registry_path.read_bytes() == before

        invalid_requests = (
            {"group": "domain", "tag_id": "studio"},
            {"group": "theme", "tag_id": "Bad Slug"},
            {"group": "subject", "tag_id": "trees"},
            {"group": "theme", "tag_id": "renewal", "description": "retired"},
        )
        for invalid_body in invalid_requests:
            try:
                tags_post_response(repo_root, "/create-tag", invalid_body, dry_run=False)
            except ValueError:
                pass
            else:
                raise AssertionError(f"invalid create request was accepted: {invalid_body!r}")
            assert registry_path.read_bytes() == before


def test_studio_create_tag_returns_compensated_rebuild_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    existing_doc_id = "d-20260501-000000-000001"
    write_analysis_tags_fixture(tmp_path, existing_doc_id)
    registry_path = (
        tmp_path
        / "studio/data/canonical/tags/tag-registry.json"
    )
    registry_path.parent.mkdir(parents=True)
    registry_path.write_text(
        """{
  "tag_registry_version": "tag_registry_v5",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "policy": {"allowed_groups": ["subject", "theme"]},
  "tags": [{"tag_id": "trees", "group": "subject", "doc_url": ["/docs/?scope=analysis&doc=d-20260430-230000-000099&subdoc=d-20260501-000000-000001"], "updated_at_utc": "2026-05-01T00:00:00Z"}]
}
""",
        encoding="utf-8",
    )
    before = registry_path.read_bytes()
    calls = 0

    def fail_then_recover(
        _repo_root: Path,
        _scope: str,
        _sub_scope: str,
        _changed_paths: list[Path],
        write_operation: Callable[[], Any],
        *,
        suppression_reason: str,
    ) -> dict[str, object]:
        nonlocal calls
        calls += 1
        write_operation()
        if calls == 1:
            raise RuntimeError("synthetic child builder failure")
        return {
            "ok": True,
            "suppression_reason": suppression_reason,
        }

    monkeypatch.setattr(
        tag_document_creation.write_rebuild,
        "perform_sub_scope_source_write_and_rebuild",
        fail_then_recover,
    )

    status, payload = tags_post_response(
        tmp_path,
        "/create-tag",
        {
            "group": "theme",
            "tag_id": "renewal",
        },
    )

    assert status == HTTPStatus.INTERNAL_SERVER_ERROR
    assert payload["ok"] is False
    assert payload["source_restored"] is True
    assert payload["recovery_rebuild"]["ok"] is True
    assert payload["retry_safe"] is True
    assert "creation was not completed" in str(payload["error"])
    assert registry_path.read_bytes() == before
    assert not (
        tmp_path
        / "docs-viewer/scopes/analysis/source/sub-scopes/tags/documents"
        / f"{payload['doc_id']}.md"
    ).exists()


def test_studio_tag_alias_dry_run_uses_alias_contract() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir)
        aliases_path = repo_root / "studio" / "data" / "canonical" / "tags" / "tag-aliases.json"
        registry_path = repo_root / "studio" / "data" / "canonical" / "tags" / "tag-registry.json"
        aliases_path.parent.mkdir(parents=True)
        aliases_path.write_text(
            """{
  "tag_aliases_version": "tag_aliases_v2",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "aliases": {"foliage": {"description": "Old foliage", "tags": ["trees"]}}
}
""",
            encoding="utf-8",
        )
        registry_path.write_text(
            """{
  "tag_registry_version": "tag_registry_v5",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "policy": {"allowed_groups": ["subject", "theme"]},
  "tags": [
    {"tag_id": "trees", "group": "subject", "doc_url": [], "updated_at_utc": "2026-05-01T00:00:00Z"},
    {"tag_id": "growth", "group": "theme", "doc_url": [], "updated_at_utc": "2026-05-01T00:00:00Z"}
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
                "tags": ["trees", "growth"],
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
                "tags": ["trees", "growth"],
                "client_time_utc": "2026-05-22T00:00:00Z",
            },
            dry_run=True,
        )

        persisted = aliases_path.read_text(encoding="utf-8")
        assert create_status == HTTPStatus.OK
        assert create_payload["ok"] is True
        assert create_payload["action"] == "create_alias"
        assert create_payload["alias"] == "canopy"
        assert create_payload["tags"] == ["trees", "growth"]
        assert create_payload["added"] == 1
        assert create_payload["dry_run"] is True
        assert create_payload["would_write"]["alias"] == "canopy"
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
            {"alias": "Bad Alias", "description": "", "tags": ["trees"]},
            {"alias": "foliage", "description": "", "tags": ["trees"]},
            {"alias": "canopy", "description": "", "tags": []},
            {"alias": "canopy", "description": "", "tags": ["missing"]},
            {"alias": "canopy", "description": "", "tags": ["trees", "trees"]},
            {"alias": "canopy", "description": "", "tags": ["trees", "other"]},
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
  "tag_registry_version": "tag_registry_v5",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "policy": {"allowed_groups": ["subject", "theme"]},
  "tags": [
    {"tag_id": "trees", "group": "subject", "doc_url": [], "updated_at_utc": "2026-05-01T00:00:00Z"},
    {"tag_id": "growth", "group": "theme", "doc_url": [], "updated_at_utc": "2026-05-01T00:00:00Z"}
  ]
}
""",
            encoding="utf-8",
        )
        aliases_path.write_text(
            """{
  "tag_aliases_version": "tag_aliases_v2",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "aliases": {"foliage": {"description": "Foliage", "tags": ["trees"]}}
}
""",
            encoding="utf-8",
        )
        assignments_path.write_text(
            """{
  "tag_assignments_version": "tag_assignments_v2",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "series": {"series-a": {"tags": [{"tag_id": "trees", "w_manual": 0.6}]}}
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
            {"tag_id": "trees", "alias_targets": ["growth"], "client_time_utc": "2026-05-22T00:00:00Z"},
            dry_run=True,
        )

        registry_persisted = registry_path.read_text(encoding="utf-8")
        aliases_persisted = json.loads(aliases_path.read_text(encoding="utf-8"))
        assert promote_status == HTTPStatus.OK
        assert promote_payload["ok"] is True
        assert promote_payload["preview"] is True
        assert promote_payload["new_tag_id"] == "foliage"
        assert demote_status == HTTPStatus.OK
        assert demote_payload["ok"] is True
        assert demote_payload["preview"] is True
        assert demote_payload["alias_key"] == "trees"
        assert demote_payload["series_tag_refs_rewritten"] == 1
        assert '"foliage"' not in registry_persisted
        assert "trees" not in aliases_persisted["aliases"]
