#!/usr/bin/env python3
"""Focused Processing Working collection customisation tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))

import docs_dotlineform_processing_customisation as processing  # noqa: E402


DOC_ID = "d-20260901-100000-000001"


@dataclass(frozen=True)
class SourceDocument:
    doc_id: str
    front_matter: dict[str, object]


def test_manifest_reports_document_subjects_without_a_folder_inventory(
    tmp_path: Path,
) -> None:
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
