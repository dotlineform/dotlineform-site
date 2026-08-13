#!/usr/bin/env python3
"""Focused checks for the Python Docs Viewer search builder."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from typing import Any

from repo_factory import docs_scope_record, docs_sub_scope_record


REPO_ROOT = Path(__file__).resolve().parents[3]
BUILD_DIR = REPO_ROOT / "docs-viewer" / "build"
V2_CONTRACT_FIXTURE = REPO_ROOT / "docs-viewer/tests/fixtures/docs_viewer_search_v2_contract.json"
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
            "schema_version": "docs_scopes_v4",
            "media_workspace": {
                "location": {
                    "provider": "external_local",
                    "path": "$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/media",
                }
            },
            "scopes": [
                docs_scope_record(
                    "studio",
                    default_doc_id="parent",
                    manage_only_tree_root_ids=["manage-root"],
                )
            ],
        },
    )


def write_external_scope_config(root: Path, external_root: Path) -> None:
    del external_root
    write_json(
        root / "docs-viewer/config/scopes/docs_scopes.json",
        {
            "schema_version": "docs_scopes_v4",
            "media_workspace": {
                "location": {
                    "provider": "external_local",
                    "path": "$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/media",
                }
            },
            "scopes": [
                docs_scope_record(
                    "private",
                    scope_type="local_external",
                    default_doc_id="private",
                )
            ],
        },
    )


def write_source_docs(root: Path, *, child_title: str = "Child") -> None:
    rows = [
        ("parent", "Parent Page", "2026-06-01", ""),
        ("child", child_title, "2026-06-02", "parent"),
        ("draft", "Draft", "2026-06-03", ""),
        ("draft-child", "Draft Child", "2026-06-04", "draft"),
        ("manage-root", "Manage Root", "2026-06-04", ""),
        ("manage-child", "Manage Child", "2026-06-05", "manage-root"),
    ]
    for doc_id, title, last_updated, parent_id in rows:
        parent_line = f"parent_id: {parent_id}\n" if parent_id else ""
        write_text(
            root / f"docs-viewer/scopes/studio/source/documents/{doc_id}.md",
            f"""---
doc_id: {doc_id}
title: {json.dumps(title)}
last_updated: {last_updated}
{parent_line}---
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
        payload = read_json(root / "docs-viewer/scopes/studio/published/search/index.json")

    assert exit_code == 0
    assert stderr == ""
    assert "Wrote docs-viewer/scopes/studio/published/search/index.json with 4 studio search docs" in stdout
    header = payload["header"]
    docs = payload["docs"]
    assert header["schema"] == "docs_viewer_search_index_v2"
    assert header["scope"] == "studio"
    assert header["version"].startswith("blake2b-")
    assert header["count"] == 4
    assert payload["fields"] == ["title", "parent_title", "identity", "last_updated"]
    assert [document["id"] for document in docs] == ["child", "draft", "draft-child", "parent"]
    child = docs[0]
    assert child["href"] == "/docs/?scope=studio&doc=child"
    assert child["parent_title"] == "Parent Page"
    assert child["display_meta"] == "2026-06-02 • Parent Page"
    assert payload["terms"]["child"] == {"title": [0, 2], "identity": [0]}
    assert payload["terms"]["parent"] == {
        "title": [3],
        "parent_title": [0],
        "identity": [3],
    }


def test_v2_tokenizer_and_index_match_shared_contract_fixture() -> None:
    fixture = read_json(V2_CONTRACT_FIXTURE)
    for case in fixture["tokenizer_cases"]:
        assert build_search.tokenize_search_value_v2(case["value"]) == case["terms"]

    payload = build_search.build_search_index_v2(
        scope="studio",
        documents=fixture["documents"],
        search_fields=tuple(fixture["fields"]),
        generated_at_utc="2026-08-13T00:00:00Z",
    )
    reversed_payload = build_search.build_search_index_v2(
        scope="studio",
        documents=list(reversed(fixture["documents"])),
        search_fields=tuple(fixture["fields"]),
        generated_at_utc="2026-08-13T00:00:00Z",
    )

    assert payload == reversed_payload
    assert payload["header"]["schema"] == "docs_viewer_search_index_v2"
    assert payload["fields"] == fixture["fields"]
    assert [document["id"] for document in payload["docs"]] == fixture["expected_document_ids"]
    for term, postings in fixture["expected_postings"].items():
        assert payload["terms"][term] == postings


