#!/usr/bin/env python3
"""Verify current document-owned Tag declaration resolution."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from tags import tag_document_declarations as declarations

def document(doc_id: str, title: str, tag_value=...) -> SimpleNamespace:
    front_matter = {} if tag_value is ... else {"tag_id": tag_value}
    return SimpleNamespace(
        doc_id=doc_id,
        front_matter=front_matter,
        title=title,
    )


def test_current_associations_are_exact_sorted_and_source_owned(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    documents = [
        document("d-20260811-000002-000002", "Second", "trees"),
        document("d-20260811-000001-000001", "First", "trees"),
        document("d-20260811-000003-000003", "Other", "growth"),
        document("d-20260811-000004-000004", "Missing"),
        document("d-20260811-000005-000005", "Malformed", " Trees "),
    ]
    load_calls: list[tuple[Path, str, str]] = []
    def load_working(_repo_root, scope, stage):
        assert (scope, stage) == ("analysis", "working")
        return SimpleNamespace(sub_scopes=[SimpleNamespace(sub_scope="concepts")])

    monkeypatch.setattr(declarations, "load_docs_scope_stage", load_working)
    monkeypatch.setattr(
        declarations.source_model,
        "load_document_collection_docs_for_config",
        lambda repo_root, parent_config, sub_scope_config: (
            load_calls.append(
                (
                    repo_root,
                    "analysis" if parent_config else "",
                    sub_scope_config.sub_scope,
                )
            )
            or documents
        ),
    )
    monkeypatch.setattr(
        declarations.document_location,
        "management_collection_viewer_url",
        lambda _repo_root, scope, sub_scope, *, stage: (
            f"/docs/?scope={scope}&stage={stage}&doc=report-{sub_scope}"
        ),
    )
    monkeypatch.setattr(
        declarations.document_location,
        "management_document_viewer_url",
        lambda collection_url, doc_id, *, sub_scope: (
            f"{collection_url}&subdoc={doc_id}" if sub_scope else "unexpected"
        ),
    )

    repo_root = Path("/fixture")
    associations = declarations.current_tag_document_associations(
        repo_root,
        "trees",
    )

    assert load_calls == [(repo_root, "analysis", "concepts")]
    assert associations == [
        {
            "target": {
                "scope": "analysis",
                "stage": "working",
                "sub_scope": "concepts",
                "doc_id": "d-20260811-000001-000001",
            },
            "title": "First",
            "url": (
                "/docs/?scope=analysis&stage=working&doc=report-concepts"
                "&subdoc=d-20260811-000001-000001"
            ),
        },
        {
            "target": {
                "scope": "analysis",
                "stage": "working",
                "sub_scope": "concepts",
                "doc_id": "d-20260811-000002-000002",
            },
            "title": "Second",
            "url": (
                "/docs/?scope=analysis&stage=working&doc=report-concepts"
                "&subdoc=d-20260811-000002-000002"
            ),
        },
    ]


def test_requested_tag_id_must_be_canonical() -> None:
    with pytest.raises(ValueError, match="exact canonical tag id"):
        declarations.current_tag_document_associations(Path("/fixture"), " Trees ")
