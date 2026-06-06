#!/usr/bin/env python3
"""Focused checks for the Python Docs Viewer search builder."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
BUILD_DIR = REPO_ROOT / "docs-viewer" / "build"
if str(BUILD_DIR) not in sys.path:
    sys.path.insert(0, str(BUILD_DIR))

import build_search  # noqa: E402


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_scope_config(root: Path) -> None:
    write_json(
        root / "docs-viewer/config/scopes/docs_scopes.json",
        {
            "schema_version": "docs_scopes_v1",
            "scopes": [
                {
                    "scope_id": "studio",
                    "scope_type": "local",
                    "source": "docs-viewer/source/studio",
                    "media_path_prefix": "docs/studio",
                    "output": "docs-viewer/generated/docs/studio",
                    "search_output": "docs-viewer/generated/search/studio/index.json",
                    "viewer_base_url": "/docs/",
                    "include_scope_param": True,
                    "default_doc_id": "parent",
                    "allow_nested_source": False,
                    "non_loadable_doc_ids": [],
                    "manage_only_tree_root_ids": ["manage-root"],
                    "show_updated_date": True,
                    "allow_unresolved_parent_ids": False,
                }
            ],
        },
    )


def write_source_docs(root: Path, *, child_title: str = "Child", child_viewable: bool = True) -> None:
    rows = [
        ("parent", "Parent Page", "2026-06-01", "", True),
        ("child", child_title, "2026-06-02", "parent", child_viewable),
        ("draft", "Draft", "2026-06-03", "", False),
        ("draft-child", "Draft Child", "2026-06-04", "draft", True),
        ("manage-root", "Manage Root", "2026-06-04", "", True),
        ("manage-child", "Manage Child", "2026-06-05", "manage-root", True),
    ]
    for doc_id, title, last_updated, parent_id, viewable in rows:
        viewable_line = "" if viewable else "viewable: false\n"
        parent_line = f"parent_id: {parent_id}\n" if parent_id else ""
        write_text(
            root / f"docs-viewer/source/studio/{doc_id}.md",
            f"""---
doc_id: {doc_id}
title: {json.dumps(title)}
last_updated: {last_updated}
{parent_line}{viewable_line}---
# {title}