def test_builder_rebuilds_whole_index_and_skips_identical_output() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        output_path = root / "docs-viewer/scopes/studio/published/search/index.json"
        builder = build_search.DocsViewerSearchDataBuilder(repo_root=root, scope="studio")
        initial, _initial_diagnostics = builder.build_docs_v2_payload(
            changed_doc_ids=["child"],
            generated_at_utc="2026-08-13T00:00:00Z",
        )
        builder.write_payload(initial, write=True, force=False)

        write_source_docs(root, child_title="Child Updated")
        write_text(
            root / "docs-viewer/scopes/studio/source/documents/created.md",
            "---\ndoc_id: created\ntitle: Created\nlast_updated: 2026-08-13\n---\n# Created\n",
        )
        (root / "docs-viewer/scopes/studio/source/documents/parent.md").unlink()
        changed, diagnostics = builder.build_docs_v2_payload(
            changed_doc_ids=["child", "created", "parent"],
            generated_at_utc="2026-08-13T00:01:00Z",
        )
        builder.write_payload(changed, write=True, force=False)
        written = output_path.read_text(encoding="utf-8")
        unchanged, _unchanged_diagnostics = builder.build_docs_v2_payload(
            changed_doc_ids=["child"],
            generated_at_utc="2026-08-13T00:02:00Z",
        )
        builder.write_payload(unchanged, write=True, force=False)
        after_skip = output_path.read_text(encoding="utf-8")

    changed_by_id = {document["id"]: document for document in changed["docs"]}
    assert diagnostics["mode"] == "full"
    assert diagnostics["requested_doc_ids"] == ["child", "created", "parent"]
    assert changed_by_id["child"]["title"] == "Child Updated"
    assert "created" in changed_by_id
    assert "parent" not in changed_by_id
    assert "page" not in changed["terms"]
    assert after_skip == written
    assert written == json.dumps(changed, ensure_ascii=False, indent=2) + "\n"


