#!/usr/bin/env python3
"""Document-owned Tag declaration and association tests."""

from __future__ import annotations

from types import SimpleNamespace

import docs_tag_documents as tag_documents


def test_tag_declarations_preserve_non_blocking_states() -> None:
    assert tag_documents.normalize_tag_declaration({}) == {
        "state": "none",
        "tag_id": "",
    }
    assert tag_documents.normalize_tag_declaration({"tag_id": "absence"}) == {
        "state": "valid",
        "tag_id": "absence",
    }
    for raw_value in ("", " Absence ", "bad_slug", True, 42):
        assert tag_documents.normalize_tag_declaration(
            {"tag_id": raw_value}
        ) == {
            "state": "malformed",
            "tag_id": "",
            "evidence": raw_value,
        }


def test_tag_associations_are_exact_ordered_and_location_optional() -> None:
    documents = [
        SimpleNamespace(
            doc_id="d-20260801-000000-000003",
            title="Third",
            viewer_url="/analysis/?doc=report&subdoc=third",
        ),
        SimpleNamespace(
            doc_id="d-20260801-000000-000001",
            title="First",
            viewer_url="/analysis/?doc=report&subdoc=first",
        ),
        SimpleNamespace(
            doc_id="d-20260801-000000-000002",
            title="Malformed",
            viewer_url="/analysis/?doc=report&subdoc=malformed",
        ),
    ]
    declarations = {
        "d-20260801-000000-000001": {"state": "valid", "tag_id": "absence"},
        "d-20260801-000000-000002": {
            "state": "malformed",
            "tag_id": "",
            "evidence": "bad_slug",
        },
        "d-20260801-000000-000003": {"state": "valid", "tag_id": "absence"},
    }
    generation = tag_documents.tag_declaration_generation(
        scope="analysis",
        sub_scope="tags",
        declarations_by_doc_id=declarations,
    )
    payload = tag_documents.project_tag_associations(
        scope="analysis",
        sub_scope="tags",
        documents=documents,
        declarations_by_doc_id=declarations,
        declaration_generation=generation,
        management_urls_by_doc_id={
            "d-20260801-000000-000001": (
                "/docs/?scope=analysis&doc=report&subdoc=first"
            ),
            "d-20260801-000000-000003": (
                "/docs/?scope=analysis&doc=report&subdoc=third"
            ),
        },
        public_location_records=[
            {
                "scope_id": "analysis",
                "sub_scope": "tags",
                "doc_id": "d-20260801-000000-000001",
                "url": "/analysis/?doc=report&subdoc=first-b",
                "document_title": "First",
                "report_title": "Tags B",
            },
            {
                "scope_id": "analysis",
                "sub_scope": "tags",
                "doc_id": "d-20260801-000000-000001",
                "url": "/analysis/?doc=report&subdoc=first-a",
                "document_title": "First",
                "report_title": "Tags A",
            },
            {
                "scope_id": "analysis",
                "sub_scope": "works",
                "doc_id": "d-20260801-000000-000001",
                "url": "/analysis/?doc=works&subdoc=first",
                "document_title": "First",
                "report_title": "Works",
            },
        ],
    )

    assert generation.startswith("sha256:")
    assert payload == {
        "schema_version": "docs_tag_associations_v1",
        "scope": "analysis",
        "sub_scope": "tags",
        "declaration_generation": generation,
        "associations": [
            {
                "tag_id": "absence",
                "documents": [
                    {
                        "target": {
                            "scope": "analysis",
                            "sub_scope": "tags",
                            "doc_id": "d-20260801-000000-000001",
                        },
                        "title": "First",
                        "locations": [
                            {
                                "access": "manage",
                                "url": "/docs/?scope=analysis&doc=report&subdoc=first",
                                "title": "First",
                                "report_title": "",
                            },
                            {
                                "access": "public",
                                "url": "/analysis/?doc=report&subdoc=first-a",
                                "title": "First",
                                "report_title": "Tags A",
                            },
                            {
                                "access": "public",
                                "url": "/analysis/?doc=report&subdoc=first-b",
                                "title": "First",
                                "report_title": "Tags B",
                            },
                        ],
                    },
                    {
                        "target": {
                            "scope": "analysis",
                            "sub_scope": "tags",
                            "doc_id": "d-20260801-000000-000003",
                        },
                        "title": "Third",
                        "locations": [
                            {
                                "access": "manage",
                                "url": "/docs/?scope=analysis&doc=report&subdoc=third",
                                "title": "Third",
                                "report_title": "",
                            }
                        ],
                    },
                ],
            }
        ],
    }


def test_generation_changes_for_non_associated_malformed_evidence() -> None:
    first = tag_documents.tag_declaration_generation(
        scope="analysis",
        sub_scope="tags",
        declarations_by_doc_id={
            "doc": {"state": "malformed", "tag_id": "", "evidence": "bad_slug"}
        },
    )
    second = tag_documents.tag_declaration_generation(
        scope="analysis",
        sub_scope="tags",
        declarations_by_doc_id={
            "doc": {"state": "malformed", "tag_id": "", "evidence": True}
        },
    )
    assert first != second
