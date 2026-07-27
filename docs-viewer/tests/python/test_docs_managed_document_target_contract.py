#!/usr/bin/env python3
"""Validate the Sub-Scope Document Editing explicit-target fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_PATH = (
    REPO_ROOT
    / "docs-viewer"
    / "tests"
    / "fixtures"
    / "docs_managed_document_targets_v1.json"
)
CASE_IDS = {
    "parent",
    "valid_sub_scope",
    "unlisted_subdoc",
    "unknown_sub_scope",
    "mismatched_front_matter_identity",
    "loading_detail",
    "failed_detail",
}
TARGET_KEYS = {"scope", "doc_id"}
SUB_SCOPE_TARGET_KEYS = {"scope", "sub_scope", "doc_id"}


def load_fixture() -> dict[str, Any]:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def assert_target_shape(target: Any, *, allow_none: bool = False) -> None:
    if allow_none and target is None:
        return
    assert isinstance(target, dict)
    keys = set(target)
    assert keys == TARGET_KEYS or keys == SUB_SCOPE_TARGET_KEYS
    assert all(isinstance(target[key], str) and target[key].strip() for key in keys)


def test_fixture_freezes_exact_target_shapes_and_cases() -> None:
    payload = load_fixture()

    assert set(payload) == {"schema", "target_shapes", "cases"}
    assert payload["schema"] == "docs_managed_document_targets_v1"
    assert set(payload["target_shapes"]) == {"parent", "sub_scope"}
    assert set(payload["target_shapes"]["parent"]) == TARGET_KEYS
    assert set(payload["target_shapes"]["sub_scope"]) == SUB_SCOPE_TARGET_KEYS
    assert {case["id"] for case in payload["cases"]} == CASE_IDS


def test_fixture_separates_shape_normalization_from_resolution_and_display_validation() -> None:
    payload = load_fixture()
    cases = {case["id"]: case for case in payload["cases"]}

    for case in cases.values():
        assert_target_shape(case["request_target"])
        expected = case["expected"]
        assert_target_shape(expected["normalized_target"])
        assert expected["normalized_target"] == case["request_target"]
        assert_target_shape(expected["validated_subdoc_target"], allow_none=True)
        assert_target_shape(expected["edit_target"], allow_none=True)
        assert_target_shape(expected["parent_source_target"])
        assert_target_shape(expected["subdoc_source_target"], allow_none=True)

    assert cases["unlisted_subdoc"]["expected"]["server_resolution"] == "unlisted_doc"
    assert cases["unknown_sub_scope"]["expected"]["server_resolution"] == "unknown_sub_scope"
    assert (
        cases["mismatched_front_matter_identity"]["expected"]["server_resolution"]
        == "mismatched_front_matter_identity"
    )
    assert cases["mismatched_front_matter_identity"]["expected"]["validated_subdoc_target"]
    assert cases["loading_detail"]["expected"]["validated_subdoc_target"] is None
    assert cases["failed_detail"]["expected"]["validated_subdoc_target"] is None


def test_fixture_keeps_parent_source_fixed_and_never_falls_back_for_invalid_detail() -> None:
    payload = load_fixture()
    cases = {case["id"]: case for case in payload["cases"]}
    parent_target = payload["target_shapes"]["parent"]

    for case in cases.values():
        assert case["expected"]["parent_source_target"] == parent_target

    for case_id in {
        "unlisted_subdoc",
        "unknown_sub_scope",
        "loading_detail",
        "failed_detail",
    }:
        assert cases[case_id]["expected"]["edit_target"] is None
        assert cases[case_id]["expected"]["subdoc_source_target"] is None
