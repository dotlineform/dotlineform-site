#!/usr/bin/env python3
"""Focused Projects authoring-subject customisation tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))

import docs_dotlineform_projects_customisation as projects  # noqa: E402


DOC_ID = "d-20260801-000000-000001"


def test_existing_subject_states_are_non_blocking_and_project_valid_folder_only() -> None:
    malformed = {"work_id": 123}
    conflicting = {"folder_path": "projects/nerve", "series_id": "026"}

    assert projects.metadata_record({}, malformed, doc_id=DOC_ID) == {
        "folder_path": "",
        "work_id": "",
        "series_id": "",
    }
    assert projects.metadata_record({}, conflicting, doc_id=DOC_ID) == {
        "folder_path": "",
        "work_id": "",
        "series_id": "",
    }
    assert projects.metadata_record(
        {}, {"work_id": "00123"}, doc_id=DOC_ID
    ) == {
        "folder_path": "",
        "work_id": "00123",
        "series_id": "",
    }


def test_strict_assignment_preserves_work_identity_and_clears_other_fields(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    projects_base = tmp_path / "Projects Base"
    projects_base.mkdir()
    monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(projects_base))

    result = projects.normalize_metadata_update(
        {},
        {"folder_path": "", "work_id": "00123", "series_id": ""},
        repo_root=tmp_path,
        front_matter={"folder_path": "projects/old"},
        doc_id=DOC_ID,
    )

    assert result == {
        "front_matter_updates": {
            "folder_path": None,
            "work_id": "00123",
            "series_id": None,
        },
        "record": {
            "folder_path": "",
            "work_id": "00123",
            "series_id": "",
        },
        "changes": {"authoring_subject_changed": True},
    }


@pytest.mark.parametrize(
    "raw",
    [
        {"folder_path": "", "work_id": "00123"},
        {"folder_path": "", "work_id": 123, "series_id": ""},
        {"folder_path": "", "work_id": "00123", "series_id": "026"},
        {"folder_path": "", "work_id": " 00123", "series_id": ""},
        {"folder_path": "", "work_id": "123", "series_id": ""},
        {"folder_path": "", "work_id": "", "series_id": "Nerve"},
    ],
)
def test_strict_assignment_rejects_incomplete_malformed_or_conflicting_input(
    raw: object,
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError):
        projects.normalize_metadata_update(
            {},
            raw,
            repo_root=tmp_path,
            front_matter={},
            doc_id=DOC_ID,
        )


def test_import_accepts_one_exact_subject_and_preserves_leading_zeroes() -> None:
    assert projects.normalize_import_front_matter(
        {}, {"work_id": "00123"}, doc_id=DOC_ID
    ) == {"work_id": "00123"}
    assert projects.normalize_import_front_matter(
        {}, {"series_id": "026"}, doc_id=DOC_ID
    ) == {"series_id": "026"}
    assert projects.normalize_import_front_matter(
        {}, {}, doc_id=DOC_ID
    ) == {}
    with pytest.raises(ValueError, match="conflicting"):
        projects.normalize_import_front_matter(
            {},
            {"work_id": "00123", "series_id": "026"},
            doc_id=DOC_ID,
        )
