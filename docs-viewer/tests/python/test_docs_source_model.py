#!/usr/bin/env python3
"""Focused checks for Docs Viewer source-model helpers."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
if str(DOCS_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(DOCS_SERVICES_DIR))

import docs_source_model as source_model  # noqa: E402


FIXTURE_DOC_ID = "d-20260101-000000-000001"


def write_doc(root: Path, scope_root: str, filename: str, front_matter: dict[str, object], body: str = "# Body\n") -> None:
    path = root / scope_root / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source_model.format_source(front_matter, body), encoding="utf-8")


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
        path=Path(f"docs-viewer/source/studio/documents/{stem or doc_id}.md"),
        source_text=source_model.format_source(front_matter, body),
        front_matter=front_matter,
        body=body,
        doc_id=doc_id,
        title=str(front_matter["title"]),
        ui_status="",
        parent_id=parent_id,
        viewable=True,
    )


def test_default_viewability_follows_scope_type() -> None:
    assert source_model.default_viewable_for_scope("library") is False
    assert source_model.default_viewable_for_scope("analysis") is False
    assert source_model.default_viewable_for_scope("moments") is False
    assert source_model.default_viewable_for_scope("studio") is True


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
                    "viewable: false",
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
    assert front_matter["viewable"] is False
    assert front_matter["summary"] == ""
    assert "parent_id: \"\"" in formatted
    assert "viewable: false" in formatted


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


def test_load_scope_docs_rejects_duplicate_doc_ids() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        write_doc(root, "docs-viewer/source/studio/documents", "first.md", {"doc_id": FIXTURE_DOC_ID, "title": "First"})
        write_doc(root, "docs-viewer/source/studio/documents", "second.md", {"doc_id": FIXTURE_DOC_ID, "title": "Second"})

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
        write_doc(root, "docs-viewer/source/studio/documents", "missing.md", {"title": "Missing"})

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
            "docs-viewer/source/studio/documents",
            "child.md",
            {"doc_id": FIXTURE_DOC_ID, "title": "Child", "parent_id": "missing"},
        )

        try:
            source_model.load_scope_docs(root, "studio")
        except ValueError as error:
            message = str(error)
        else:
            raise AssertionError("unknown Studio parent_id should fail")

    assert f"Unknown parent_id 'missing' for doc '{FIXTURE_DOC_ID}'" in message


def test_load_scope_docs_allows_unknown_library_parent() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        write_doc(
            root,
            "docs-viewer/source/library/documents",
            "child.md",
            {"doc_id": FIXTURE_DOC_ID, "title": "Child", "parent_id": "external-parent"},
        )

        docs = source_model.load_scope_docs(root, "library")

    assert [doc.doc_id for doc in docs] == [FIXTURE_DOC_ID]
    assert docs[0].parent_id == "external-parent"


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

        doc.front_matter["viewable"] = True

        metadata_text = source_model.rewrite_doc_source(doc, {"title": "Updated", "viewable": False})
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
        "viewable": False,
    }
    assert placement_front_matter == {
        "doc_id": "sample",
        "title": "Sample",
        "added_date": "2026-01-01",
        "last_updated": "2026-01-02 09:00",
        "parent_id": "",
        "viewable": True,
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
        test_atomic_new_source_write_refuses_existing_destination,
        test_load_scope_docs_rejects_duplicate_doc_ids,
        test_load_scope_docs_rejects_unknown_studio_parent,
        test_load_scope_docs_allows_unknown_library_parent,
        test_title_order_and_child_helpers_are_stable,
        test_descendant_helper_handles_cycles_without_looping,
        test_source_rewrite_advances_only_for_recent_edit_content,
        test_recent_edit_content_positive_allowlist_is_body_title_and_summary,
        test_advance_doc_front_matter_requires_a_full_timestamp,
        test_allocate_doc_id_uses_timestamp_and_retries_collisions,
    ]
    for test in tests:
        test()


if __name__ == "__main__":
    main()
