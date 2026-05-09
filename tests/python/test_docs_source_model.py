#!/usr/bin/env python3
"""Focused checks for Docs Viewer source-model helpers."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DOCS_DIR = REPO_ROOT / "scripts" / "docs"
if str(SCRIPTS_DOCS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DOCS_DIR))

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
    sort_order: int | None = None,
    stem: str | None = None,
) -> source_model.ScopeDoc:
    front_matter: dict[str, object] = {
        "doc_id": doc_id,
        "title": title or doc_id.title(),
        "parent_id": parent_id,
    }
    if sort_order is not None:
        front_matter["sort_order"] = sort_order
    body = f"# {front_matter['title']}\n"
    return source_model.ScopeDoc(
        scope="studio",
        path=Path(f"_docs/{stem or doc_id}.md"),
        source_text=source_model.format_source(front_matter, body),
        front_matter=front_matter,
        body=body,
        doc_id=doc_id,
        title=str(front_matter["title"]),
        ui_status="",
        parent_id=parent_id,
        sort_order=sort_order,
        published=True,
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
                    "sort_order: 20",
                    "published: false",
                    "viewable: true",
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
    assert front_matter["sort_order"] == 20
    assert front_matter["published"] is False
    assert front_matter["viewable"] is True
    assert front_matter["summary"] == ""
    assert "parent_id: \"\"" in formatted
    assert "sort_order: 20" in formatted
    assert "published: false" in formatted
    assert "viewable: true" in formatted


def test_load_scope_docs_rejects_duplicate_doc_ids() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        write_doc(root, "_docs", "first.md", {"doc_id": "duplicate", "title": "First"})
        write_doc(root, "_docs", "second.md", {"doc_id": "duplicate", "title": "Second"})

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
        write_doc(root, "_docs", "child.md", {"doc_id": "child", "title": "Child", "parent_id": "missing"})

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
            "_docs_library",
            "child.md",
            {"doc_id": "child", "title": "Child", "parent_id": "external-parent"},
        )

        docs = source_model.load_scope_docs(root, "library")

    assert [doc.doc_id for doc in docs] == ["child"]
    assert docs[0].parent_id == "external-parent"


def test_sort_order_and_child_helpers_are_stable() -> None:
    parent = make_doc("parent", title="Parent")
    first = make_doc("first", title="First", parent_id="parent", sort_order=20)
    second = make_doc("second", title="Second", parent_id="parent", sort_order=10)
    blank = make_doc("blank", title="Blank", parent_id="parent")
    docs = [parent, first, second, blank]

    assert source_model.next_sort_order(docs, "parent") == 30
    assert [doc.doc_id for doc in source_model.sorted_siblings(docs, "parent")] == ["second", "first", "blank"]
    assert source_model.create_sort_order_after(docs, first) == 21
    assert source_model.create_sort_order_after(docs, blank) == 30
    assert source_model.direct_child_doc_ids(docs, "parent") == ["second", "first", "blank"]


def test_descendant_helper_handles_cycles_without_looping() -> None:
    alpha = make_doc("alpha", parent_id="beta")
    beta = make_doc("beta", parent_id="alpha")

    assert source_model.descendant_doc_ids([alpha, beta], "alpha") == {"alpha", "beta"}


def test_move_placement_normalizes_inside_and_after_positions() -> None:
    parent = make_doc("parent", title="Parent")
    target = make_doc("target", title="Target", parent_id="parent", sort_order=10)
    sibling = make_doc("sibling", title="Sibling", parent_id="parent", sort_order=20)
    moving = make_doc("moving", title="Moving", parent_id="", sort_order=10)
    docs = [parent, target, sibling, moving]

    inside = source_model.normalized_move_placements(docs, moving, parent, "inside")
    after = source_model.normalized_move_placements(docs, moving, target, "after")

    assert [(doc.doc_id, parent_id, sort_order) for doc, parent_id, sort_order in inside] == [
        ("target", "parent", 10),
        ("sibling", "parent", 20),
        ("moving", "parent", 30),
    ]
    assert [(doc.doc_id, parent_id, sort_order) for doc, parent_id, sort_order in after] == [
        ("target", "parent", 10),
        ("moving", "parent", 20),
        ("sibling", "parent", 30),
    ]


def test_source_rewrite_preserves_added_date_updates_last_updated_and_removes_blank_sort_order() -> None:
    original_timestamp = source_model.current_doc_timestamp
    source_model.current_doc_timestamp = lambda: "2026-05-09 13:00"
    try:
        doc = make_doc("sample", title="Sample", parent_id="parent", sort_order=10)
        doc.front_matter["added_date"] = "2026-01-01"
        doc.front_matter["last_updated"] = "2026-01-02 09:00"

        metadata_text = source_model.rewrite_doc_source(doc, {"title": "Updated", "viewable": False})
        placement_text = source_model.rewrite_doc_placement_source(doc, "", None)
    finally:
        source_model.current_doc_timestamp = original_timestamp

    assert "added_date: 2026-01-01" in metadata_text
    assert 'last_updated: "2026-05-09 13:00"' in metadata_text
    assert "title: Updated" in metadata_text
    assert "viewable: false" in metadata_text
    assert "parent_id: \"\"" in placement_text
    assert "sort_order:" not in placement_text


def test_ensure_unique_stem_checks_existing_stems_and_doc_ids() -> None:
    docs = [
        make_doc("first-doc", stem="first-doc"),
        make_doc("legacy-id", stem="first-doc-2"),
    ]

    assert source_model.ensure_unique_stem(docs, "First Doc") == "first-doc-3"


def main() -> None:
    tests = [
        test_front_matter_parses_and_formats_supported_scalar_values,
        test_load_scope_docs_rejects_duplicate_doc_ids,
        test_load_scope_docs_rejects_unknown_studio_parent,
        test_load_scope_docs_allows_unknown_library_parent,
        test_sort_order_and_child_helpers_are_stable,
        test_descendant_helper_handles_cycles_without_looping,
        test_move_placement_normalizes_inside_and_after_positions,
        test_source_rewrite_preserves_added_date_updates_last_updated_and_removes_blank_sort_order,
        test_ensure_unique_stem_checks_existing_stems_and_doc_ids,
    ]
    for test in tests:
        test()


if __name__ == "__main__":
    main()
