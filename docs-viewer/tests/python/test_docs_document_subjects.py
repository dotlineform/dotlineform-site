#!/usr/bin/env python3
"""Focused document subject normalization and association tests."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))

import docs_document_subjects as subjects  # noqa: E402


def test_detail_uid_is_exact_identity_without_catalogue_lookup() -> None:
    assert subjects.parse_detail_uid("00008-001") == ("00008", "001")
    normalized = subjects.normalize_authoring_subject(
        {"detail_uid": "00008-001"}, folder_supported=False
    )
    assert normalized == {
        "state": "valid", "kind": "detail", "key": "00008-001",
        "fields": ["detail_uid"],
    }
    document = SimpleNamespace(doc_id="detail-doc", viewer_url="/docs/?doc=detail-doc")
    payload = subjects.project_subject_associations(
        scope="analysis", sub_scope="works", documents=[document],
        subjects_by_doc_id={document.doc_id: normalized}, subject_generation="test",
    )
    assert payload["associations"][0]["subject"] == {
        "kind": "detail", "key": "00008-001",
    }
    assert subjects.normalize_authoring_subject(
        {"detail_uid": "00008-001", "work_id": "00008"}, folder_supported=False
    )["state"] == "conflicting"


@pytest.mark.parametrize("value", ["8-1", "00008-01", "00008-0001", "00008_001", "00008-001\n", "٠٠٠٠٨-001"])
def test_detail_uid_rejects_noncanonical_identity(value: str) -> None:
    with pytest.raises(ValueError):
        subjects.parse_detail_uid(value)
    assert subjects.normalize_authoring_subject(
        {"detail_uid": value}, folder_supported=False
    )["state"] == "malformed"


def test_normalized_subject_states_preserve_exact_scalar_identity() -> None:
    assert subjects.normalize_authoring_subject({}, folder_supported=True) == {
        "state": "none",
        "kind": "none",
        "key": "",
        "fields": [],
    }
    assert subjects.normalize_authoring_subject(
        {"folder_path": "projects/nerve"},
        folder_supported=True,
    ) == {
        "state": "valid",
        "kind": "folder",
        "key": "projects/nerve",
        "fields": ["folder_path"],
    }
    assert subjects.normalize_authoring_subject(
        {"work_id": "00123"},
        folder_supported=False,
    ) == {
        "state": "valid",
        "kind": "work",
        "key": "00123",
        "fields": ["work_id"],
    }
    assert subjects.normalize_authoring_subject(
        {"series_id": "026"},
        folder_supported=False,
    ) == {
        "state": "valid",
        "kind": "series",
        "key": "026",
        "fields": ["series_id"],
    }
    assert subjects.normalize_authoring_subject(
        {"work_id": 123},
        folder_supported=False,
    ) == {
        "state": "malformed",
        "kind": "work",
        "key": "",
        "fields": ["work_id"],
        "evidence": {"work_id": 123},
    }
    assert subjects.normalize_authoring_subject(
        {"work_id": "123"},
        folder_supported=False,
    )["state"] == "malformed"
    assert subjects.normalize_authoring_subject(
        {"series_id": "Nerve"},
        folder_supported=False,
    )["state"] == "malformed"
    assert subjects.normalize_authoring_subject(
        {"folder_path": "projects/nerve", "series_id": "026"},
        folder_supported=True,
    ) == {
        "state": "conflicting",
        "kind": "conflict",
        "key": "",
        "fields": ["folder_path", "series_id"],
        "evidence": {
            "folder_path": "projects/nerve",
            "series_id": "026",
        },
    }
    assert subjects.normalize_authoring_subject(
        {"folder_path": "projects/nerve"},
        folder_supported=False,
    )["state"] == "malformed"


def test_associations_group_zero_to_many_exact_targets_and_locations() -> None:
    docs = [
        SimpleNamespace(
            doc_id="d-20260801-000000-000002",
            viewer_url="/docs/?scope=dotlineform&doc=projects&subdoc=d-20260801-000000-000002",
        ),
        SimpleNamespace(
            doc_id="d-20260801-000000-000001",
            viewer_url="/docs/?scope=dotlineform&doc=projects&subdoc=d-20260801-000000-000001",
        ),
        SimpleNamespace(
            doc_id="d-20260801-000000-000003",
            viewer_url="/docs/?scope=dotlineform&doc=projects&subdoc=d-20260801-000000-000003",
        ),
    ]
    normalized = {
        docs[0].doc_id: subjects.normalize_authoring_subject(
            {"work_id": "00123"}, folder_supported=True
        ),
        docs[1].doc_id: subjects.normalize_authoring_subject(
            {"work_id": "00123"}, folder_supported=True
        ),
        docs[2].doc_id: subjects.normalize_authoring_subject(
            {"series_id": 26}, folder_supported=True
        ),
    }
    generation = subjects.subject_projection_generation(
        scope="dotlineform",
        sub_scope="projects",
        subjects_by_doc_id=normalized,
    )
    payload = subjects.project_subject_associations(
        scope="dotlineform",
        sub_scope="projects",
        documents=docs,
        subjects_by_doc_id=normalized,
        subject_generation=generation,
    )

    assert generation.startswith("sha256:")
    assert payload == {
        "schema_version": "docs_subject_associations_v1",
        "scope": "dotlineform",
        "sub_scope": "projects",
        "subject_generation": generation,
        "associations": [
            {
                "subject": {"kind": "work", "key": "00123"},
                "documents": [
                    {
                        "target": {
                            "scope": "dotlineform",
                            "sub_scope": "projects",
                            "doc_id": "d-20260801-000000-000001",
                        },
                        "locations": [
                            {
                                "access": "manage",
                                "url": "/docs/?scope=dotlineform&doc=projects&subdoc=d-20260801-000000-000001",
                            }
                        ],
                    },
                    {
                        "target": {
                            "scope": "dotlineform",
                            "sub_scope": "projects",
                            "doc_id": "d-20260801-000000-000002",
                        },
                        "locations": [
                            {
                                "access": "manage",
                                "url": "/docs/?scope=dotlineform&doc=projects&subdoc=d-20260801-000000-000002",
                            }
                        ],
                    },
                ],
            }
        ],
    }


def test_projection_generation_changes_with_normalized_source_evidence() -> None:
    valid = {
        "d-20260801-000000-000001": subjects.normalize_authoring_subject(
            {"work_id": "00123"}, folder_supported=False
        )
    }
    malformed = {
        "d-20260801-000000-000001": subjects.normalize_authoring_subject(
            {"work_id": 123}, folder_supported=False
        )
    }
    assert subjects.subject_projection_generation(
        scope="analysis", sub_scope="works", subjects_by_doc_id=valid
    ) != subjects.subject_projection_generation(
        scope="analysis", sub_scope="works", subjects_by_doc_id=malformed
    )


def test_associations_use_only_normalized_front_matter_subject_identity() -> None:
    document = SimpleNamespace(
        doc_id="d-20260801-000000-000001",
        title="Work 00123",
        filename="series-026.md",
        body="Folder projects/nerve",
        viewer_url="/docs/?scope=dotlineform&doc=work-00123",
        selected_row="00123",
        report_host="series-026",
        ui_state={"work_id": "00123"},
    )
    normalized = {
        document.doc_id: subjects.normalize_authoring_subject(
            {},
            folder_supported=True,
        )
    }
    generation = subjects.subject_projection_generation(
        scope="dotlineform",
        sub_scope="projects",
        subjects_by_doc_id=normalized,
    )

    payload = subjects.project_subject_associations(
        scope="dotlineform",
        sub_scope="projects",
        documents=[document],
        subjects_by_doc_id=normalized,
        subject_generation=generation,
    )

    assert normalized[document.doc_id] == {
        "state": "none",
        "kind": "none",
        "key": "",
        "fields": [],
    }
    assert payload["associations"] == []
