#!/usr/bin/env python3
"""Focused checks for the folder-centred Project State producer and lookup."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
if str(DOCS_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(DOCS_SERVICES_DIR))

from docs_project_state import (  # noqa: E402
    LOOKUP_SCHEMA_VERSION,
    REPORT_SCHEMA_VERSION,
    ProjectStatePaths,
    ProjectStateProducer,
)


SUBJECT_GENERATION = "sha256:" + "1" * 64
GENERATED_AT = "2026-08-05T14:13:05Z"
DOC_ALPHA_A = "d-20260101-000000-000001"
DOC_ALPHA_B = "d-20260101-000000-000002"
DOC_BETA = "d-20260101-000000-000003"
DOC_DELTA = "d-20260101-000000-000004"
DOC_RECORDED_ONLY = "d-20260101-000000-000005"
DOC_WORK = "d-20260101-000000-000006"
DOC_SERIES = "d-20260101-000000-000007"
DOC_WORK_NO_SERIES = "d-20260101-000000-000008"
DOC_UNKNOWN_WORK = "d-20260101-000000-000009"
DOC_EMPTY_SERIES = "d-20260101-000000-000010"
DOC_NONE = "d-20260101-000000-000011"


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def manifest_doc(doc_id: str, title: str, subject: dict[str, object]) -> dict[str, object]:
    return {
        "doc_id": doc_id,
        "title": title,
        "ui_status": "",
        "viewable": True,
        "last_updated": "2026-08-05 12:00:00",
        "authoring_subject": subject,
    }


def valid_subject(kind: str, key: str, field: str) -> dict[str, object]:
    return {"state": "valid", "kind": kind, "key": key, "fields": [field]}


def fixture_manifest() -> dict[str, object]:
    return {
        "subject_generation": SUBJECT_GENERATION,
        "docs": [
            manifest_doc(DOC_ALPHA_A, "Alpha note", valid_subject("folder", "projects/alpha", "folder_path")),
            manifest_doc(DOC_ALPHA_B, "Second alpha note", valid_subject("folder", "projects/alpha", "folder_path")),
            manifest_doc(DOC_BETA, "Beta note", valid_subject("folder", "projects/beta", "folder_path")),
            manifest_doc(DOC_DELTA, "Delta note", valid_subject("folder", "projects/delta", "folder_path")),
            manifest_doc(
                DOC_RECORDED_ONLY,
                "Recorded only",
                valid_subject("folder", "projects/recorded-only", "folder_path"),
            ),
            manifest_doc(DOC_WORK, "Work note", valid_subject("work", "00001", "work_id")),
            manifest_doc(DOC_SERIES, "Series one note", valid_subject("series", "001", "series_id")),
            manifest_doc(
                DOC_WORK_NO_SERIES,
                "Work without Series note",
                valid_subject("work", "00003", "work_id"),
            ),
            manifest_doc(
                DOC_UNKNOWN_WORK,
                "Unknown Work note",
                valid_subject("work", "99999", "work_id"),
            ),
            manifest_doc(
                DOC_EMPTY_SERIES,
                "Empty Series note",
                valid_subject("series", "003", "series_id"),
            ),
            manifest_doc(
                DOC_NONE,
                "Ordinary note",
                {"state": "none", "kind": "none", "key": "", "fields": []},
            ),
        ],
    }


def fixture_associations(manifest: dict[str, object]) -> dict[str, object]:
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for document in manifest["docs"]:
        subject = document["authoring_subject"]
        if subject["state"] != "valid":
            continue
        grouped[(subject["kind"], subject["key"])].append(
            {
                "target": {
                    "scope": "dotlineform",
                    "sub_scope": "projects",
                    "doc_id": document["doc_id"],
                },
                "locations": [
                    {
                        "access": "manage",
                        "url": (
                            "/docs/?scope=dotlineform&doc=d-20260801-073826-8865a8"
                            f"&subdoc={document['doc_id']}"
                        ),
                    }
                ],
            }
        )
    return {
        "schema_version": "docs_subject_associations_v1",
        "scope": "dotlineform",
        "sub_scope": "projects",
        "subject_generation": manifest["subject_generation"],
        "associations": [
            {
                "subject": {"kind": kind, "key": key},
                "documents": documents,
            }
            for (kind, key), documents in sorted(grouped.items())
        ],
    }


def fixture_works() -> dict[str, object]:
    return {
        "header": {"schema": "catalogue_source_works_v1", "count": 6},
        "works": {
            "00001": {
                "work_id": "00001",
                "status": "published",
                "published_date": "2026-01-01",
                "series_ids": ["001", "002"],
                "project_folder": "alpha",
                "project_subfolder": "ink",
                "project_filename": "alpha-1.jpg",
                "title": "Alpha one",
            },
            "00002": {
                "work_id": "00002",
                "status": "draft",
                "series_ids": ["001"],
                "project_folder": "alpha",
                "project_filename": "alpha-2.jpg",
                "title": "Alpha two",
            },
            "00003": {
                "work_id": "00003",
                "status": "published",
                "series_ids": [],
                "project_folder": "beta",
                "project_filename": "beta.jpg",
                "title": "Beta",
            },
            "00004": {
                "work_id": "00004",
                "status": "published",
                "series_ids": ["999"],
                "project_folder": "gamma",
                "project_filename": "gamma.jpg",
                "title": "Gamma",
            },
            "00005": {
                "work_id": "00005",
                "status": "published",
                "series_ids": ["001"],
                "project_folder": "recorded-only",
                "project_filename": "recorded.jpg",
                "title": "Recorded only",
            },
            "00006": {
                "work_id": "00006",
                "status": "published",
                "series_ids": ["001"],
                "project_folder": "epsilon",
                "project_filename": "epsilon.jpg",
                "title": "Epsilon",
            },
        },
    }


def fixture_series() -> dict[str, object]:
    return {
        "header": {"schema": "catalogue_source_series_v1", "count": 3},
        "series": {
            "001": {"series_id": "001", "title": "Series one", "status": "published"},
            "002": {"series_id": "002", "title": "Series two", "status": "draft"},
            "003": {"series_id": "003", "title": "Series three", "status": "draft"},
        },
    }


def build_fixture(root: Path) -> ProjectStatePaths:
    projects_base = root / "external-projects"
    projects_root = projects_base / "projects"
    for name in ("alpha", "beta", "gamma", "delta", "epsilon"):
        (projects_root / name).mkdir(parents=True, exist_ok=True)
    (projects_root / "alpha" / "ink").mkdir()
    (projects_root / ".hidden").mkdir()
    (projects_base / "sibling-tree" / "outside").mkdir(parents=True)

    manifest_path = root / "inputs/manage-manifest.json"
    associations_path = root / "inputs/subject-associations.json"
    catalogue_dir = root / "studio/data/canonical/catalogue"
    lookup_path = root / "var/docs/project-state/folder-lookup.json"
    manifest = fixture_manifest()
    write_json(manifest_path, manifest)
    write_json(associations_path, fixture_associations(manifest))
    write_json(catalogue_dir / "works.json", fixture_works())
    write_json(catalogue_dir / "series.json", fixture_series())
    (catalogue_dir / "work_details").mkdir(parents=True)
    return ProjectStatePaths(
        projects_base_dir=projects_base,
        manage_manifest_path=manifest_path,
        subject_associations_path=associations_path,
        catalogue_source_dir=catalogue_dir,
        lookup_path=lookup_path,
    )


def row_by_key(report: dict[str, object], key: str) -> dict[str, object]:
    return next(row for row in report["rows"] if row["folder"]["key"] == key)


def test_project_state_service_import_bootstraps_canonical_readers() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "sys.path.insert(0, 'docs-viewer/services'); "
                "import docs_project_state"
            ),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr


def test_project_state_builds_only_scanned_folder_rows_and_exact_relationships() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        paths = build_fixture(root)
        result = ProjectStateProducer(
            repo_root=root,
            paths=paths,
            clock=lambda: GENERATED_AT,
        ).run(write_lookup=True)
        report = result["report"]
        lookup = read_json(paths.lookup_path)

    assert report["schema_version"] == REPORT_SCHEMA_VERSION
    assert lookup["schema_version"] == LOOKUP_SCHEMA_VERSION
    assert report["generation"] == lookup["generation"]
    assert lookup["status"] == {"state": "current"}
    assert [row["folder"]["key"] for row in report["rows"]] == [
        "projects/alpha",
        "projects/beta",
        "projects/delta",
        "projects/epsilon",
        "projects/gamma",
    ]
    assert "projects/alpha/ink" not in lookup["folders"]
    assert "projects/recorded-only" not in lookup["folders"]

    alpha = row_by_key(report, "projects/alpha")
    assert alpha["folder"] == {
        "key": "projects/alpha",
        "label": "/alpha",
        "href": "dlf-local:projects/alpha",
        "present": True,
    }
    assert alpha["states"] == {
        "reconciliation": "reconciled",
        "documents": "multiple",
        "series": "complete",
    }
    assert alpha["matched_work_count"] == 2
    assert alpha["matched_document_count"] == 4
    assert [work["target"]["target_id"] for work in alpha["works"]] == ["00001", "00002"]
    assert [(series["target"]["target_id"], series["work_count"]) for series in alpha["series"]] == [
        ("001", 2),
        ("002", 1),
    ]

    beta = row_by_key(report, "projects/beta")
    assert beta["states"]["series"] == "incomplete"
    assert beta["series_issues"] == [{"state": "missing_series", "work_id": "00003"}]
    assert row_by_key(report, "projects/delta")["states"]["reconciliation"] == "documents_only"
    epsilon = row_by_key(report, "projects/epsilon")
    assert epsilon["states"]["reconciliation"] == "reconciled"
    assert [document["target"]["doc_id"] for document in epsilon["documents"]] == [DOC_SERIES]
    assert epsilon["documents"][0]["declared_subject"] == {"kind": "series", "key": "001"}
    assert epsilon["documents"][0]["applicable_series_ids"] == ["001"]
    gamma = row_by_key(report, "projects/gamma")
    assert gamma["states"]["reconciliation"] == "works_only"
    assert gamma["series_issues"] == [
        {"state": "unknown_series", "work_id": "00004", "series_id": "999"}
    ]

    assert report["summary"]["recorded_only_document_folder_count"] == 1
    assert report["summary"]["recorded_only_work_folder_count"] == 1
    assert report["summary"]["matched_document_count"] == 7
    assert report["summary"]["document_placement_count"] == 8
    assert report["summary"]["unmatched_document_count"] == 3
    assert report["summary"]["matched_work_count"] == 5
    assert report["summary"]["series_membership_count"] == 4

    alpha_lookup = lookup["folders"]["projects/alpha"]
    assert alpha_lookup["works"][0] == {
        "target": {"family": "catalogue", "target_type": "work", "target_id": "00001"},
        "series_ids": ["001", "002"],
    }
    assert alpha_lookup["series"][0] == {
        "target": {"family": "catalogue", "target_type": "series", "target_id": "001"},
        "work_ids": ["00001", "00002"],
    }
    assert alpha_lookup["documents"] == [
        {
            "target": {"scope": "dotlineform", "sub_scope": "projects", "doc_id": DOC_ALPHA_A},
            "declared_subject": {"kind": "folder", "key": "projects/alpha"},
            "applicable_series_ids": ["001", "002"],
        },
        {
            "target": {"scope": "dotlineform", "sub_scope": "projects", "doc_id": DOC_ALPHA_B},
            "declared_subject": {"kind": "folder", "key": "projects/alpha"},
            "applicable_series_ids": ["001", "002"],
        },
        {
            "target": {"scope": "dotlineform", "sub_scope": "projects", "doc_id": DOC_SERIES},
            "declared_subject": {"kind": "series", "key": "001"},
            "applicable_series_ids": ["001"],
        },
        {
            "target": {"scope": "dotlineform", "sub_scope": "projects", "doc_id": DOC_WORK},
            "declared_subject": {"kind": "work", "key": "00001"},
            "applicable_series_ids": ["001", "002"],
        },
    ]
    beta = row_by_key(report, "projects/beta")
    assert beta["matched_document_count"] == 2
    assert all(not document["applicable_series_ids"] for document in beta["documents"])
    lookup_text = json.dumps(lookup)
    for excluded in (
        "project_subfolder",
        "project_filename",
        "published_date",
        "Alpha one",
        "/series/?series=",
        "/docs/?scope=",
    ):
        assert excluded not in lookup_text
    assert not (root / "site/assets/data/docs/project-state").exists()


def test_project_state_ignores_non_relationship_work_fields() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        paths = build_fixture(root)
        producer = ProjectStateProducer(repo_root=root, paths=paths, clock=lambda: GENERATED_AT)
        before = producer.run(write_lookup=False)
        works_payload = read_json(paths.catalogue_source_dir / "works.json")
        works_payload["works"]["00001"].update(
            {
                "project_subfolder": "different/nesting",
                "project_filename": "replacement.png",
                "title": "Changed presentation",
                "status": "draft",
                "published_date": "2026-08-05",
            }
        )
        write_json(paths.catalogue_source_dir / "works.json", works_payload)
        after = producer.run(write_lookup=False)

    assert after["report"] == before["report"]
    assert after["lookup"] == before["lookup"]


def test_project_state_relationship_changes_replace_the_generation() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        paths = build_fixture(root)
        producer = ProjectStateProducer(repo_root=root, paths=paths, clock=lambda: GENERATED_AT)
        before = producer.run(write_lookup=False)
        works_payload = read_json(paths.catalogue_source_dir / "works.json")
        works_payload["works"]["00002"]["series_ids"] = ["002"]
        write_json(paths.catalogue_source_dir / "works.json", works_payload)
        after = producer.run(write_lookup=False)

    assert after["report"]["generation"] != before["report"]["generation"]
    alpha = row_by_key(after["report"], "projects/alpha")
    assert [(series["target"]["target_id"], series["work_count"]) for series in alpha["series"]] == [
        ("001", 1),
        ("002", 2),
    ]


def test_series_subject_reaches_each_distinct_member_work_folder() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        paths = build_fixture(root)
        manifest = read_json(paths.manage_manifest_path)
        alpha_document = next(document for document in manifest["docs"] if document["doc_id"] == DOC_ALPHA_A)
        alpha_document["authoring_subject"] = valid_subject("series", "001", "series_id")
        manifest["subject_generation"] = "sha256:" + "3" * 64
        write_json(paths.manage_manifest_path, manifest)
        write_json(paths.subject_associations_path, fixture_associations(manifest))

        report = ProjectStateProducer(
            repo_root=root,
            paths=paths,
            clock=lambda: GENERATED_AT,
        ).run(write_lookup=False)["report"]

    placements = [
        (row["folder"]["key"], document)
        for row in report["rows"]
        for document in row["documents"]
        if document["target"]["doc_id"] == DOC_ALPHA_A
    ]
    assert [folder_key for folder_key, _document in placements] == [
        "projects/alpha",
        "projects/epsilon",
    ]
    assert all(
        document["declared_subject"] == {"kind": "series", "key": "001"}
        and document["applicable_series_ids"] == ["001"]
        for _folder_key, document in placements
    )
    assert report["summary"]["matched_document_count"] == 7
    assert report["summary"]["document_placement_count"] == 9


def test_failed_refresh_preserves_the_complete_lookup_and_marks_it_stale() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        paths = build_fixture(root)
        timestamps = iter([GENERATED_AT, "2026-08-05T14:20:00Z"])
        producer = ProjectStateProducer(repo_root=root, paths=paths, clock=lambda: next(timestamps))
        producer.run(write_lookup=True)
        complete = read_json(paths.lookup_path)
        associations = read_json(paths.subject_associations_path)
        associations["subject_generation"] = "sha256:" + "2" * 64
        write_json(paths.subject_associations_path, associations)

        with pytest.raises(ValueError, match="generation receipts do not match"):
            producer.run(write_lookup=True)
        stale = read_json(paths.lookup_path)

    assert stale["generation"] == complete["generation"]
    assert stale["folders"] == complete["folders"]
    assert stale["status"] == {
        "state": "stale",
        "failed_at": "2026-08-05T14:20:00Z",
        "reason": "Projects subject generation receipts do not match",
    }


def test_failed_dry_run_does_not_create_a_lookup() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        paths = build_fixture(root)
        associations = read_json(paths.subject_associations_path)
        associations["scope"] = "studio"
        write_json(paths.subject_associations_path, associations)
        producer = ProjectStateProducer(repo_root=root, paths=paths, clock=lambda: GENERATED_AT)

        with pytest.raises(ValueError, match="wrong collection"):
            producer.run(write_lookup=False)

        assert not paths.lookup_path.exists()
