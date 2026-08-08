#!/usr/bin/env python3
"""Focused checks for the private Working-owned Editorial lineage table."""

from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
if str(DOCS_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(DOCS_SERVICES_DIR))

import docs_document_publication_lineage as lineage  # noqa: E402


SOURCE_ID = "d-20260801-100000-aaaaaa"
SECOND_SOURCE_ID = "d-20260801-101000-bbbbbb"
EDITORIAL_ID = "d-20260802-110000-cccccc"
SECOND_EDITORIAL_ID = "d-20260802-120000-dddddd"


def empty_table() -> lineage.DocumentLineageTable:
    return lineage.empty_table(
        working_scope="dotlineform",
        working_sub_scope="projects",
        editorial_scope="analysis",
        editorial_sub_scope="works",
    )


def editorial(
    doc_id: str,
    *,
    published_url: str | None = None,
) -> lineage.DocumentEditorialChild:
    return lineage.DocumentEditorialChild(
        doc_id=doc_id,
        created_at="2026-08-08T10:00:00Z",
        last_copied_at="2026-08-08T10:00:00Z",
        published_url=published_url,
    )


def record(
    working_doc_id: str,
    *editorials: lineage.DocumentEditorialChild,
) -> lineage.DocumentLineageRecord:
    return lineage.DocumentLineageRecord(
        working_doc_id=working_doc_id,
        editorials=tuple(editorials),
    )


def test_empty_table_freezes_the_exact_v3_envelope(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"

    assert lineage.load_table(repo_root) is None
    assert json.loads(lineage.render_table(empty_table())) == {
        "schema_version": "docs_document_publication_lineage_v3",
        "working_collection": {
            "scope": "dotlineform",
            "sub_scope": "projects",
        },
        "editorial_collection": {
            "scope": "analysis",
            "sub_scope": "works",
        },
        "records": [],
    }

    written = lineage.write_table_atomic(repo_root, empty_table())
    assert lineage.load_table(repo_root) == written
    assert not hasattr(lineage, "lineage_id_for_copy")
    assert not hasattr(lineage, "load_rows")
    assert not hasattr(lineage, "write_rows_atomic")


def test_new_creates_ordered_children_and_replace_updates_one_exact_child(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = tmp_path / "repo"
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
                "target_doc_id": SECOND_EDITORIAL_ID,
                "action": "new",
            },
            {
                "source_doc_id": SOURCE_ID,
                "target_doc_id": EDITORIAL_ID,
                "action": "new",
            },
            {
                "source_doc_id": SECOND_SOURCE_ID,
                "target_doc_id": "d-20260802-130000-eeeeee",
                "action": "new",
            },
        ],
    )

    assert tuple(item.working_doc_id for item in created.records) == (
        SOURCE_ID,
        SECOND_SOURCE_ID,
    )
    assert tuple(item.doc_id for item in created.records[0].editorials) == (
        EDITORIAL_ID,
        SECOND_EDITORIAL_ID,
    )
    published = replace(
        created.records[0].editorials[0],
        published_url="/analysis/current",
    )
    seeded = replace(
        created,
        records=(
            replace(
                created.records[0],
                editorials=(published, created.records[0].editorials[1]),
            ),
            created.records[1],
        ),
    )
    lineage.write_table_atomic(repo_root, seeded)

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
    exact_child = replaced.records[0].editorials[0]
    assert exact_child.created_at == "2026-08-08T10:00:00Z"
    assert exact_child.last_copied_at == "2026-08-08T11:00:00Z"
    assert exact_child.published_url == "/analysis/current"


