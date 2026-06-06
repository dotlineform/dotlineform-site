#!/usr/bin/env python3
"""Validate Rubyless generated-output contract fixtures."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_PATH = REPO_ROOT / "studio" / "tests" / "fixtures" / "generated_output_contracts.json"
REQUIRED_TOP_LEVEL_SECTIONS = {
    "schema",
    "policy",
    "docs_viewer",
    "docs_search",
    "catalogue_search",
    "catalogue_prose",
}
REQUIRED_CATALOGUE_PROSE_KINDS = {"work", "series", "moment"}
REQUIRED_CATALOGUE_SEARCH_KINDS = {"work", "series", "moment"}


def assert_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def assert_true(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)


def assert_contains(haystack: str, needle: str, label: str) -> None:
    if needle not in haystack:
        raise AssertionError(f"{label}: expected {needle!r} in {haystack!r}")


def assert_not_contains(haystack: str, needle: str, label: str) -> None:
    if needle in haystack:
        raise AssertionError(f"{label}: did not expect {needle!r} in {haystack!r}")


def load_fixture() -> dict[str, Any]:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert_true(isinstance(payload, dict), "fixture top level must be an object")
    return payload


def assert_required_keys(payload: dict[str, Any], required: list[str], label: str) -> None:
    missing = [key for key in required if key not in payload]
    assert_equal(missing, [], f"{label} missing keys")


def assert_allowed_keys(payload: dict[str, Any], allowed: list[str], label: str) -> None:
    extra = [key for key in payload if key not in allowed]
    assert_equal(extra, [], f"{label} extra keys")


def assert_search_entry(entry: dict[str, Any], label: str, *, requires_href: bool = True) -> None:
    required = ["id", "kind", "title", "search_terms", "search_text"]
    if requires_href:
        required.append("href")
    assert_required_keys(entry, required, label)
    assert_true(isinstance(entry["search_terms"], list) and entry["search_terms"], f"{label} search_terms")
    assert_equal(entry["search_text"], " ".join(entry["search_terms"]), f"{label} search_text")


def assert_no_non_contract_fragments(html: str, fragments: list[str], label: str) -> None:
    for fragment in fragments:
        assert_not_contains(html, fragment, f"{label} non-contract fragment")


def test_fixture_declares_contract_policy() -> None:
    payload = load_fixture()
    assert_equal(set(payload.keys()), REQUIRED_TOP_LEVEL_SECTIONS, "top-level sections")
    assert_equal(payload["schema"], "rubyless_generated_output_contract_fixtures_v1", "schema")

    policy = payload["policy"]
    renderer = policy["renderer_contract"]
    assert_equal(policy["protects"], "app-facing generated data contracts", "policy protects")
    assert_true("Jekyll output" in policy["does_not_protect"], "policy rejects Jekyll output lock-in")
    assert_true("Kramdown-specific wrapping" in policy["does_not_protect"], "policy rejects Kramdown lock-in")
    assert_equal(renderer["markdown_library"], "markdown-it-py", "renderer library")
    assert_equal(renderer["preset"], "commonmark", "renderer preset")
    assert_equal(renderer["enabled_rules"], ["table"], "renderer enabled rules")
    assert_equal(renderer["enabled_plugins"], [], "renderer plugins")
    assert_equal(renderer["jekyll_kramdown_parity"], False, "renderer parity policy")


def test_docs_viewer_index_contract_fixture() -> None:
    fixture = load_fixture()["docs_viewer"]["index_json"]
    doc_entry = fixture["doc_entry"]

    assert_equal(fixture["path_pattern"], "<docs_scope.output>/index.json", "docs index path pattern")
    assert_equal(fixture["required_top_level_keys"], ["docs", "generated_at", "viewer_options"], "docs index keys")
    assert_true(isinstance(fixture["viewer_options"]["non_loadable_doc_ids"], list), "non-loadable ids")
    assert_true(isinstance(fixture["viewer_options"]["manage_only_tree_root_ids"], list), "manage-only roots")
    assert_equal(fixture["viewer_options"]["show_updated_date"], True, "show updated date")
    assert_required_keys(
        doc_entry,
        [
            "doc_id",
            "title",
            "added_date",
            "last_updated",
            "parent_id",
            "source_path",
            "viewer_url",
            "content_url",
            "content_text_length",
        ],
        "docs index entry",
    )
    assert_contains(doc_entry["viewer_url"], "scope=studio", "viewer URL scope")
    assert_contains(doc_entry["content_url"], "/by-id/contract-fixture.json", "content URL by-id path")
    assert_true(isinstance(doc_entry["content_text_length"], int), "content text length type")
    assert_true(doc_entry["content_text_length"] >= 0, "content text length non-negative")


def test_docs_viewer_index_tree_contract_fixture() -> None:
    fixture = load_fixture()["docs_viewer"]["index_tree_json"]
    doc_entry = fixture["doc_entry"]

    assert_equal(fixture["path_pattern"], "<docs_scope.output>/index-tree.json", "docs tree path pattern")
    assert_equal(fixture["schema"], "docs_index_tree_v1", "docs tree schema")
    assert_equal(fixture["required_top_level_keys"], ["schema", "docs", "generated_at", "viewer_options"], "docs tree keys")
    assert_allowed_keys(doc_entry, fixture["allowed_doc_entry_keys"], "docs tree entry")
    assert_contains(doc_entry["content_url"], "/by-id/contract-fixture.json", "tree content URL by-id path")


def test_docs_viewer_recently_added_contract_fixture() -> None:
    fixture = load_fixture()["docs_viewer"]["recently_added_json"]
    doc_entry = fixture["doc_entry"]

    assert_equal(fixture["path_pattern"], "<docs_scope.output>/recently-added.json", "recent path pattern")
    assert_equal(fixture["schema"], "docs_recently_added_v1", "recent schema")
    assert_equal(fixture["limit"], 10, "recent limit")
    assert_equal(fixture["required_top_level_keys"], ["schema", "docs", "generated_at", "limit"], "recent keys")
    assert_allowed_keys(doc_entry, fixture["allowed_doc_entry_keys"], "recent entry")
    assert_contains(doc_entry["content_url"], "/by-id/contract-fixture.json", "recent content URL by-id path")
    assert_true(doc_entry["added_date"], "recent entry added date")


def test_docs_viewer_by_id_contract_fixture() -> None:
    fixture = load_fixture()["docs_viewer"]["by_id_json"]
    payload = fixture["payload"]

    assert_equal(fixture["path_pattern"], "<docs_scope.output>/by-id/<doc_id>.json", "by-id path pattern")
    assert_equal(fixture["scope_contract"], "manage/local rich selected-document payload", "by-id scope contract")
    assert_required_keys(payload, fixture["required_top_level_keys"], "by-id payload")
    assert_equal(payload["doc_id"], "contract-fixture", "by-id doc id")
    assert_equal(payload["viewer_url"], "/docs/?scope=studio&doc=contract-fixture", "by-id viewer URL")
    for snippet in fixture["html_semantics_contains"]:
        assert_contains(payload["content_html"], snippet, "by-id HTML semantics")
    assert_no_non_contract_fragments(payload["content_html"], fixture["non_contract_fragments"], "by-id HTML")


def test_docs_viewer_public_by_id_contract_fixture() -> None:
    fixture = load_fixture()["docs_viewer"]["public_by_id_json"]
    payload = fixture["payload"]

    assert_equal(fixture["path_pattern"], "<public_docs_scope.output>/by-id/<doc_id>.json", "public by-id path pattern")
    assert_equal(fixture["scope_contract"], "public reader selected-document payload", "public by-id scope contract")
    assert_required_keys(payload, fixture["required_top_level_keys"], "public by-id payload")
    assert_allowed_keys(payload, fixture["allowed_top_level_keys"], "public by-id payload")
    assert_contains(payload["content_html"], "<h1 id=\"public-contract-fixture\">", "public by-id HTML semantics")


def test_docs_viewer_reference_payload_contract_fixtures() -> None:
    references = load_fixture()["docs_viewer"]["references"]
    index_fixture = references["index_json"]
    target_fixture = references["by_target_json"]

    assert_required_keys(index_fixture, index_fixture["required_top_level_keys"], "references index")
    assert_equal(index_fixture["header"]["schema"], "docs_semantic_references_index_v1", "references index schema")
    assert_equal(index_fixture["header"]["target_count"], len(index_fixture["targets"]), "references target count")
    target = index_fixture["targets"][0]
    for key in ("target_kind", "target_id", "target_key", "target_title", "target_status", "target_href", "count"):
        assert_true(target.get(key) not in (None, ""), f"references index target {key}")
    assert_contains(target["bucket_url"], "/references/by-target/work/00638.json", "target bucket URL")

    assert_required_keys(target_fixture, target_fixture["required_top_level_keys"], "references by-target")
    assert_equal(target_fixture["header"]["schema"], "docs_semantic_references_by_target_v1", "target schema")
    assert_equal(target_fixture["header"]["count"], len(target_fixture["references"]), "target reference count")
    for key in ("target_kind", "target_id", "target_key", "target_status", "target_href", "target_title", "count"):
        assert_true(target_fixture.get(key) not in (None, ""), f"target payload {key}")
    sample_reference = target_fixture["references"][0]
    for key in (
        "source_scope",
        "source_doc_id",
        "source_title",
        "source_path",
        "source_viewer_url",
        "label",
        "action",
        "ordinal",
    ):
        assert_true(sample_reference.get(key) not in (None, ""), f"reference sample {key}")
    assert_equal(sample_reference["ordinal"], 1, "reference ordinal")


def test_docs_search_payload_contract_fixture() -> None:
    fixture = load_fixture()["docs_search"]["index_json"]
    header = fixture["header"]
    entry = fixture["entry"]

    assert_equal(fixture["path_pattern"], "<docs_scope.search_output>", "docs search path pattern")
    assert_equal(header["schema"], "search_index_studio_v1", "docs search schema")
    assert_equal(header["scope"], "studio", "docs search scope")
    assert_true(re.fullmatch(header["version_pattern"], "blake2b-0123456789abcdef0123456789abcdef"), "docs version pattern")
    assert_equal(header["count"], 1, "docs search count")
    assert_search_entry(entry, "docs search entry")
    assert_equal(entry["kind"], "doc", "docs search kind")
    assert_contains(entry["href"], "/docs/?scope=studio&doc=", "docs search href")
    assert_true("parent_title" in entry, "docs search includes parent title when available")


def test_catalogue_search_payload_contract_fixture() -> None:
    fixture = load_fixture()["catalogue_search"]["index_json"]
    header = fixture["header"]
    entries = fixture["entries"]

    assert_equal(fixture["path_pattern"], "assets/data/search/catalogue/index.json", "catalogue search path")
    assert_equal(header["schema"], "search_index_v1", "catalogue search schema")
    assert_true(re.fullmatch(header["version_pattern"], "blake2b-fedcba9876543210fedcba9876543210"), "catalogue version pattern")
    assert_equal(header["count"], len(entries), "catalogue search count")
    assert_equal({entry["kind"] for entry in entries}, REQUIRED_CATALOGUE_SEARCH_KINDS, "catalogue search kinds")
    for entry in entries:
        assert_search_entry(entry, f"catalogue search {entry['kind']}", requires_href=False)
        assert_true("href" not in entry, f"catalogue search {entry['kind']} should derive public URLs at runtime")

    work_entry = next(entry for entry in entries if entry["kind"] == "work")
    assert_true(isinstance(work_entry["series_ids"], list), "work series ids")
    assert_true(isinstance(work_entry["series_titles"], list), "work series titles")


def test_catalogue_prose_content_html_contract_fixtures() -> None:
    fixture = load_fixture()["catalogue_prose"]
    cases = fixture["content_html_cases"]

    assert_equal({case["kind"] for case in cases}, REQUIRED_CATALOGUE_PROSE_KINDS, "catalogue prose kinds")
    for case in cases:
        assert_true(case.get("id"), f"{case['kind']} case id")
        assert_true(case.get("source_markdown"), f"{case['kind']} source markdown")
        assert_true(case.get("content_html"), f"{case['kind']} content_html")
        for snippet in case["html_semantics_contains"]:
            assert_contains(case["content_html"], snippet, f"{case['kind']} content HTML semantics")
        assert_no_non_contract_fragments(case["content_html"], fixture["non_contract_fragments"], f"{case['kind']} content_html")


def main() -> None:
    test_fixture_declares_contract_policy()
    test_docs_viewer_index_contract_fixture()
    test_docs_viewer_index_tree_contract_fixture()
    test_docs_viewer_recently_added_contract_fixture()
    test_docs_viewer_by_id_contract_fixture()
    test_docs_viewer_public_by_id_contract_fixture()
    test_docs_viewer_reference_payload_contract_fixtures()
    test_docs_search_payload_contract_fixture()
    test_catalogue_search_payload_contract_fixture()
    test_catalogue_prose_content_html_contract_fixtures()
    print("Generated-output contract fixture tests OK")


if __name__ == "__main__":
    main()
