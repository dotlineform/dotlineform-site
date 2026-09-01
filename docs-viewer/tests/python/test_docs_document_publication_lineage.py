#!/usr/bin/env python3
"""Focused checks for the private Working-owned Editorial lineage table."""

from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from repo_factory import docs_scope_record, docs_sub_scope_record, write_docs_scope_config


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
if str(DOCS_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(DOCS_SERVICES_DIR))

import docs_document_publication_lineage as lineage  # noqa: E402


SOURCE_ID = "d-20260801-100000-aaaaaa"
SECOND_SOURCE_ID = "d-20260801-101000-bbbbbb"
EDITORIAL_ID = "d-20260802-110000-cccccc"
SECOND_EDITORIAL_ID = "d-20260802-120000-dddddd"
PROJECTS_CONTRACT = "dotlineform_projects_to_analysis_works"
PROCESSING_CONTRACT = "dotlineform_processing_to_analysis_works"


@pytest.fixture(autouse=True)
def configured_lineage_authority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    projects_base = tmp_path / "projects"
    (projects_base / "docs-viewer").mkdir(parents=True)
    monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(projects_base))
    write_docs_scope_config(
        tmp_path / "repo",
        [
            docs_scope_record(
                "dotlineform",
                scope_root_provider="external_local",
                sub_scopes=[
                    docs_sub_scope_record(
                        "dotlineform",
                        "projects",
                        sub_scope_customisation={
                            "id": "dotlineform_projects",
                            "settings": {},
                        },
                    ),
                    docs_sub_scope_record(
                        "dotlineform",
                        "processing",
                        sub_scope_customisation={
                            "id": "dotlineform_processing",
                            "settings": {},
                        },
                    ),
                ],
            ),
            docs_scope_record(
                "analysis",
                scope_type="public",
                scope_root_provider="external_local",
                viewer_base_url="/analysis/",
                include_scope_param=False,
                sub_scopes=[
                    docs_sub_scope_record(
                        "analysis",
                        "works",
                        scope_type="public",
                        sub_scope_customisation={
                            "id": "analysis_works",
                            "settings": {},
                        },
                    )
                ],
            ),
        ],
    )


def empty_table() -> lineage.DocumentLineageTable:
    return lineage.empty_table(
        working_scope="dotlineform",
        working_sub_scope="projects",
        editorial_scope="analysis",
        editorial_sub_scope="works",
    )