Search source body.
""",
        )


def prepare_repo(root: Path) -> None:
    write_scope_config(root)
    write_source_docs(root)


def run_cli(root: Path, args: list[str]) -> tuple[int, str, str]:
    cwd = Path.cwd()
    stdout = StringIO()
    stderr = StringIO()
    try:
        os.chdir(root)
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = build_search.main(args)
    finally:
        os.chdir(cwd)
    return exit_code, stdout.getvalue(), stderr.getvalue()


def test_python_docs_search_builder_writes_current_schema_and_hash() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        exit_code, stdout, stderr = run_cli(root, ["--scope", "studio", "--write"])
        payload = read_json(root / "docs-viewer/generated/search/studio/index.json")

    assert exit_code == 0
    assert stderr == ""
    assert "Wrote docs-viewer/generated/search/studio/index.json with 2 studio search entries" in stdout
    header = payload["header"]
    entries = payload["entries"]
    assert header["schema"] == "search_index_studio_v1"
    assert header["scope"] == "studio"
    assert header["version"].startswith("blake2b-")
    assert header["count"] == 2
    assert [entry["id"] for entry in entries] == ["parent", "child"]
    child = entries[1]
    assert child["kind"] == "doc"
    assert child["href"] == "/docs/?scope=studio&doc=child"
    assert child["parent_title"] == "Parent Page"
    assert child["display_meta"] == "2026-06-02 • Parent Page"
    assert child["search_terms"] == [
        "child",
        "parent page",
        "parent",
        "page",
        "2026-06-02",
        "2026",
        "06",
        "02",
    ]
    assert child["search_text"] == " ".join(child["search_terms"])


def test_python_docs_search_builder_dry_run_does_not_write() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        exit_code, stdout, stderr = run_cli(root, ["--scope", "studio"])

        assert exit_code == 0
        assert stderr == ""
        assert "Dry run: 2 studio search entries" in stdout
        assert "Would write: docs-viewer/generated/search/studio/index.json" in stdout
        assert not (root / "docs-viewer/generated/search/studio/index.json").exists()


def test_python_docs_search_builder_skips_unchanged_second_write_and_force_rewrites() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        run_cli(root, ["--scope", "studio", "--write"])
        first_payload = read_json(root / "docs-viewer/generated/search/studio/index.json")
        second_exit, second_stdout, second_stderr = run_cli(root, ["--scope", "studio", "--write"])
        force_exit, force_stdout, force_stderr = run_cli(root, ["--scope", "studio", "--write", "--force"])
        force_payload = read_json(root / "docs-viewer/generated/search/studio/index.json")

    assert second_exit == 0
    assert second_stderr == ""
    assert "Search index JSON done. Wrote: 0. Skipped: 1." in second_stdout
    assert force_exit == 0
    assert force_stderr == ""
    assert "Wrote docs-viewer/generated/search/studio/index.json with 2 studio search entries" in force_stdout
    assert force_payload["header"]["version"] == first_payload["header"]["version"]


def test_python_docs_search_builder_targeted_update_patches_existing_entry() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        run_cli(root, ["--scope", "studio", "--write"])
        write_source_docs(root, child_title="Child Updated")

        exit_code, stdout, stderr = run_cli(root, ["--scope", "studio", "--write", "--only-doc-ids", "child", "--remove-missing"])
        payload = read_json(root / "docs-viewer/generated/search/studio/index.json")

    assert exit_code == 0
    assert stderr == ""
    assert "Targeted search index JSON done. Wrote: 1. Skipped: 0. Changed: 1. Removed: 0. Unchanged: 0. Full fallback: 0." in stdout
    assert [entry["id"] for entry in payload["entries"]] == ["parent", "child"]
    assert payload["entries"][1]["title"] == "Child Updated"


def test_python_docs_search_builder_targeted_remove_requires_remove_missing() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        run_cli(root, ["--scope", "studio", "--write"])
        write_source_docs(root, child_viewable=False)

        try:
            run_cli(root, ["--scope", "studio", "--write", "--only-doc-ids", "child"])
        except SystemExit as exc:
            error = str(exc)
        else:
            raise AssertionError("targeted removal without --remove-missing should fail")

        exit_code, stdout, stderr = run_cli(root, ["--scope", "studio", "--write", "--only-doc-ids", "child", "--remove-missing"])
        payload = read_json(root / "docs-viewer/generated/search/studio/index.json")

    assert "requires --remove-missing" in error
    assert exit_code == 0
    assert stderr == ""
    assert "Changed: 0. Removed: 1. Unchanged: 0. Full fallback: 0." in stdout
    assert [entry["id"] for entry in payload["entries"]] == ["parent"]


def test_python_docs_search_builder_targeted_without_existing_index_falls_back_full() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        exit_code, stdout, stderr = run_cli(root, ["--scope", "studio", "--write", "--only-doc-ids", "child", "--remove-missing"])
        payload = read_json(root / "docs-viewer/generated/search/studio/index.json")

    assert exit_code == 0
    assert stderr == ""
    assert "Changed: 2. Removed: 0. Unchanged: 0. Full fallback: 1." in stdout
    assert [entry["id"] for entry in payload["entries"]] == ["parent", "child"]


def test_python_docs_search_builder_rejects_catalogue_targeted_records_flag() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        try:
            run_cli(root, ["--scope", "studio", "--only-records", "work:00001"])
        except SystemExit as exc:
            error = str(exc)
        else:
            raise AssertionError("--only-records should fail for docs search")

    assert error == "Docs Viewer search does not support --only-records"


def main() -> None:
    test_python_docs_search_builder_writes_current_schema_and_hash()
    test_python_docs_search_builder_dry_run_does_not_write()
    test_python_docs_search_builder_skips_unchanged_second_write_and_force_rewrites()
    test_python_docs_search_builder_targeted_update_patches_existing_entry()
    test_python_docs_search_builder_targeted_remove_requires_remove_missing()
    test_python_docs_search_builder_targeted_without_existing_index_falls_back_full()
    test_python_docs_search_builder_rejects_catalogue_targeted_records_flag()
    print("Python Docs Viewer search builder tests OK")


if __name__ == "__main__":
    main()
