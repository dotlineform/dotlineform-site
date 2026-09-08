"""Destination-owned source membership, with no generated payload contract."""

from pathlib import Path

import pytest

import docs_source_model as source_model
from docs_import_content import CONTENT_FORMAT_MARKDOWN, CONTENT_INTENT_REPLACE, ImportContent
from docs_import_document import IMPORT_DOCUMENT_CREATE, IMPORT_DOCUMENT_OVERWRITE, plan_import_document
from docs_management_document_target import resolve_managed_document_collection
from repo_factory import docs_scope_record, docs_sub_scope_record, write_docs_scope_config, write_site_tools_config


@pytest.mark.parametrize("sub_scope", ["", "concepts", "arbitrary-collection"])
@pytest.mark.parametrize("incoming", [None, "", "wrong-collection", ["untrusted"]])
def test_source_membership_uses_destination_and_preserves_other_bytes(sub_scope, incoming):
    original = source_model.format_source({"doc_id": "sample", "title": "Sample", "sub-scope": incoming}, "# Body\n\nTail")
    rewritten = source_model.rewrite_source_sub_scope(original, sub_scope)
    before, body = source_model.parse_source_text(original)
    after, after_body = source_model.parse_source_text(rewritten)
    assert after_body == body
    assert {k: v for k, v in after.items() if k != "sub-scope"} == {k: v for k, v in before.items() if k != "sub-scope"}
    assert after.get("sub-scope") == (sub_scope or None)
    assert source_model.rewrite_source_sub_scope(rewritten, sub_scope) == rewritten
    assert rewritten.endswith("Tail")


@pytest.mark.parametrize("sub_scope", ["", "concepts", "moments"])
@pytest.mark.parametrize("operation", [IMPORT_DOCUMENT_CREATE, IMPORT_DOCUMENT_OVERWRITE])
def test_import_membership_comes_from_resolved_destination(tmp_path: Path, sub_scope: str, operation: str):
    write_site_tools_config(tmp_path)
    write_docs_scope_config(tmp_path, [docs_scope_record("custom", sub_scopes=[docs_sub_scope_record("custom", name) for name in ("concepts", "moments")])])
    scope_root = tmp_path / "docs-viewer/scopes/custom/source"
    (scope_root / "documents").mkdir(parents=True)
    for name in ("concepts", "moments"):
        (scope_root / "sub-scopes" / name / "documents").mkdir(parents=True)
    collection = resolve_managed_document_collection(tmp_path, scope="custom", sub_scope=sub_scope or None)
    doc_id = "d-20260908-190000-abcdef"
    target = None
    if operation == IMPORT_DOCUMENT_OVERWRITE:
        (collection.source_root / f"{doc_id}.md").write_text(source_model.format_source({
            "doc_id": doc_id, "title": "Before", "added_date": "2026-09-08 19:00:00", "sub-scope": "stale-collection",
        }, "# Before\n"), encoding="utf-8")
        target = source_model.load_document_collection_docs_for_config(tmp_path, collection.parent_config, collection.document_config)[0]
    record = ImportContent(
        source_kind="test", source_identity="source", record_identity="record", doc_id=doc_id,
        title="Imported", content_intent=CONTENT_INTENT_REPLACE, content_format=CONTENT_FORMAT_MARKDOWN,
        content="# Imported\n", front_matter={"sub-scope": "incoming-collection"},
    )
    plan = plan_import_document(
        tmp_path, "custom", record, operation=operation, docs=[target] if target else [], target=target,
        import_preview={"markdown_preview": record.content, "media_plans": []}, collection=collection,
        create_doc_id=doc_id, create_added_date="2026-09-08 19:00:00",
    )
    fields, body = source_model.parse_source_text(plan.source_text)
    assert fields.get("sub-scope") == (sub_scope or None)
    assert fields["doc_id"] == doc_id
    assert body == "# Imported\n"