def test_targeted_local_search_build_does_not_resolve_unselected_external_scope() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        write_json(
            root / "docs-viewer/config/scopes/docs_scopes.json",
            {
                "schema_version": "docs_scopes_v4",
                "media_workspace": {
                    "location": {
                        "provider": "external_local",
                        "path": "$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/media",
                    }
                },
                "scopes": [
                    docs_scope_record(
                        "studio",
                        default_doc_id="parent",
                        manage_only_tree_root_ids=["manage-root"],
                    ),
                    docs_scope_record(
                        "private",
                        scope_type="local_external",
                        default_doc_id="private",
                    ),
                ],
            },
        )
        write_source_docs(root)
        unavailable_projects = root / "unavailable-projects"
        env = dict(os.environ)
        env["DOTLINEFORM_PROJECTS_BASE_DIR"] = str(unavailable_projects)
        result = subprocess.run(
            [
                sys.executable,
                str(BUILD_DIR / "build_search.py"),
                "--scope",
                "studio",
            ],
            cwd=root,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    assert result.returncode == 0
    assert result.stderr == ""
    assert "Would write: docs-viewer/scopes/studio/published/search/index.json" in result.stdout


def test_doc_search_keeps_exact_opaque_id_without_fragment_tokens() -> None:
    doc_id = "d-20260715-094411-2b6e65"
    terms = build_search.tokenize_search_value_v2(doc_id)
    payload = build_search.build_search_index_v2(
        scope="studio",
        documents=[{"id": doc_id, "title": "Document Identity", "href": f"/docs/?scope=studio&doc={doc_id}"}],
        search_fields=("title", "identity"),
        generated_at_utc="2026-08-13T00:00:00Z",
    )

    assert terms == []
    assert payload["terms"][doc_id] == {"identity": [0]}


def test_python_docs_search_builder_excludes_configured_sub_scope_sources() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        config_path = root / "docs-viewer/config/scopes/docs_scopes.json"
        payload = read_json(config_path)
        payload["scopes"][0]["sub_scopes"] = [
            docs_sub_scope_record("studio", "tags")
        ]
        write_json(config_path, payload)
        write_text(
            root / "docs-viewer/scopes/studio/source/sub-scopes/tags/documents/detail.md",
            """---
doc_id: detail
title: Detail
---
# Detail

Sub-scope detail body.
""",
        )

        exit_code, stdout, stderr = run_cli(root, ["--scope", "studio", "--write"])
        payload = read_json(root / "docs-viewer/scopes/studio/published/search/index.json")

    assert exit_code == 0
    assert stderr == ""
    assert "Wrote docs-viewer/scopes/studio/published/search/index.json with 4 studio search docs" in stdout
    assert "detail" not in {document["id"] for document in payload["docs"]}


def test_python_docs_search_builder_dry_run_does_not_write() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        exit_code, stdout, stderr = run_cli(root, ["--scope", "studio"])

        assert exit_code == 0
        assert stderr == ""
        assert "Dry run: 4 studio search docs" in stdout
        assert "Would write: docs-viewer/scopes/studio/published/search/index.json" in stdout
        assert not (root / "docs-viewer/scopes/studio/published/search/index.json").exists()


def test_python_docs_search_builder_skips_unchanged_second_write_and_force_rewrites() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        run_cli(root, ["--scope", "studio", "--write"])
        first_payload = read_json(root / "docs-viewer/scopes/studio/published/search/index.json")
        second_exit, second_stdout, second_stderr = run_cli(root, ["--scope", "studio", "--write"])
        force_exit, force_stdout, force_stderr = run_cli(root, ["--scope", "studio", "--write", "--force"])
        force_payload = read_json(root / "docs-viewer/scopes/studio/published/search/index.json")

    assert second_exit == 0
    assert second_stderr == ""
    assert "Search index JSON done. Wrote: 0. Skipped: 1." in second_stdout
    assert force_exit == 0
    assert force_stderr == ""
    assert "Wrote docs-viewer/scopes/studio/published/search/index.json with 4 studio search docs" in force_stdout
    assert force_payload["header"]["version"] == first_payload["header"]["version"]


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


def test_python_docs_search_builder_writes_external_local_scope_index() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        projects_root = (root.parent / f"{root.name}-external").resolve()
        external_root = projects_root / "docs-viewer"
        external_root.mkdir(parents=True)
        old_projects_base = os.environ.get("DOTLINEFORM_PROJECTS_BASE_DIR")
        os.environ["DOTLINEFORM_PROJECTS_BASE_DIR"] = projects_root.as_posix()
        write_external_scope_config(root, external_root)
        write_text(
            external_root / "scopes/private/source/documents/private.md",
            """---
doc_id: private
title: Private Search
last_updated: 2026-06-01
---
# Private Search

External search body.
""",
        )
        try:
            exit_code, stdout, stderr = run_cli(root, ["--scope", "private", "--write"])
            payload = read_json(external_root / "scopes/private/published/search/index.json")
        finally:
            if old_projects_base is None:
                os.environ.pop("DOTLINEFORM_PROJECTS_BASE_DIR", None)
            else:
                os.environ["DOTLINEFORM_PROJECTS_BASE_DIR"] = old_projects_base

    assert exit_code == 0
    assert stderr == ""
    assert "with 1 private search docs" in stdout
    assert payload["header"]["scope"] == "private"
    assert payload["docs"][0]["href"] == "/docs/?scope=private&doc=private"


def main() -> None:
    test_python_docs_search_builder_writes_current_schema_and_hash()
    test_python_docs_search_builder_dry_run_does_not_write()
    test_python_docs_search_builder_skips_unchanged_second_write_and_force_rewrites()
    test_python_docs_search_builder_rejects_catalogue_targeted_records_flag()
    test_python_docs_search_builder_writes_external_local_scope_index()
    print("Python Docs Viewer search builder tests OK")


if __name__ == "__main__":
    main()
