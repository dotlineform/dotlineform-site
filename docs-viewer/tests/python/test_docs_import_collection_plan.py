#!/usr/bin/env python3
"""Write-free Data Sharing documents collection-plan tests."""

from __future__ import annotations

import json
from pathlib import Path

import docs_import_preview
import pytest
from docs_import_data_sharing_documents import plan_data_sharing_documents_collection
from services.paths import configured_workspace_paths

from docs_import_test_support import handle_import_source, make_repo, write_staged
from repo_factory import data_sharing_workspace_root


def write_collection_metadata(
    export_id: str,
    *,
    profile_id: str = "document-content",
    content_format: str = "markdown",
) -> None:
    path = data_sharing_workspace_root() / "meta" / f"{export_id}.meta.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "data_sharing_export_meta_v1",
                "export_id": export_id,
                "app": "docs-viewer",
                "adapter_id": "documents",
                "data_domain": "library",
                "scope": "library",
                "profile_id": profile_id,
                "config_id": profile_id,
                "target_format": "jsonl",
                "record_shape": "document_rows",
                "supports_return_import": True,
                "content_format": content_format,
            }
        )
        + "\n",
        encoding="utf-8",
    )


def stub_markdown_validation(monkeypatch) -> None:
    monkeypatch.setattr(
        docs_import_preview,
        "validate_markdown_preview",
        lambda markdown, *, title="": {
            "ok": True,
            "html_chars": len(markdown),
            "renderer": "stub",
        },
    )


def files_snapshot(*roots: Path) -> dict[str, bytes]:
    snapshot: dict[str, bytes] = {}
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if path.is_file():
                snapshot[f"{root.name}/{path.relative_to(root).as_posix()}"] = path.read_bytes()
    return snapshot


def plan_package(root: Path, filename: str):
    paths = configured_workspace_paths(root)
    return plan_data_sharing_documents_collection(
        root,
        scope="library",
        staged_filename=filename,
        staging_root=paths.import_staging,
        workspace_root=paths.root,
        metadata_root=paths.meta,
    )


def test_collection_preview_dispatches_through_existing_import_post(monkeypatch) -> None:
    stub_markdown_validation(monkeypatch)
    with make_repo() as temp:
        root = Path(temp)
        export_id = "ds_20260712T150001Z"
        write_collection_metadata(export_id)
        write_staged(
            root,
            "post-preview.jsonl",
            [
                {"record_type": "data_sharing_header", "export_id": export_id},
                {"doc_id": "post-preview", "title": "POST Preview", "content": "Body."},
            ],
        )

        payload = handle_import_source(
            root,
            {
                "scope": "library",
                "staged_filename": "post-preview.jsonl",
                "preview_only": True,
            },
            False,
        )
        with pytest.raises(ValueError, match="preview_only false"):
            handle_import_source(
                root,
                {
                    "scope": "library",
                    "staged_filename": "post-preview.jsonl",
                },
                False,
            )

    assert payload["collection"] is True
    assert payload["source_format"] == "data_sharing_documents"
    assert payload["preview_only"] is True
    assert payload["counts"]["records"] == 1


def test_collection_plan_covers_every_record_collision_parent_and_media_without_writes(monkeypatch) -> None:
    stub_markdown_validation(monkeypatch)
    with make_repo() as temp:
        root = Path(temp)
        export_id = "ds_20260712T130000Z"
        write_collection_metadata(export_id)
        write_staged(
            root,
            "collection.jsonl",
            [
                {
                    "record_type": "data_sharing_header",
                    "schema_version": "data_sharing_returned_package_v1",
                    "export_id": export_id,
                },
                {"doc_id": "new-parent", "title": "New Parent", "parent_id": ""},
                {
                    "doc_id": "beta",
                    "title": "Beta",
                    "parent_id": "new-parent",
                    "content": (
                        "# Beta\n\n[Keep this link](../alpha/)\n\n"
                        "![Diagram](data:image/png;base64,aGVsbG8=)\n"
                    ),
                    "links": [{"target": "../alpha/"}],
                    "assets": [
                        {
                            "asset_id": "asset-1",
                            "kind": "image",
                            "package_path": "assets/media/diagram.webp",
                            "source_token": "[[media:docs/library/img/diagram.webp]]",
                        }
                    ],
                },
                {"doc_id": "alpha", "title": "Alpha", "parent_id": "new-parent"},
            ],
        )
        paths = configured_workspace_paths(root)
        before = files_snapshot(
            root / "docs-viewer/source/library",
            paths.import_staging,
        )

        plan = plan_package(root, "collection.jsonl")
        payload = plan.as_dict()
        after = files_snapshot(
            root / "docs-viewer/source/library",
            paths.import_staging,
        )

    assert before == after
    assert payload["ok"] is True
    assert payload["ready_for_confirmation"] is False
    assert payload["requires_decisions"] is True
    assert payload["counts"] == {
        "records": 3,
        "creates": 2,
        "collisions": 1,
        "record_errors": 0,
        "media_plans": 1,
        "warnings": 2,
        "blockers": 0,
    }
    assert [record["action"] for record in payload["records"]] == [
        "create",
        "create",
        "decision-required",
    ]
    assert [record["content_intent"] for record in payload["records"]] == [
        "empty-new",
        "replace",
        "preserve-existing",
    ]
    assert payload["records"][2]["decision_kind"] == "collision"
    assert payload["records"][2]["allowed_actions"] == ["overwrite", "skip", "cancel"]
    assert payload["records"][2]["collision"]["doc_id"] == "alpha"
    new_parent_id = payload["records"][0]["doc_id"]
    beta_id = payload["records"][1]["doc_id"]
    assert payload["records"][0]["source_doc_id"] == "new-parent"
    assert payload["records"][1]["source_doc_id"] == "beta"
    assert payload["records"][1]["parent"] == {
        "parent_id": new_parent_id,
        "resolution": "package-create",
        "record_index": 0,
    }
    assert payload["records"][1]["link_count"] == 1
    assert payload["records"][1]["media_plans"][0]["source"] == "inline_data_url"
    assert payload["records"][1]["declared_asset_plans"][0]["status"] == "mapping-required"
    assert payload["new_parent_dependencies"] == [
        {"doc_id": beta_id, "record_index": 1, "parent_id": new_parent_id, "parent_record_index": 0},
        {"doc_id": "alpha", "record_index": 2, "parent_id": new_parent_id, "parent_record_index": 0},
    ]
    serialized = json.dumps(payload)
    assert "Keep this link" not in serialized
    assert "markdown_preview" not in serialized
    assert "source_text" not in serialized
    assert str(root) not in serialized
    assert str(paths.root) not in serialized
    assert all(item is not None for item in plan.document_plans)
    assert "[Keep this link](../alpha/)" in plan.document_plans[1].source_text
    assert not any("link" in warning["message"].lower() for warning in payload["records"][1]["warnings"])


