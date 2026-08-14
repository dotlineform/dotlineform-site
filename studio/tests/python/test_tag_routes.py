#!/usr/bin/env python3
"""Verify Studio tag service route ownership and handler dispatch."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
for path in (
    REPO_ROOT / "studio" / "services",
    REPO_ROOT / "studio" / "app" / "server" / "studio",
):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

from tags import tag_routes as routes  # noqa: E402
from studio_tag_api import aliases  # noqa: E402
from studio_tag_api import assignments  # noqa: E402
from studio_tag_api import promotions  # noqa: E402
from studio_tag_api import registry  # noqa: E402
import studio_tags_api  # noqa: E402


def assert_no_duplicates(values: tuple[str, ...], label: str) -> None:
    duplicates = sorted({value for value in values if values.count(value) > 1})
    assert not duplicates, f"{label} contains duplicate routes: {duplicates!r}"


def test_post_routes_are_unique() -> None:
    assert_no_duplicates(routes.POST_PATHS, "POST_PATHS")


def test_options_routes_cover_each_post_route() -> None:
    assert_no_duplicates(routes.OPTIONS_PATHS, "OPTIONS_PATHS")
    assert set(routes.OPTIONS_PATHS) == set(routes.POST_PATHS)
    assert routes.HEALTH_PATH not in routes.OPTIONS_PATHS


def test_studio_adapter_covers_each_tag_route() -> None:
    assert set(studio_tags_api.TAG_POST_PATHS) == set(routes.POST_PATHS)
    assert set(studio_tags_api.POST_HANDLERS) == set(routes.POST_PATHS)
    assert routes.TAG_ASSOCIATIONS_PATH == "/tag-associations"


def test_retired_import_routes_are_absent() -> None:
    retired_paths = {
        "/import-tag-registry",
        "/import-tag-aliases",
        "/import-tag-assignments-preview",
        "/import-tag-assignments",
    }
    assert retired_paths.isdisjoint(routes.POST_PATHS)
    assert retired_paths.isdisjoint(studio_tags_api.POST_HANDLERS)


def test_tag_write_handlers_live_in_functional_modules() -> None:
    expected_handlers = (
        assignments.save_tags_response,
        registry.create_tag_response,
        registry.mutate_tag_response,
        aliases.create_tag_alias_response,
        aliases.delete_tag_alias_response,
        aliases.mutate_tag_alias_response,
        promotions.promote_tag_alias_response,
        promotions.demote_tag_response,
    )
    assert all(callable(handler) for handler in expected_handlers)


def test_registry_edit_preserves_source_and_omitted_primary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry_path = tmp_path / registry.tag_source.REGISTRY_REL_PATH
    aliases_path = tmp_path / registry.tag_source.ALIASES_REL_PATH
    assignments_path = tmp_path / registry.tag_source.ASSIGNMENTS_REL_PATH
    document_path = (
        tmp_path
        / "docs-viewer/scopes/analysis/source/sub-scopes/tags/documents/"
        "d-20260727-225608-000001.md"
    )
    for path in (registry_path, aliases_path, assignments_path, document_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    primary = {
        "scope": "analysis",
        "sub_scope": "tags",
        "doc_id": "d-20260727-225608-000001",
    }
    registry_path.write_text(
        json.dumps(
            {
                "tag_registry_version": "tag_registry_v6",
                "updated_at_utc": "2026-07-28T12:00:00Z",
                "policy": {"allowed_groups": ["subject", "theme"]},
                "tags": [
                    {
                        "tag_id": "trees",
                        "group": "subject",
                        "primary_document": primary,
                        "updated_at_utc": "2026-07-28T12:00:00Z",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    aliases_path.write_text(
        json.dumps({"tag_aliases_version": "tag_aliases_v2", "aliases": {}}),
        encoding="utf-8",
    )
    assignments_path.write_text(
        json.dumps({"tag_assignments_version": "tag_assignments_v2", "series": {}}),
        encoding="utf-8",
    )
    document_path.write_text(
        "---\n"
        "doc_id: d-20260727-225608-000001\n"
        "title: trees\n"
        "group: subject\n"
        "tag_id: trees\n"
        "---\n"
        "# trees\n",
        encoding="utf-8",
    )
    document_before = document_path.read_bytes()
    writes: dict[Path, dict[str, object]] = {}
    monkeypatch.setattr(
        registry.tag_transactions,
        "atomic_write_many",
        lambda payloads: writes.update(payloads),
    )
    monkeypatch.setattr(registry.common, "utc_now", lambda: "2026-07-29T12:00:00Z")
    monkeypatch.setattr(registry.common, "log_event", lambda *_args, **_kwargs: None)

    result = registry.mutate_tag_response(
        tmp_path,
        {"action": "edit", "tag_id": "trees", "new_group": "theme"},
        preview=False,
    )

    assert result["group_changed"] is True
    assert result["primary_document_changed"] is False
    assert set(writes) == {registry_path.resolve()}
    assert writes[registry_path.resolve()]["tags"][0]["primary_document"] == primary
    assert document_path.read_bytes() == document_before


def test_registry_primary_replacement_requires_current_association(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry_path = tmp_path / registry.tag_source.REGISTRY_REL_PATH
    aliases_path = tmp_path / registry.tag_source.ALIASES_REL_PATH
    assignments_path = tmp_path / registry.tag_source.ASSIGNMENTS_REL_PATH
    registry_path.parent.mkdir(parents=True)
    registry_path.write_text(
        json.dumps(
            {
                "tag_registry_version": "tag_registry_v6",
                "updated_at_utc": "2026-07-28T12:00:00Z",
                "policy": {"allowed_groups": ["subject", "theme"]},
                "tags": [
                    {
                        "tag_id": "trees",
                        "group": "subject",
                        "updated_at_utc": "2026-07-28T12:00:00Z",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    aliases_path.write_text(json.dumps({"aliases": {}}), encoding="utf-8")
    assignments_path.write_text(json.dumps({"series": {}}), encoding="utf-8")
    current = {
        "scope": "analysis",
        "sub_scope": "tags",
        "doc_id": "d-20260729-111111-abcdef",
    }
    monkeypatch.setattr(
        registry.tag_document_declarations,
        "current_tag_document_associations",
        lambda *_args: [{"target": current, "title": "Current", "url": "/analysis/"}],
    )
    writes: dict[Path, dict[str, object]] = {}
    monkeypatch.setattr(
        registry.tag_transactions,
        "atomic_write_many",
        lambda payloads: writes.update(payloads),
    )
    monkeypatch.setattr(registry.common, "log_event", lambda *_args, **_kwargs: None)

    result = registry.mutate_tag_response(
        tmp_path,
        {
            "action": "edit",
            "tag_id": "trees",
            "primary_document": current,
        },
        preview=False,
    )
    assert result["primary_document_changed"] is True
    assert writes[registry_path.resolve()]["tags"][0]["primary_document"] == current

    with pytest.raises(ValueError, match="current associated document"):
        registry.mutate_tag_response(
            tmp_path,
            {
                "action": "edit",
                "tag_id": "trees",
                "primary_document": {**current, "doc_id": "d-20260729-222222-fedcba"},
            },
            preview=False,
        )
