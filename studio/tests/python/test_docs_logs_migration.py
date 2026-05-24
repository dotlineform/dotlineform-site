#!/usr/bin/env python3
"""Focused checks for legacy docs-log migration parsing."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DOCS_LOGS_DIR = REPO_ROOT / "studio" / "workflows" / "change-requests" / "services" / "docs_logs"
if str(SCRIPTS_DOCS_LOGS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DOCS_LOGS_DIR))

import migrate_legacy_logs as migration  # noqa: E402


def test_parse_entries_splits_dated_h2_sections_with_line_ranges() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        (root / "_config.yml").write_text("title: test\n", encoding="utf-8")
        path = root / "studio/docs-viewer/source/studio" / "site-change-log.md"
        path.parent.mkdir(parents=True)
        path.write_text(
            "\n".join(
                [
                    "---",
                    "doc_id: site-change-log",
                    "---",
                    "# Site Change Log",
                    "",
                    "Intro.",
                    "",
                    "## [2026-05-19] First Entry",
                    "",
                    "**Status:** implemented",
                    "",
                    "## [2026-05-18] Second Entry",
                    "",
                    "**Status:** completed",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        entries = migration.parse_entries(path, root)

    assert [entry.title for entry in entries] == ["First Entry", "Second Entry"]
    assert entries[0].start_line == 8
    assert entries[0].end_line == 11
    assert entries[1].start_line == 12


def test_build_record_extracts_metadata_and_validates() -> None:
    entry = migration.LegacyEntry(
        source_file="studio/docs-viewer/source/studio/site-change-log.md",
        start_line=20,
        end_line=42,
        date="2026-05-19",
        title="Added Targeted Docs Payload Rebuilds",
        body=(
            "**Status:** implemented\n\n"
            "**Area:** Docs Viewer builder / management\n\n"
            "**Summary:**\n"
            "`./scripts/build_docs.rb --scope <scope> --write --only-doc-ids <ids>` now supports targeted same-scope docs payload rebuilds.\n\n"
            "**Effect:**\n"
            "Small docs source writes can avoid rendering every per-doc payload.\n\n"
            "**Affected files/docs:**\n\n"
            "- `studio/docs-viewer/build/build_docs.rb`\n"
            "- `studio/docs-viewer/services/docs_write_rebuild.py`\n"
            "- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)\n"
            "- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)\n"
            "- [Targeted Docs Build Request](/docs/?scope=studio&doc=site-request-docs-build-incremental)\n"
        ),
    )

    record, warnings = migration.build_record(entry)

    assert warnings == []
    assert record["id"] == "change-2026-05-19-added-targeted-docs-payload-rebuilds"
    assert record["status"] == "implemented"
    assert record["type"] == "implementation"
    assert "docs-viewer" in record["domains"]
    assert "build" in record["domains"]
    assert record["related_files"] == ["studio/docs-viewer/build/build_docs.rb", "studio/docs-viewer/services/docs_write_rebuild.py"]
    assert record["related_docs"] == [
        "scripts-docs-builder",
        "scripts-docs-management-server",
        "site-request-docs-build-incremental",
    ]
    assert record["change_request_doc_id"] == "site-request-docs-build-incremental"
    assert record["source"] == {"file": "studio/docs-viewer/source/studio/site-change-log.md", "line": 20, "archive": "current"}


def test_build_records_suffixes_duplicate_generated_ids() -> None:
    entries = [
        migration.LegacyEntry("studio/docs-viewer/source/studio/site-change-log.md", 10, 20, "2026-05-19", "Repeated Title", "**Status:** implemented\n\nBody."),
        migration.LegacyEntry("studio/docs-viewer/source/studio/site-change-log.md", 30, 40, "2026-05-19", "Repeated Title", "**Status:** implemented\n\nBody."),
    ]

    records = migration.build_records(entries)

    assert records[0]["id"] == "change-2026-05-19-repeated-title"
    assert records[1]["id"] == "change-2026-05-19-repeated-title-2"
    assert "duplicate generated id; numeric suffix added" in records[1]["migration"]["warnings"]


def test_write_entry_records_creates_per_entry_json_and_refuses_existing_output() -> None:
    records = [
        {
            "id": "change-2026-05-19-one",
            "date": "2026-05-19",
            "title": "One",
            "status": "implemented",
            "type": "implementation",
            "domains": ["site"],
            "summary": "One.",
            "source": {"file": "studio/docs-viewer/source/studio/site-change-log.md"},
        },
        {
            "id": "change-2026-04-30-two",
            "date": "2026-04-30",
            "title": "Two",
            "status": "implemented",
            "type": "implementation",
            "domains": ["search"],
            "summary": "Two.",
            "source": {"file": "studio/docs-viewer/source/studio/search-change-log.md"},
        },
    ]

    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        (root / "_config.yml").write_text("title: test\n", encoding="utf-8")
        written = migration.write_entry_records(root, records)
        try:
            migration.write_entry_records(root, records)
        except FileExistsError as exc:
            error = str(exc)
        else:
            error = ""

        may = root / "studio/workflows/change-requests" / "logs" / "entries" / "change-2026-05-19-one.json"
        april = root / "studio/workflows/change-requests" / "logs" / "entries" / "change-2026-04-30-two.json"
        assert written == [
            "studio/workflows/change-requests/logs/entries/change-2026-04-30-two.json",
            "studio/workflows/change-requests/logs/entries/change-2026-05-19-one.json",
        ]
        assert may.exists()
        assert april.exists()
        assert "already exists" in error


def test_write_entry_records_rejects_duplicate_ids() -> None:
    records = [
        {
            "id": "change-2026-05-19-one",
            "date": "2026-05-19",
            "title": "One",
            "status": "implemented",
            "type": "implementation",
            "domains": ["site"],
            "summary": "One.",
            "source": {"file": "studio/docs-viewer/source/studio/site-change-log.md"},
        },
        {
            "id": "change-2026-05-19-one",
            "date": "2026-05-19",
            "title": "One Copy",
            "status": "implemented",
            "type": "implementation",
            "domains": ["site"],
            "summary": "One copy.",
            "source": {"file": "studio/docs-viewer/source/studio/site-change-log.md"},
        },
    ]

    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        (root / "_config.yml").write_text("title: test\n", encoding="utf-8")
        try:
            migration.write_entry_records(root, records)
        except ValueError as exc:
            error = str(exc)
        else:
            error = ""

    assert "duplicate generated ids" in error
