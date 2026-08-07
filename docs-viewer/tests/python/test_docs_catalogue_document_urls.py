#!/usr/bin/env python3
"""Focused SSP-5.1 public Catalogue document URL projection checks."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from repo_factory import (
    docs_scope_record,
    docs_sub_scope_record,
    write_docs_scope_config,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))

import docs_catalogue_document_urls as projection  # noqa: E402


REPORT_ID = "d-20260807-141500-a1b2c3"
PUBLIC_CHILD_ID = "d-20260807-141501-b2c3d4"
PRIVATE_CHILD_ID = "d-20260807-141502-c3d4e5"
MOMENT_ID = "d-20260807-141503-d4e5f6"


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_source(path: Path, front_matter: dict[str, object], body: str = "# Body\n") -> None:
    def scalar(value: object) -> str:
        if value is True:
            return "true"
        if value is False:
            return "false"
        if isinstance(value, str):
            return json.dumps(value, ensure_ascii=False)
        return str(value)

    lines = ["---"]
    lines.extend(f"{key}: {scalar(value)}" for key, value in front_matter.items())
    lines.extend(["---", "", body.rstrip(), ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def test_projection_is_exact_deterministic_and_subject_only() -> None:
    locations = [
        {"scope_id": "analysis", "sub_scope": "works", "doc_id": "work", "url": "/z"},
        {"scope_id": "analysis", "sub_scope": "works", "doc_id": "work", "url": "/a"},
        {"scope_id": "analysis", "sub_scope": "works", "doc_id": "work", "url": "/a"},
        {"scope_id": "analysis", "sub_scope": "works", "doc_id": "series", "url": "/series"},
        {"scope_id": "analysis", "sub_scope": "works", "doc_id": "none", "url": "/none"},
        {"scope_id": "analysis", "sub_scope": "works", "doc_id": "malformed", "url": "/malformed"},
        {"scope_id": "analysis", "sub_scope": "works", "doc_id": "conflict", "url": "/conflict"},
        {"scope_id": "analysis", "sub_scope": "works", "doc_id": "folder", "url": "/folder"},
    ]
    front_matter = {
        ("analysis", "works", "work"): {"work_id": "00042"},
        ("analysis", "works", "series"): {"series_id": "009"},
        ("analysis", "works", "none"): {"title": "Semantic token only"},
        ("analysis", "works", "malformed"): {"work_id": "42"},
        ("analysis", "works", "conflict"): {"work_id": "00042", "series_id": "009"},
        ("analysis", "works", "folder"): {"folder_path": "project"},
        ("analysis", "works", "private"): {"work_id": "99999"},
    }

    result = projection.project_catalogue_document_urls(
        exact_locations=locations,
        front_matter_by_target=front_matter,
    )

    assert result == {
        "work": {"00042": ["/a", "/z"]},
        "series": {"009": ["/series"]},
    }


def test_projection_rejects_public_location_without_exact_source() -> None:
    try:
        projection.project_catalogue_document_urls(
            exact_locations=[
                {
                    "scope_id": "analysis",
                    "sub_scope": "works",
                    "doc_id": "missing",
                    "url": "/analysis/?doc=report&subdoc=missing",
                }
            ],
            front_matter_by_target={},
        )
    except ValueError as exc:
        assert "no exact canonical source" in str(exc)
    else:
        raise AssertionError("missing canonical public source should fail closed")


def test_loader_joins_public_parent_and_sub_scope_sources_across_configured_scopes() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        write_docs_scope_config(
            root,
            [
                docs_scope_record(
                    "analysis",
                    scope_type="public",
                    viewer_base_url="/analysis/",
                    include_scope_param=False,
                    default_doc_id=REPORT_ID,
                    sub_scopes=[
                        docs_sub_scope_record(
                            "analysis",
                            "works",
                            title="Works",
                            scope_type="public",
                            sub_scope_customisation={
                                "id": "analysis_works",
                                "settings": {},
                            },
                        )
                    ],
                ),
                docs_scope_record(
                    "moments",
                    scope_type="public",
                    viewer_base_url="/moments/",
                    include_scope_param=False,
                    default_doc_id=MOMENT_ID,
                ),
                docs_scope_record("studio", default_doc_id=""),
            ],
        )

        write_json(
            root / "site/assets/data/search/analysis/index.json",
            {
                "header": {"scope": "analysis"},
                "entries": [
                    {
                        "id": REPORT_ID,
                        "kind": "doc",
                        "title": "Works",
                        "href": f"/analysis/?doc={REPORT_ID}",
                    }
                ],
            },
        )
        write_json(
            root / f"site/assets/data/docs/scopes/analysis/by-id/{REPORT_ID}.json",
            {
                "viewer_report": "docs_subscope",
                "viewer_report_access": "public",
                "viewer_report_subscope": "works",
            },
        )
        write_json(
            root / "site/assets/data/docs/scopes/analysis/works/manifest.json",
            {"docs": [{"doc_id": PUBLIC_CHILD_ID, "title": "Public Series Note"}]},
        )
        write_json(
            root / "site/assets/data/search/moments/index.json",
            {
                "header": {"scope": "moments"},
                "entries": [
                    {
                        "id": MOMENT_ID,
                        "kind": "doc",
                        "title": "Public Work Moment",
                        "href": f"/moments/?doc={MOMENT_ID}",
                    }
                ],
            },
        )
        write_json(
            root / f"site/assets/data/docs/scopes/moments/by-id/{MOMENT_ID}.json",
            {"title": "Public Work Moment"},
        )

        write_source(
            root / f"docs-viewer/scopes/analysis/source/documents/{REPORT_ID}.md",
            {"doc_id": REPORT_ID, "title": "Works", "publishable": True},
        )
        write_source(
            root
            / f"docs-viewer/scopes/analysis/source/sub-scopes/works/documents/{PUBLIC_CHILD_ID}.md",
            {
                "doc_id": PUBLIC_CHILD_ID,
                "title": "Public Series Note",
                "series_id": "001",
                "ui_status": "done",
                "publishable": True,
            },
        )
        write_source(
            root
            / f"docs-viewer/scopes/analysis/source/sub-scopes/works/documents/{PRIVATE_CHILD_ID}.md",
            {
                "doc_id": PRIVATE_CHILD_ID,
                "title": "Private Work Note",
                "work_id": "00001",
                "ui_status": "done",
                "publishable": False,
            },
        )
        write_source(
            root / f"docs-viewer/scopes/moments/source/documents/{MOMENT_ID}.md",
            {
                "doc_id": MOMENT_ID,
                "title": "Public Work Moment",
                "work_id": "00002",
                "publishable": True,
            },
            body="A semantic token mention does not change the declared subject.",
        )

        result = projection.load_public_catalogue_document_urls(root)

    assert result == {
        "work": {"00002": [f"/moments/?doc={MOMENT_ID}"]},
        "series": {
            "001": [
                f"/analysis/?doc={REPORT_ID}&subdoc={PUBLIC_CHILD_ID}"
            ]
        },
    }
