"""Production parser, registry, projection, and usage checks for Catalogue tokens."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any

from repo_factory import docs_scope_record, write_docs_scope_config, write_json, write_site_tools_config, write_text


REPO_ROOT = Path(__file__).resolve().parents[3]
BUILD_DIR = REPO_ROOT / "docs-viewer" / "build"
SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
for path in (BUILD_DIR, SERVICES_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from docs_builder.pipeline import DocsDataBuilder  # noqa: E402
from docs_builder.semantic_token_registry import (  # noqa: E402
    load_semantic_token_registry,
    parse_semantic_token_registry,
)
from docs_builder.semantic_tokens import (  # noqa: E402
    parse_catalogue_tokens,
    semantic_token_at_selection,
    serialize_semantic_token,
)
from docs_scope_config import load_docs_scope_configs  # noqa: E402


FIXTURE_PATH = REPO_ROOT / "docs-viewer/tests/fixtures/semantic_tokens_catalogue_v1.json"


def load_fixture() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def fixture_registry_payload() -> dict[str, Any]:
    return {
        "schema_version": "docs_semantic_token_registry_v1",
        "target_lookup_url": "/docs-viewer/data/generated/semantic-tokens/target-lookup.json",
        "families": [load_fixture()["catalogue_definition"]],
    }


def test_registry_and_python_parser_match_the_frozen_fixture() -> None:
    fixture = load_fixture()
    registry = parse_semantic_token_registry(fixture_registry_payload())
    assert registry is not None

    for case in fixture["cases"]:
        tokens = parse_catalogue_tokens(case["source"], registry=registry)
        assert len(tokens) == len(case["tokens"]), case["id"]
        for actual, expected in zip(tokens, case["tokens"], strict=True):
            assert actual.raw == expected["raw"], case["id"]
            assert actual.source_range == expected["source_range"], case["id"]
            assert actual.family == expected["family"], case["id"]
            assert actual.target_type == expected["target_type"], case["id"]
            assert actual.target_id == expected["target_id"], case["id"]
            assert actual.title == expected["title"], case["id"]
            assert actual.supported is expected["supported"], case["id"]
            if actual.supported:
                assert serialize_semantic_token(
                    family=actual.family,
                    target_type=actual.target_type,
                    target_id=actual.target_id,
                    title=expected.get("input_title", actual.title),
                ) == expected["serialized"], case["id"]
        for expectation in case.get("caret_expectations", []):
            active = semantic_token_at_selection(
                tokens,
                start=expectation["offset"],
                end=expectation["offset"],
            )
            expected_index = expectation["active_token_index"]
            assert active is (tokens[expected_index] if expected_index is not None else None), case["id"]


def test_production_registry_is_the_accepted_catalogue_definition() -> None:
    payload = json.loads(
        (
            REPO_ROOT / "docs-viewer/config/semantic-tokens/registry.json"
        ).read_text(encoding="utf-8")
    )
    assert payload == fixture_registry_payload()
    assert load_semantic_token_registry(REPO_ROOT) is not None


def write_builder_fixture(root: Path) -> tuple[str, str]:
    resolved_case = next(
        case for case in load_fixture()["cases"] if case["id"] == "resolved_work_00638"
    )
    broken_case = next(
        case for case in load_fixture()["cases"] if case["id"] == "broken_missing_work"
    )
    scope_record = docs_scope_record(
        "analysis",
        default_doc_id=resolved_case["source_doc_id"],
    )
    write_docs_scope_config(root, [scope_record])
    write_site_tools_config(root)
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
    write_json(
        root / "docs-viewer/config/semantic-tokens/registry.json",
        fixture_registry_payload(),
    )
    target_lookup = load_fixture()["target_lookup_example"]
    target_lookup["targets"].append(
        {
            "family": "catalogue",
            "target_type": "work",
            "target_id": "99999",
            "title": "missing work",
            "href": "",
            "meta": [],
        }
    )
    write_json(
        root / "docs-viewer/data/generated/semantic-tokens/target-lookup.json",
        target_lookup,
    )
    write_text(
        root / f"docs-viewer/scopes/analysis/source/documents/{resolved_case['source_doc_id']}.md",
        (
            "---\n"
            f"doc_id: {resolved_case['source_doc_id']}\n"
            "title: Resolved fixture\n"
            "added_date: 2026-07-26\n"
            "last_updated: 2026-07-26 12:00:00\n"
            'parent_id: ""\n'
            "---\n"
            f"{resolved_case['source']}"
        ),
    )
    write_text(
        root / f"docs-viewer/scopes/analysis/source/documents/{broken_case['source_doc_id']}.md",
        (
            "---\n"
            f"doc_id: {broken_case['source_doc_id']}\n"
            "title: Broken fixture\n"
            "added_date: 2026-07-26\n"
            "last_updated: 2026-07-26 12:00:00\n"
            'parent_id: ""\n'
            "---\n"
            f"{broken_case['source']}"
        ),
    )
    return resolved_case["source_doc_id"], broken_case["source_doc_id"]


def test_builder_projects_only_resolved_lookup_rows_and_writes_usage() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        resolved_doc_id, broken_doc_id = write_builder_fixture(root)
        registry = load_semantic_token_registry(root)
        assert registry is not None
        builder = DocsDataBuilder(
            repo_root=root,
            config=load_docs_scope_configs(root)["analysis"],
            skip_media_builds=True,
        )
        result = builder.run(write=True)
        resolved_payload = json.loads(
            (
                root
                / f"docs-viewer/scopes/analysis/published/documents/by-id/{resolved_doc_id}.json"
            ).read_text(encoding="utf-8")
        )
        broken_payload = json.loads(
            (
                root
                / f"docs-viewer/scopes/analysis/published/documents/by-id/{broken_doc_id}.json"
            ).read_text(encoding="utf-8")
        )
        usage_index = json.loads(
            (
                root
                / "docs-viewer/scopes/analysis/published/documents/semantic-tokens/index.json"
            ).read_text(encoding="utf-8")
        )
        by_document = json.loads(
            (
                root
                / (
                    "docs-viewer/scopes/analysis/published/documents/"
                    f"semantic-tokens/by-document/{resolved_doc_id}.json"
                )
            ).read_text(encoding="utf-8")
        )
        by_target = json.loads(
            (
                root
                / (
                    "docs-viewer/scopes/analysis/published/documents/"
                    "semantic-tokens/by-target/catalogue/work/00638.json"
                )
            ).read_text(encoding="utf-8")
        )
        broken_usage_path_exists = (
            root
            / f"docs-viewer/scopes/analysis/published/documents/semantic-tokens/by-document/{broken_doc_id}.json"
        ).exists()

    assert '<a href="/works/?work=00638"' in resolved_payload["content_html"]
    assert "[[catalogue:work:99999|missing work]]" in broken_payload["content_html"]
    assert result["diagnostics"]["warning_count"] == 0
    assert usage_index == load_fixture()["usage_index_example"]
    assert by_document["occurrences"] == usage_index["occurrences"]
    assert by_target["target"] == {
        "family": "catalogue",
        "target_type": "work",
        "target_id": "00638",
        "href": "/works/?work=00638",
    }
    assert by_target["occurrences"] == usage_index["occurrences"]
    assert not broken_usage_path_exists
