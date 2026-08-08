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


def branch_id(character: str) -> str:
    return f"sha256:{character * 64}"


def test_lineage_id_is_sha256_of_the_canonical_initial_copy_pair() -> None:
    assert lineage.lineage_id_for_copy(
        identity("dotlineform", "projects", SOURCE_ID),
        identity("analysis", "works", EDITORIAL_ID),
    ) == (
        "sha256:5b3f7cbe35d9ed4598f857f97e286c05"
        "e1e183b8380345f59bec164d209d8a98"
    )


def test_new_then_replace_updates_one_exact_branch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = tmp_path / "repo"
    assert lineage.load_rows(repo_root) == ()
    assert json.loads(lineage.render_table(())) == {
        "schema_version": "docs_document_publication_lineage_v2",
        "rows": [],
    }

    working = identity("dotlineform", "projects", SOURCE_ID)
    editorial = identity("analysis", "works", EDITORIAL_ID)
    expected_lineage_id = lineage.lineage_id_for_copy(working, editorial)

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
    assert row.lineage_id == expected_lineage_id
    assert row.working == working
    assert row.editorial == editorial
    assert row.created_at == "2026-08-08T10:00:00Z"
    assert row.last_copied_at == row.created_at
    assert row.published is None

    lineage.write_rows_atomic(
        repo_root,
        (replace_published(row, "/analysis/current"),),
    )
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
    assert replaced[0].lineage_id == expected_lineage_id
    assert replaced[0].created_at == "2026-08-08T10:00:00Z"
    assert replaced[0].last_copied_at == "2026-08-08T11:00:00Z"
    assert replaced[0].published == lineage.DocumentPublishedState(
        public_url="/analysis/current"
    )


def replace_published(
    row: lineage.DocumentLineageRow,
    public_url: str,
) -> lineage.DocumentLineageRow:
    return lineage.DocumentLineageRow(
        lineage_id=row.lineage_id,
        working=row.working,
        editorial=row.editorial,
        created_at=row.created_at,
        last_copied_at=row.last_copied_at,
        published=lineage.DocumentPublishedState(public_url=public_url),
    )


