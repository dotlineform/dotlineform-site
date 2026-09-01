#!/usr/bin/env python3
"""Focused Processing Working collection customisation tests."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))

import docs_dotlineform_processing_customisation as processing  # noqa: E402
import docs_document_publication_lineage as publication_lineage  # noqa: E402
from repo_factory import (  # noqa: E402
    docs_scope_record,
    docs_sub_scope_record,
    write_docs_scope_config,
)


DOC_ID = "d-20260901-100000-000001"


@dataclass(frozen=True)
class SourceDocument:
    doc_id: str
    front_matter: dict[str, object]


def write_lineage_config(repo_root: Path) -> None:
    write_docs_scope_config(
        repo_root,
        [
            docs_scope_record(
                "dotlineform",
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


def test_manifest_reports_document_subjects_without_a_folder_inventory(
    tmp_path: Path,
) -> None:
    write_lineage_config(tmp_path)
    payload = processing.project_manifest(
        {},
        [
            SourceDocument(DOC_ID, {"folder_path": "processing/Ink Engine"}),
            SourceDocument(
                "d-20260901-100001-000002",
                {"folder_path": "projects/Other Project"},
            ),
        ],
        tmp_path,
        "dotlineform",
        "processing",
    )

    assert payload == {
        "root": {"id": "dotlineform_processing", "data": {}},
        "rows": {
            DOC_ID: {"folder_path": "processing/Ink Engine"},
            "d-20260901-100001-000002": {
                "folder_path": "projects/Other Project"
            },
        },
    }


def test_manifest_projects_publication_cues_from_processing_lineage(
    tmp_path: Path,
) -> None:
    write_lineage_config(tmp_path)
    editorial_id = "d-20260901-110000-000002"
    report_id = "d-20260901-090000-000003"
    report_path = tmp_path / (
        "docs-viewer/scopes/analysis/source/documents/"
        f"{report_id}.md"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        "---\n"
        f"doc_id: {report_id}\n"
        "title: Works\n"
        "---\n"
        "# Works\n\n"
        ":::report\n"
        "id: docs_subscope\n"
        "access: public\n"
        "sub_scope: works\n"
        ":::\n",
        encoding="utf-8",
    )
    generated_path = tmp_path / (
        "docs-viewer/scopes/analysis/generated/documents/sub-scopes/works/by-id/"
        f"{editorial_id}.json"
    )
    generated_path.parent.mkdir(parents=True, exist_ok=True)
    generated_path.write_text(
        json.dumps({"doc_id": editorial_id, "title": "Editorial"}),
        encoding="utf-8",
    )
    table = publication_lineage.empty_table(
        working_scope="dotlineform",
        working_sub_scope="processing",
        editorial_scope="analysis",
        editorial_sub_scope="works",
    )
    table = publication_lineage.DocumentLineageTable(
        working_collection=table.working_collection,
        editorial_collection=table.editorial_collection,
        records=(
            publication_lineage.DocumentLineageRecord(
                working_doc_id=DOC_ID,
                editorials=(
                    publication_lineage.DocumentEditorialChild(
                        doc_id=editorial_id,
                        created_at="2026-09-01T11:00:00Z",
                        last_copied_at="2026-09-01T11:00:00Z",
                        published_url=None,
                    ),
                ),
            ),
        ),
    )
    publication_lineage.write_table_atomic(
        tmp_path,
        table,
        contract_id=processing.LINEAGE_CONTRACT_ID,
    )

    payload = processing.project_manifest(
        {},
        [SourceDocument(DOC_ID, {"folder_path": "processing/ink-engine"})],
        tmp_path,
        "dotlineform",
        "processing",
    )

    assert payload["rows"][DOC_ID]["publication_targets"] == [
        {
            "editorial": {
                "scope": "analysis",
                "sub_scope": "works",
                "doc_id": editorial_id,
            },
            "available": True,
            "title": "Editorial",
            "viewer_url": (
                f"/docs/?scope=analysis&doc={report_id}&subdoc={editorial_id}"
            ),
            "publication": None,
        }
    ]


def test_metadata_uses_the_existing_base_relative_subject_semantics(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    processing_folder = tmp_path / "processing/ink-engine"
    processing_folder.mkdir(parents=True)
    monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(tmp_path))

    result = processing.normalize_metadata_update(
        {},
        {"folder_path": str(processing_folder), "work_id": "", "series_id": ""},
        repo_root=tmp_path,
        front_matter={"work_id": "00123"},
        doc_id=DOC_ID,
    )

    assert result == {
        "front_matter_updates": {
            "folder_path": "processing/ink-engine",
            "work_id": None,
            "series_id": None,
        },
        "record": {
            "folder_path": "processing/ink-engine",
            "work_id": "",
            "series_id": "",
        },
        "changes": {"authoring_subject_changed": True},
    }
    assert processing.normalize_import_front_matter(
        {},
        {"folder_path": "projects/another-project"},
        doc_id=DOC_ID,
    ) == {"folder_path": "projects/another-project"}
    assert processing.normalize_import_front_matter(
        {},
        {"work_id": "00123"},
        doc_id=DOC_ID,
    ) == {"work_id": "00123"}
    assert processing.normalize_import_front_matter(
        {},
        {"series_id": "026"},
        doc_id=DOC_ID,
    ) == {"series_id": "026"}


def test_subject_assignment_still_rejects_an_unsafe_folder_target(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(tmp_path))

    with pytest.raises(ValueError, match="invalid"):
        processing.normalize_metadata_update(
            {},
            {
                "folder_path": "../processing/ink-engine",
                "work_id": "",
                "series_id": "",
            },
            repo_root=tmp_path,
            front_matter={},
            doc_id=DOC_ID,
        )
    with pytest.raises(ValueError, match="invalid"):
        processing.normalize_import_front_matter(
            {},
            {"folder_path": "../processing/ink-engine"},
            doc_id=DOC_ID,
        )
