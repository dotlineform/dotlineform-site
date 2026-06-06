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
        path=Path(f"docs-viewer/source/studio/{stem or doc_id}.md"),
        source_text=source_model.format_source(front_matter, body),
        front_matter=front_matter,
        body=body,
        doc_id=doc_id,
        title=str(front_matter["title"]),
        ui_status="",
        parent_id=parent_id,
        viewable=True,
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


def test_load_scope_docs_rejects_duplicate_doc_ids() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        write_doc(root, "docs-viewer/source/studio", "first.md", {"doc_id": "duplicate", "title": "First"})
        write_doc(root, "docs-viewer/source/studio", "second.md", {"doc_id": "duplicate", "title": "Second"})

        try:
            source_model.load_scope_docs(root, "studio")
        except ValueError as error:
            message = str(error)
        else:
            raise AssertionError("duplicate doc_id should fail")

    assert "Duplicate doc_id 'duplicate'" in message


def test_load_scope_docs_rejects_unknown_studio_parent() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        write_doc(root, "docs-viewer/source/studio", "child.md", {"doc_id": "child", "title": "Child", "parent_id": "missing"})

        try:
            source_model.load_scope_docs(root, "studio")
        except ValueError as error:
            message = str(error)
        else:
            raise AssertionError("unknown Studio parent_id should fail")

    assert "Unknown parent_id 'missing' for doc 'child'" in message


def test_load_scope_docs_allows_unknown_library_parent() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        write_doc(
            root,
            "docs-viewer/source/library",
            "child.md",
            {"doc_id": "child", "title": "Child", "parent_id": "external-parent"},
        )

        docs = source_model.load_scope_docs(root, "library")

    assert [doc.doc_id for doc in docs] == ["child"]
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


def test_source_rewrite_preserves_doc_dates_and_normalizes_front_matter() -> None:
    original_timestamp = source_model.current_doc_timestamp
    source_model.current_doc_timestamp = lambda: "2026-05-09 13:00"
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
        "last_updated": "2026-01-02 09:00",
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


def test_ensure_unique_stem_checks_existing_stems_and_doc_ids() -> None:
    docs = [
        make_doc("first-doc", stem="first-doc"),
        make_doc("alternate-id", stem="first-doc-2"),
    ]

    assert source_model.ensure_unique_stem(docs, "First Doc") == "first-doc-3"


def main() -> None:
    tests = [
        test_front_matter_parses_and_formats_supported_scalar_values,
        test_load_scope_docs_rejects_duplicate_doc_ids,
        test_load_scope_docs_rejects_unknown_studio_parent,
        test_load_scope_docs_allows_unknown_library_parent,
        test_title_order_and_child_helpers_are_stable,
        test_descendant_helper_handles_cycles_without_looping,
        test_source_rewrite_preserves_doc_dates_and_normalizes_front_matter,
        test_ensure_unique_stem_checks_existing_stems_and_doc_ids,
    ]
    for test in tests:
        test()


if __name__ == "__main__":
    main()
