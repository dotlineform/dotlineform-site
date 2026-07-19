#!/usr/bin/env python3
"""Docs Import collection apply, revalidation, and result contract tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import docs_import_collection_apply as collection_apply
import docs_import_collection_decisions as collection_decisions
from docs_import_collection_result import safe_generation_result
import docs_import_preview
import docs_source_model
import docs_write_rebuild
from docs_import_data_sharing_documents import (
    apply_data_sharing_documents_collection,
    plan_data_sharing_documents_collection,
)
from services.paths import configured_workspace_paths

from docs_import_test_support import handle_import_source, make_repo, write_library_doc, write_staged
from repo_factory import data_sharing_workspace_root


def write_collection_metadata(export_id: str) -> None:
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
                "profile_id": "document-content",
                "config_id": "document-content",
                "target_format": "jsonl",
                "record_shape": "document_rows",
                "supports_return_import": True,
                "content_format": "markdown",
            }
        )
        + "\n",
        encoding="utf-8",
    )


def write_collection(root: Path, filename: str, records: list[dict[str, object]], export_id: str) -> None:
    write_collection_metadata(export_id)
    write_staged(
        root,
        filename,
        [{"record_type": "data_sharing_header", "export_id": export_id}, *records],
    )


def stub_markdown_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        docs_import_preview,
        "validate_markdown_preview",
        lambda markdown, *, title="": {"ok": True, "html_chars": len(markdown), "renderer": "stub"},
    )


def fake_rebuild(calls: list[dict[str, object]], *, fail_generation: bool = False):
    def perform(repo_root, scope, changed_paths, write_operation, **kwargs):
        write_operation()
        calls.append(
            {
                "scope": scope,
                "changed_paths": [path.name for path in changed_paths],
                "docs_doc_ids": list(kwargs.get("docs_doc_ids") or []),
                "search_doc_ids": list(kwargs.get("search_doc_ids") or []),
            }
        )
        if fail_generation:
            raise RuntimeError("simulated generation failure")
        return {
            "ok": True,
            "docs": {"mode": "targeted", "doc_ids": list(kwargs.get("docs_doc_ids") or [])},
            "search": {"mode": "targeted", "doc_ids": list(kwargs.get("search_doc_ids") or [])},
        }

    return perform


def apply_package(
    root: Path,
    filename: str,
    decisions: list[dict[str, object]],
    *,
    rebuild,
    logs: list[tuple[str, dict[str, object]]] | None = None,
    export_id: str | None = None,
    source_sha256: str | None = None,
) -> dict[str, object]:
    paths = configured_workspace_paths(root)
    preview = plan_data_sharing_documents_collection(
        root,
        scope="library",
        staged_filename=filename,
        staging_root=paths.import_staging,
        workspace_root=paths.root,
        metadata_root=paths.meta,
    ).as_dict()
    return apply_data_sharing_documents_collection(
        root,
        scope="library",
        staged_filename=filename,
        body={
            "scope": "library",
            "staged_filename": filename,
            "preview_only": False,
            "confirm": True,
            "decisions": decisions,
            "planned_identities": preview.get("planned_identities", []),
            "export_id": export_id if export_id is not None else preview.get("package", {}).get("export_id", ""),
            "source_sha256": source_sha256 if source_sha256 is not None else preview.get("package", {}).get("source_sha256", ""),
        },
        staging_root=paths.import_staging,
        workspace_root=paths.root,
        metadata_root=paths.meta,
        log_event=lambda _root, event, details: (logs.append((event, details)) if logs is not None else None),
        perform_source_write_and_rebuild=rebuild,
    )


def test_collection_apply_creates_overwrites_skips_reports_and_rebuilds_once(monkeypatch) -> None:
    stub_markdown_validation(monkeypatch)
    rebuild_calls: list[dict[str, object]] = []
    logs: list[tuple[str, dict[str, object]]] = []
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(
            root,
            "alpha.md",
            {"doc_id": "alpha", "title": "Old Alpha", "parent_id": "", "added_date": "2020-01-01"},
            body="# Old Alpha\n\nOld body.\n",
        )
        write_collection(
            root,
            "apply.jsonl",
            [
                {"doc_id": "alpha", "title": "Alpha", "content": "# Alpha\n\nNew body."},
                {"doc_id": "new-doc", "title": "New Doc", "content": "# New Doc\n\nBody."},
                {"doc_id": "invalid", "title": "Invalid", "content": "Body.", "viewable": "false"},
            ],
            "ds_20260712T160000Z",
        )

        payload = apply_package(
            root,
            "apply.jsonl",
            [
                {"record_index": 0, "action": "overwrite", "target_doc_id": "alpha"},
                {"record_index": 2, "action": "skip", "note": "Needs metadata repair."},
            ],
            rebuild=fake_rebuild(rebuild_calls),
            logs=logs,
        )
        alpha_front_matter, alpha_body = docs_source_model.parse_source(root / "docs-viewer/scopes/library/source/documents/alpha.md")
        new_doc_id = payload["records"][1]["doc_id"]
        new_front_matter, new_body = docs_source_model.parse_source(
                root / "docs-viewer/scopes/library/source/documents" / f"{new_doc_id}.md"
        )
        report_path = configured_workspace_paths(root).root / str(payload["report_path"]).split("data-sharing/", 1)[1]
        report_text = report_path.read_text(encoding="utf-8")

    assert payload["outcome"] == "completed"
    assert payload["counts"] == {
        "created": 1,
        "overwritten": 1,
        "skipped": 1,
        "failed": 0,
        "not_attempted": 0,
    }
    assert [record["status"] for record in payload["records"]] == ["overwritten", "created", "skipped"]
    assert payload["records"][2]["note"] == "Needs metadata repair."
    assert alpha_front_matter["added_date"] == "2020-01-01"
    assert "New body." in alpha_body
    assert new_front_matter["doc_id"] == new_doc_id
    assert payload["records"][1]["source_doc_id"] == "new-doc"
    assert "Body." in new_body
    assert rebuild_calls == [
        {
            "scope": "library",
            "changed_paths": ["alpha.md", f"{new_doc_id}.md"],
            "docs_doc_ids": ["alpha", new_doc_id],
            "search_doc_ids": ["alpha", new_doc_id],
        }
    ]
    assert payload["report_path"].startswith(
        "$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-staging/results/"
    )
    assert "## overwritten" in report_text
    assert "## created" in report_text
    assert "## skipped" in report_text
    assert any(event == "docs-import-collection-record-skipped" for event, _details in logs)


def test_collection_confirmed_apply_dispatches_through_existing_import_post(monkeypatch) -> None:
    stub_markdown_validation(monkeypatch)
    rebuild_calls: list[dict[str, object]] = []
    monkeypatch.setattr(
        docs_write_rebuild,
        "perform_source_write_and_rebuild",
        fake_rebuild(rebuild_calls),
    )
    with make_repo() as temp:
        root = Path(temp)
        write_collection(
            root,
            "post-apply.jsonl",
            [{"doc_id": "post-applied", "title": "POST Applied", "content": "Body."}],
            "ds_20260712T160008Z",
        )
        preview = handle_import_source(
            root,
            {"scope": "library", "staged_filename": "post-apply.jsonl", "preview_only": True},
            False,
        )

        payload = handle_import_source(
            root,
            {
                "scope": "library",
                "staged_filename": "post-apply.jsonl",
                "preview_only": False,
                "confirm": True,
                "export_id": preview["package"]["export_id"],
                "source_sha256": preview["package"]["source_sha256"],
                "planned_identities": preview["planned_identities"],
                "decisions": [],
            },
            False,
        )

    assert payload["preview_only"] is False
    assert payload["records"][0]["status"] == "created"
    assert rebuild_calls[0]["docs_doc_ids"] == [payload["records"][0]["doc_id"]]


def test_collection_all_skipped_writes_report_without_rebuild(monkeypatch) -> None:
    stub_markdown_validation(monkeypatch)
    rebuild_calls: list[dict[str, object]] = []
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "skipped.md", {"doc_id": "skipped", "title": "Skipped", "parent_id": ""})
        write_collection(
            root,
            "all-skipped.jsonl",
            [{"doc_id": "skipped", "title": "Returned", "content": "Replacement."}],
            "ds_20260712T160010Z",
        )

        payload = apply_package(
            root,
            "all-skipped.jsonl",
            [{"record_index": 0, "action": "skip", "target_doc_id": "skipped"}],
            rebuild=fake_rebuild(rebuild_calls),
        )

    assert payload["outcome"] == "completed"
    assert payload["counts"]["skipped"] == 1
    assert payload["generation"]["status"] == "not-run"
    assert payload["report_path"]
    assert rebuild_calls == []


def test_collection_apply_returns_refreshed_plan_for_missing_or_changed_collision_decision(monkeypatch) -> None:
    stub_markdown_validation(monkeypatch)
    rebuild_calls: list[dict[str, object]] = []
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "alpha.md", {"doc_id": "alpha", "title": "Alpha", "parent_id": ""})
        write_collection(
            root,
            "drift.jsonl",
            [{"doc_id": "alpha", "title": "Returned Alpha", "content": "Body."}],
            "ds_20260712T160001Z",
        )

        missing = apply_package(root, "drift.jsonl", [], rebuild=fake_rebuild(rebuild_calls))
        changed = apply_package(
            root,
            "drift.jsonl",
            [{"record_index": 0, "action": "overwrite", "target_doc_id": "different"}],
            rebuild=fake_rebuild(rebuild_calls),
        )
        package_changed = apply_package(
            root,
            "drift.jsonl",
            [{"record_index": 0, "action": "overwrite", "target_doc_id": "alpha"}],
            rebuild=fake_rebuild(rebuild_calls),
            source_sha256="different",
        )

    assert missing["preview_only"] is True
    assert missing["reconfirmation_required"] is True
    assert missing["revalidation_issues"][0]["code"] == "decision_required"
    assert changed["revalidation_issues"][0]["code"] == "collision_target_changed"
    assert package_changed["revalidation_issues"][0]["code"] == "package_identity_changed"
    assert rebuild_calls == []


def test_preserve_existing_apply_uses_current_body_without_revision_reconfirmation(monkeypatch) -> None:
    stub_markdown_validation(monkeypatch)
    rebuild_calls: list[dict[str, object]] = []
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(
            root,
            "preserved.md",
            {
                "doc_id": "preserved",
                "title": "Old title",
                "parent_id": "",
                "custom_field": "before",
            },
            body="# Current\n\nInitial canonical body.\n",
        )
        write_collection(
            root,
            "preserve.jsonl",
            [{"doc_id": "preserved", "title": "Returned title"}],
            "ds_20260712T160009Z",
        )
        paths = configured_workspace_paths(root)
        preview = plan_data_sharing_documents_collection(
            root,
            scope="library",
            staged_filename="preserve.jsonl",
            staging_root=paths.import_staging,
            workspace_root=paths.root,
            metadata_root=paths.meta,
        ).as_dict()
        write_library_doc(
            root,
            "preserved.md",
            {
                "doc_id": "preserved",
                "title": "Changed after preview",
                "parent_id": "",
                "custom_field": "changed after preview",
            },
            body="# Current\n\nNewest canonical body.\n",
        )

        payload = apply_data_sharing_documents_collection(
            root,
            scope="library",
            staged_filename="preserve.jsonl",
            body={
                "scope": "library",
                "staged_filename": "preserve.jsonl",
                "preview_only": False,
                "confirm": True,
                "export_id": preview["package"]["export_id"],
                "source_sha256": preview["package"]["source_sha256"],
                "planned_identities": preview.get("planned_identities", []),
                "decisions": [
                    {"record_index": 0, "action": "overwrite", "target_doc_id": "preserved"}
                ],
            },
            staging_root=paths.import_staging,
            workspace_root=paths.root,
            metadata_root=paths.meta,
            log_event=lambda *_args: None,
            perform_source_write_and_rebuild=fake_rebuild(rebuild_calls),
        )
        front_matter, body = docs_source_model.parse_source(root / "docs-viewer/scopes/library/source/documents/preserved.md")

    assert payload["preview_only"] is False
    assert payload["records"][0]["status"] == "overwritten"
    assert front_matter["title"] == "Returned title"
    assert front_matter["custom_field"] == "changed after preview"
    assert "Newest canonical body." in body


def test_collection_apply_stops_after_source_failure_and_rebuilds_completed_writes(monkeypatch) -> None:
    stub_markdown_validation(monkeypatch)
    rebuild_calls: list[dict[str, object]] = []
    original_write = collection_apply.apply_import_document_source

    def fail_epsilon(plan) -> None:
        if plan.record.provenance.get("source_doc_id") == "epsilon":
            raise OSError("simulated epsilon write failure")
        original_write(plan)

    monkeypatch.setattr(collection_apply, "apply_import_document_source", fail_epsilon)
    with make_repo() as temp:
        root = Path(temp)
        write_collection(
            root,
            "partial.jsonl",
            [
                {"doc_id": "delta", "title": "Delta", "content": "Delta."},
                {"doc_id": "epsilon", "title": "Epsilon", "content": "Epsilon."},
                {"doc_id": "zeta", "title": "Zeta", "content": "Zeta."},
            ],
            "ds_20260712T160002Z",
        )

        payload = apply_package(root, "partial.jsonl", [], rebuild=fake_rebuild(rebuild_calls))
        result_ids = [record["doc_id"] for record in payload["records"]]
        delta_exists, epsilon_exists, zeta_exists = [
                (root / "docs-viewer/scopes/library/source/documents" / f"{doc_id}.md").exists()
            for doc_id in result_ids
        ]

    assert payload["outcome"] == "partial"
    assert [record["status"] for record in payload["records"]] == ["created", "failed", "not-attempted"]
    assert delta_exists is True
    assert epsilon_exists is False
    assert zeta_exists is False
    assert rebuild_calls[0]["docs_doc_ids"] == [result_ids[0]]
    assert payload["report_path"].startswith(
        "$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-staging/results/"
    )


def test_collection_apply_keeps_source_success_when_generation_or_report_write_fails(monkeypatch) -> None:
    stub_markdown_validation(monkeypatch)
    rebuild_calls: list[dict[str, object]] = []
    with make_repo() as temp:
        root = Path(temp)
        write_collection(
            root,
            "generation.jsonl",
            [{"doc_id": "delta", "title": "Delta", "content": "Delta."}],
            "ds_20260712T160003Z",
        )

        payload = apply_package(
            root,
            "generation.jsonl",
            [],
            rebuild=fake_rebuild(rebuild_calls, fail_generation=True),
        )
        source_exists = (
            root / "docs-viewer/scopes/library/source/documents" / f"{payload['records'][0]['doc_id']}.md"
        ).exists()

    assert source_exists is True
    assert payload["records"][0]["status"] == "created"
    assert payload["outcome"] == "generation-failed"
    assert payload["generation"]["status"] == "failed"
    assert payload["report_path"]

    monkeypatch.setattr(
        collection_apply,
        "write_collection_result_report",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("report denied")),
    )
    with make_repo() as temp:
        root = Path(temp)
        write_collection(
            root,
            "report-failure.jsonl",
            [{"doc_id": "delta", "title": "Delta", "content": "Delta."}],
            "ds_20260712T160004Z",
        )
        report_failure = apply_package(root, "report-failure.jsonl", [], rebuild=fake_rebuild([]))

    assert report_failure["outcome"] == "completed"
    assert report_failure["report_path"] == ""
    assert report_failure["warnings"][-1]["code"] == "result_report_write_failed"


def test_collection_apply_materializes_inline_media_and_blocks_source_when_publication_fails(monkeypatch) -> None:
    stub_markdown_validation(monkeypatch)
    with make_repo() as temp:
        root = Path(temp)
        write_collection(
            root,
            "media.jsonl",
            [
                {
                    "doc_id": "media-doc",
                    "title": "Media Doc",
                    "content": "# Media Doc\n\n![Diagram](data:image/png;base64,aGVsbG8=)",
                }
            ],
            "ds_20260712T160006Z",
        )

        payload = apply_package(root, "media.jsonl", [], rebuild=fake_rebuild([]))
        local_doc_id = payload["records"][0]["doc_id"]
        media_path = root / "site/assets/data/docs/scopes/library/media/img" / f"{local_doc_id}-image-01.png"
        _front_matter, body = docs_source_model.parse_source(
                root / "docs-viewer/scopes/library/source/documents" / f"{payload['records'][0]['doc_id']}.md"
        )
        media_bytes = media_path.read_bytes()

    assert media_bytes == b"hello"
    assert f"[[media:docs/library/img/{local_doc_id}-image-01.png]]" in body
    assert payload["records"][0]["inline_media_written"][0]["source_path"] == media_path.name
    assert payload["records"][0]["inline_media_written"][0]["location_provider"] == "repository"
    assert payload["records"][0]["inline_media_written"][0]["publish_status"] == "uploaded"
    assert payload["manual_copy_instructions"] == []

    monkeypatch.setattr(
        collection_apply,
        "materialize_import_document_media",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("asset store unavailable")),
    )
    with make_repo() as temp:
        root = Path(temp)
        write_collection(
            root,
            "asset-failure.jsonl",
            [
                {
                    "doc_id": "asset-doc",
                    "title": "Asset Doc",
                    "content": "![Asset](data:image/png;base64,aGVsbG8=)",
                }
            ],
            "ds_20260712T160007Z",
        )
        asset_failure = apply_package(root, "asset-failure.jsonl", [], rebuild=fake_rebuild([]))
        asset_doc_id = asset_failure["records"][0]["doc_id"]
        source_path = root / "docs-viewer/scopes/library/source/documents" / f"{asset_doc_id}.md"
        source_exists = source_path.exists()

    assert source_exists is False
    assert asset_failure["outcome"] == "failed"
    assert asset_failure["records"][0]["status"] == "failed"
    assert asset_failure["records"][0]["error"] == "asset store unavailable"


def test_collection_apply_rejects_browser_plan_fields_and_skipped_new_parent(monkeypatch) -> None:
    stub_markdown_validation(monkeypatch)
    with pytest.raises(ValueError, match="does not accept fields"):
        collection_decisions.parse_collection_decisions(
            {
                "scope": "library",
                "staged_filename": "unsafe.jsonl",
                "preview_only": False,
                "confirm": True,
                "decisions": [],
                "export_id": "ds_unsafe",
                "source_sha256": "unsafe",
                "target_path": "/tmp/unsafe.md",
            }
        )

    with make_repo() as temp:
        root = Path(temp)
        write_collection(
            root,
            "parent-skip.jsonl",
            [
                {"doc_id": "parent", "title": "Parent", "content": "", "viewable": "false"},
                {"doc_id": "child", "title": "Child", "parent_id": "parent", "content": "Child."},
            ],
            "ds_20260712T160005Z",
        )
        payload = apply_package(
            root,
            "parent-skip.jsonl",
            [{"record_index": 0, "action": "skip", "note": "Invalid parent."}],
            rebuild=fake_rebuild([]),
        )

    assert payload["preview_only"] is True
    assert payload["revalidation_issues"][-1]["code"] == "plan_blocked"


def test_collection_generation_projection_omits_commands_output_and_diagnostics() -> None:
    projected = safe_generation_result(
        {
            "status": "completed",
            "error": "",
            "rebuild": {
                "ok": True,
                "steps": [{"command": "/Users/example/python build.py", "stdout": "private"}],
                "docs": {"mode": "targeted", "doc_ids": ["alpha"], "reason": "/Users/example/output"},
                "search": {"mode": "targeted", "doc_ids": ["alpha"]},
                "diagnostics": {"path": "/Users/example/output"},
            },
        }
    )

    assert projected == {
        "status": "completed",
        "error": "",
        "rebuild": {
            "ok": True,
            "docs": {"mode": "targeted", "doc_ids": ["alpha"]},
            "search": {"mode": "targeted", "doc_ids": ["alpha"]},
        },
    }
