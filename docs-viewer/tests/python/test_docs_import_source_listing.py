#!/usr/bin/env python3
"""Docs source import listing and preview tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import docs_import_collection_apply
import docs_import_media
import docs_import_preview
import docs_import_review_source_folder
import docs_import_source_service as import_source_service
import docs_management_import_service
import docs_source_model
import docs_write_rebuild
from docs_import_common import FILE_MEDIA_STAGED_SUFFIXES
from docs_import_docx_test_support import semantic_docx_bytes
from docs_management_document_target import resolve_managed_document_collection
from docs_document_packages.workspace import configured_workspace_paths

from docs_import_test_support import (
    make_repo,
    write_returned_jsonl,
    write_staged,
    write_staged_bytes,
    write_staged_html,
    write_staged_markdown,
    write_staged_package_file,
    write_staged_text,
)


REVIEW_FOLDER_ID = "20260730-095512-documents-document-content"
REVIEW_EXPORT_ID = "ds_20260730T095512Z"


def review_source_text(doc_id: str, title: str) -> str:
    return (
        "---\n"
        f"doc_id: {doc_id}\n"
        f"title: {title}\n"
        "added_date: 2026-07-30\n"
        "last_updated: 2026-07-30\n"
        f"review_folder_id: {REVIEW_FOLDER_ID}\n"
        f"review_source_export_id: {REVIEW_EXPORT_ID}\n"
        "review_source_scope: library\n"
        "review_profile_id: document-content\n"
        "---\n"
        f"# {title}\n"
    )


def write_review_source_fixture(
    root: Path,
    *,
    staged_folder: str = "edited-review-copy",
    supports_return_import: bool = True,
) -> Path:
    paths = configured_workspace_paths(root)
    records = [
        ("alpha", "Alpha"),
        ("beta", "Beta"),
    ]
    retained_source = paths.import_preview / REVIEW_FOLDER_ID / "source"
    staged_source = paths.import_staging / staged_folder
    retained_source.mkdir(parents=True, exist_ok=True)
    staged_source.mkdir(parents=True, exist_ok=True)
    for doc_id, title in records:
        source_text = review_source_text(doc_id, title)
        (retained_source / f"{doc_id}.md").write_text(
            source_text,
            encoding="utf-8",
        )
        (staged_source / f"{doc_id}.md").write_text(
            source_text,
            encoding="utf-8",
        )
    manifest = {
        "schema_version": "docs_review_validated_package_v1",
        "package_id": REVIEW_FOLDER_ID,
        "status": "validated",
        "source_scope": "library",
        "source_sub_scope": "",
        "profile_id": "document-content",
        "supports_docs_review": True,
        "supports_return_import": supports_return_import,
        "selected_doc_ids": [doc_id for doc_id, _title in records],
        "default_doc_id": "alpha",
        "source_export_id": REVIEW_EXPORT_ID,
        "source_files": [
            {
                "doc_id": doc_id,
                "path": f"source/{doc_id}.md",
            }
            for doc_id, _title in records
        ],
    }
    (retained_source.parent / "manifest.json").write_text(
        json.dumps(manifest) + "\n",
        encoding="utf-8",
    )
    metadata = {
        "schema_version": "data_sharing_export_meta_v1",
        "export_id": REVIEW_EXPORT_ID,
        "app": "docs-viewer",
        "adapter_id": "documents",
        "data_domain": "documents",
        "profile_id": "document-content",
        "config_id": "document-content",
        "scope": "library",
        "target_format": "jsonl",
        "record_shape": "document_rows",
        "supports_docs_review": True,
        "supports_return_import": supports_return_import,
        "generated_at": "2026-07-30T09:55:12Z",
        "selected_doc_ids": [doc_id for doc_id, _title in records],
        "source_last_updated": {
            doc_id: "2026-07-29 12:00:00"
            for doc_id, _title in records
        },
    }
    paths.meta.mkdir(parents=True, exist_ok=True)
    (paths.meta / f"{REVIEW_EXPORT_ID}.meta.json").write_text(
        json.dumps(metadata) + "\n",
        encoding="utf-8",
    )
    return staged_source


def import_dependencies() -> import_source_service.ImportSourceDependencies:
    return import_source_service.ImportSourceDependencies(
        log_event=lambda *_args, **_kwargs: None,
        perform_source_write_and_rebuild=lambda *_args, **_kwargs: {},
        perform_scope_source_write_and_rebuild_atomic=(
            lambda *_args, **_kwargs: {}
        ),
        perform_sub_scope_source_write_and_rebuild=(
            lambda *_args, **_kwargs: {}
        ),
    )


def write_review_scope_targets(root: Path) -> dict[str, Path]:
    targets = {
        "alpha": root / "docs-viewer/scopes/library/source/documents/alpha.md",
        "beta": root / "docs-viewer/scopes/library/source/documents/beta.md",
    }
    targets["alpha"].write_text(
        docs_source_model.format_source(
            {
            "doc_id": "alpha",
            "title": "Alpha",
            "added_date": "2026-07-01 10:00:00",
            "last_updated": "2026-07-29 12:00:00",
            "parent_id": "library",
            "summary": "Original Alpha summary.",
            "group": "protected-alpha",
            "ui_status": "draft",
            },
            "# Alpha\n",
        ),
        encoding="utf-8",
    )
    targets["beta"].write_text(
        docs_source_model.format_source(
            {
            "doc_id": "beta",
            "title": "Beta",
            "added_date": "2026-07-02 10:00:00",
            "last_updated": "2026-07-29 12:00:00",
            "parent_id": "library",
            "group": "protected-beta",
            "ui_status": "done",
            },
            "# Beta\n",
        ),
        encoding="utf-8",
    )
    return targets


def edit_review_alpha(staged_folder: Path) -> None:
    path = staged_folder / "alpha.md"
    path.write_text(
        path.read_text(encoding="utf-8")
        .replace("title: Alpha", "title: Edited Alpha")
        .replace(
            "---\n# Alpha",
            "summary: Edited Alpha summary.\n"
            "parent_id: library\n"
            "viewable: false\n"
            "---\n"
            "# Edited Alpha\n\nEdited reviewed body.",
        ),
        encoding="utf-8",
    )


def stub_markdown_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        docs_import_preview,
        "validate_markdown_preview",
        lambda markdown, *, title="": {
            "ok": True,
            "html_chars": len(markdown),
            "renderer": "stub",
        },
    )


def reviewed_scope_preview(root: Path, staged_filename: str) -> dict[str, object]:
    return docs_management_import_service.handle_import_source(
        root,
        {
            "scope": "library",
            "staged_filename": staged_filename,
            "preview_only": True,
        },
        dry_run=False,
    )


def reviewed_scope_apply(
    root: Path,
    staged_filename: str,
    preview: dict[str, object],
) -> dict[str, object]:
    package = preview["package"]
    assert isinstance(package, dict)
    return docs_management_import_service.handle_import_source(
        root,
        {
            "scope": "library",
            "staged_filename": staged_filename,
            "preview_only": False,
            "confirm": True,
            "export_id": package["export_id"],
            "source_sha256": package["source_sha256"],
            "trusted_metadata_sha256": package["trusted_metadata_sha256"],
            "planned_identities": preview["planned_identities"],
            "planned_actions": preview["planned_actions"],
        },
        dry_run=False,
    )


def test_source_import_files_list_registered_document_formats() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged_html(root, "source.html", "<html><body><h1>Source</h1></body></html>")
        write_staged_markdown(root, "source.md", "# Source\n")
        write_staged_text(root, "source.txt", "Source\n")
        write_staged_bytes(root, "source.docx", semantic_docx_bytes())
        write_staged_text(root, "source.svg", "<svg viewBox='0 0 10 10'></svg>\n")
        write_staged_bytes(root, "source.png", b"fake image")
        write_staged_bytes(root, "source.pdf", b"fake pdf")
        write_staged_package_file(root, "package-note", "Note.md", "# Package Note\n")

        files = import_source_service.handle_import_source_files(root)["files"]

    by_filename = {item["filename"]: item for item in files}
    assert by_filename["source.html"]["source_format"] == "html"
    assert by_filename["source.md"]["source_format"] == "markdown"
    assert by_filename["source.txt"]["source_format"] == "text"
    assert by_filename["source.docx"]["source_format"] == "docx"
    assert ".docx" in FILE_MEDIA_STAGED_SUFFIXES
    assert by_filename["package-note"]["source_format"] == "markdown_package"
    assert by_filename["package-note"]["package_markdown_count"] == 1
    assert by_filename["source.md"]["path"] == "$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-staging/source.md"
    assert {"source.svg", "source.png", "source.pdf"}.isdisjoint(by_filename)


def test_source_import_lists_valid_edited_review_folder_with_display_identity() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_review_source_fixture(root)

        files = import_source_service.handle_import_source_files(root)["files"]

    by_filename = {item["filename"]: item for item in files}
    reviewed = by_filename["edited-review-copy"]
    assert reviewed["source_format"] == (
        docs_import_review_source_folder.EDITED_REVIEW_SOURCE_FORMAT
    )
    assert reviewed["display_name"] == f"{REVIEW_FOLDER_ID} (reviewed)"
    assert reviewed["filename"] == "edited-review-copy"
    assert reviewed["review_folder_id"] == REVIEW_FOLDER_ID
    assert reviewed["document_count"] == 2


@pytest.mark.parametrize(
    ("case", "error"),
    (
        ("incomplete", "selected_doc_ids does not match"),
        ("mixed", "added_date must be a non-blank string"),
        ("non-importable", "supports_return_import must be true"),
        ("nested", "only direct Markdown files"),
        ("unsupported", "unsupported entries"),
        ("duplicate-field", "duplicate front matter fields"),
        ("mixed-provenance", "one consistent review_source_export_id"),
        ("missing-source-version", "source_last_updated membership"),
        ("symlink", "must not contain symlinks"),
    ),
)
def test_source_import_blocks_invalid_edited_review_folders(
    case: str,
    error: str,
) -> None:
    with make_repo() as temp:
        root = Path(temp)
        staged_folder = f"{case}-review"
        staged = write_review_source_fixture(
            root,
            staged_folder=staged_folder,
            supports_return_import=case != "non-importable",
        )
        paths = configured_workspace_paths(root)
        if case == "incomplete":
            (staged / "beta.md").unlink()
        elif case == "mixed":
            (staged / "ordinary.md").write_text(
                "---\ndoc_id: ordinary\ntitle: Ordinary\n---\nBody\n",
                encoding="utf-8",
            )
        elif case == "nested":
            nested = staged / "nested"
            nested.mkdir()
            (staged / "beta.md").rename(nested / "beta.md")
        elif case == "unsupported":
            (staged / "notes.txt").write_text("not a source\n", encoding="utf-8")
        elif case == "duplicate-field":
            alpha = staged / "alpha.md"
            alpha.write_text(
                alpha.read_text(encoding="utf-8").replace(
                    "---\n# Alpha",
                    f"review_folder_id: {REVIEW_FOLDER_ID}\n---\n# Alpha",
                ),
                encoding="utf-8",
            )
        elif case == "mixed-provenance":
            alpha = staged / "alpha.md"
            alpha.write_text(
                alpha.read_text(encoding="utf-8").replace(
                    REVIEW_EXPORT_ID,
                    "ds_20260730T095513Z",
                ),
                encoding="utf-8",
            )
        elif case == "missing-source-version":
            metadata_path = paths.meta / f"{REVIEW_EXPORT_ID}.meta.json"
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            metadata["source_last_updated"].pop("beta")
            metadata_path.write_text(
                json.dumps(metadata) + "\n",
                encoding="utf-8",
            )
        elif case == "symlink":
            (staged / "linked.md").symlink_to(
                paths.import_preview / REVIEW_FOLDER_ID / "source/alpha.md",
            )

        with pytest.raises(ValueError, match=error):
            docs_import_review_source_folder.recognize_edited_review_source_folder(
                root,
                candidate=staged,
                staging_root=paths.import_staging,
                metadata_root=paths.meta,
            )
        files = import_source_service.handle_import_source_files(root)["files"]

    assert staged_folder not in {
        item["filename"]
        for item in files
    }


def test_source_import_rejects_review_file_and_plans_folder_before_generic_markdown() -> None:
    with make_repo() as temp:
        root = Path(temp)
        staged_folder = write_review_source_fixture(root)
        paths = configured_workspace_paths(root)
        standalone = paths.import_staging / "alpha-reviewed.md"
        standalone.write_text(
            (staged_folder / "alpha.md").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        destination = resolve_managed_document_collection(
            root,
            scope="library",
        )

        with pytest.raises(
            ValueError,
            match="Stage and select the complete edited review source folder",
        ):
            import_source_service.handle_import_source(
                root,
                {
                    "scope": "library",
                    "staged_filename": "alpha-reviewed.md",
                },
                True,
                import_dependencies(),
                staging_root=paths.import_staging,
                workspace_root=paths.root,
                metadata_root=paths.meta,
                destination=destination,
            )
        preview = import_source_service.handle_import_source(
            root,
            {
                "scope": "library",
                "staged_filename": staged_folder.name,
                "preview_only": True,
            },
            True,
            import_dependencies(),
            staging_root=paths.import_staging,
            workspace_root=paths.root,
            metadata_root=paths.meta,
            destination=destination,
        )

    assert preview["collection"] is True
    assert preview["source_format"] == "edited_review_sources"
    assert preview["target"] == {"scope": "library"}
    assert preview["ready_for_confirmation"] is False
    assert {
        blocker["code"]
        for blocker in preview["blockers"]
    } >= {"stale_prepared_sources", "overwrite_target_missing"}


def test_edited_review_scope_preview_is_write_free_exact_and_overwrite_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub_markdown_validation(monkeypatch)
    with make_repo() as temp:
        root = Path(temp)
        targets = write_review_scope_targets(root)
        staged_folder = write_review_source_fixture(root)
        edit_review_alpha(staged_folder)
        originals = {
            doc_id: path.read_bytes()
            for doc_id, path in targets.items()
        }

        preview = reviewed_scope_preview(root, staged_folder.name)

        assert {
            doc_id: path.read_bytes()
            for doc_id, path in targets.items()
        } == originals

    assert preview["ready_for_confirmation"] is True
    assert preview["source_format"] == "edited_review_sources"
    assert preview["target"] == {"scope": "library"}
    assert preview["staged_filename"] == "edited-review-copy"
    assert preview["planned_identities"] == []
    assert [record["action"] for record in preview["records"]] == [
        "overwrite",
        "overwrite",
    ]
    assert preview["counts"]["creates"] == 0
    assert preview["counts"]["collisions"] == 2
    assert preview["warnings"] == [
        {
            "level": "warning",
            "code": "derived_markdown_fidelity",
            "message": (
                "Edited review sources are derived Markdown. Rich content, "
                "tokens, comments, raw embeds, source formatting, and package "
                "assets may not survive this import."
            ),
        }
    ]
    package = preview["package"]
    assert package["review_folder_id"] == REVIEW_FOLDER_ID
    assert package["export_id"] == REVIEW_EXPORT_ID
    assert package["document_count"] == 2
    assert package["source_last_updated"] == {
        "alpha": "2026-07-29 12:00:00",
        "beta": "2026-07-29 12:00:00",
    }
    assert "added_date" not in package
    assert "last_updated" not in package


def test_edited_review_scope_apply_preserves_authority_and_refreshes_scope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub_markdown_validation(monkeypatch)
    boundary_calls: list[dict[str, object]] = []

    def atomic_scope_boundary(
        repo_root,
        scope,
        changed_paths,
        write_operation,
        **kwargs,
    ):
        snapshots = kwargs["source_snapshots"]
        assert set(path.resolve() for path in changed_paths) == set(snapshots)
        write_operation()
        boundary_calls.append(
            {
                "scope": scope,
                "changed_paths": [path.name for path in changed_paths],
                "docs_doc_ids": list(kwargs.get("docs_doc_ids") or []),
                "search_doc_ids": list(kwargs.get("search_doc_ids") or []),
                "reason": kwargs.get("suppression_reason"),
            }
        )
        return {
            "ok": True,
            "docs": {
                "mode": "targeted",
                "doc_ids": list(kwargs.get("docs_doc_ids") or []),
            },
            "search": {
                "mode": "targeted",
                "doc_ids": list(kwargs.get("search_doc_ids") or []),
            },
        }

    monkeypatch.setattr(
        docs_write_rebuild,
        "perform_scope_source_write_and_rebuild_atomic",
        atomic_scope_boundary,
    )
    with make_repo() as temp:
        root = Path(temp)
        targets = write_review_scope_targets(root)
        staged_folder = write_review_source_fixture(root)
        edit_review_alpha(staged_folder)

        preview = reviewed_scope_preview(root, staged_folder.name)
        payload = reviewed_scope_apply(root, staged_folder.name, preview)
        alpha_front_matter, alpha_body = docs_source_model.parse_source(
            targets["alpha"],
        )
        beta_front_matter, beta_body = docs_source_model.parse_source(
            targets["beta"],
        )

    assert payload["outcome"] == "completed"
    assert payload["target"] == {"scope": "library"}
    assert payload["counts"] == {
        "created": 0,
        "overwritten": 2,
        "failed": 0,
        "not_attempted": 0,
    }
    assert payload["rollback"]["status"] == "not-needed"
    assert boundary_calls == [
        {
            "scope": "library",
            "changed_paths": ["alpha.md", "beta.md"],
            "docs_doc_ids": ["alpha", "beta"],
            "search_doc_ids": ["alpha", "beta"],
            "reason": "docs-import-reviewed-scope-collection-apply",
        }
    ]
    assert alpha_front_matter["doc_id"] == "alpha"
    assert alpha_front_matter["added_date"] == "2026-07-01 10:00:00"
    assert alpha_front_matter["group"] == "protected-alpha"
    assert alpha_front_matter["ui_status"] == "draft"
    assert alpha_front_matter["title"] == "Edited Alpha"
    assert alpha_front_matter["summary"] == "Edited Alpha summary."
    assert alpha_front_matter["parent_id"] == "library"
    assert alpha_front_matter["viewable"] is False
    assert alpha_front_matter["last_updated"] not in {
        "2026-07-29 12:00:00",
        "2026-07-30",
    }
    assert "Edited reviewed body." in alpha_body
    assert beta_front_matter["doc_id"] == "beta"
    assert beta_front_matter["added_date"] == "2026-07-02 10:00:00"
    assert beta_front_matter["group"] == "protected-beta"
    assert beta_front_matter["ui_status"] == "done"
    assert beta_front_matter["last_updated"] == "2026-07-29 12:00:00"
    assert beta_body.strip() == "# Beta"


def test_edited_review_scope_revalidates_versions_and_folder_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub_markdown_validation(monkeypatch)
    with make_repo() as temp:
        root = Path(temp)
        targets = write_review_scope_targets(root)
        staged_folder = write_review_source_fixture(root)
        preview = reviewed_scope_preview(root, staged_folder.name)
        targets["alpha"].write_text(
            targets["alpha"].read_text(encoding="utf-8").replace(
                "last_updated: \"2026-07-29 12:00:00\"",
                "last_updated: \"2026-07-30 21:00:00\"",
            ),
            encoding="utf-8",
        )

        stale = reviewed_scope_apply(root, staged_folder.name, preview)

        write_review_scope_targets(root)
        refreshed_preview = reviewed_scope_preview(root, staged_folder.name)
        (staged_folder / "alpha.md").write_text(
            (staged_folder / "alpha.md").read_text(encoding="utf-8")
            + "\nEdited after preview.\n",
            encoding="utf-8",
        )
        changed_folder = reviewed_scope_apply(
            root,
            staged_folder.name,
            refreshed_preview,
        )

    assert stale["preview_only"] is True
    assert stale["reconfirmation_required"] is True
    assert stale["ready_for_confirmation"] is False
    assert "stale_prepared_sources" in {
        blocker["code"]
        for blocker in stale["blockers"]
    }
    assert changed_folder["preview_only"] is True
    assert changed_folder["reconfirmation_required"] is True
    assert changed_folder["revalidation_issues"][0]["code"] == (
        "package_identity_changed"
    )


def test_edited_review_scope_rechecks_snapshot_inside_write_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub_markdown_validation(monkeypatch)
    original_boundary = (
        docs_write_rebuild.perform_scope_source_write_and_rebuild_atomic
    )
    raced = False

    def race_boundary(
        repo_root,
        scope,
        changed_paths,
        write_operation,
        **kwargs,
    ):
        nonlocal raced
        snapshots = kwargs["source_snapshots"]
        if not raced:
            raced = True
            first_path = next(iter(snapshots))
            first_path.write_text(
                first_path.read_text(encoding="utf-8")
                + "\nExternal concurrent edit.\n",
                encoding="utf-8",
            )
        return original_boundary(
            repo_root,
            scope,
            changed_paths,
            write_operation,
            **kwargs,
        )

    monkeypatch.setattr(
        docs_write_rebuild,
        "perform_scope_source_write_and_rebuild_atomic",
        race_boundary,
    )
    with make_repo() as temp:
        root = Path(temp)
        targets = write_review_scope_targets(root)
        staged_folder = write_review_source_fixture(root)
        edit_review_alpha(staged_folder)
        preview = reviewed_scope_preview(root, staged_folder.name)

        refreshed = reviewed_scope_apply(root, staged_folder.name, preview)
        source_after = targets["alpha"].read_text(encoding="utf-8")

    assert raced is True
    assert refreshed["preview_only"] is True
    assert refreshed["reconfirmation_required"] is True
    assert refreshed["revalidation_issues"][0]["code"] == "target_state_changed"
    assert "External concurrent edit." in source_after
    assert "Edited reviewed body." not in source_after


@pytest.mark.parametrize("failure_mode", ["source-write", "rebuild"])
def test_edited_review_scope_failure_restores_every_source_and_projection(
    monkeypatch: pytest.MonkeyPatch,
    failure_mode: str,
) -> None:
    stub_markdown_validation(monkeypatch)
    original_apply = docs_import_collection_apply.apply_import_document_source
    source_write_count = 0
    rebuild_count = 0

    def apply_source(document_plan):
        nonlocal source_write_count
        source_write_count += 1
        if failure_mode == "source-write" and source_write_count == 2:
            raise RuntimeError("simulated second source-write failure")
        original_apply(document_plan)

    def rebuild_scope(
        repo_root,
        scope,
        *,
        include_search,
        search_doc_ids,
        docs_doc_ids,
        skip_media_builds,
    ):
        nonlocal rebuild_count
        rebuild_count += 1
        if failure_mode == "rebuild" and rebuild_count == 1:
            raise RuntimeError("simulated scope rebuild failure")
        return {
            "ok": True,
            "docs": {
                "mode": "targeted",
                "doc_ids": list(docs_doc_ids or []),
            },
            "search": {
                "mode": "targeted",
                "doc_ids": list(search_doc_ids or []),
            },
        }

    monkeypatch.setattr(
        docs_import_collection_apply,
        "apply_import_document_source",
        apply_source,
    )
    monkeypatch.setattr(
        docs_write_rebuild,
        "rebuild_scope_outputs",
        rebuild_scope,
    )
    with make_repo() as temp:
        root = Path(temp)
        targets = write_review_scope_targets(root)
        staged_folder = write_review_source_fixture(root)
        edit_review_alpha(staged_folder)
        originals = {
            doc_id: path.read_bytes()
            for doc_id, path in targets.items()
        }
        preview = reviewed_scope_preview(root, staged_folder.name)

        payload = reviewed_scope_apply(root, staged_folder.name, preview)
        restored = {
            doc_id: path.read_bytes()
            for doc_id, path in targets.items()
        }

    assert restored == originals
    assert payload["outcome"] == "generation-failed"
    assert payload["counts"] == {
        "created": 0,
        "overwritten": 0,
        "failed": 2,
        "not_attempted": 0,
    }
    assert payload["rollback"]["status"] == "completed"
    assert payload["rollback"]["sources_restored"] is True
    assert rebuild_count == (1 if failure_mode == "source-write" else 2)


def test_supported_documents_collection_registers_before_generic_json_fallback() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_returned_jsonl(
            root,
            "reviewed-documents.jsonl",
            [{"doc_id": "reviewed-doc", "title": "Reviewed Doc", "content": "Body."}],
            export_id="ds_20260712T150000Z",
        )
        write_staged(root, "ordinary.json", {"kind": "ordinary-attachment"})

        files = import_source_service.handle_import_source_files(root)["files"]

    by_filename = {item["filename"]: item for item in files}
    assert by_filename["reviewed-documents.jsonl"]["source_format"] == "data_sharing_documents"
    assert "ordinary.json" not in by_filename


def test_source_import_ignores_repo_local_staging_and_rejects_traversal() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged_markdown(root, "external.md", "# External\n")
        repo_local = root / "var/docs/import-staging/repo-local.md"
        repo_local.parent.mkdir(parents=True, exist_ok=True)
        repo_local.write_text("# Repo local\n", encoding="utf-8")
        paths = configured_workspace_paths(root)
        outside = root / "outside.md"
        outside.write_text("# Outside\n", encoding="utf-8")
        (paths.import_staging / "linked.md").symlink_to(outside)

        payload = import_source_service.handle_import_source_files(root)
        with pytest.raises(ValueError, match="configured import staging root"):
            docs_import_preview.resolve_staged_import_source(paths.import_staging, "../outside.md")
        with pytest.raises(ValueError, match="must not be symlinks"):
            docs_import_preview.resolve_staged_import_source(paths.import_staging, "linked.md")

    assert payload["available"] is True
    assert payload["staging_root"] == "$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-staging"
    assert [item["filename"] for item in payload["files"]] == ["external.md"]


def test_source_import_listing_reports_unavailable_workspace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_repo() as temp:
        root = Path(temp)
        monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(tmp_path / "missing-projects"))

        payload = import_source_service.handle_import_source_files(root)

    assert payload["ok"] is True
    assert payload["available"] is False
    assert payload["staging_root"] == "$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing"
    assert payload["files"] == []
    assert "does not exist" in payload["message"]


def test_source_import_listing_reports_missing_configured_staging_root() -> None:
    with make_repo() as temp:
        root = Path(temp)
        paths = configured_workspace_paths(root)
        paths.import_staging.rmdir()

        payload = import_source_service.handle_import_source_files(root)

    assert payload["available"] is False
    assert payload["files"] == []
    assert "$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-staging" in payload["message"]

def test_source_import_previews_validate_with_python_renderer() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged_html(root, "source.html", "<html><body><h1>Source</h1><p>Body.</p></body></html>")
        write_staged_markdown(root, "source.md", "# Source\n\n| A | B |\n| - | - |\n| 1 | 2 |\n")
        write_staged_text(root, "source.txt", "Source\n\nSee https://example.com/path.\n")
        write_staged_package_file(root, "package-note", "Note.md", "# Package Note\n\nBody.\n")
        paths = configured_workspace_paths(root)

        previews = [
            docs_import_preview.generate_import_preview(
                root,
                staging_root=paths.import_staging,
                workspace_root=paths.root,
                source_path=docs_import_preview.resolve_staged_import_source(paths.import_staging, staged_filename),
                scope="library",
                include_prompt_meta=False,
            )
            for staged_filename in [
                "source.html",
                "source.md",
                "source.txt",
                "package-note",
            ]
        ]

    source_formats = {preview["source_format"] for preview in previews}
    assert source_formats == {"html", "markdown", "text", "markdown_package"}
    for preview in previews:
        validation = preview["markdown_validation"]
        assert validation["ok"] is True
        assert validation["renderer"] == "studio/shared/python/markdown_renderer.py"
        assert validation["renderer_contract"]["library"] == "markdown-it-py"
        assert validation["sanitizer_boundary"]["import_html"] == "structured conversion plus sanitized SVG media extraction"

def test_media_path_comes_from_scope_config() -> None:
    assert docs_import_media.media_path_for("analysis", "img", "diagram.png") == "docs/analysis/img/diagram.png"
    assert docs_import_media.media_token("analysis", "img", "diagram.png") == "[[media:docs/analysis/img/diagram.png]]"
    assert docs_import_media.media_path_for("analysis", "svg", "diagram.svg") == "docs/analysis/svg/diagram.svg"
    assert docs_import_media.media_token("analysis", "svg", "diagram.svg") == "[[media:docs/analysis/svg/diagram.svg]]"