def test_editorials_for_working_requires_the_exact_configured_collections() -> None:
    table = replace(
        empty_table(),
        records=(record(SOURCE_ID, editorial(EDITORIAL_ID)),),
    )

    assert lineage.editorials_for_working(
        table,
        working_scope="dotlineform",
        working_sub_scope="projects",
        editorial_scope="analysis",
        editorial_sub_scope="works",
        working_doc_id=SOURCE_ID,
    ) == (editorial(EDITORIAL_ID),)
    assert lineage.editorials_for_working(
        table,
        working_scope="dotlineform",
        working_sub_scope="projects",
        editorial_scope="analysis",
        editorial_sub_scope="works",
        working_doc_id=SECOND_SOURCE_ID,
    ) == ()
    with pytest.raises(ValueError, match="collections do not match Copy"):
        lineage.editorials_for_working(
            table,
            working_scope="dotlineform",
            working_sub_scope="projects",
            editorial_scope="library",
            editorial_sub_scope="works",
            working_doc_id=SOURCE_ID,
        )


@pytest.mark.parametrize(
    ("payload", "error"),
    [
        (
            {"schema_version": "docs_document_publication_lineage_v2", "rows": []},
            "unknown fields",
        ),
        (
            {
                "schema_version": "docs_document_publication_lineage_v3",
                "working_collection": {
                    "scope": "dotlineform",
                    "sub_scope": "projects",
                },
                "editorial_collection": {
                    "scope": "analysis",
                    "sub_scope": "works",
                },
                "records": [
                    {"working_doc_id": SOURCE_ID, "editorials": []}
                ],
            },
            "at least one Editorial child",
        ),
        (
            {
                "schema_version": "docs_document_publication_lineage_v3",
                "working_collection": {
                    "scope": "dotlineform",
                    "sub_scope": "projects",
                },
                "editorial_collection": {
                    "scope": "analysis",
                    "sub_scope": "works",
                },
                "records": [
                    {
                        "working_doc_id": SOURCE_ID,
                        "editorials": [
                            editorial(EDITORIAL_ID).payload(),
                            editorial(EDITORIAL_ID).payload(),
                        ],
                    }
                ],
            },
            "Editorial doc_id is duplicated",
        ),
    ],
)
def test_table_rejects_v2_nullable_and_non_exact_shapes(
    tmp_path: Path,
    payload: dict[str, object],
    error: str,
) -> None:
    repo_root = tmp_path / "repo"
    path = lineage.table_path(repo_root)
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match=error):
        lineage.load_table(repo_root)


def test_table_rejects_duplicate_working_and_cross_record_editorial_ids() -> None:
    duplicate_working = replace(
        empty_table(),
        records=(
            record(SOURCE_ID, editorial(EDITORIAL_ID)),
            record(SOURCE_ID, editorial(SECOND_EDITORIAL_ID)),
        ),
    )
    with pytest.raises(ValueError, match="Working doc_id is duplicated"):
        lineage.render_table(duplicate_working)

    duplicate_editorial = replace(
        empty_table(),
        records=(
            record(SOURCE_ID, editorial(EDITORIAL_ID)),
            record(SECOND_SOURCE_ID, editorial(EDITORIAL_ID)),
        ),
    )
    with pytest.raises(ValueError, match="Editorial doc_id is duplicated"):
        lineage.render_table(duplicate_editorial)


def test_replace_requires_an_exact_current_editorial_child(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="exact current Editorial child"):
        lineage.apply_copy_results(
            tmp_path / "repo",
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


def test_reconcile_publications_updates_urls_on_current_children_only(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    table = replace(
        empty_table(),
        records=(
            record(
                SOURCE_ID,
                editorial(EDITORIAL_ID),
                editorial(SECOND_EDITORIAL_ID, published_url="/analysis/old"),
            ),
        ),
    )
    lineage.write_table_atomic(repo_root, table)

    reconciled = lineage.reconcile_publications(
        repo_root,
        editorial_scope="analysis",
        editorial_sub_scope="works",
        publication_urls={EDITORIAL_ID: "/analysis/current"},
    )

    assert reconciled is not None
    assert reconciled.records[0].editorials == (
        editorial(EDITORIAL_ID, published_url="/analysis/current"),
        editorial(SECOND_EDITORIAL_ID),
    )