def test_collection_plan_resolves_multi_level_new_parents_without_reordering() -> None:
    with make_repo() as temp:
        root = Path(temp)
        export_id = "ds_20260712T130008Z"
        write_collection_metadata(export_id)
        write_staged(
            root,
            "parent-chain.jsonl",
            [
                {"record_type": "data_sharing_header", "export_id": export_id},
                {"doc_id": "child", "title": "Child", "parent_id": "parent"},
                {"doc_id": "parent", "title": "Parent", "parent_id": "grandparent"},
                {"doc_id": "grandparent", "title": "Grandparent", "parent_id": ""},
            ],
        )

        payload = plan_package(root, "parent-chain.jsonl").as_dict()

    assert payload["ok"] is True
    assert payload["ready_for_confirmation"] is True
    child_id, parent_id, grandparent_id = [record["doc_id"] for record in payload["records"]]
    assert [record["source_doc_id"] for record in payload["records"]] == ["child", "parent", "grandparent"]
    assert payload["new_parent_dependencies"] == [
        {"doc_id": child_id, "record_index": 0, "parent_id": parent_id, "parent_record_index": 1},
        {"doc_id": parent_id, "record_index": 1, "parent_id": grandparent_id, "parent_record_index": 2},
    ]


def test_collection_plan_blocks_missing_parents_and_hierarchy_cycles(monkeypatch) -> None:
    stub_markdown_validation(monkeypatch)
    with make_repo() as temp:
        root = Path(temp)
        export_id = "ds_20260712T130001Z"
        write_collection_metadata(export_id)
        write_staged(
            root,
            "invalid-hierarchy.jsonl",
            [
                {"record_type": "data_sharing_header", "export_id": export_id},
                {"doc_id": "orphan", "title": "Orphan", "parent_id": "missing", "content": "Body."},
                {"doc_id": "cycle-a", "title": "Cycle A", "parent_id": "cycle-b", "content": "A."},
                {"doc_id": "cycle-b", "title": "Cycle B", "parent_id": "cycle-a", "content": "B."},
            ],
        )

        payload = plan_package(root, "invalid-hierarchy.jsonl").as_dict()

    assert payload["ok"] is True
    assert payload["plan_valid"] is False
    assert payload["ready_for_confirmation"] is False
    assert {blocker["code"] for blocker in payload["blockers"]} == {
        "missing_parent",
        "hierarchy_cycle",
    }
    assert payload["records"][0]["parent"]["resolution"] == "missing"


def test_collection_plan_blocks_malformed_or_unsafe_record_identity(monkeypatch) -> None:
    stub_markdown_validation(monkeypatch)
    with make_repo() as temp:
        root = Path(temp)
        export_id = "ds_20260712T130002Z"
        write_collection_metadata(export_id)
        write_staged(
            root,
            "unsafe-records.jsonl",
            [
                {"record_type": "data_sharing_header", "export_id": export_id},
                {"doc_id": "../outside", "title": "Outside", "content": "Body."},
                {"doc_id": "same", "title": "Same", "content": "Body."},
                {"doc_id": "same", "title": "Duplicate", "content": "Body."},
                {"doc_id": "missing-title", "content": "Body."},
            ],
        )

        payload = plan_package(root, "unsafe-records.jsonl").as_dict()

    assert payload["ok"] is True
    assert payload["plan_valid"] is False
    assert {blocker["code"] for blocker in payload["blockers"]} >= {
        "unsafe_doc_id",
        "duplicate_doc_id",
        "missing_title",
    }
    assert len(payload["records"]) == 4
    assert payload["records"][3]["action"] == "blocked"


