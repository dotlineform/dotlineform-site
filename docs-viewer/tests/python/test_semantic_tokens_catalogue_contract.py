"""Contract checks for the CT-P0 shared Catalogue semantic-token fixtures."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_PATH = REPO_ROOT / "docs-viewer/tests/fixtures/semantic_tokens_catalogue_v1.json"
FIXTURE_SCHEMA = "docs_semantic_tokens_catalogue_contract_fixtures_v1"
REQUIRED_CASE_CATEGORIES = {
    "valid",
    "escaped",
    "malformed",
    "code-context",
    "adjacent-token",
    "caret-boundary",
    "broken",
}


def load_fixture() -> dict[str, Any]:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def assert_required_fields(record: dict[str, Any], fields: list[str]) -> None:
    assert set(fields).issubset(record), f"missing fields: {set(fields) - set(record)}"


def token_at_caret(tokens: list[dict[str, Any]], offset: int) -> int | None:
    active: list[int] = []
    for index, token in enumerate(tokens):
        source_range = token["source_range"]
        if token["activatable"] and source_range["start"] < offset < source_range["end"]:
            active.append(index)
    return active[0] if len(active) == 1 else None


def serialize_supported_token(token: dict[str, Any]) -> str:
    title = str(token.get("input_title", token["title"])).strip()
    escaped_title = title.replace("\\", "\\\\").replace("|", "\\|").replace("]", "\\]")
    return (
        f"[[{token['family']}:{token['target_type']}:{token['target_id']}"
        f"|{escaped_title}]]"
    )


def test_fixture_is_versioned_and_covers_the_frozen_cases() -> None:
    fixture = load_fixture()

    assert fixture["schema_version"] == FIXTURE_SCHEMA
    categories = {
        category
        for case in fixture["cases"]
        for category in case["categories"]
    }
    assert REQUIRED_CASE_CATEGORIES.issubset(categories)


def test_catalogue_definition_freezes_minimum_additive_contract() -> None:
    fixture = load_fixture()
    definition = fixture["catalogue_definition"]

    assert definition["schema_version"] == "docs_semantic_token_family_definition_v1"
    assert definition["key"] == "catalogue"
    assert definition["labels"] == {
        "family": "Catalogue",
        "source_action": "Add catalogue token",
        "info_view": "Catalogue token",
    }
    assert definition["ui_contributions"] == {
        "source_action": "source-add-catalogue-token",
        "modal": "catalogue-token-add-modal",
        "info_view": "catalogue-token-info",
    }
    assert definition["occurrence_fields"] == [
        {
            "key": "title",
            "label": "Title",
            "required": True,
            "editable": True,
            "control": "text",
        }
    ]

    targets = {target["key"]: target for target in definition["target_types"]}
    assert set(targets) == {"work", "series"}
    for target in targets.values():
        assert target["lookup_adapter"]
        assert target["lookup_fields"] == ["title", "href", "meta"]
        re.compile(target["id_policy"]["input_pattern"])
        re.compile(target["id_policy"]["canonical_pattern"])


def test_token_ranges_serialization_and_caret_boundaries_are_exact() -> None:
    fixture = load_fixture()
    definitions = {
        target["key"]: target
        for target in fixture["catalogue_definition"]["target_types"]
    }

    for case in fixture["cases"]:
        source = case["source"]
        tokens = case["tokens"]
        for token in tokens:
            source_range = token["source_range"]
            assert source[source_range["start"]:source_range["end"]] == token["raw"], case["id"]
            if token["supported"]:
                definition = definitions[token["target_type"]]
                canonical_pattern = definition["id_policy"]["canonical_pattern"]
                assert re.fullmatch(canonical_pattern, token["target_id"]), case["id"]
                assert serialize_supported_token(token) == token["serialized"] == token["raw"], case["id"]
        for expectation in case.get("caret_expectations", []):
            assert token_at_caret(tokens, expectation["offset"]) == expectation["active_token_index"], case["id"]


def test_versioned_json_examples_include_the_required_minimum() -> None:
    fixture = load_fixture()
    shapes = fixture["json_shapes"]
    lookup = fixture["target_lookup_example"]
    usage = fixture["usage_index_example"]
    broken = fixture["broken_link_example"]

    assert lookup["schema_version"] == shapes["target_lookup"]["schema_version"]
    assert_required_fields(lookup, shapes["target_lookup"]["required_envelope_fields"])
    for row in lookup["targets"]:
        assert_required_fields(row, shapes["target_lookup"]["required_row_fields"])
        assert row["href"].startswith("/")
        assert isinstance(row.get("meta", []), list)

    assert usage["schema_version"] == shapes["usage_index"]["schema_version"]
    assert_required_fields(usage, shapes["usage_index"]["required_envelope_fields"])
    for row in usage["occurrences"]:
        assert_required_fields(row, shapes["usage_index"]["required_row_fields"])

    assert_required_fields(broken, shapes["broken_link"]["required_row_fields"])
    assert broken["reason"] in shapes["broken_link"]["reason_values"]


def test_resolved_and_broken_examples_match_their_source_fixtures() -> None:
    fixture = load_fixture()
    cases = {case["id"]: case for case in fixture["cases"]}
    resolved = cases["resolved_work_00638"]
    broken = cases["broken_missing_work"]
    usage_row = fixture["usage_index_example"]["occurrences"][0]
    broken_row = fixture["broken_link_example"]

    assert usage_row["source_scope"] == resolved["source_scope"]
    assert usage_row["source_doc_id"] == resolved["source_doc_id"]
    assert usage_row["source_range"] == resolved["tokens"][0]["source_range"]
    assert usage_row["raw"] == resolved["tokens"][0]["raw"]
    assert usage_row["href"] == resolved["tokens"][0]["projection"]["href"]

    assert broken_row["source_scope"] == broken["source_scope"]
    assert broken_row["source_doc_id"] == broken["source_doc_id"]
    assert broken_row["source_range"] == broken["tokens"][0]["source_range"]
    assert broken_row["raw"] == broken["tokens"][0]["raw"]
    assert broken_row["reason"] == broken["tokens"][0]["projection"]["reason"]
