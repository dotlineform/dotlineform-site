"""Focused parser, builder, usage, and targeted-build checks for Tag tokens."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any

from repo_factory import docs_scope_record, write_docs_scope_config, write_json, write_text


REPO_ROOT = Path(__file__).resolve().parents[3]
BUILD_DIR = REPO_ROOT / "docs-viewer" / "build"
SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
for path in (BUILD_DIR, SERVICES_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from docs_builder.pipeline import DocsDataBuilder  # noqa: E402
from docs_builder.semantic_token_registry import (  # noqa: E402
    load_semantic_token_registry,
)
from docs_builder.semantic_tokens import (  # noqa: E402
    parse_catalogue_tokens,
    parse_semantic_tokens,
    semantic_token_at_selection,
    serialize_semantic_token,
)
from docs_scope_config import load_docs_scope_configs  # noqa: E402


FIRST_DOC_ID = "d-20260811-140000-a1b2c3"
SECOND_DOC_ID = "d-20260811-140001-d4e5f6"
TAG_HREF = (
    "/analysis/?doc=d-20260624-213316-478639"
    "&subdoc=d-20260727-225608-63967a"
)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def source_text(doc_id: str, title: str, body: str) -> str:
    return (
        "---\n"
        f"doc_id: {doc_id}\n"
        f"title: {title}\n"
        "added_date: 2026-08-11\n"
        "last_updated: 2026-08-11 14:00:00\n"
        'parent_id: ""\n'
        "---\n"
        f"{body}\n"
    )


def prepare_repo(root: Path) -> None:
    write_json(
        root / "site-tools/config/site-tools.json",
        {"schema_version": "site_tools_config_v1", "media": {"base": ""}},
    )
    write_docs_scope_config(
        root,
        [docs_scope_record("analysis", default_doc_id=FIRST_DOC_ID)],
    )
    write_json(
        root / "docs-viewer/config/routes/docs-viewer-routes.json",
        {
            "schema_version": "docs_viewer_routes_v1",
            "routes": [
                {
                    "route_id": "docs-manage",
                    "app_kind": "manage",
                    "default_scope_id": "analysis",
                    "features": ["recent"],
                    "recent_basis": "edited",
                }
            ],
        },
    )
    write_text(
        root / "docs-viewer/config/semantic-tokens/registry.json",
        (
            REPO_ROOT / "docs-viewer/config/semantic-tokens/registry.json"
        ).read_text(encoding="utf-8"),
    )
    write_json(
        root / "docs-viewer/data/generated/semantic-tokens/target-lookup.json",
        {
            "schema_version": "docs_semantic_token_target_lookup_v2",
            "targets": [
                {
                    "family": "catalogue",
                    "target_type": "work",
                    "target_id": "00638",
                    "title": "3 symbols",
                    "href": "/works/?work=00638",
                    "meta": ["2007"],
                },
                {
                    "family": "tag",
                    "target_type": "tag",
                    "target_id": "nerve",
                    "title": "nerve",
                    "href": TAG_HREF,
                    "meta": ["subject", "Nerve"],
                    "aliases": ["neural"],
                },
                {
                    "family": "tag",
                    "target_type": "tag",
                    "target_id": "unavailable",
                    "title": "unavailable",
                    "href": "",
                    "meta": ["theme", "Unavailable"],
                    "aliases": [],
                },
            ],
        },
    )
    source_dir = root / "docs-viewer/scopes/analysis/source/documents"
    write_text(
        source_dir / f"{FIRST_DOC_ID}.md",
        source_text(
            FIRST_DOC_ID,
            "First",
            (
                "Known [[tag:tag:nerve|Nerve]] and "
                "[[catalogue:work:00638|three signs]].\n\n"
                "Unknown [[tag:tag:missing|Missing]] and "
                "unavailable [[tag:tag:unavailable|Unavailable]]."
            ),
        ),
    )
    write_text(
        source_dir / f"{SECOND_DOC_ID}.md",
        source_text(
            SECOND_DOC_ID,
            "Second",
            "Another [[tag:tag:nerve|Nerve again]].",
        ),
    )


def builder(root: Path, *, only_doc_ids: list[str] | None = None) -> DocsDataBuilder:
    return DocsDataBuilder(
        repo_root=root,
        config=load_docs_scope_configs(root)["analysis"],
        only_doc_ids=only_doc_ids,
        skip_media_builds=True,
    )


def test_tag_registry_defines_separate_authoring_and_info_contributions() -> None:
    payload = read_json(
        REPO_ROOT / "docs-viewer/config/semantic-tokens/registry.json"
    )
    families = {family["key"]: family for family in payload["families"]}
    tag = families["tag"]

    assert tag["labels"] == {
        "family": "Tag",
        "source_action": "Add tag token",
        "info_view": "Tag token",
    }
    assert tag["ui_contributions"] == {
        "source_action": "source-add-tag-token",
        "modal": "tag-token-add-modal",
        "info_view": "tag-token-info",
    }
    assert tag["occurrence_fields"] == [
        {
            "key": "title",
            "label": "Title",
            "required": True,
            "editable": True,
            "control": "text",
        }
    ]
    assert tag["target_types"] == [
        {
            "key": "tag",
            "label": "Tag",
            "id_policy": {
                "normalizer": "slug",
                "input_pattern": "^[a-z0-9][a-z0-9-]*$",
                "canonical_pattern": "^[a-z0-9][a-z0-9-]*$",
            },
            "lookup_adapter": "tag-target-lookup",
            "lookup_fields": ["title", "href", "meta", "aliases"],
        }
    ]
    assert families["catalogue"]["ui_contributions"]["source_action"] == (
        "source-add-catalogue-token"
    )


def test_tag_parser_is_tolerant_context_aware_and_exact() -> None:
    registry = load_semantic_token_registry(REPO_ROOT)
    assert registry is not None
    valid = "[[tag:tag:nerve|Nerve \\| signal]]"
    unsupported = "[[future:item:alpha|Future]]"
    source = (
        f"{valid} {unsupported}\n"
        f"`{valid}`\n"
        f"<!-- {valid} -->\n"
        f"```\n{valid}\n```\n"
        "[[tag:tag:Nerve|wrong identity]]\n"
        "[[tag:image:tag:nerve|alt=wrong]]\n"
    )

    tokens = parse_semantic_tokens(source, registry=registry)

    assert [token.raw for token in tokens] == [valid, unsupported]
    assert tokens[0].family == tokens[0].target_type == "tag"
    assert tokens[0].target_id == "nerve"
    assert tokens[0].title == "Nerve | signal"
    assert tokens[0].supported is True
    assert tokens[1].supported is False
    assert source[tokens[0].start:tokens[0].end] == valid
    assert parse_catalogue_tokens(source, registry=registry) == []
    assert semantic_token_at_selection(
        tokens,
        start=tokens[0].start + 2,
        end=tokens[0].start + 2,
    ) is tokens[0]
    assert serialize_semantic_token(
        family="tag",
        target_type="tag",
        target_id="nerve",
        title="Nerve | signal",
    ) == valid


def test_tag_builder_renders_one_link_and_records_only_resolved_usage() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        result = builder(root).run(write=True)
        first = read_json(
            root
            / f"docs-viewer/scopes/analysis/published/documents/by-id/{FIRST_DOC_ID}.json"
        )
        usage = read_json(
            root
            / "docs-viewer/scopes/analysis/published/documents/semantic-tokens/index.json"
        )

    content = first["content_html"]
    assert (
        '<a href="/analysis/?doc=d-20260624-213316-478639&amp;subdoc='
        'd-20260727-225608-63967a" data-semantic-token-family="tag" '
        'data-semantic-token-target-type="tag" '
        'data-semantic-token-target-id="nerve" target="_blank" '
        'rel="noopener noreferrer">Nerve</a>'
    ) in content
    assert '<a href="/works/?work=00638" data-semantic-token-family="catalogue"' in content
    assert "[[tag:tag:missing|Missing]]" in content
    assert "[[tag:tag:unavailable|Unavailable]]" in content
    assert "neural" not in content
    assert "tag_registry_version" not in json.dumps(first)
    resolved = usage["occurrences"]
    assert usage["schema_version"] == "docs_semantic_token_usage_index_v1"
    assert len(resolved) == 3
    first_tag = next(
        row
        for row in resolved
        if row["source_doc_id"] == FIRST_DOC_ID and row["family"] == "tag"
    )
    assert first_tag == {
        "source_scope": "analysis",
        "source_doc_id": FIRST_DOC_ID,
        "source_range": {"start": 6, "end": 29},
        "raw": "[[tag:tag:nerve|Nerve]]",
        "title": "Nerve",
        "family": "tag",
        "target_type": "tag",
        "target_id": "nerve",
        "href": TAG_HREF,
    }
    assert result["diagnostics"]["warning_count"] == 0
    assert not (root / "site").exists()


def test_targeted_build_preserves_untouched_tag_usage_and_payload() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        builder(root).run(write=True)
        second_path = (
            root
            / f"docs-viewer/scopes/analysis/published/documents/by-id/{SECOND_DOC_ID}.json"
        )
        second_before = read_json(second_path)
        first_source = (
            root
            / f"docs-viewer/scopes/analysis/source/documents/{FIRST_DOC_ID}.md"
        )
        write_text(
            first_source,
            first_source.read_text(encoding="utf-8").replace(
                "[[tag:tag:nerve|Nerve]]",
                "[[tag:tag:nerve|Neural feeling]]",
            ),
        )

        result = builder(root, only_doc_ids=[FIRST_DOC_ID]).run(write=True)
        second_after = read_json(second_path)
        usage = read_json(
            root
            / "docs-viewer/scopes/analysis/published/documents/semantic-tokens/index.json"
        )

    assert result["diagnostics"]["build_mode"] == "targeted"
    assert result["diagnostics"]["only_doc_ids"] == [FIRST_DOC_ID]
    assert second_after == second_before
    tag_rows = [row for row in usage["occurrences"] if row["family"] == "tag"]
    assert [(row["source_doc_id"], row["title"]) for row in tag_rows] == [
        (FIRST_DOC_ID, "Neural feeling"),
        (SECOND_DOC_ID, "Nerve again"),
    ]
