#!/usr/bin/env python3
"""Focused checks for Docs Viewer source-model helpers."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
if str(DOCS_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(DOCS_SERVICES_DIR))

import docs_source_model as source_model  # noqa: E402
from repo_factory import docs_scope_record, write_docs_scope_config  # noqa: E402


FIXTURE_DOC_ID = "d-20260101-000000-000001"


def write_doc(root: Path, scope_root: str, filename: str, front_matter: dict[str, object], body: str = "# Body\n") -> None:
    path = root / scope_root / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source_model.format_source(front_matter, body), encoding="utf-8")


def configure_repository_scope(root: Path) -> None:
    write_docs_scope_config(root, [docs_scope_record("studio")])


def make_doc(
    doc_id: str,
    *,
    title: str | None = None,
    parent_id: str = "",
    stem: str | None = None,
) -> source_model.ScopeDoc:
    front_matter: dict[str, object] = {
        "doc_id": doc_id,
        "title": title or doc_id.title(),
        "parent_id": parent_id,
    }
    body = f"# {front_matter['title']}\n"
    return source_model.ScopeDoc(
        scope="studio",
        path=Path(f"docs-viewer/scopes/studio/source/documents/{stem or doc_id}.md"),
        source_text=source_model.format_source(front_matter, body),
        front_matter=front_matter,
        body=body,
        doc_id=doc_id,
        title=str(front_matter["title"]),
        ui_status="",
        parent_id=parent_id,
        publishable=True,
    )


def test_publishable_support_follows_exact_public_projection() -> None:
    assert source_model.collection_supports_publishable(
        SimpleNamespace(public_projection=object())
    ) is True
    assert source_model.collection_supports_publishable(
        SimpleNamespace(public_projection=None)
    ) is False


def test_publishable_front_matter_rejects_legacy_and_local_fields() -> None:
    public = SimpleNamespace(public_projection=object())
    local = SimpleNamespace(public_projection=None)

    source_model.validate_publishable_front_matter(
        {"publishable": False},
        collection_config=public,
        source_name="public.md",
    )
    with pytest.raises(ValueError, match="legacy viewable"):
        source_model.validate_publishable_front_matter(
            {"viewable": False},
            collection_config=public,
            source_name="legacy.md",
        )
    with pytest.raises(ValueError, match="not supported in local collection"):
        source_model.validate_publishable_front_matter(
            {"publishable": False},
            collection_config=local,
            source_name="local.md",
        )
    with pytest.raises(ValueError, match="must be a boolean"):
        source_model.validate_publishable_front_matter(
            {"publishable": "false"},
            collection_config=public,
            source_name="invalid.md",
        )


def test_front_matter_parses_and_formats_supported_scalar_values() -> None:
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / "sample.md"
        path.write_text(
            "\n".join(
                [
                    "---",
                    "doc_id: sample",
                    "title: \"Quoted Title\"",
                    "parent_id: \"\"",
                    "publishable: false",
                    "summary: \"\"",
                    "---",
                    "# Sample",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        front_matter, body = source_model.parse_source(path)
        formatted = source_model.format_source(front_matter, body)

    assert front_matter["title"] == "Quoted Title"
    assert front_matter["parent_id"] == ""
    assert front_matter["publishable"] is False
    assert front_matter["summary"] == ""
    assert "parent_id: \"\"" in formatted
    assert "publishable: false" in formatted


def test_front_matter_formatter_quotes_digit_only_string_identity() -> None:
    source = source_model.format_source(
        {
            "doc_id": FIXTURE_DOC_ID,
            "title": "Catalogue subject",
            "work_id": "00123",
            "series_id": "026",
        },
        "# Catalogue subject\n",
    )
    front_matter, _body = source_model.parse_source_text(source)

    assert 'work_id: "00123"' in source
    assert 'series_id: "026"' in source
    assert front_matter["work_id"] == "00123"
    assert front_matter["series_id"] == "026"


def test_scope_loader_preserves_exact_source_bytes_and_newlines() -> None:
    raw_source = (
        "---\r\n"
        f"doc_id: {FIXTURE_DOC_ID}\r\n"
        "title: Exact Source\r\n"
        'parent_id: ""\r\n'
        "---\r\n"
        "# Exact Source\r\n"
    ).encode("utf-8")
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        path = (
            root
            / "docs-viewer/scopes/studio/source/documents/exact-source.md"
        )
        path.parent.mkdir(parents=True)
        path.write_bytes(raw_source)
        configure_repository_scope(root)

        docs = source_model.load_scope_docs(root, "studio")

    assert len(docs) == 1
    assert docs[0].source_text.encode("utf-8") == raw_source
    assert docs[0].body == "# Exact Source\r\n"
    assert source_model.source_revision(
        docs[0].source_text.encode("utf-8")
    ) == source_model.source_revision(raw_source)


def test_scope_loader_does_not_fallback_to_repository_scope_copy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_doc(
        tmp_path,
        "docs-viewer/scopes/studio/source/documents",
        "retired-copy.md",
        {"doc_id": FIXTURE_DOC_ID, "title": "Retired copy"},
    )
    projects_root = tmp_path / "projects"
    (projects_root / "docs-viewer").mkdir(parents=True)
    monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(projects_root))
    config = docs_scope_record(
        "studio",
        scope_root_path="$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/scopes/studio",
    )
    config["scope_root"] = {
        "provider": "external_local",
        "path": "$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/scopes/studio",
    }
    write_docs_scope_config(tmp_path, [config])

    with pytest.raises(ValueError, match="missing source root for scope studio") as error:
        source_model.load_scope_docs(tmp_path, "studio")

    assert str(projects_root / "docs-viewer/scopes/studio") in str(error.value)
    assert "retired-copy.md" not in str(error.value)


def test_document_collection_loader_selects_exact_configured_sub_scope() -> None:
    child_config = SimpleNamespace(
        sub_scope="tags",
        ui_statuses=("draft",),
        sub_scope_customisation=SimpleNamespace(
            customisation_id="analysis_tags",
            settings={"groups": ("subject",)},
        ),
        source=SimpleNamespace(
            location=SimpleNamespace(path=Path("analysis-tags")),
            documents_path=Path("documents"),
        ),
    )
    parent_config = SimpleNamespace(
        scope_id="analysis",
        allow_unresolved_parent_ids=False,
        source=SimpleNamespace(
            location=SimpleNamespace(path=Path("analysis-parent")),
            documents_path=Path("documents"),
        ),
        sub_scopes=(child_config,),
    )
    original_configs = dict(source_model.DOCS_SCOPE_CONFIGS)

    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        write_doc(
            root,
            "analysis-parent/documents",
            "shared.md",
            {"doc_id": FIXTURE_DOC_ID, "title": "Parent version"},
        )
        write_doc(
            root,
            "analysis-tags/documents",
            "shared.md",
            {
                "doc_id": FIXTURE_DOC_ID,
                "title": "Tag version",
                "ui_status": "draft",
                "group": "subject",
            },
        )
        source_model.DOCS_SCOPE_CONFIGS.clear()
        source_model.DOCS_SCOPE_CONFIGS["analysis"] = parent_config
        try:
            docs = source_model.load_document_collection_docs(
                root,
                "analysis",
                "tags",
            )
            try:
                source_model.load_document_collection_docs(
                    root,
                    "analysis",
                    "missing",
                )
            except ValueError as exc:
                missing_error = str(exc)
            else:
                raise AssertionError("unknown sub-scope should not load parent docs")
        finally:
            source_model.DOCS_SCOPE_CONFIGS.clear()
            source_model.DOCS_SCOPE_CONFIGS.update(original_configs)

    assert [(doc.doc_id, doc.title, doc.group) for doc in docs] == [
        (FIXTURE_DOC_ID, "Tag version", "subject")
    ]
    assert "unknown sub_scope 'missing' for scope 'analysis'" in missing_error


def test_projects_collection_loader_keeps_malformed_folder_source_loadable() -> None:
    child_config = SimpleNamespace(
        sub_scope="projects",
        ui_statuses=("draft", "done"),
        sub_scope_customisation=SimpleNamespace(
            customisation_id="dotlineform_projects",
            settings={},
        ),
        source=SimpleNamespace(
            location=SimpleNamespace(path=Path("dotlineform-projects")),
            documents_path=Path("documents"),
        ),
    )
    parent_config = SimpleNamespace(
        scope_id="dotlineform",
        allow_unresolved_parent_ids=False,
        source=SimpleNamespace(
            location=SimpleNamespace(path=Path("dotlineform-parent")),
            documents_path=Path("documents"),
        ),
        sub_scopes=(child_config,),
    )
    original_configs = dict(source_model.DOCS_SCOPE_CONFIGS)

    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        path = root / "dotlineform-projects/documents/project.md"
        write_doc(
            root,
            "dotlineform-projects/documents",
            "project.md",
            {
                "doc_id": FIXTURE_DOC_ID,
                "title": "Project",
                "folder_path": "projects/Future Folder",
            },
        )
        source_model.DOCS_SCOPE_CONFIGS.clear()
        source_model.DOCS_SCOPE_CONFIGS["dotlineform"] = parent_config
        try:
            docs = source_model.load_document_collection_docs(
                root,
                "dotlineform",
                "projects",
            )
            path.write_text(
                source_model.format_source(
                    {
                        "doc_id": FIXTURE_DOC_ID,
                        "title": "Project",
                        "folder_path": "/absolute/not-stored",
                    },
                    "# Project\n",
                ),
                encoding="utf-8",
            )
            malformed_docs = source_model.load_document_collection_docs(
                root,
                "dotlineform",
                "projects",
            )
        finally:
            source_model.DOCS_SCOPE_CONFIGS.clear()
            source_model.DOCS_SCOPE_CONFIGS.update(original_configs)

    assert docs[0].front_matter["folder_path"] == "projects/Future Folder"
    assert malformed_docs[0].front_matter["folder_path"] == "/absolute/not-stored"


def test_atomic_new_source_write_refuses_existing_destination() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        existing = root / "existing.md"
        created = root / "created.md"
        existing.write_text("original\n", encoding="utf-8")

        try:
            source_model.write_text_atomic_new(existing, "replacement\n")
        except FileExistsError as exc:
            assert "source path already exists" in str(exc)
        else:
            raise AssertionError("atomic new source write should refuse overwrite")
        source_model.write_text_atomic_new(created, "created\n")

        assert existing.read_text(encoding="utf-8") == "original\n"
        assert created.read_text(encoding="utf-8") == "created\n"


def test_atomic_source_write_failure_preserves_existing_file() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        existing = root / "existing.md"
        existing.write_text("original\n", encoding="utf-8")
        original_replace = source_model.os.replace

        def fail_replace(_source: Path, _target: Path) -> None:
            raise OSError("simulated replace failure")

        source_model.os.replace = fail_replace
        try:
            try:
                source_model.write_text_atomic(existing, "replacement\n")
            except OSError as exc:
                assert "simulated replace failure" in str(exc)
            else:
                raise AssertionError("atomic source write failure should propagate")
        finally:
            source_model.os.replace = original_replace

        assert existing.read_text(encoding="utf-8") == "original\n"
        assert list(root.glob("existing.md.*.tmp")) == []


def test_load_scope_docs_rejects_duplicate_doc_ids() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        write_doc(root, "docs-viewer/scopes/studio/source/documents", "first.md", {"doc_id": FIXTURE_DOC_ID, "title": "First"})
        write_doc(root, "docs-viewer/scopes/studio/source/documents", "second.md", {"doc_id": FIXTURE_DOC_ID, "title": "Second"})
        configure_repository_scope(root)

        try:
            source_model.load_scope_docs(root, "studio")
        except ValueError as error:
            message = str(error)
        else:
            raise AssertionError("duplicate doc_id should fail")

    assert f"Duplicate doc_id '{FIXTURE_DOC_ID}'" in message


def test_load_scope_docs_rejects_missing_doc_id() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        write_doc(root, "docs-viewer/scopes/studio/source/documents", "missing.md", {"title": "Missing"})
        configure_repository_scope(root)

        try:
            source_model.load_scope_docs(root, "studio")
        except ValueError as error:
            message = str(error)
        else:
            raise AssertionError("missing doc_id should fail")

    assert "missing required doc_id in missing.md" in message


def test_load_scope_docs_rejects_unknown_studio_parent() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        write_doc(
            root,
            "docs-viewer/scopes/studio/source/documents",
            "child.md",
            {"doc_id": FIXTURE_DOC_ID, "title": "Child", "parent_id": "missing"},
        )
        configure_repository_scope(root)

        try:
            source_model.load_scope_docs(root, "studio")
        except ValueError as error:
            message = str(error)
        else:
            raise AssertionError("unknown Studio parent_id should fail")

    assert f"Unknown parent_id 'missing' for doc '{FIXTURE_DOC_ID}'" in message


def test_title_order_and_child_helpers_are_stable() -> None:
    parent = make_doc("parent", title="Parent")
    first = make_doc("first", title="bravo", parent_id="parent")
    second = make_doc("second", title="Alpha", parent_id="parent")
    blank = make_doc("blank", title="alpha", parent_id="parent")
    docs = [parent, first, second, blank]

    assert [doc.doc_id for doc in source_model.sorted_siblings(docs, "parent")] == ["blank", "second", "first"]
    assert source_model.direct_child_doc_ids(docs, "parent") == ["blank", "second", "first"]


def test_descendant_helper_handles_cycles_without_looping() -> None:
    alpha = make_doc("alpha", parent_id="beta")
    beta = make_doc("beta", parent_id="alpha")

    assert source_model.descendant_doc_ids([alpha, beta], "alpha") == {"alpha", "beta"}


def test_source_rewrite_advances_only_for_recent_edit_content() -> None:
    original_timestamp = source_model.current_doc_timestamp
    source_model.current_doc_timestamp = lambda: "2026-05-09 13:00:00"
    try:
        doc = make_doc("sample", title="Sample", parent_id="parent")
        doc.front_matter["sort_order"] = 10
        doc.front_matter["added_date"] = "2026-01-01"
        doc.front_matter["last_updated"] = "2026-01-02 09:00"

        doc.front_matter["publishable"] = True

        metadata_text = source_model.rewrite_doc_source(doc, {"title": "Updated", "publishable": False})
        placement_text = source_model.rewrite_doc_placement_source(doc, "")
    finally:
        source_model.current_doc_timestamp = original_timestamp

    with tempfile.TemporaryDirectory() as temp:
        metadata_path = Path(temp) / "metadata.md"
        placement_path = Path(temp) / "placement.md"
        metadata_path.write_text(metadata_text, encoding="utf-8")
        placement_path.write_text(placement_text, encoding="utf-8")
        metadata_front_matter, _ = source_model.parse_source(metadata_path)
        placement_front_matter, _ = source_model.parse_source(placement_path)

    assert metadata_front_matter == {
        "doc_id": "sample",
        "title": "Updated",
        "added_date": "2026-01-01",
        "last_updated": "2026-05-09 13:00:00",
        "parent_id": "parent",
        "publishable": False,
    }
    assert placement_front_matter == {
        "doc_id": "sample",
        "title": "Sample",
        "added_date": "2026-01-01",
        "last_updated": "2026-01-02 09:00",
        "parent_id": "",
        "publishable": True,
    }


def test_recent_edit_content_positive_allowlist_is_body_title_and_summary() -> None:
    previous = {
        "doc_id": "sample",
        "title": "Title",
        "summary": "Summary",
        "parent_id": "",
        "future_field": "old",
    }
    structural = {
        **previous,
        "parent_id": "parent",
        "future_field": "new",
    }

    assert source_model.recent_edit_content(previous, "# Body\n") == source_model.recent_edit_content(
        structural,
        "# Body\n",
    )
    assert source_model.recent_edit_content(previous, "# Body\n") != source_model.recent_edit_content(
        {**structural, "title": "Changed"},
        "# Body\n",
    )
    assert source_model.recent_edit_content(previous, "# Body\n") != source_model.recent_edit_content(
        {**structural, "summary": "Changed"},
        "# Body\n",
    )
    assert source_model.recent_edit_content(previous, "# Body\n") != source_model.recent_edit_content(
        structural,
        "# Changed body\n",
    )


def test_advance_doc_front_matter_requires_a_full_timestamp() -> None:
    try:
        source_model.advance_doc_front_matter({}, timestamp="2026-07-16")
    except ValueError as exc:
        assert "YYYY-MM-DD HH:MM:SS" in str(exc)
    else:
        raise AssertionError("date-only document write timestamp should be rejected")


def test_strictly_later_doc_timestamp_handles_same_second_and_invalid_history() -> None:
    assert source_model.strictly_later_doc_timestamp(
        "2026-07-16 10:00:00",
        "2026-07-16 10:00:01",
    ) == "2026-07-16 10:00:01"
    assert source_model.strictly_later_doc_timestamp(
        "2026-07-16 10:00:00",
        "2026-07-16 10:00:00",
    ) == "2026-07-16 10:00:01"
    assert source_model.strictly_later_doc_timestamp(
        "2026-07-16 10:00:00",
        "2026-07-16 09:59:59",
    ) == "2026-07-16 10:00:01"
    assert source_model.strictly_later_doc_timestamp(
        "2026-07-16",
        "2026-07-16 10:00:00",
    ) == "2026-07-16 10:00:00"

    try:
        source_model.strictly_later_doc_timestamp(
            "2026-07-16 10:00:00",
            "2026-07-16",
        )
    except ValueError as exc:
        assert "YYYY-MM-DD HH:MM:SS" in str(exc)
    else:
        raise AssertionError("invalid captured timestamp should be rejected")


def test_timestamp_rewrite_preserves_unrelated_raw_front_matter() -> None:
    front_matter_source = (
        "---\r\n"
        "# retained comment\r\n"
        'title: "Retained title"\r\n'
        "last_updated: 2026-07-16 10:00:00\r\n"
        "custom_field: retained\r\n"
        "---\r\n"
    )

    rewritten = source_model.rewrite_front_matter_source_timestamp(
        front_matter_source,
        {
            "title": "Retained title",
            "added_date": "2026-07-15 09:00:00",
            "last_updated": "2026-07-16 10:00:00",
            "custom_field": "retained",
        },
        timestamp="2026-07-16 10:00:01",
    )

    assert rewritten == (
        "---\r\n"
        "# retained comment\r\n"
        'title: "Retained title"\r\n'
        'added_date: "2026-07-15 09:00:00"\r\n'
        'last_updated: "2026-07-16 10:00:01"\r\n'
        "custom_field: retained\r\n"
        "---\r\n"
    )


def test_allocate_doc_id_uses_timestamp_and_retries_collisions() -> None:
    tokens = iter(["abcdef", "123abc"])

    doc_id = source_model.allocate_doc_id(
        "2026-07-15 09:44:11",
        {"d-20260715-094411-abcdef"},
        token_factory=lambda _bytes: next(tokens),
    )

    assert doc_id == "d-20260715-094411-123abc"
    assert source_model.is_immutable_doc_id(doc_id) is True
    assert source_model.is_immutable_doc_id("document-title") is False


def main() -> None:
    tests = [
        test_front_matter_parses_and_formats_supported_scalar_values,
        test_scope_loader_preserves_exact_source_bytes_and_newlines,
        test_document_collection_loader_selects_exact_configured_sub_scope,
        test_atomic_new_source_write_refuses_existing_destination,
        test_atomic_source_write_failure_preserves_existing_file,
        test_load_scope_docs_rejects_duplicate_doc_ids,
        test_load_scope_docs_rejects_unknown_studio_parent,
        test_title_order_and_child_helpers_are_stable,
        test_descendant_helper_handles_cycles_without_looping,
        test_source_rewrite_advances_only_for_recent_edit_content,
        test_recent_edit_content_positive_allowlist_is_body_title_and_summary,
        test_advance_doc_front_matter_requires_a_full_timestamp,
        test_strictly_later_doc_timestamp_handles_same_second_and_invalid_history,
        test_timestamp_rewrite_preserves_unrelated_raw_front_matter,
        test_allocate_doc_id_uses_timestamp_and_retries_collisions,
    ]
    for test in tests:
        test()


if __name__ == "__main__":
    main()
