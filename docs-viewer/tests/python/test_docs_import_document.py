#!/usr/bin/env python3
"""Shared per-document Docs Import plan/apply tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from docs_import_content import (
    CONTENT_FORMAT_MARKDOWN,
    CONTENT_INTENT_REPLACE,
    ImportContent,
)
from docs_import_document import (
    IMPORT_DOCUMENT_CREATE,
    IMPORT_DOCUMENT_OVERWRITE,
    plan_import_document,
)
from docs_management_document_target import resolve_managed_document_collection
from docs_scope_config import load_docs_scope_configs
import docs_source_model as source_model

from docs_import_test_support import make_repo, write_example_doc
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
        "scope": "example",
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


def test_import_rejects_report_host_targets_and_incoming_report_blocks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_example_doc(
            root,
            "alpha.md",
            {"doc_id": "alpha", "title": "Alpha", "parent_id": ""},
            body=(
                "# Alpha\n\n"
                ":::report\n"
                "id: reports_list\n"
                "access: public\n"
                ":::\n"
            ),
        )
        config = load_docs_scope_configs(root)["example"]
        monkeypatch.setitem(source_model.DOCS_SCOPE_CONFIGS, "example", config)
        monkeypatch.setitem(
            source_model.DOCUMENT_SOURCE_ROOTS,
            "example",
            root / "docs-viewer/scopes/example/source/documents",
        )
        docs = source_model.load_scope_docs_for_config(root, config)
        target = next(doc for doc in docs if doc.doc_id == "alpha")
        overwrite = import_content()
        incoming = import_content(
            doc_id="incoming-report",
            content=(
                "# Incoming\n\n"
                ":::report\n"
                "id: reports_list\n"
                "access: public\n"
                ":::\n"
            ),
        )

        with pytest.raises(ValueError, match="cannot replace a report-host"):
            plan_import_document(
                root,
                "example",
                overwrite,
                operation=IMPORT_DOCUMENT_OVERWRITE,
                docs=docs,
                target=target,
                import_preview=normalized_preview(overwrite),
            )
        with pytest.raises(ValueError, match="cannot create report-host"):
            plan_import_document(
                root,
                "example",
                incoming,
                operation=IMPORT_DOCUMENT_CREATE,
                docs=docs,
                import_preview=normalized_preview(incoming),
            )
