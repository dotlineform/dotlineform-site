#!/usr/bin/env python3
"""Verify generated catalogue write-decision helpers."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from catalogue import catalogue_generation_writes as writes  # noqa: E402


def test_route_stub_content_is_metadata_free() -> None:
    assert writes.build_route_stub_content() == "---\n---\n"


def test_route_stub_skips_existing_route_without_force() -> None:
    decision = writes.decide_route_stub_write(path_exists=True, force=False)

    assert decision.should_write is False
    assert decision.overwrite is True
    assert decision.skip_reason == writes.ROUTE_EXISTS


def test_route_stub_force_overwrites_existing_route() -> None:
    decision = writes.decide_route_stub_write(path_exists=True, force=True)

    assert decision.should_write is True
    assert decision.overwrite is True
    assert decision.skip_reason is None


def test_json_header_scalar_extraction_is_tolerant() -> None:
    assert writes.extract_header_scalar_from_json_text('{"header": {"version": "abc"}}', "version") == "abc"
    assert writes.extract_header_scalar_from_json_text('{"header": {"version": 123}}', "version") == "123"
    assert writes.extract_header_scalar_from_json_text('{"header": {"version": ""}}', "version") is None
    assert writes.extract_header_scalar_from_json_text("not json", "version") is None


def test_json_version_match_skips_without_force() -> None:
    decision = writes.decide_json_payload_write(
        path_exists=True,
        existing_version="abc",
        payload_version="abc",
        force=False,
    )

    assert decision.should_write is False
    assert decision.overwrite is True
    assert decision.skip_reason == writes.VERSION_MATCH
    assert decision.existing_version == "abc"
    assert decision.payload_version == "abc"


def test_json_force_overwrites_version_match() -> None:
    decision = writes.decide_json_payload_write(
        path_exists=True,
        existing_version="abc",
        payload_version="abc",
        force=True,
    )

    assert decision.should_write is True
    assert decision.overwrite is True
    assert decision.skip_reason is None


def test_json_dry_run_decision_does_not_write_files(tmp_path: Path) -> None:
    target = tmp_path / "payload.json"

    decision = writes.decide_json_payload_write(
        path_exists=target.exists(),
        existing_version=None,
        payload_version="new",
        force=False,
    )

    assert decision.should_write is True
    assert decision.overwrite is False
    assert not target.exists()
