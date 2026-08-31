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


def write_scope_config(
    root: Path,
    *,
    search_fields: list[str] | None = None,
) -> None:
    scope = docs_scope_record(
        "studio",
        default_doc_id="parent",
        manage_only_tree_root_ids=["manage-root"],
    )
    scope["search_fields"] = search_fields or [
        "title",
        "parent_title",
        "identity",
        "last_updated",
    ]
    write_json(
        root / "docs-viewer/config/scopes/docs_scopes.json",
        {
            "schema_version": "docs_scopes_v5",
            "scopes": [scope],
        },
    )


def write_external_scope_config(root: Path, external_root: Path) -> None:
    del external_root
    scope = docs_scope_record(
        "private",
        scope_type="local",
        scope_root_provider="external_local",
        default_doc_id="private",
    )
    scope["search_fields"] = [
        "title",
        "parent_title",
        "identity",
        "last_updated",
    ]
    write_json(
        root / "docs-viewer/config/scopes/docs_scopes.json",
        {
            "schema_version": "docs_scopes_v5",
            "scopes": [scope],
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
        payload = read_json(root / "docs-viewer/scopes/studio/generated/search/index.json")

    assert exit_code == 0
    assert stderr == ""
    assert "Wrote docs-viewer/scopes/studio/generated/search/index.json with 6 studio search docs" in stdout
    header = payload["header"]
    docs = payload["docs"]
    assert header["schema"] == "docs_viewer_search_index_v2"
    assert header["scope"] == "studio"
    assert header["version"].startswith("blake2b-")
    assert header["count"] == 6
    assert payload["fields"] == ["title", "parent_title", "identity", "last_updated"]
    assert [document["id"] for document in docs] == [
        "child",
        "draft",
        "draft-child",
        "manage-child",
        "manage-root",
        "parent",
    ]
    child = docs[0]
    assert child["href"] == "/docs/?scope=studio&doc=child"
    assert child["parent_title"] == "Parent Page"
    assert child["display_meta"] == "2026-06-02 • Parent Page"
    assert payload["terms"]["child"] == {"title": [0, 2, 3], "identity": [0]}
    assert payload["terms"]["parent"] == {
        "title": [5],
        "parent_title": [0],
        "identity": [5],
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


def test_studio_full_text_extracts_visible_fields_without_configuration_leaks() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        write_scope_config(
            root,
            search_fields=["title", "heading", "body", "code"],
        )
        write_source_docs(root)
        write_text(
            root / "docs-viewer/config/reports/reports.json",
            (REPO_ROOT / "docs-viewer/config/reports/reports.json").read_text(encoding="utf-8"),
        )
        write_text(
            root / "docs-viewer/scopes/studio/source/documents/child.md",
            """---
doc_id: d-20260813-000001-aaaaaa
title: "Representative Search"
summary: FrontMatterLeak
last_updated: 2026-06-02
parent_id: parent
---
# Representative Search

## Known `weak` spots

Readable prose with a [compatibility key](https://leak.example/secret-destination) and `DOCS_VIEWER_BASE_URL`.

```python
docs_subscope = handleEditMetadataSave()
```

<section><h3>Raw Visible Heading</h3><p>Visible raw prose <code>raw_html_code</code></p><script>private_script()</script><style>.private_style { color: red; }</style></section>

![Accessible diagram]([[media:docs/studio/img/private-media.png]])

[[html-media:docs/studio/html/private-demo.html]]

[[catalogue:work:01942|Linked Artwork]]

:::report
id: docs_backlinks
access: local
:::
""",
        )

        payload = build_search.DocsViewerSearchDataBuilder(
            repo_root=root,
            scope="studio",
        ).build_docs_v2_payload(generated_at_utc="2026-08-13T00:00:00Z")

    assert payload["fields"] == ["title", "heading", "body", "code"]
    child = payload["docs"][0]
    assert child["id"] == "d-20260813-000001-aaaaaa"
    assert child["parent_title"] == "Parent Page"
    assert child["display_meta"] == "2026-06-02 • Parent Page"
    assert payload["terms"]["representative"] == {"title": [0]}
    assert payload["terms"]["known"] == {"heading": [0]}
    assert payload["terms"]["weak"] == {"heading": [0]}
    assert payload["terms"]["spots"] == {"heading": [0]}
    assert payload["terms"]["compatibility"] == {"body": [0]}
    assert payload["terms"]["visible"] == {"heading": [0], "body": [0]}
    assert payload["terms"]["docs_viewer_base_url"] == {"code": [0]}
    assert payload["terms"]["docs_subscope"] == {"code": [0]}
    assert payload["terms"]["raw_html_code"] == {"code": [0]}
    assert payload["terms"]["accessible"] == {"body": [0]}
    assert payload["terms"]["linked"] == {"body": [0]}
    assert all(
        set(field_postings).issubset({"title", "heading", "body", "code"})
        for field_postings in payload["terms"].values()
    )
    for excluded in (
        "frontmatterleak",
        "secret-destination",
        "private_script",
        "private_style",
        "private-media",
        "private-demo",
        "docs_backlinks",
        "backlinks",
        "catalogue",
        "d-20260813-000001-aaaaaa",
        "2026-06-02",
    ):
        assert excluded not in payload["terms"]


def test_builder_rebuilds_whole_index_and_skips_identical_output() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        output_path = root / "docs-viewer/scopes/studio/generated/search/index.json"
        builder = build_search.DocsViewerSearchDataBuilder(repo_root=root, scope="studio")
        initial = builder.build_docs_v2_payload(
            generated_at_utc="2026-08-13T00:00:00Z",
        )
        builder.write_payload(initial, write=True, force=False)

        write_source_docs(root, child_title="Child Updated")
        write_text(
            root / "docs-viewer/scopes/studio/source/documents/created.md",
            "---\ndoc_id: created\ntitle: Created\nlast_updated: 2026-08-13\n---\n# Created\n",
        )
        (root / "docs-viewer/scopes/studio/source/documents/parent.md").unlink()
        changed = builder.build_docs_v2_payload(
            generated_at_utc="2026-08-13T00:01:00Z",
        )
        builder.write_payload(changed, write=True, force=False)
        written = output_path.read_text(encoding="utf-8")
        unchanged = builder.build_docs_v2_payload(
            generated_at_utc="2026-08-13T00:02:00Z",
        )
        builder.write_payload(unchanged, write=True, force=False)
        after_skip = output_path.read_text(encoding="utf-8")

    changed_by_id = {document["id"]: document for document in changed["docs"]}
    assert changed_by_id["child"]["title"] == "Child Updated"
    assert "created" in changed_by_id
    assert "parent" not in changed_by_id
    assert "page" not in changed["terms"]
    assert after_skip == written
    assert written == json.dumps(changed, ensure_ascii=False, indent=2) + "\n"


def test_selected_scope_search_build_does_not_resolve_unselected_external_scope() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        write_json(
            root / "docs-viewer/config/scopes/docs_scopes.json",
            {
                "schema_version": "docs_scopes_v5",
                "scopes": [
                    docs_scope_record(
                        "studio",
                        default_doc_id="parent",
                        manage_only_tree_root_ids=["manage-root"],
                    ),
                    docs_scope_record(
                        "private",
                        scope_type="local",
                        scope_root_provider="external_local",
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
    assert "Would write: docs-viewer/scopes/studio/generated/search/index.json" in result.stdout


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


def test_v2_index_keeps_same_doc_id_for_distinct_exact_targets() -> None:
    doc_id = "d-20260814-000001-aaaaaa"
    documents = [
        {
            "id": doc_id,
            "title": "Parent",
            "href": f"/docs/?scope=studio&doc={doc_id}",
        },
        {
            "id": doc_id,
            "title": "Child",
            "href": f"/docs/?scope=studio&doc=d-20260814-000002-bbbbbb&subdoc={doc_id}",
            "sub_scope": "tags",
            "report_doc_id": "d-20260814-000002-bbbbbb",
            "collection_title": "Tags",
        },
    ]

    payload = build_search.build_search_index_v2(
        scope="studio",
        documents=documents,
        search_fields=("title", "identity"),
        generated_at_utc="2026-08-14T00:00:00Z",
    )

    assert payload["header"]["count"] == 2
    assert [row.get("sub_scope", "") for row in payload["docs"]] == ["", "tags"]
    assert payload["terms"][doc_id] == {"identity": [0, 1]}


def test_python_docs_search_builder_includes_manage_owned_sub_scope_docs() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        host_id = "d-20260814-000001-aaaaaa"
        child_id = "d-20260814-000002-bbbbbb"
        excluded_id = "d-20260814-000003-cccccc"
        sub_scope = docs_sub_scope_record(
            "analysis",
            "tags",
            title="Tags",
            public_title="Concepts",
            scope_type="public",
        )
        scope = docs_scope_record(
            "analysis",
            scope_type="public",
            viewer_base_url="/analysis/",
            include_scope_param=False,
            default_doc_id=host_id,
            sub_scopes=[sub_scope],
        )
        scope["search_fields"] = ["title", "heading", "body", "code"]
        write_json(
            root / "docs-viewer/config/scopes/docs_scopes.json",
            {
                "schema_version": "docs_scopes_v5",
                "scopes": [scope],
            },
        )
        write_text(
            root / "docs-viewer/config/reports/reports.json",
            (REPO_ROOT / "docs-viewer/config/reports/reports.json").read_text(
                encoding="utf-8"
            ),
        )
        write_text(
            root / f"docs-viewer/scopes/analysis/source/documents/{host_id}.md",
            f"""---
doc_id: {host_id}
title: Concepts
last_updated: 2026-08-14 09:00:00
---
# Concepts

:::report
id: docs_subscope
access: public
sub_scope: tags
:::
""",
        )
        source_root = root / "docs-viewer/scopes/analysis/source/sub-scopes/tags/documents"
        write_text(
            source_root / f"{child_id}.md",
            f"""---
doc_id: {child_id}
title: Visible Child
added_date: 2026-08-14 09:01:00
last_updated: 2026-08-14 09:02:00
ui_status: done
---
# Visible Child

## Searchable Heading

EligibleVocabulary appears once.
""",
        )
        write_text(
            source_root / f"{excluded_id}.md",
            f"""---
doc_id: {excluded_id}
title: Hidden Child
added_date: 2026-08-14 09:03:00
last_updated: 2026-08-14 09:04:00
ui_status: draft
publishable: false
---
# Hidden Child

ExcludedVocabulary must not leak.
""",
        )
        output_root = root / "docs-viewer/scopes/analysis/generated/documents/sub-scopes/tags"
        write_json(
            output_root / "manage-manifest.json",
            {
                "docs": [
                    {"doc_id": child_id, "title": "Visible Child"},
                    {"doc_id": excluded_id, "title": "Hidden Child"},
                ]
            },
        )
        write_json(
            output_root / "by-id" / f"{child_id}.json",
            {
                "doc_id": child_id,
                "title": "Visible Child",
                "last_updated": "2026-08-14 09:02:00",
                "viewer_url": f"/analysis/?doc={host_id}&subdoc={child_id}",
                "content_html": "<h1>Visible Child</h1><p>EligibleVocabulary appears once.</p>",
            },
        )
        write_json(
            output_root / "by-id" / f"{excluded_id}.json",
            {
                "doc_id": excluded_id,
                "title": "Hidden Child",
                "last_updated": "2026-08-14 09:04:00",
                "viewer_url": f"/analysis/?doc={host_id}&subdoc={excluded_id}",
                "content_html": "<h1>Hidden Child</h1><p>ExcludedVocabulary remains manageable.</p>",
            },
        )

        exit_code, stdout, stderr = run_cli(root, ["--scope", "analysis", "--write"])
        payload = read_json(root / "docs-viewer/scopes/analysis/generated/search/index.json")

    assert exit_code == 0
    assert stderr == ""
    assert "with 3 analysis search docs" in stdout
    sub_scope_docs = [row for row in payload["docs"] if row.get("sub_scope") == "tags"]
    child = next(row for row in sub_scope_docs if row["id"] == child_id)
    assert child == {
        "id": child_id,
        "title": "Visible Child",
        "href": f"/analysis/?doc={host_id}&subdoc={child_id}",
        "last_updated": "2026-08-14 09:02:00",
        "display_meta": "2026-08-14 09:02:00 • Tags",
        "sub_scope": "tags",
        "report_doc_id": host_id,
        "collection_title": "Tags",
    }
    assert "eligiblevocabulary" in payload["terms"]
    assert {document["id"] for document in sub_scope_docs} == {child_id, excluded_id}
    assert "excludedvocabulary" in payload["terms"]


def test_python_docs_search_builder_rejects_ambiguous_sub_scope_placement() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        first_host_id = "d-20260814-000011-aaaaaa"
        second_host_id = "d-20260814-000012-bbbbbb"
        scope = docs_scope_record(
            "studio",
            default_doc_id=first_host_id,
            sub_scopes=[docs_sub_scope_record("studio", "tags", title="Tags")],
        )
        write_json(
            root / "docs-viewer/config/scopes/docs_scopes.json",
            {
                "schema_version": "docs_scopes_v5",
                "scopes": [scope],
            },
        )
        write_text(
            root / "docs-viewer/config/reports/reports.json",
            (REPO_ROOT / "docs-viewer/config/reports/reports.json").read_text(
                encoding="utf-8"
            ),
        )
        for host_id in (first_host_id, second_host_id):
            write_text(
                root / f"docs-viewer/scopes/studio/source/documents/{host_id}.md",
                f"""---
doc_id: {host_id}
title: Tags
last_updated: 2026-08-14 10:00:00
---
# Tags

:::report
id: docs_subscope
access: local
sub_scope: tags
:::
""",
            )

        try:
            build_search.DocsViewerSearchDataBuilder(
                repo_root=root,
                scope="studio",
            ).build_docs_v2_payload()
        except SystemExit as exc:
            error = str(exc)
        else:
            raise AssertionError("ambiguous sub-scope placement should fail")

    assert "studio/tags; found 2" in error


def test_python_docs_search_builder_dry_run_does_not_write() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        exit_code, stdout, stderr = run_cli(root, ["--scope", "studio"])

        assert exit_code == 0
        assert stderr == ""
        assert "Dry run: 6 studio search docs" in stdout
        assert "Would write: docs-viewer/scopes/studio/generated/search/index.json" in stdout
        assert not (root / "docs-viewer/scopes/studio/generated/search/index.json").exists()


def test_python_docs_search_builder_skips_unchanged_second_write_and_force_rewrites() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        run_cli(root, ["--scope", "studio", "--write"])
        first_payload = read_json(root / "docs-viewer/scopes/studio/generated/search/index.json")
        second_exit, second_stdout, second_stderr = run_cli(root, ["--scope", "studio", "--write"])
        force_exit, force_stdout, force_stderr = run_cli(root, ["--scope", "studio", "--write", "--force"])
        force_payload = read_json(root / "docs-viewer/scopes/studio/generated/search/index.json")

    assert second_exit == 0
    assert second_stderr == ""
    assert "Search index JSON done. Wrote: 0. Skipped: 1." in second_stdout
    assert force_exit == 0
    assert force_stderr == ""
    assert "Wrote docs-viewer/scopes/studio/generated/search/index.json with 6 studio search docs" in force_stdout
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
            payload = read_json(external_root / "scopes/private/generated/search/index.json")
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
