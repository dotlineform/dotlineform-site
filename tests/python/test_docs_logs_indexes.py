#!/usr/bin/env python3
"""Focused checks for generated docs-log indexes."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DOCS_LOGS_DIR = REPO_ROOT / "scripts" / "docs_logs"
if str(SCRIPTS_DOCS_LOGS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DOCS_LOGS_DIR))

import build_indexes  # noqa: E402


def sample_record(entry_id: str, change_date: str, title: str, domain: str) -> dict[str, object]:
    return {
        "id": entry_id,
        "date": change_date,
        "title": title,
        "status": "implemented",
        "type": "implementation",
        "domains": [domain],
        "subjects": ["payloads"],
        "related_docs": ["scripts-docs-builder"],
        "related_files": ["scripts/docs/build_docs.rb"],
        "change_request_doc_id": "site-request-docs-build-incremental",
        "summary": f"{title} summary.",
        "effect": f"{title} effect.",
        "source": {"file": "_docs/site-change-log.md", "line": 20},
    }


def test_build_outputs_groups_entries_by_required_indexes() -> None:
    records = [
        sample_record("change-2026-05-19-one", "2026-05-19", "One", "docs-viewer"),
        sample_record("change-2026-04-30-two", "2026-04-30", "Two", "search"),
    ]

    outputs = build_indexes.build_outputs(records)

    assert outputs["by_date"]["years"][0]["year"] == "2026"
    assert outputs["by_date"]["years"][0]["months"][0]["month"] == "2026-05"
    assert outputs["by_domain"]["domains"]["docs-viewer"][0]["id"] == "change-2026-05-19-one"
    assert outputs["by_related_doc"]["related_docs"]["scripts-docs-builder"][0]["id"] == "change-2026-05-19-one"
    assert outputs["by_related_file"]["related_files"]["scripts/docs/build_docs.rb"][1]["id"] == "change-2026-04-30-two"
    assert outputs["by_change_request"]["change_requests"]["site-request-docs-build-incremental"][0]["id"] == "change-2026-05-19-one"
    assert outputs["search_index"]["entries"][0]["search_text"]["trace"].count("scripts-docs-builder") == 1


def test_read_jsonl_entries_validates_and_sorts_records() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        (root / "_config.yml").write_text("title: test\n", encoding="utf-8")
        entries_path = root / "_docs_logs" / "entries" / "2026-05.jsonl"
        entries_path.parent.mkdir(parents=True)
        records = [
            sample_record("change-2026-05-18-two", "2026-05-18", "Two", "search"),
            sample_record("change-2026-05-19-one", "2026-05-19", "One", "docs-viewer"),
        ]
        entries_path.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")

        loaded = build_indexes.read_jsonl_entries(root)

    assert [record["id"] for record in loaded] == ["change-2026-05-19-one", "change-2026-05-18-two"]


def test_write_outputs_creates_expected_generated_files() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        (root / "_config.yml").write_text("title: test\n", encoding="utf-8")
        outputs = build_indexes.build_outputs([sample_record("change-2026-05-19-one", "2026-05-19", "One", "docs-viewer")])
        written = build_indexes.write_outputs(root, outputs)

        assert written == [
            "_docs_logs/generated/by-date.json",
            "_docs_logs/generated/by-domain.json",
            "_docs_logs/generated/by-related-doc.json",
            "_docs_logs/generated/by-related-file.json",
            "_docs_logs/generated/by-change-request.json",
            "_docs_logs/generated/search-index.json",
        ]
        assert (root / "_docs_logs" / "generated" / "search-index.json").exists()
