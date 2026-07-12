#!/usr/bin/env python3
"""Data Sharing documents to ImportContent adapter tests."""

from __future__ import annotations

import pytest

from adapters.documents.returned import normalize_documents_import_content
from docs_import_content import (
    CONTENT_INTENT_EMPTY_NEW,
    CONTENT_INTENT_PRESERVE_EXISTING,
    CONTENT_INTENT_REPLACE,
)


def compact_metadata(**changes: object) -> dict[str, object]:
    metadata: dict[str, object] = {
        "schema_version": "data_sharing_returned_package_v1",
        "export_id": "ds_20260712T120000Z",
        "profile_id": "document-content",
        "scope": "library",
        "content_format": "markdown",
    }
    metadata.update(changes)
    return metadata


def full_source_metadata(**changes: object) -> dict[str, object]:
    metadata: dict[str, object] = {
        "schema_version": "documents_full_package_v1",
        "export_id": "ds_20260712T120000Z",
        "profile_id": "document-full-source",
        "scope": "library",
    }
    metadata.update(changes)
    return metadata


def test_compact_content_uses_only_explicit_profile_mapping() -> None:
    batch = normalize_documents_import_content(
        [
            {
                "doc_id": "alpha",
                "title": "Alpha",
                "parent_id": "library",
                "summary": "Returned summary.",
                "content": "# Alpha\n\nReturned body.\n",
                "arbitrary_body": "must not be imported",
            }
        ],
        package_metadata=compact_metadata(),
        current_doc_ids={"alpha"},
        staged_filename="returned.jsonl",
    )

    record = batch.records[0]
    assert record.content_intent == CONTENT_INTENT_REPLACE
    assert record.content_format == "markdown"
    assert record.content == "# Alpha\n\nReturned body.\n"
    assert record.front_matter == {
        "title": "Alpha",
        "parent_id": "library",
        "summary": "Returned summary.",
    }
    assert record.provenance["export_id"] == "ds_20260712T120000Z"
    assert any(item["code"] == "unmapped_fields_ignored" for item in record.diagnostics)


def test_compact_plain_text_preserves_declared_content_format() -> None:
    batch = normalize_documents_import_content(
        [{"doc_id": "alpha", "title": "Alpha", "content": "Plain body."}],
        package_metadata=compact_metadata(content_format="plain_text"),
    )

    assert batch.records[0].content_format == "plain_text"
    assert batch.records[0].content == "Plain body."


def test_full_source_parses_canonical_front_matter_once_and_excludes_it_from_body() -> None:
    canonical = """---
doc_id: alpha
title: Canonical Alpha
parent_id: library
summary: Canonical summary.
added_date: 2026-01-01
custom_field: not-importable
---
# Canonical Alpha

Returned body.
"""
    batch = normalize_documents_import_content(
        [
            {
                "record_type": "document",
                "doc_id": "alpha",
                "document": {"title": "Duplicated title", "parent_id": "wrong-parent"},
                "canonical_markdown": canonical,
                "assets": [{"asset_id": "asset-1", "kind": "image"}],
            }
        ],
        package_metadata=full_source_metadata(),
        current_doc_ids={"alpha"},
    )

    record = batch.records[0]
    assert record.content_intent == CONTENT_INTENT_REPLACE
    assert record.title == "Canonical Alpha"
    assert record.parent_id == "library"
    assert record.content == "# Canonical Alpha\n\nReturned body.\n"
    assert record.front_matter == {
        "title": "Canonical Alpha",
        "parent_id": "library",
        "summary": "Canonical summary.",
    }
    assert record.assets == ({"asset_id": "asset-1", "kind": "image"},)
    assert len([item for item in record.diagnostics if item["code"] == "duplicated_metadata_ignored"]) == 2


def test_omitted_content_retains_preserve_existing_and_empty_new_intent() -> None:
    batch = normalize_documents_import_content(
        [
            {"doc_id": "alpha", "title": "Existing Alpha", "parent_id": "library"},
            {"doc_id": "new-parent", "title": "New Parent", "parent_id": ""},
        ],
        package_metadata=compact_metadata(),
        current_doc_ids={"alpha"},
    )

    existing, new = batch.records
    assert existing.content_intent == CONTENT_INTENT_PRESERVE_EXISTING
    assert existing.content is None
    assert new.content_intent == CONTENT_INTENT_EMPTY_NEW
    assert new.content is None

    trusted_missing = normalize_documents_import_content(
        [{"doc_id": "exported-but-missing", "title": "Exported"}],
        package_metadata=compact_metadata(selected_doc_ids=["exported-but-missing"]),
        current_doc_ids=set(),
    ).records[0]
    assert trusted_missing.content_intent == CONTENT_INTENT_PRESERVE_EXISTING


def test_adapter_rejects_unmapped_or_ambiguous_wrapper_contracts() -> None:
    with pytest.raises(ValueError, match="unsupported Data Sharing documents import contract"):
        normalize_documents_import_content(
            [{"doc_id": "alpha", "title": "Alpha", "content": "Body"}],
            package_metadata={"export_id": "ds_1"},
        )
    with pytest.raises(ValueError, match="must not supply both"):
        normalize_documents_import_content(
            [
                {
                    "doc_id": "alpha",
                    "title": "Alpha",
                    "content": "Body",
                    "canonical_markdown": "Body",
                }
            ],
            package_metadata=compact_metadata(),
        )
    with pytest.raises(ValueError, match="does not match normalized intent"):
        normalize_documents_import_content(
            [
                {
                    "doc_id": "alpha",
                    "title": "Alpha",
                    "content_intent": "replace",
                }
            ],
            package_metadata=compact_metadata(),
        )


def test_full_source_rejects_identity_mismatch_and_duplicate_front_matter() -> None:
    with pytest.raises(ValueError, match="does not match"):
        normalize_documents_import_content(
            [
                {
                    "record_type": "document",
                    "doc_id": "alpha",
                    "canonical_markdown": "---\ndoc_id: beta\ntitle: Beta\n---\n# Beta\n",
                }
            ],
            package_metadata=full_source_metadata(),
        )
    with pytest.raises(ValueError, match="duplicate front matter"):
        normalize_documents_import_content(
            [
                {
                    "record_type": "document",
                    "doc_id": "alpha",
                    "canonical_markdown": "---\ndoc_id: alpha\ntitle: Alpha\ntitle: Again\n---\n# Alpha\n",
                }
            ],
            package_metadata=full_source_metadata(),
        )