def test_collection_plan_keeps_invalid_front_matter_as_explicit_record_decision(monkeypatch) -> None:
    stub_markdown_validation(monkeypatch)
    with make_repo() as temp:
        root = Path(temp)
        export_id = "ds_20260712T130003Z"
        write_collection_metadata(export_id)
        write_staged(
            root,
            "invalid-front-matter.jsonl",
            [
                {"record_type": "data_sharing_header", "export_id": export_id},
                {
                    "doc_id": "invalid-metadata",
                    "title": "Invalid Metadata",
                    "viewable": "false",
                    "content": "Body.",
                },
            ],
        )

        payload = plan_package(root, "invalid-front-matter.jsonl").as_dict()

    assert payload["ok"] is True
    assert payload["counts"]["blockers"] == 0
    assert payload["counts"]["record_errors"] == 1
    record = payload["records"][0]
    assert record["action"] == "decision-required"
    assert record["decision_kind"] == "invalid-record"
    assert record["allowed_actions"] == ["skip", "cancel"]
    assert record["errors"][0]["code"] == "invalid_front_matter"


def test_collection_plan_preserves_existing_parent_when_parent_is_omitted() -> None:
    with make_repo() as temp:
        root = Path(temp)
        export_id = "ds_20260712T130007Z"
        write_collection_metadata(export_id)
        write_staged(
            root,
            "preserve-parent.jsonl",
            [
                {"record_type": "data_sharing_header", "export_id": export_id},
                {"doc_id": "alpha", "title": "Alpha"},
            ],
        )

        payload = plan_package(root, "preserve-parent.jsonl").as_dict()

    assert payload["ok"] is True
    assert payload["records"][0]["content_intent"] == "preserve-existing"
    assert payload["records"][0]["parent"] == {
        "parent_id": "library",
        "resolution": "existing",
        "record_index": None,
    }


def test_collection_plan_keeps_unsupported_content_format_as_record_decision() -> None:
    with make_repo() as temp:
        root = Path(temp)
        export_id = "ds_20260712T130004Z"
        write_collection_metadata(export_id, content_format="docx")
        write_staged(
            root,
            "unsupported-format.jsonl",
            [
                {"record_type": "data_sharing_header", "export_id": export_id},
                {"doc_id": "unsupported", "title": "Unsupported", "content": "Body."},
            ],
        )

        plan = plan_package(root, "unsupported-format.jsonl")
        payload = plan.as_dict()

    assert payload["ok"] is True
    assert payload["counts"]["record_errors"] == 1
    assert payload["records"][0]["errors"][0]["code"] == "unsupported_content_format"
    assert payload["records"][0]["allowed_actions"] == ["skip", "cancel"]
    assert plan.normalized_records == (None,)
    assert plan.document_plans == (None,)


def test_collection_plan_accepts_full_source_title_from_canonical_front_matter(monkeypatch) -> None:
    stub_markdown_validation(monkeypatch)
    with make_repo() as temp:
        root = Path(temp)
        export_id = "ds_20260712T130005Z"
        write_collection_metadata(export_id, profile_id="document-full-source")
        write_staged(
            root,
            "full-source.jsonl",
            [
                {
                    "record_type": "data_sharing_header",
                    "schema_version": "documents_full_package_v1",
                    "export_id": export_id,
                },
                {
                    "record_type": "document",
                    "doc_id": "full-source-doc",
                    "canonical_markdown": (
                        "---\n"
                        "doc_id: full-source-doc\n"
                        "title: Full Source Doc\n"
                        "parent_id: library\n"
                        "---\n"
                        "# Full Source Doc\n\nBody.\n"
                    ),
                },
            ],
        )

        payload = plan_package(root, "full-source.jsonl").as_dict()

    assert payload["ok"] is True
    assert payload["ready_for_confirmation"] is True
    assert payload["records"][0]["title"] == "Full Source Doc"
    assert payload["records"][0]["action"] == "create"
    assert payload["records"][0]["parent"]["resolution"] == "existing"


def test_collection_plan_rejects_missing_trusted_export_metadata() -> None:
    with make_repo() as temp:
        root = Path(temp)
        export_id = "ds_20260712T130006Z"
        write_staged(
            root,
            "missing-metadata.jsonl",
            [
                {"record_type": "data_sharing_header", "export_id": export_id},
                {"doc_id": "new-doc", "title": "New Doc", "content": "Body."},
            ],
        )

        payload = plan_package(root, "missing-metadata.jsonl").as_dict()

    assert payload["ok"] is True
    assert payload["plan_valid"] is False
    assert payload["records"] == []
    assert [blocker["code"] for blocker in payload["blockers"]] == ["missing_export_metadata"]
