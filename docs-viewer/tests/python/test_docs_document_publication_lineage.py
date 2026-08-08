#!/usr/bin/env python3
"""Focused checks for the private document-publication lineage table."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
if str(DOCS_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(DOCS_SERVICES_DIR))

import docs_document_publication_lineage as lineage  # noqa: E402


SOURCE_ID = "d-20260801-100000-aaaaaa"
EDITORIAL_ID = "d-20260802-110000-bbbbbb"


def identity(scope: str, sub_scope: str, doc_id: str) -> lineage.DocumentLineageIdentity:
    return lineage.DocumentLineageIdentity(
        scope=scope,
        sub_scope=sub_scope,
        doc_id=doc_id,
    )


def test_new_then_replace_updates_one_exact_row(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = tmp_path / "repo"
    assert lineage.load_rows(repo_root) == ()
    assert json.loads(lineage.render_table(())) == {
        "schema_version": lineage.LINEAGE_SCHEMA_VERSION,
        "rows": [],
    }

    monkeypatch.setattr(lineage, "current_timestamp", lambda: "2026-08-08T10:00:00Z")
    created = lineage.apply_copy_results(
        repo_root,
        source_scope="dotlineform",
        source_sub_scope="projects",
        editorial_scope="analysis",
        editorial_sub_scope="works",
        results=[
            {
                "source_doc_id": SOURCE_ID,
                "target_doc_id": EDITORIAL_ID,
                "action": "new",
            }
        ],
    )
    row = created[0]
    assert row.source == identity("dotlineform", "projects", SOURCE_ID)
    assert row.editorial == identity("analysis", "works", EDITORIAL_ID)
    assert row.created_at == "2026-08-08T10:00:00Z"
    assert row.last_copied_at == row.created_at
    assert row.publication is None

    monkeypatch.setattr(lineage, "current_timestamp", lambda: "2026-08-08T11:00:00Z")
    replaced = lineage.apply_copy_results(
        repo_root,
        source_scope="dotlineform",
        source_sub_scope="projects",
        editorial_scope="analysis",
        editorial_sub_scope="works",
        results=[
            {
                "source_doc_id": SOURCE_ID,
                "target_doc_id": EDITORIAL_ID,
                "action": "replace",
            }
        ],
    )
    assert replaced[0].created_at == "2026-08-08T10:00:00Z"
    assert replaced[0].last_copied_at == "2026-08-08T11:00:00Z"


def test_table_requires_its_basic_schema_and_exact_replace_row(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    path = lineage.table_path(repo_root)
    path.parent.mkdir(parents=True)
    path.write_text('{"schema_version":"wrong","rows":[]}', encoding="utf-8")
    with pytest.raises(ValueError, match="schema_version"):
        lineage.load_rows(repo_root)

    path.write_bytes(lineage.render_table(()))
    with pytest.raises(ValueError, match="exact current lineage row"):
        lineage.apply_copy_results(
            repo_root,
            source_scope="dotlineform",
            source_sub_scope="projects",
            editorial_scope="analysis",
            editorial_sub_scope="works",
            results=[
                {
                    "source_doc_id": SOURCE_ID,
                    "target_doc_id": EDITORIAL_ID,
                    "action": "replace",
                }
            ],
        )
