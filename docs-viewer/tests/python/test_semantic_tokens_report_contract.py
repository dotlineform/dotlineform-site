"""Focused configuration and public-boundary checks for the Semantic Tokens report."""

from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_manage_registry_declares_semantic_tokens_report() -> None:
    payload = read_json(REPO_ROOT / "docs-viewer/config/reports/reports.json")
    records = {
        str(record.get("report_id") or ""): record
        for record in payload["reports"]
        if isinstance(record, dict)
    }

    assert records["semantic_tokens"] == {
        "report_id": "semantic_tokens",
        "title": "Semantic Tokens",
        "description": "Lists resolved semantic-token occurrences for a selected docs scope.",
        "default_access": "local",
        "loader_id": "semantic_tokens",
        "presets": [],
    }


def test_public_registry_does_not_expose_semantic_tokens_report() -> None:
    payload = read_json(REPO_ROOT / "site/assets/data/docs/public-reports.json")
    report_ids = {
        str(record.get("report_id") or "")
        for record in payload["reports"]
        if isinstance(record, dict)
    }

    assert "semantic_tokens" not in report_ids


def test_manage_loader_owns_semantic_tokens_module() -> None:
    loader_source = (
        REPO_ROOT / "docs-viewer/runtime/js/reports/docs-viewer-reports.js"
    ).read_text(encoding="utf-8")

    assert 'import("./semantic-tokens-report.js")' in loader_source
    assert (
        REPO_ROOT / "docs-viewer/runtime/js/reports/semantic-tokens-report.js"
    ).is_file()
