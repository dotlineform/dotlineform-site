#!/usr/bin/env python3
"""Docs scope config validation tests."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest

from docs_management_test_support import docs_scope_config, make_repo, write_docs_scope_config, write_json
from repo_factory import docs_scope_record, docs_sub_scope_record


REPO_ROOT = Path(__file__).resolve().parents[3]


def write_scope_record(repo_root: Path, record: dict[str, object]) -> None:
    write_json(
        repo_root / "docs-viewer/config/scopes/docs_scopes.json",
        {"schema_version": "docs_scopes_v3", "scopes": [record]},
    )


def test_docs_scope_config_selected_local_scope_does_not_resolve_external_workspace() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_json(
            repo_root / "docs-viewer/config/scopes/docs_scopes.json",
            {
                "schema_version": "docs_scopes_v3",
                "scopes": [
                    docs_scope_record("studio", default_doc_id="studio"),
                    docs_scope_record(
                        "private",
                        scope_type="local_external",
                        default_doc_id="private",
                    ),
                ],
            },
        )
        unavailable_projects = repo_root / "unavailable-projects"
        with patch.dict(
            "os.environ",
            {"DOTLINEFORM_PROJECTS_BASE_DIR": str(unavailable_projects)},
        ):
            configs = docs_scope_config.load_docs_scope_configs(
                repo_root,
                scope_ids=("studio",),
            )
            try:
                docs_scope_config.load_docs_scope_configs(
                    repo_root,
                    scope_ids=("private",),
                )
            except ValueError as exc:
                external_error = str(exc)
            else:
                raise AssertionError("Expected a selected external scope to require its configured workspace")

    assert list(configs) == ["studio"]
    assert "external_data_root does not exist" in external_error


def sub_scope_record(
    scope_id: str,
    sub_scope: str,
    *,
    source_path: str | None = None,
    public_docs_path: str | None = None,
    ui_statuses: list[str] | None = None,
    analysis_tag_groups: list[str] | None = None,
) -> dict[str, object]:
    record = docs_sub_scope_record(
        scope_id,
        sub_scope,
        title=sub_scope.title(),
        scope_type="public",
        public_docs_path=public_docs_path,
        ui_statuses=ui_statuses,
        analysis_tag_groups=analysis_tag_groups,
    )
    if source_path is not None:
        record["source"] = {
            "location": {"provider": "repository", "path": source_path},
        }
    return record


def test_docs_scope_config_rejects_repeated_published_search_role() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        record = docs_scope_record("studio", default_doc_id="child")
        published = record["published"]
        assert isinstance(published, dict)
        published["search"] = {
            "location": {
                "provider": "repository",
                "path": "docs-viewer/scopes/studio/published/search/index.json",
            }
        }
        write_scope_record(repo_root, record)
        try:
            docs_scope_config.load_docs_scope_configs(repo_root)
        except ValueError as exc:
            assert "must not repeat scope-root paths: search" in str(exc)
        else:
            raise AssertionError("Expected docs scope config to reject a repeated published search role")


def test_docs_scope_config_requires_named_document_and_sub_scope_children() -> None:
    for field in ("documents_path", "sub_scopes_path"):
        with make_repo() as temp_path:
            repo_root = Path(temp_path)
            record = docs_scope_record("studio", default_doc_id="child")
            record["source"][field] = "."  # type: ignore[index]
            write_scope_record(repo_root, record)
            try:
                docs_scope_config.load_docs_scope_configs(repo_root)
            except ValueError as exc:
                assert f"must not repeat scope-root paths: {field}" in str(exc)
            else:
                raise AssertionError(f"Expected docs scope config to reject source {field}=.")


def test_docs_scope_config_rejects_local_published_payloads_in_public_assets() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        record = docs_scope_record("studio", default_doc_id="child")
        record["scope_root"]["path"] = "site/assets/data/docs/scopes/studio"  # type: ignore[index]
        write_scope_record(repo_root, record)
        try:
            docs_scope_config.load_docs_scope_configs(repo_root)
        except ValueError as exc:
            assert "scopes[0].scope_root.path must be docs-viewer/scopes/studio" in str(exc)
        else:
            raise AssertionError("Expected local scope config to reject public asset payload roots")


def test_docs_scope_config_accepts_separate_public_projection() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_scope_record(
            repo_root,
            docs_scope_record(
                "research",
                scope_type="public",
                viewer_base_url="/research/",
                include_scope_param=False,
                default_doc_id="research",
            ),
        )
        config = docs_scope_config.load_docs_scope_configs(repo_root)["research"]

    assert docs_scope_config.published_documents_path(config).as_posix() == "docs-viewer/scopes/research/published/documents"
    assert docs_scope_config.published_search_path(config).as_posix() == "docs-viewer/scopes/research/published/search/index.json"
    assert docs_scope_config.public_documents_path(config).as_posix() == "site/assets/data/docs/scopes/research"
    assert docs_scope_config.public_search_path(config).as_posix() == "site/assets/data/search/research/index.json"


def test_docs_scope_config_accepts_nested_sub_scopes() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        record = docs_scope_record(
            "research",
            scope_type="public",
            viewer_base_url="/research/",
            include_scope_param=False,
            default_doc_id="research",
            sub_scopes=[
                sub_scope_record(
                    "research",
                    "tags",
                    ui_statuses=["draft", "done"],
                    analysis_tag_groups=["subject", "theme"],
                )
            ],
        )
        write_scope_record(repo_root, record)
        config = docs_scope_config.load_docs_scope_configs(repo_root)["research"]

    sub_scope = config.sub_scopes[0]
    assert sub_scope.sub_scope == "tags"
    assert sub_scope.title == "Tags"
    assert sub_scope.public_title == "Tags"
    assert sub_scope.supports_return_import is False
    assert sub_scope.lifecycle is None
    assert sub_scope.ui_statuses == ("draft", "done")
    assert sub_scope.sub_scope_customisation is not None
    assert sub_scope.sub_scope_customisation.customisation_id == "analysis_tags"
    assert sub_scope.sub_scope_customisation.settings == {
        "groups": ("subject", "theme")
    }
    assert docs_scope_config.document_source_path(sub_scope).as_posix() == (
        "docs-viewer/scopes/research/source/sub-scopes/tags/documents"
    )
    assert docs_scope_config.published_documents_path(sub_scope).as_posix() == (
        "docs-viewer/scopes/research/published/documents/sub-scopes/tags"
    )
    assert docs_scope_config.public_documents_path(sub_scope).as_posix() == "site/assets/data/docs/scopes/research/tags"


def test_docs_scope_config_validates_sub_scope_lifecycle_association() -> None:
    association = {
        "tool_id": "docs-viewer-scope-lifecycle",
        "report_host_doc_id": "d-20260731-120000-a1b2c3",
        "report_host_source_revision": f"sha256:{'0' * 64}",
    }
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_scope_record(
            repo_root,
            docs_scope_record(
                "studio",
                sub_scopes=[docs_sub_scope_record("studio", "tags", lifecycle=association)],
            ),
        )
        lifecycle = docs_scope_config.load_docs_scope_configs(repo_root)["studio"].sub_scopes[0].lifecycle
        assert lifecycle is not None
        assert lifecycle.report_host_doc_id == association["report_host_doc_id"]

        association["report_host_source_revision"] = "stale"
        write_scope_record(
            repo_root,
            docs_scope_record(
                "studio",
                sub_scopes=[docs_sub_scope_record("studio", "tags", lifecycle=association)],
            ),
        )
        with pytest.raises(ValueError, match="sha256 revision receipt"):
            docs_scope_config.load_docs_scope_configs(repo_root)


def test_docs_scope_config_accepts_route_specific_sub_scope_public_title() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        sub_scope = sub_scope_record("research", "tags")
        sub_scope["public_title"] = "Concepts"
        write_scope_record(
            repo_root,
            docs_scope_record(
                "research",
                scope_type="public",
                viewer_base_url="/research/",
                include_scope_param=False,
                default_doc_id="research",
                sub_scopes=[sub_scope],
            ),
        )

        config = docs_scope_config.load_docs_scope_configs(repo_root)["research"]

    assert config.sub_scopes[0].title == "Tags"
    assert config.sub_scopes[0].public_title == "Concepts"


def test_docs_scope_config_accepts_registered_sub_scope_customisation() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        sub_scope = docs_sub_scope_record(
            "studio",
            "tags",
            sub_scope_customisation={
                "id": "analysis_tags",
                "settings": {"groups": ["Subject", "theme"]},
            },
        )
        write_scope_record(
            repo_root,
            docs_scope_record("studio", sub_scopes=[sub_scope]),
        )

        config = docs_scope_config.load_docs_scope_configs(repo_root)["studio"]

    customisation = config.sub_scopes[0].sub_scope_customisation
    assert customisation is not None
    assert customisation.customisation_id == "analysis_tags"
    assert customisation.settings == {"groups": ("subject", "theme")}


def test_docs_scope_config_selects_projects_customisation_from_configured_collection() -> None:
    projects_customisation = {
        "id": "dotlineform_projects",
        "settings": {},
    }
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_scope_record(
            repo_root,
            docs_scope_record(
                "studio",
                sub_scopes=[
                    docs_sub_scope_record(
                        "studio",
                        "project-notes",
                        sub_scope_customisation=projects_customisation,
                    )
                ],
            ),
        )
        config = docs_scope_config.load_docs_scope_configs(repo_root)["studio"]

    customisation = config.sub_scopes[0].sub_scope_customisation
    assert customisation is not None
    assert customisation.customisation_id == "dotlineform_projects"
    assert customisation.settings == {}


@pytest.mark.parametrize(
    ("sub_scope_customisation", "error"),
    [
        ("analysis_tags", "must be an object"),
        ({"id": "analysis_tags"}, "missing required fields: settings"),
        (
            {"id": "analysis_tags", "settings": {"groups": ["subject"]}, "module": "bad.js"},
            "unknown fields: module",
        ),
        ({"id": "analysis-tags", "settings": {"groups": ["subject"]}}, "id is invalid"),
        ({"id": "unknown", "settings": {}}, "id is unknown"),
        ({"id": "analysis_tags", "settings": {}}, "missing required fields: groups"),
        ({"id": "analysis_tags", "settings": {"groups": []}}, "must not be empty"),
        (
            {"id": "analysis_tags", "settings": {"groups": ["subject", "subject"]}},
            "must not contain duplicates",
        ),
        (
            {"id": "dotlineform_projects", "settings": {"extra": True}},
            "unknown fields: extra",
        ),
    ],
)
def test_docs_scope_config_rejects_invalid_sub_scope_customisation(
    sub_scope_customisation: object,
    error: str,
) -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        sub_scope = docs_sub_scope_record("studio", "tags")
        sub_scope["sub_scope_customisation"] = sub_scope_customisation
        write_scope_record(
            repo_root,
            docs_scope_record("studio", sub_scopes=[sub_scope]),
        )

        with pytest.raises(ValueError, match=error):
            docs_scope_config.load_docs_scope_configs(repo_root)


def test_docs_scope_config_rejects_legacy_document_groups_field() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        sub_scope = docs_sub_scope_record(
            "studio",
            "tags",
            sub_scope_customisation={
                "id": "analysis_tags",
                "settings": {"groups": ["subject"]},
            },
        )
        sub_scope["document_groups"] = ["subject"]
        write_scope_record(
            repo_root,
            docs_scope_record("studio", sub_scopes=[sub_scope]),
        )

        with pytest.raises(ValueError, match="document_groups is no longer supported"):
            docs_scope_config.load_docs_scope_configs(repo_root)


def test_docs_scope_config_rejects_unknown_sub_scope_fields() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        sub_scope = docs_sub_scope_record("studio", "notes")
        sub_scope["unregistered_extension"] = {"id": "example"}
        write_scope_record(
            repo_root,
            docs_scope_record("studio", sub_scopes=[sub_scope]),
        )

        with pytest.raises(ValueError, match="unknown fields: unregistered_extension"):
            docs_scope_config.load_docs_scope_configs(repo_root)


def test_docs_scope_config_accepts_explicit_sub_scope_return_import_opt_in() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        sub_scope = sub_scope_record("research", "tags")
        sub_scope["supports_return_import"] = True
        write_scope_record(
            repo_root,
            docs_scope_record(
                "research",
                scope_type="public",
                viewer_base_url="/research/",
                include_scope_param=False,
                default_doc_id="research",
                sub_scopes=[sub_scope],
            ),
        )

        config = docs_scope_config.load_docs_scope_configs(repo_root)["research"]

    assert config.sub_scopes[0].supports_return_import is True


def test_checked_scope_config_opts_only_analysis_tags_into_return_import() -> None:
    configs = docs_scope_config.load_docs_scope_configs(
        REPO_ROOT,
        scope_ids=["analysis"],
    )

    analysis_tags = configs["analysis"].sub_scopes[0]
    assert [
        (sub_scope.sub_scope, sub_scope.supports_return_import)
        for sub_scope in configs["analysis"].sub_scopes
    ] == [("tags", True)]
    assert not hasattr(analysis_tags, "document_groups")
    assert analysis_tags.sub_scope_customisation is not None
    assert analysis_tags.sub_scope_customisation.customisation_id == "analysis_tags"
    assert analysis_tags.sub_scope_customisation.settings == {
        "groups": ("subject", "domain", "form", "theme")
    }


@pytest.mark.parametrize("value", [None, 1, "true", []])
def test_docs_scope_config_rejects_invalid_sub_scope_return_import_opt_in(
    value: object,
) -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        sub_scope = docs_sub_scope_record(
            "studio",
            "tags",
            scope_type="local",
        )
        sub_scope["supports_return_import"] = value
        record = docs_scope_record("studio", sub_scopes=[sub_scope])
        write_scope_record(repo_root, record)

        with pytest.raises(ValueError, match="supports_return_import must be true or false"):
            docs_scope_config.load_docs_scope_configs(repo_root)


def test_docs_scope_config_rejects_invalid_sub_scope_metadata_vocabularies() -> None:
    invalid_values = (
        ("ui_statuses", "draft", "must be an array"),
        ("ui_statuses", ["draft", "draft"], "must not contain duplicates"),
    )
    for field, value, error in invalid_values:
        with make_repo() as temp_path:
            repo_root = Path(temp_path)
            sub_scope = docs_sub_scope_record("studio", "tags")
            sub_scope[field] = value
            record = docs_scope_record("studio", sub_scopes=[sub_scope])
            write_scope_record(repo_root, record)
            try:
                docs_scope_config.load_docs_scope_configs(repo_root)
            except ValueError as exc:
                assert error in str(exc)
            else:
                raise AssertionError(
                    f"Expected invalid sub-scope {field} to be rejected"
                )


def test_docs_scope_config_rejects_duplicate_sub_scopes() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(repo_root)
        config_path = repo_root / "docs-viewer/config/scopes/docs_scopes.json"
        payload = json.loads(config_path.read_text(encoding="utf-8"))
        payload["scopes"][0]["sub_scopes"] = [
            sub_scope_record("studio", "tags"),
            sub_scope_record("studio", "tags"),
        ]
        for item in payload["scopes"][0]["sub_scopes"]:
            item["public_projection"] = None
        write_json(config_path, payload)
        try:
            docs_scope_config.load_docs_scope_configs(repo_root)
        except ValueError as exc:
            assert "duplicated in scope 'studio'" in str(exc)
        else:
            raise AssertionError("Expected duplicate sub_scope ids to be rejected")


def test_docs_scope_config_rejects_repeated_sub_scope_paths() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(repo_root)
        config_path = repo_root / "docs-viewer/config/scopes/docs_scopes.json"
        payload = json.loads(config_path.read_text(encoding="utf-8"))
        item = sub_scope_record("studio", "tags", source_path="docs-viewer/scopes/tags/source")
        item["public_projection"] = None
        payload["scopes"][0]["sub_scopes"] = [item]
        write_json(config_path, payload)
        try:
            docs_scope_config.load_docs_scope_configs(repo_root)
        except ValueError as exc:
            assert "sub-scope studio/tags" in str(exc)
            assert "derives source and published paths from its parent scope_root" in str(exc)
        else:
            raise AssertionError("Expected repeated sub_scope source paths to be rejected")


def test_docs_scope_config_rejects_public_sub_scope_projection_outside_parent() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        record = docs_scope_record(
            "research",
            scope_type="public",
            viewer_base_url="/research/",
            include_scope_param=False,
            default_doc_id="research",
            sub_scopes=[
                sub_scope_record(
                    "research",
                    "tags",
                    public_docs_path="site/assets/data/docs/scopes/elsewhere/tags",
                )
            ],
        )
        write_scope_record(repo_root, record)
        try:
            docs_scope_config.load_docs_scope_configs(repo_root)
        except ValueError as exc:
            assert "sub-scope research/tags" in str(exc)
            assert "public documents must be site/assets/data/docs/scopes/research/tags" in str(exc)
        else:
            raise AssertionError("Expected public sub_scope projection outside the parent root to be rejected")


def test_docs_scope_config_accepts_explicit_mermaid_to_svg_build_contract() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        record = docs_scope_record("studio", default_doc_id="child")
        record["source"]["build_media"] = {  # type: ignore[index]
            "mermaid": {
                "path": "media/mermaid",
                "producer": "mermaid",
                "publishes_to": "svg",
            }
        }
        record["published"]["media"]["svg"]["build_inputs"] = ["mermaid"]  # type: ignore[index]
        write_scope_record(repo_root, record)

        config = docs_scope_config.load_docs_scope_configs(repo_root)["studio"]

    assert config.source.build_media["mermaid"].path == Path("media/mermaid")
    assert config.published.media["svg"].build_inputs == ("mermaid",)


def test_docs_scope_config_rejects_unhandled_media_types() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        record = docs_scope_record("studio", default_doc_id="child")
        record["published"]["media"]["video"] = {  # type: ignore[index]
            "reference_prefix": "docs/studio/video",
            "location": {
                "provider": "repository",
                "path": "docs-viewer/scopes/studio/published/documents/media/video",
            },
            "served_path_prefix": "/docs/media/studio/video",
            "build_inputs": [],
        }
        write_scope_record(repo_root, record)

        try:
            docs_scope_config.load_docs_scope_configs(repo_root)
        except ValueError as exc:
            assert "unsupported published media type" in str(exc)
        else:
            raise AssertionError("Expected unhandled published media type to require an explicit contract")


def test_docs_scope_policy_rejects_competing_producers_for_one_published_type() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        record = docs_scope_record("studio", default_doc_id="child")
        write_scope_record(repo_root, record)
        config = docs_scope_config.load_docs_scope_configs(repo_root)["studio"]

    builds = {
        "mermaid": docs_scope_config.DocsBuildMediaConfig(
            path=Path("media/mermaid"),
            producer="first",
            publishes_to="img",
        ),
        "other": docs_scope_config.DocsBuildMediaConfig(
            path=Path("media/other"),
            producer="second",
            publishes_to="img",
        ),
    }
    media = dict(config.published.media)
    media["img"] = replace(media["img"], build_inputs=("mermaid", "other"))
    competing = replace(
        config,
        source=replace(config.source, build_media=builds),
        published=replace(config.published, media=media),
    )

    try:
        docs_scope_config.validate_scope_policy(competing, field="scopes[0]")
    except ValueError as exc:
        assert "compete for published media 'img'" in str(exc)
    else:
        raise AssertionError("Expected competing media producers to be rejected")
