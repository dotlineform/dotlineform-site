#!/usr/bin/env python3
"""Verify Studio tag service route ownership and handler dispatch."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
STUDIO_SERVICES_DIR = REPO_ROOT / "studio" / "services"
STUDIO_SERVER_DIR = REPO_ROOT / "studio" / "app" / "server" / "studio"
for path in (STUDIO_SERVICES_DIR, STUDIO_SERVER_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from tags import tag_routes as routes  # noqa: E402
from studio_tag_api import aliases  # noqa: E402
from studio_tag_api import assignments  # noqa: E402
from studio_tag_api import promotions  # noqa: E402
from studio_tag_api import registry  # noqa: E402
import studio_tags_api  # noqa: E402


def assert_equal(actual, expected, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def assert_no_duplicates(values: tuple[str, ...], label: str) -> None:
    duplicates = sorted({value for value in values if values.count(value) > 1})
    if duplicates:
        raise AssertionError(f"{label} contains duplicate routes: {duplicates!r}")


def test_post_routes_are_unique() -> None:
    assert_no_duplicates(routes.POST_PATHS, "POST_PATHS")


def test_options_routes_cover_each_post_route() -> None:
    assert_no_duplicates(routes.OPTIONS_PATHS, "OPTIONS_PATHS")
    assert_equal(set(routes.OPTIONS_PATHS), set(routes.POST_PATHS), "OPTIONS_PATHS")
    if routes.HEALTH_PATH in routes.OPTIONS_PATHS:
        raise AssertionError("health route should not gain CORS preflight handling implicitly")


def test_studio_adapter_covers_each_post_route() -> None:
    assert_equal(set(studio_tags_api.TAG_POST_PATHS), set(routes.POST_PATHS), "Studio tag route keys")
    assert_equal(set(studio_tags_api.POST_HANDLERS), set(routes.POST_PATHS), "Studio tag handler keys")


def test_retired_vocabulary_import_routes_are_absent() -> None:
    retired_paths = {"/import-tag-registry", "/import-tag-aliases"}
    assert_equal(retired_paths.isdisjoint(routes.POST_PATHS), True, "retired routes in POST_PATHS")
    assert_equal(retired_paths.isdisjoint(studio_tags_api.POST_HANDLERS), True, "retired routes in POST_HANDLERS")


def test_retired_assignment_import_routes_are_absent() -> None:
    retired_paths = {"/import-tag-assignments-preview", "/import-tag-assignments"}
    assert_equal(retired_paths.isdisjoint(routes.POST_PATHS), True, "retired assignment routes in POST_PATHS")
    assert_equal(retired_paths.isdisjoint(studio_tags_api.POST_HANDLERS), True, "retired assignment routes in POST_HANDLERS")


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
    if not all(callable(handler) for handler in expected_handlers):
        raise AssertionError("tag write handlers must be callable from functional modules")


def test_registry_group_edit_writes_only_registry_and_preserves_linked_document(
    tmp_path,
    monkeypatch,
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
    registry_path.write_text(
        json.dumps(
            {
                "tag_registry_version": "tag_registry_v4",
                "policy": {"allowed_groups": ["subject", "theme"]},
                "tags": [
                    {
                        "tag_id": "trees",
                        "group": "subject",
                        "description": "",
                        "doc_id": "d-20260727-225608-000001",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    aliases_path.write_text(
        json.dumps(
            {
                "tag_aliases_version": "tag_aliases_v2",
                "aliases": {},
            }
        ),
        encoding="utf-8",
    )
    assignments_path.write_text(
        json.dumps(
            {
                "tag_assignments_version": "tag_assignments_v2",
                "series": {},
            }
        ),
        encoding="utf-8",
    )
    document_path.write_text(
        "---\n"
        "doc_id: d-20260727-225608-000001\n"
        "title: trees\n"
        "group: subject\n"
        "---\n"
        "# trees\n",
        encoding="utf-8",
    )
    document_before = document_path.read_bytes()
    writes = {}
    monkeypatch.setattr(
        registry.tag_transactions,
        "atomic_write_many",
        lambda payloads: writes.update(payloads),
    )
    monkeypatch.setattr(
        registry.tag_document_creation,
        "build_tag_document_create_plan",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("Tag edit must not invoke document creation")
        ),
    )
    monkeypatch.setattr(registry.common, "utc_now", lambda: "2026-07-29T12:00:00Z")
    monkeypatch.setattr(registry.common, "log_event", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        registry.common,
        "attach_tag_activity",
        lambda *_args, **_kwargs: None,
    )

    result = registry.mutate_tag_response(
        tmp_path,
        {
            "action": "edit",
            "tag_id": "trees",
            "new_group": "theme",
        },
        preview=False,
    )

    assert result["group_changed"] is True
    assert set(writes) == {registry_path.resolve()}
    assert writes[registry_path.resolve()]["tags"][0]["group"] == "theme"
    assert (
        writes[registry_path.resolve()]["tags"][0]["doc_id"]
        == "d-20260727-225608-000001"
    )
    assert document_path.read_bytes() == document_before


def main() -> None:
    test_post_routes_are_unique()
    test_options_routes_cover_each_post_route()
    test_studio_adapter_covers_each_post_route()
    test_retired_vocabulary_import_routes_are_absent()
    test_retired_assignment_import_routes_are_absent()
    test_tag_write_handlers_live_in_functional_modules()
    print("Tag route tests OK")


if __name__ == "__main__":
    main()