def processing_empty_table() -> lineage.DocumentLineageTable:
    return lineage.empty_table(
        working_scope="dotlineform",
        working_sub_scope="processing",
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

    assert lineage.load_table(repo_root, contract_id=PROJECTS_CONTRACT) is None
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

    written = lineage.write_table_atomic(
        repo_root,
        empty_table(),
        contract_id=PROJECTS_CONTRACT,
    )
    assert lineage.load_table(repo_root, contract_id=PROJECTS_CONTRACT) == written
    assert not hasattr(lineage, "lineage_id_for_copy")
    assert not hasattr(lineage, "load_rows")
    assert not hasattr(lineage, "write_rows_atomic")
    assert lineage.table_path(repo_root, contract_id=PROJECTS_CONTRACT) == (
        tmp_path
        / "projects/docs-viewer/scopes/dotlineform/source/sub-scopes/projects/data/document-publication-lineage.json"
    )


def test_repository_canonical_path_is_not_a_fallback(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    old_path = repo_root / "docs-viewer/data/canonical/document-publication-lineage.json"
    old_path.parent.mkdir(parents=True, exist_ok=True)
    old_path.write_bytes(lineage.render_table(empty_table()))

    assert lineage.load_table(repo_root, contract_id=PROJECTS_CONTRACT) is None


def test_workflow_discovery_keeps_independent_working_owned_paths(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"

    workflows = lineage.configured_workflows(repo_root)

    assert [workflow.contract_id for workflow in workflows] == [
        PROCESSING_CONTRACT,
        PROJECTS_CONTRACT,
    ]
    assert lineage.table_path(repo_root, contract_id=PROJECTS_CONTRACT) == (
        tmp_path
        / "projects/docs-viewer/scopes/dotlineform/source/sub-scopes/projects/data/document-publication-lineage.json"
    )
    assert lineage.table_path(repo_root, contract_id=PROCESSING_CONTRACT) == (
        tmp_path
        / "projects/docs-viewer/scopes/dotlineform/source/sub-scopes/processing/data/document-publication-lineage.json"
    )
    assert not lineage.table_path(
        repo_root,
        contract_id=PROCESSING_CONTRACT,
    ).exists()


def test_processing_copy_creates_only_its_exact_table(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = tmp_path / "repo"
    monkeypatch.setattr(lineage, "current_timestamp", lambda: "2026-09-01T12:00:00Z")

    table = lineage.apply_copy_results(
        repo_root,
        contract_id=PROCESSING_CONTRACT,
        source_scope="dotlineform",
        source_sub_scope="processing",
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

    assert table.working_collection.sub_scope == "processing"
    assert lineage.load_table(repo_root, contract_id=PROJECTS_CONTRACT) is None
    assert lineage.load_table(repo_root, contract_id=PROCESSING_CONTRACT) == table


def test_cross_table_editorial_ownership_is_rejected(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    projects = replace(
        empty_table(),
        records=(record(SOURCE_ID, editorial(EDITORIAL_ID)),),
    )
    processing = replace(
        processing_empty_table(),
        records=(record(SECOND_SOURCE_ID, editorial(EDITORIAL_ID)),),
    )
    lineage.write_table_atomic(
        repo_root,
        projects,
        contract_id=PROJECTS_CONTRACT,
    )

    with pytest.raises(ValueError, match="cross-table ownership"):
        lineage.write_table_atomic(
            repo_root,
            processing,
            contract_id=PROCESSING_CONTRACT,
        )
    assert not lineage.table_path(
        repo_root,
        contract_id=PROCESSING_CONTRACT,
    ).exists()


def test_workflow_discovery_rejects_incomplete_and_duplicate_roles(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    analysis = docs_scope_record(
        "analysis",
        scope_type="public",
        viewer_base_url="/analysis/",
        include_scope_param=False,
        sub_scopes=[
            docs_sub_scope_record(
                "analysis",
                "works",
                scope_type="public",
                sub_scope_customisation={
                    "id": "analysis_works",
                    "settings": {},
                },
            )
        ],
    )
    projects = docs_sub_scope_record(
        "dotlineform",
        "projects",
        sub_scope_customisation={
            "id": "dotlineform_projects",
            "settings": {},
        },
    )
    write_docs_scope_config(
        repo_root,
        [docs_scope_record("dotlineform", sub_scopes=[projects]), analysis],
    )
    with pytest.raises(ValueError, match=PROCESSING_CONTRACT):
        lineage.configured_workflows(repo_root)

    processing = docs_sub_scope_record(
        "dotlineform",
        "processing",
        sub_scope_customisation={
            "id": "dotlineform_processing",
            "settings": {},
        },
    )
    duplicate_projects = docs_sub_scope_record(
        "dotlineform",
        "project_archive",
        sub_scope_customisation={
            "id": "dotlineform_projects",
            "settings": {},
        },
    )
    write_docs_scope_config(
        repo_root,
        [
            docs_scope_record(
                "dotlineform",
                sub_scopes=[projects, duplicate_projects, processing],
            ),
            analysis,
        ],
    )
    with pytest.raises(ValueError, match=PROJECTS_CONTRACT):
        lineage.configured_workflows(repo_root)


def test_new_creates_ordered_children_and_replace_updates_one_exact_child(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = tmp_path / "repo"
    monkeypatch.setattr(lineage, "current_timestamp", lambda: "2026-08-08T10:00:00Z")

    created = lineage.apply_copy_results(
        repo_root,
        contract_id=PROJECTS_CONTRACT,
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
    lineage.write_table_atomic(
        repo_root,
        seeded,
        contract_id=PROJECTS_CONTRACT,
    )

    monkeypatch.setattr(lineage, "current_timestamp", lambda: "2026-08-08T11:00:00Z")
    replaced = lineage.apply_copy_results(
        repo_root,
        contract_id=PROJECTS_CONTRACT,
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
            editorial_scope="example",
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
    path = lineage.table_path(repo_root, contract_id=PROJECTS_CONTRACT)
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match=error):
        lineage.load_table(repo_root, contract_id=PROJECTS_CONTRACT)


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
            contract_id=PROJECTS_CONTRACT,
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


def test_editorial_delete_removes_exact_children_and_empty_records(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    third_editorial_id = "d-20260802-130000-eeeeee"
    table = replace(
        empty_table(),
        records=(
            record(
                SOURCE_ID,
                editorial(EDITORIAL_ID),
                editorial(SECOND_EDITORIAL_ID),
            ),
            record(SECOND_SOURCE_ID, editorial(third_editorial_id)),
        ),
    )
    lineage.write_table_atomic(
        repo_root,
        table,
        contract_id=PROJECTS_CONTRACT,
    )

    result = lineage.apply_document_deletes(
        repo_root,
        scope="analysis",
        sub_scope="works",
        doc_ids=[SECOND_EDITORIAL_ID, third_editorial_id],
    )

    assert result.role == "editorial"
    assert result.changed
    assert result.workflows[0].affected_working_doc_ids == (
        SOURCE_ID,
        SECOND_SOURCE_ID,
    )
    assert len(result.workflows) == 1
    assert result.workflows[0].table.records == (
        record(SOURCE_ID, editorial(EDITORIAL_ID)),
    )
    assert lineage.load_table(
        repo_root,
        contract_id=PROJECTS_CONTRACT,
    ) == result.workflows[0].table


def test_working_delete_removes_the_record_and_unrelated_delete_is_neutral(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    table = replace(
        empty_table(),
        records=(record(SOURCE_ID, editorial(EDITORIAL_ID)),),
    )
    lineage.write_table_atomic(
        repo_root,
        table,
        contract_id=PROJECTS_CONTRACT,
    )
    before = lineage.table_path(
        repo_root,
        contract_id=PROJECTS_CONTRACT,
    ).read_bytes()

    unrelated = lineage.apply_document_deletes(
        repo_root,
        scope="example",
        sub_scope="works",
        doc_ids=[EDITORIAL_ID],
    )
    assert unrelated.role == ""
    assert not unrelated.changed
    assert lineage.table_path(repo_root, contract_id=PROJECTS_CONTRACT).read_bytes() == before

    direct_editorial = lineage.apply_document_deletes(
        repo_root,
        scope="analysis",
        sub_scope="works",
        doc_ids=["d-20260802-140000-ffffff"],
    )
    assert direct_editorial.role == "editorial"
    assert not direct_editorial.changed
    assert lineage.table_path(repo_root, contract_id=PROJECTS_CONTRACT).read_bytes() == before

    deleted = lineage.apply_document_deletes(
        repo_root,
        scope="dotlineform",
        sub_scope="projects",
        doc_ids=[SOURCE_ID],
    )
    assert deleted.role == "working"
    assert deleted.workflows[0].affected_working_doc_ids == (SOURCE_ID,)
    assert deleted.workflows[0].table.records == ()


def test_shared_editorial_delete_updates_only_the_owning_workflow(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    projects = replace(
        empty_table(),
        records=(record(SOURCE_ID, editorial(EDITORIAL_ID)),),
    )
    processing = replace(
        processing_empty_table(),
        records=(record(SECOND_SOURCE_ID, editorial(SECOND_EDITORIAL_ID)),),
    )
    lineage.write_table_atomic(
        repo_root,
        projects,
        contract_id=PROJECTS_CONTRACT,
    )
    lineage.write_table_atomic(
        repo_root,
        processing,
        contract_id=PROCESSING_CONTRACT,
    )
    projects_before = lineage.table_path(
        repo_root,
        contract_id=PROJECTS_CONTRACT,
    ).read_bytes()

    result = lineage.apply_document_deletes(
        repo_root,
        scope="analysis",
        sub_scope="works",
        doc_ids=[SECOND_EDITORIAL_ID],
    )

    by_contract = {change.contract_id: change for change in result.workflows}
    assert by_contract[PROJECTS_CONTRACT].affected_working_doc_ids == ()
    assert by_contract[PROCESSING_CONTRACT].affected_working_doc_ids == (
        SECOND_SOURCE_ID,
    )
    assert by_contract[PROCESSING_CONTRACT].table.records == ()
    assert lineage.table_path(
        repo_root,
        contract_id=PROJECTS_CONTRACT,
    ).read_bytes() == projects_before
