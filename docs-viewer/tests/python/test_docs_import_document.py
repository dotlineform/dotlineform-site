#!/usr/bin/env python3
"""Shared per-document Docs Import plan/apply tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from docs_import_content import (
    CONTENT_FORMAT_MARKDOWN,
    CONTENT_INTENT_EMPTY_NEW,
    CONTENT_INTENT_PRESERVE_EXISTING,
    CONTENT_INTENT_REPLACE,
    ImportContent,
)
from docs_import_document import (
    IMPORT_DOCUMENT_CREATE,
    IMPORT_DOCUMENT_OVERWRITE,
    apply_import_document,
    plan_import_document,
)
from docs_management_document_target import resolve_managed_document_collection
import docs_source_model as source_model

from docs_import_test_support import make_repo, write_library_doc
from repo_factory import docs_scope_record, docs_sub_scope_record, write_docs_scope_config


def import_content(**changes: object) -> ImportContent:
    fields: dict[str, object] = {
        "source_kind": "test-collection",
        "source_identity": "test-package",
        "record_identity": "record-1",
        "doc_id": "alpha",
        "title": "Alpha",
        "content_intent": CONTENT_INTENT_REPLACE,
        "content_format": CONTENT_FORMAT_MARKDOWN,
        "content": "# Alpha\n\nReplacement body.\n",
    }
    fields.update(changes)
    return ImportContent(**fields)  # type: ignore[arg-type]


def normalized_preview(record: ImportContent) -> dict[str, object]:
    return {
        "scope": "library",
        "source_format": "markdown",
        "title": record.title,
        "proposed_doc_id": record.doc_id,
        "markdown_preview": record.content,
        "media_plans": [],
    }


def test_projects_create_plan_accepts_only_custom_folder_path(
    external_data_sharing_workspace: Path,
) -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_docs_scope_config(
            root,
            [
                docs_scope_record(
                    "dotlineform",
                    scope_type="local_external",
                    sub_scopes=[
                        docs_sub_scope_record(
                            "dotlineform",
                            "projects",
                            sub_scope_customisation={
                                "id": "dotlineform_projects",
                                "settings": {},
                            },
                        )
                    ],
                )
            ],
        )
        source_root = (
            external_data_sharing_workspace.parent
            / "docs-viewer/scopes/dotlineform/source/sub-scopes/projects/documents"
        )
        source_root.mkdir(parents=True)
        collection = resolve_managed_document_collection(
            root,
            scope="dotlineform",
            sub_scope="projects",
        )
        record = import_content(
            doc_id="d-20260801-120000-a1b2c3",
            title="Architecture notes",
        )
        preview = {
            **normalized_preview(record),
            "scope": "dotlineform",
        }

        plan = plan_import_document(
            root,
            "dotlineform",
            record,
            operation=IMPORT_DOCUMENT_CREATE,
            docs=[],
            import_preview=preview,
            create_doc_id=record.doc_id,
            create_added_date="2026-08-01 12:00:00",
            collection=collection,
            custom_front_matter={"folder_path": "projects/architecture"},
        )
        front_matter, _body = source_model.parse_source_text(plan.source_text)

        with pytest.raises(ValueError, match="unknown fields"):
            plan_import_document(
                root,
                "dotlineform",
                record,
                operation=IMPORT_DOCUMENT_CREATE,
                docs=[],
                import_preview=preview,
                create_doc_id=record.doc_id,
                create_added_date="2026-08-01 12:00:00",
                collection=collection,
                custom_front_matter={"folder_path": "projects/architecture", "extra": "no"},
            )

    assert front_matter["folder_path"] == "projects/architecture"


def test_create_plan_applies_allowed_front_matter_and_empty_new_body() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        docs = source_model.load_scope_docs(root, "library")
        record = import_content(
            doc_id="new-parent",
            title="New Parent",
            content_intent=CONTENT_INTENT_EMPTY_NEW,
            content=None,
            parent_id="library",
            front_matter={
                "title": "New Parent",
                "parent_id": "library",
                "summary": "Structural parent.",
                "publishable": False,
                "children": ["ignored-child"],
            },
        )

        plan = plan_import_document(
            root,
            "library",
            record,
            operation=IMPORT_DOCUMENT_CREATE,
            docs=docs,
        )
        assert not plan.target_path.exists()
        apply_import_document(root, plan)
        front_matter, body = source_model.parse_source(plan.target_path)

    assert source_model.is_immutable_doc_id(plan.doc_id)
    assert plan.record.provenance["source_doc_id"] == "new-parent"
    assert plan.parent_id == "library"
    assert plan.publishable is False
    assert plan.search_doc_ids == (plan.doc_id,)
    assert front_matter["summary"] == "Structural parent."
    assert front_matter["publishable"] is False
    assert "children" not in front_matter
    assert body == ""


def test_preserve_existing_plan_changes_only_allowed_front_matter_and_keeps_body() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        write_library_doc(root, "parent.md", {"doc_id": "parent", "title": "Parent", "parent_id": ""})
        write_library_doc(
            root,
            "alpha.md",
            {
                "doc_id": "alpha",
                "title": "Old Alpha",
                "parent_id": "",
                "summary": "Old summary.",
                "ui_status": "active",
                "sort_order": 7,
                "custom_field": "preserve me",
                "publishable": False,
            },
            body="# Canonical Alpha\n\nKeep this exact canonical body.\n",
        )
        docs = source_model.load_scope_docs(root, "library")
        target = next(doc for doc in docs if doc.doc_id == "alpha")
        current_body = target.body
        record = import_content(
            title="Returned Alpha",
            content_intent=CONTENT_INTENT_PRESERVE_EXISTING,
            content=None,
            parent_id="parent",
            front_matter={
                "title": "Returned Alpha",
                "parent_id": "parent",
                "summary": "Returned summary.",
                "publishable": True,
                "children": ["ignored-child"],
            },
        )

        plan = plan_import_document(
            root,
            "library",
            record,
            operation=IMPORT_DOCUMENT_OVERWRITE,
            docs=docs,
            target=target,
        )
        planned_path = plan.target_path
        assert planned_path.read_text(encoding="utf-8") == target.source_text
        apply_import_document(root, plan)
        front_matter, body = source_model.parse_source(planned_path)

    assert body == current_body
    assert front_matter["title"] == "Returned Alpha"
    assert front_matter["parent_id"] == "parent"
    assert front_matter["summary"] == "Returned summary."
    assert front_matter["ui_status"] == "active"
    assert front_matter["sort_order"] == 7
    assert front_matter["custom_field"] == "preserve me"
    assert "publishable" not in front_matter
    assert "children" not in front_matter


def test_replace_plan_retains_single_source_overwrite_behavior() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        write_library_doc(root, "child.md", {"doc_id": "child", "title": "Child", "parent_id": "alpha"})
        write_library_doc(
            root,
            "alpha.md",
            {
                "doc_id": "alpha",
                "title": "Old Alpha",
                "parent_id": "",
                "sort_order": 3,
                "custom_field": "preserved",
            },
            body="# Old body\n",
        )
        docs = source_model.load_scope_docs(root, "library")
        target = next(doc for doc in docs if doc.doc_id == "alpha")
        record = import_content(title="New Alpha")

        plan = plan_import_document(
            root,
            "library",
            record,
            operation=IMPORT_DOCUMENT_OVERWRITE,
            docs=docs,
            target=target,
            import_preview=normalized_preview(record),
        )
        apply_import_document(root, plan)
        front_matter, body = source_model.parse_source(plan.target_path)

    assert "Replacement body." in body
    assert "Old body" not in body
    assert front_matter["custom_field"] == "preserved"
    assert "sort_order" not in front_matter
    assert plan.search_doc_ids == ("alpha", "child")


def test_replace_plan_normalizes_unicode_markdown_separators() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "alpha.md", {"doc_id": "alpha", "title": "Alpha", "parent_id": ""})
        docs = source_model.load_scope_docs(root, "library")
        target = next(doc for doc in docs if doc.doc_id == "alpha")
        record = import_content(content="# Alpha\n\nFirst\u2028Second\u2029Third\n")

        plan = plan_import_document(
            root,
            "library",
            record,
            operation=IMPORT_DOCUMENT_OVERWRITE,
            docs=docs,
            target=target,
            import_preview=normalized_preview(record),
        )
        _front_matter, body = source_model.parse_source_text(plan.source_text)

    assert body == "# Alpha\n\nFirst  \nSecond\n\nThird\n"


@pytest.mark.parametrize(
    ("record", "operation", "with_target", "message"),
    [
        (
            import_content(
                doc_id="preserved-without-target",
                content_intent=CONTENT_INTENT_PRESERVE_EXISTING,
                content=None,
            ),
            IMPORT_DOCUMENT_CREATE,
            False,
            "preserve-existing content requires an existing import target",
        ),
        (
            import_content(content_intent=CONTENT_INTENT_EMPTY_NEW, content=None),
            IMPORT_DOCUMENT_OVERWRITE,
            True,
            "empty-new content cannot overwrite an existing import target",
        ),
    ],
)
def test_content_intent_must_match_create_or_overwrite_target(
    record: ImportContent,
    operation: str,
    with_target: bool,
    message: str,
) -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        if with_target:
            write_library_doc(root, "alpha.md", {"doc_id": "alpha", "title": "Alpha", "parent_id": ""})
        docs = source_model.load_scope_docs(root, "library")
        target = next(doc for doc in docs if doc.doc_id == "alpha") if with_target else None

        with pytest.raises(ValueError, match=message):
            plan_import_document(
                root,
                "library",
                record,
                operation=operation,
                docs=docs,
                target=target,
            )


def test_plan_rejects_ambiguous_parent_metadata() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        docs = source_model.load_scope_docs(root, "library")
        record = import_content(parent_id="library", front_matter={"parent_id": "other"})

        with pytest.raises(ValueError, match="parent_id must match"):
            plan_import_document(
                root,
                "library",
                record,
                operation=IMPORT_DOCUMENT_CREATE,
                docs=docs,
                import_preview=normalized_preview(record),
            )


@pytest.mark.parametrize(
    ("front_matter", "message"),
    [
        ({"title": "Different"}, "title must match"),
        ({"summary": ["not", "text"]}, "summary must be a string"),
        ({"publishable": "false"}, "publishable must be a boolean"),
    ],
)
def test_plan_rejects_invalid_allowed_front_matter(
    front_matter: dict[str, object],
    message: str,
) -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        docs = source_model.load_scope_docs(root, "library")
        record = import_content(doc_id="valid-new-doc", front_matter=front_matter)

        with pytest.raises(ValueError, match=message):
            plan_import_document(
                root,
                "library",
                record,
                operation=IMPORT_DOCUMENT_CREATE,
                docs=docs,
                import_preview=normalized_preview(record),
            )


def test_create_plan_treats_external_identity_as_provenance_not_a_local_path() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        docs = source_model.load_scope_docs(root, "library")
        record = import_content(doc_id="../outside")

        plan = plan_import_document(
            root,
            "library",
            record,
            operation=IMPORT_DOCUMENT_CREATE,
            docs=docs,
            import_preview=normalized_preview(record),
        )

    assert source_model.is_immutable_doc_id(plan.doc_id)
    assert plan.record.provenance["source_doc_id"] == "../outside"
    assert plan.target_path.parent.name == "documents"


def test_create_apply_refuses_a_target_that_appeared_after_planning() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        docs = source_model.load_scope_docs(root, "library")
        record = import_content(doc_id="new-document")
        plan = plan_import_document(
            root,
            "library",
            record,
            operation=IMPORT_DOCUMENT_CREATE,
            docs=docs,
            import_preview=normalized_preview(record),
        )
        plan.target_path.write_text("appeared after planning\n", encoding="utf-8")

        with pytest.raises(FileExistsError, match="source path already exists"):
            apply_import_document(root, plan)

        assert plan.target_path.read_text(encoding="utf-8") == "appeared after planning\n"