def test_optional_states_round_trip_and_sort_by_stable_branch_id(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    working = identity("dotlineform", "projects", SOURCE_ID)
    editorial = identity("analysis", "works", EDITORIAL_ID)
    rows = (
        lineage.DocumentLineageRow(
            lineage_id=branch_id("c"),
            working=None,
            editorial=None,
            created_at="2026-08-08T10:00:00Z",
            last_copied_at="2026-08-08T10:00:00Z",
            published=lineage.DocumentPublishedState(public_url="/analysis/published"),
        ),
        lineage.DocumentLineageRow(
            lineage_id=branch_id("a"),
            working=working,
            editorial=None,
            created_at="2026-08-08T10:00:00Z",
            last_copied_at="2026-08-08T10:00:00Z",
            published=None,
        ),
        lineage.DocumentLineageRow(
            lineage_id=branch_id("b"),
            working=None,
            editorial=editorial,
            created_at="2026-08-08T10:00:00Z",
            last_copied_at="2026-08-08T10:00:00Z",
            published=None,
        ),
    )

    written = lineage.write_rows_atomic(repo_root, rows)

    assert tuple(row.lineage_id for row in written) == (
        branch_id("a"),
        branch_id("b"),
        branch_id("c"),
    )
    assert lineage.load_rows(repo_root) == written
    payload = json.loads(lineage.table_path(repo_root).read_text(encoding="utf-8"))
    assert payload["rows"][0] == {
        "lineage_id": branch_id("a"),
        "working": working.payload(),
        "editorial": None,
        "created_at": "2026-08-08T10:00:00Z",
        "last_copied_at": "2026-08-08T10:00:00Z",
        "published": None,
    }


def test_table_rejects_v1_empty_duplicate_and_invalid_branches(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    path = lineage.table_path(repo_root)
    path.parent.mkdir(parents=True)
    path.write_text(
        '{"schema_version":"docs_document_publication_lineage_v1","rows":[]}',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="schema_version"):
        lineage.load_rows(repo_root)

    empty = lineage.DocumentLineageRow(
        lineage_id=branch_id("a"),
        working=None,
        editorial=None,
        created_at="2026-08-08T10:00:00Z",
        last_copied_at="2026-08-08T10:00:00Z",
        published=None,
    )
    with pytest.raises(ValueError, match="at least one lineage state"):
        lineage.render_table((empty,))

    valid = lineage.DocumentLineageRow(
        lineage_id=branch_id("b"),
        working=identity("dotlineform", "projects", SOURCE_ID),
        editorial=None,
        created_at="2026-08-08T10:00:00Z",
        last_copied_at="2026-08-08T10:00:00Z",
        published=None,
    )
    with pytest.raises(ValueError, match="duplicated"):
        lineage.render_table((valid, valid))

    invalid = lineage.DocumentLineageRow(
        lineage_id="branch-1",
        working=valid.working,
        editorial=None,
        created_at=valid.created_at,
        last_copied_at=valid.last_copied_at,
        published=None,
    )
    with pytest.raises(ValueError, match="lineage_id is invalid"):
        lineage.render_table((invalid,))


def test_replace_requires_exact_current_states(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    working = identity("dotlineform", "projects", SOURCE_ID)
    editorial = identity("analysis", "works", EDITORIAL_ID)
    lineage.write_rows_atomic(
        repo_root,
        (
            lineage.DocumentLineageRow(
                lineage_id=lineage.lineage_id_for_copy(working, editorial),
                working=working,
                editorial=None,
                created_at="2026-08-08T10:00:00Z",
                last_copied_at="2026-08-08T10:00:00Z",
                published=None,
            ),
        ),
    )

    with pytest.raises(ValueError, match="exact current lineage branch"):
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


def test_reconcile_publications_changes_only_rows_with_current_editorial(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    working = identity("dotlineform", "projects", SOURCE_ID)
    published_editorial = identity("analysis", "works", EDITORIAL_ID)
    removed_editorial = identity(
        "analysis",
        "works",
        "d-20260802-120000-cccccc",
    )
    other_editorial = identity(
        "library",
        "works",
        "d-20260802-130000-dddddd",
    )
    published_only = lineage.DocumentLineageRow(
        lineage_id=branch_id("d"),
        working=None,
        editorial=None,
        created_at="2026-08-08T10:00:00Z",
        last_copied_at="2026-08-08T10:00:00Z",
        published=lineage.DocumentPublishedState(public_url="/analysis/retained"),
    )
    rows = (
        lineage.DocumentLineageRow(
            lineage_id=lineage.lineage_id_for_copy(working, published_editorial),
            working=working,
            editorial=published_editorial,
            created_at="2026-08-08T10:00:00Z",
            last_copied_at="2026-08-08T10:00:00Z",
            published=None,
        ),
        lineage.DocumentLineageRow(
            lineage_id=lineage.lineage_id_for_copy(working, removed_editorial),
            working=working,
            editorial=removed_editorial,
            created_at="2026-08-08T10:00:00Z",
            last_copied_at="2026-08-08T10:00:00Z",
            published=lineage.DocumentPublishedState(public_url="/analysis/old"),
        ),
        lineage.DocumentLineageRow(
            lineage_id=lineage.lineage_id_for_copy(working, other_editorial),
            working=working,
            editorial=other_editorial,
            created_at="2026-08-08T10:00:00Z",
            last_copied_at="2026-08-08T10:00:00Z",
            published=lineage.DocumentPublishedState(public_url="/library/current"),
        ),
        published_only,
    )
    lineage.write_rows_atomic(repo_root, rows)

    reconciled = lineage.reconcile_publications(
        repo_root,
        editorial_collections={("analysis", "works")},
        publication_urls={
            published_editorial: "/analysis/?doc=report&subdoc=" + EDITORIAL_ID,
        },
    )
    by_id = {row.lineage_id: row for row in reconciled}

    assert by_id[lineage.lineage_id_for_copy(working, published_editorial)].published == (
        lineage.DocumentPublishedState(
            public_url="/analysis/?doc=report&subdoc=" + EDITORIAL_ID
        )
    )
    assert by_id[lineage.lineage_id_for_copy(working, removed_editorial)].published is None
    assert by_id[lineage.lineage_id_for_copy(working, other_editorial)].published == (
        lineage.DocumentPublishedState(public_url="/library/current")
    )
    assert by_id[published_only.lineage_id] == published_only
