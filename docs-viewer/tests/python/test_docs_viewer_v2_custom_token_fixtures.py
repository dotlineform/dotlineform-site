#!/usr/bin/env python3
"""Validate Docs Viewer v2 custom-token contract fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_PATH = REPO_ROOT / "docs-viewer" / "tests" / "fixtures" / "docs_viewer_v2_custom_tokens.json"
REQUIRED_COVERAGE = {
    "media_token",
    "html_media_token",
    "invalid_missing_reference",
    "generated_search_text",
}


def assert_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def assert_true(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)


def load_fixture() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def case_by_id(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    cases = payload.get("cases")
    assert_true(isinstance(cases, list) and cases, "fixture must contain cases")
    by_id = {}
    for case in cases:
        assert_true(isinstance(case, dict), "case must be an object")
        case_id = case.get("id")
        assert_true(isinstance(case_id, str) and case_id, "case id must be a non-empty string")
        assert_true(case_id not in by_id, f"duplicate case id {case_id}")
        by_id[case_id] = case
    return by_id


def test_fixture_declares_renderer_contract() -> None:
    payload = load_fixture()
    contract = payload.get("renderer_contract")

    assert_equal(payload.get("schema"), "docs_viewer_v2_custom_token_fixtures_v1", "schema")
    assert_equal(contract.get("markdown_library"), "markdown-it-py", "markdown library")
    assert_equal(contract.get("preset"), "commonmark", "preset")
    assert_equal(contract.get("enabled_rules"), ["table"], "enabled rules")
    assert_equal(contract.get("enabled_plugins"), [], "enabled plugins")
    assert_equal(contract.get("jekyll_kramdown_parity"), False, "jekyll parity")


def test_fixture_covers_required_custom_token_behaviors() -> None:
    payload = load_fixture()
    coverage = set()
    for case in case_by_id(payload).values():
        covers = case.get("covers")
        assert_true(isinstance(covers, list) and covers, f"{case['id']} must declare coverage")
        coverage.update(covers)

    missing = REQUIRED_COVERAGE - coverage
    assert_equal(sorted(missing), [], "missing coverage")


def test_fixture_expected_outputs_are_explicit() -> None:
    payload = load_fixture()
    for case in case_by_id(payload).values():
        assert_true(isinstance(case.get("source_markdown"), str), f"{case['id']} must include source markdown")
        if "expected_error" in case:
            assert_true(isinstance(case["expected_error"], str) and case["expected_error"], f"{case['id']} error")
            continue

        expected = case.get("expected")
        assert_true(isinstance(expected, dict), f"{case['id']} must include expected output")
        assert_true(
            any(key in expected for key in ("resolved_markdown", "html_contains", "plain_text", "warnings")),
            f"{case['id']} must include at least one observable expected output",
        )
        assert_true(isinstance(expected.get("warnings", []), list), f"{case['id']} warnings must be a list")


def main() -> None:
    test_fixture_declares_renderer_contract()
    test_fixture_covers_required_custom_token_behaviors()
    test_fixture_expected_outputs_are_explicit()
    print("Docs Viewer v2 custom-token fixture tests OK")


if __name__ == "__main__":
    main()
