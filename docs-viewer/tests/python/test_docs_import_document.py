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
from docs_scope_config import load_docs_scope_configs, select_scope_stage
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
    return {"stage": "working",
        "scope": "example",
        "source_format": "markdown",
        "title": record.title,
        "proposed_doc_id": record.doc_id,
        "markdown_preview": record.content,
        "media_plans": [],
    }


def test_working_works_create_plan_accepts_only_custom_folder_path(
    external_data_sharing_workspace: Path,
) -> None:
    with make_repo() as temp:
        root = Path(temp)
        from copy import deepcopy
        from docs_scope_config import document_source_path, load_docs_scope_stage

        scope = docs_scope_record("analysis")
        scope["stages"] = {
            stage: {
                "media": deepcopy(scope["media"]),
                "sub_scopes": [docs_sub_scope_record("analysis", "works", sub_scope_customisation={
                    "id": "working_works" if stage == "working" else "pre_publish_works", "settings": {},
                })],
            }
            for stage in ("working", "pre-publish")
        }
        write_docs_scope_config(root, [scope])
        config = load_docs_scope_stage(root, "analysis", "working")
        source_root = root / document_source_path(config.sub_scopes[0])
        source_root.mkdir(parents=True)
        collection = resolve_managed_document_collection(root, scope="analysis", stage="working", sub_scope="works")
        record = import_content(
            doc_id="d-20260801-120000-a1b2c3",
            title="Architecture notes",
        )
        preview = {"stage": "working",
            **normalized_preview(record),
            "scope": "analysis",
        }

        plan = plan_import_document(
            root,
            "analysis",
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
                "analysis",
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
                ":::\n"
            ),
        )
        config = select_scope_stage(load_docs_scope_configs(root)["example"], "working")
        monkeypatch.setitem(source_model.DOCS_SCOPE_CONFIGS, "example", config)
        docs = source_model.load_scope_docs_for_config(root, config)
        target = next(doc for doc in docs if doc.doc_id == "alpha")
        overwrite = import_content()
        incoming = import_content(
            doc_id="incoming-report",
            content=(
                "# Incoming\n\n"
                ":::report\n"
                "id: reports_list\n"
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
                collection=resolve_managed_document_collection(root, scope="example", stage="working"),
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
                collection=resolve_managed_document_collection(root, scope="example", stage="working"),
                import_preview=normalized_preview(incoming),
            )
