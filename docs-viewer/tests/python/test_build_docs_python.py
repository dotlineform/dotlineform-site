#!/usr/bin/env python3
"""Focused checks for the Python Docs Viewer payload builder."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
BUILD_DIR = REPO_ROOT / "docs-viewer" / "build"
SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
for path in (BUILD_DIR, SERVICES_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import build_docs  # noqa: E402
from docs_scope_config import load_docs_scope_configs  # noqa: E402

EXTERNAL_DATA_ROOT_MARKER = "$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_semantic_reference_registry(root: Path) -> None:
    write_json(
        root / "docs-viewer/config/semantic-references/registry.json",
        {
            "schema_version": "docs_semantic_reference_registry_v1",
            "target_lookup_url": "/docs-viewer/generated/semantic-references/target-lookup.json",
            "kinds": [
                {
                    "kind": "work",
                    "id": {
                        "normalizer": "digits_left_pad",
                        "width": 5,
                        "input_pattern": "^\\d{1,5}$",
                        "canonical_pattern": "^\\d{5}$",
                        "example": "00638",
                    },
                    "route": {"type": "query", "path": "/works/", "param": "work"},
                    "source_editor": {"selection_search": True, "picker": True},
                },
                {
                    "kind": "series",
                    "id": {
                        "normalizer": "series_id_or_slug",
                        "input_pattern": "^[a-z0-9][a-z0-9-]*$",
                        "example": "009",
                    },
                    "route": {"type": "query", "path": "/series/", "param": "series"},
                    "source_editor": {"selection_search": True, "picker": True},
                },
                {
                    "kind": "moment",
                    "id": {
                        "normalizer": "slug",
                        "input_pattern": "^[a-z0-9][a-z0-9-]*$",
                        "example": "lotus-pond",
                    },
                    "route": {"type": "query", "path": "/moments/", "param": "doc"},
                    "source_editor": {"selection_search": True, "picker": True},
                },
            ],
        },
    )


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_site_tools_config(root: Path, *, media_base: str = "https://media.example.test") -> None:
    write_json(
        root / "site-tools/config/site-tools.json",
        {
            "schema_version": "site_tools_config_v1",
            "media": {
                "base": media_base,
            },
        },
    )


def write_scope_config(root: Path) -> None:
    write_json(
        root / "docs-viewer/config/scopes/docs_scopes.json",
        {
            "schema_version": "docs_scopes_v1",
            "scopes": [
                {
                    "scope_id": "studio",
                    "scope_type": "local",
                    "meta": "local management",
                    "source": "docs-viewer/source/studio",
                    "media_path_prefix": "docs/studio",
                    "output": "docs-viewer/generated/docs/studio",
                    "search_output": "docs-viewer/generated/search/studio/index.json",
                    "viewer_base_url": "/docs/",
                    "include_scope_param": True,
                    "default_doc_id": "parent",
                    "non_loadable_doc_ids": [],
                    "manage_only_tree_root_ids": [],
                    "allow_unresolved_parent_ids": False,
                }
            ],
            "docs_viewer": {
                "recently_added_limit": 10,
                "ui_statuses_by_scope": {
                    "studio": [{"ui_status": "done", "label": "Done"}],
                    "library": [{"ui_status": "draft", "label": "Draft"}],
                },
            },
        },
    )


def write_external_scope_config(root: Path, external_root: Path) -> None:
    del external_root
    write_json(
        root / "docs-viewer/config/scopes/docs_scopes.json",
        {
            "schema_version": "docs_scopes_v1",
            "scopes": [
                {
                    "scope_id": "private",
                    "scope_type": "local_external",
                    "meta": "external local",
                    "external_data_root": EXTERNAL_DATA_ROOT_MARKER,
                    "source": f"{EXTERNAL_DATA_ROOT_MARKER}/source/private",
                    "media_path_prefix": "docs/private",
                    "output": f"{EXTERNAL_DATA_ROOT_MARKER}/generated/docs/private",
                    "search_output": f"{EXTERNAL_DATA_ROOT_MARKER}/generated/search/private/index.json",
                    "viewer_base_url": "/docs/",
                    "include_scope_param": True,
                    "default_doc_id": "private",
                    "non_loadable_doc_ids": [],
                    "manage_only_tree_root_ids": [],
                    "allow_unresolved_parent_ids": False,
                }
            ],
        },
    )


def write_public_scope_config(root: Path) -> None:
    write_json(
        root / "docs-viewer/config/scopes/docs_scopes.json",
        {
            "schema_version": "docs_scopes_v1",
            "scopes": [
                {
                    "scope_id": "library",
                    "scope_type": "public",
                    "meta": "public scope",
                    "source": "docs-viewer/source/library",
                    "media_path_prefix": "docs/library",
                    "output": "docs-viewer/generated/docs/library",
                    "search_output": "docs-viewer/generated/search/library/index.json",
                    "publish_output": "site/assets/data/docs/scopes/library",
                    "publish_search_output": "site/assets/data/search/library/index.json",
                    "viewer_base_url": "/library/",
                    "include_scope_param": False,
                    "default_doc_id": "parent",
                    "non_loadable_doc_ids": [],
                    "manage_only_tree_root_ids": ["manage-root"],
                    "allow_unresolved_parent_ids": False,
                }
            ],
            "docs_viewer": {
                "recently_added_limit": 2,
            },
        },
    )


def write_catalogue_records(root: Path) -> None:
    base = root / "studio/data/canonical/catalogue"
    write_json(
        base / "works.json",
        {"works": {"00638": {"work_id": "00638", "title": "3 symbols", "status": "published"}}},
    )
    write_json(
        base / "series.json",
        {"series": {"026": {"series_id": "026", "title": "Collected", "status": "published"}}},
    )
    write_json(
        base / "moments.json",
        {"moments": {"dark-sky": {"moment_id": "dark-sky", "title": "Dark Sky", "status": "published"}}},
    )


def write_source_docs(root: Path, *, child_body_suffix: str = "") -> None:
    write_text(
        root / "docs-viewer/source/studio/parent.md",
        """---
doc_id: parent
title: Parent
added_date: 2026-06-01
last_updated: 2026-06-01
parent_id: ""
---
# Parent

Parent body.
""",
    )
    write_text(
        root / "docs-viewer/source/studio/child.md",
        f"""---
doc_id: child
title: Child
date: 2026-06-02
date_display: June 2026
added_date: 2026-06-01
last_updated: 2026-06-01
summary: Child summary
ui_status: done
parent_id: parent
viewer_report: semantic_references
viewer_report_subscope: tags
---
# Child

Intro with [parent](parent.md), ![Diagram]([[media:docs/studio/diagram.png]]), and [[ref:work:638|three signs]].

![Measured diagram]([[media:docs/studio/measured-diagram.png width=800 height=600]])

<!-- [[ref:work:638999|commented missing work]] -->

<!--
[[ref:work:638998|commented missing work multiline]]
-->

`[[ref:series:26]]`

```text
[[ref:moment:dark-sky]]
```

[[interactive-html:chart.html height=420]]

<img src="/image.jpg" alt="Alt text">

{child_body_suffix}
""",
    )


def write_public_source_docs(root: Path) -> None:
    rows = [
        ("parent", "Parent", "2026-06-01", "2026-06-01", "", True),
        ("child", "Child", "2026-06-03", "2026-06-03", "parent", True),
        ("hidden", "Hidden", "2026-06-04", "2026-06-04", "parent", False),
        ("hidden-child", "Hidden Child", "2026-06-05", "2026-06-05", "hidden", True),
        ("manage-root", "Manage Root", "2026-06-05", "2026-06-05", "", True),
        ("manage-child", "Manage Child", "2026-06-06", "2026-06-06", "manage-root", True),
    ]
    for doc_id, title, added_date, last_updated, parent_id, viewable in rows:
        viewable_line = "" if viewable else "viewable: false\n"
        parent_line = f"parent_id: {parent_id}\n" if parent_id else ""
        date_lines = "date: 2026-06-02\ndate_display: June 2026\n" if doc_id == "child" else ""
        write_text(
            root / f"docs-viewer/source/library/{doc_id}.md",
            f"""---
doc_id: {doc_id}
title: {json.dumps(title)}
{date_lines}added_date: {added_date}
last_updated: {last_updated}
summary: {json.dumps(title + " summary")}
ui_status: done
{parent_line}{viewable_line}---
# {title}

{title} body.
""",
        )


def prepare_repo(root: Path) -> None:
    write_site_tools_config(root)
    write_scope_config(root)
    write_semantic_reference_registry(root)
    write_catalogue_records(root)
    write_text(root / "site/assets/docs/interactive/studio/chart.html", "<!doctype html><title>Chart</title>")
    write_source_docs(root)


def run_builder(root: Path, *, only_doc_ids: list[str] | None = None, write: bool = True):
    config = load_docs_scope_configs(root)["studio"]
    builder = build_docs.DocsDataBuilder(repo_root=root, config=config, only_doc_ids=only_doc_ids)
    return builder.run(write=write)


def run_cli(root: Path, args: list[str]) -> tuple[int, str, str]:
    cwd = Path.cwd()
    stdout = StringIO()
    stderr = StringIO()
    try:
        os.chdir(root)
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = build_docs.main(args)
    finally:
        os.chdir(cwd)
    return exit_code, stdout.getvalue(), stderr.getvalue()


def diagnostics_from_stdout(stdout: str) -> dict[str, object]:
    prefix = "Docs builder diagnostics: "
    lines = [line.removeprefix(prefix) for line in stdout.splitlines() if line.startswith(prefix)]
    assert lines
    return json.loads(lines[-1])


def test_python_docs_builder_writes_docs_payloads_and_references() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        result = run_builder(root)

        index_tree = read_json(root / "docs-viewer/generated/docs/studio/index-tree.json")
        recently_added = read_json(root / "docs-viewer/generated/docs/studio/recently-added.json")
        child = read_json(root / "docs-viewer/generated/docs/studio/by-id/child.json")
        references_index = read_json(root / "docs-viewer/generated/docs/studio/references/index.json")
        target_payload = read_json(root / "docs-viewer/generated/docs/studio/references/by-target/work/00638.json")
        by_doc = read_json(root / "docs-viewer/generated/docs/studio/references/by-doc/child.json")

    docs = result["index_payload"]["docs"]
    assert [doc["doc_id"] for doc in docs] == ["parent", "child"]
    assert docs[1]["summary"] == "Child summary"
    assert docs[1]["date"] == "2026-06-02"
    assert docs[1]["date_display"] == "June 2026"
    assert docs[1]["ui_status"] == "done"
    assert docs[1]["content_url"] == "/docs-viewer/generated/docs/studio/by-id/child.json"
    assert isinstance(docs[1]["content_text_length"], int)

    assert index_tree["schema"] == "docs_index_tree_v1"
    assert [doc["doc_id"] for doc in index_tree["docs"]] == ["parent"]
    assert [doc["doc_id"] for doc in index_tree["docs"][0]["children"]] == ["child"]
    tree_child = index_tree["docs"][0]["children"][0]
    assert tree_child == {
        "doc_id": "child",
        "title": "Child",
        "content_url": "/docs-viewer/generated/docs/studio/by-id/child.json",
        "ui_status": "done",
    }
    assert "parent_id" not in tree_child
    assert "summary" not in tree_child
    assert "added_date" not in tree_child
    assert "last_updated" not in tree_child
    assert "source_path" not in tree_child
    assert "viewer_url" not in tree_child
    assert "content_text_length" not in tree_child

    assert recently_added["schema"] == "docs_recently_added_v1"
    assert recently_added["limit"] == 10
    assert recently_added["docs"][0]["doc_id"] == "child"
    assert recently_added["docs"][0]["added_date"] == "2026-06-01"
    assert recently_added["docs"][0]["parent_title"] == "Parent"

    content_html = child["content_html"]
    assert 'href="/docs/?scope=studio&doc=parent"' in content_html
    assert 'src="https://media.example.test/docs/studio/diagram.png"' in content_html
    assert (
        '<img src="https://media.example.test/docs/studio/measured-diagram.png" '
        'alt="Measured diagram" width="800" height="600"'
    ) in content_html
    assert 'title="Alt text"' in content_html
    assert 'class="docsViewer__interactiveFrame"' in content_html
    assert "--docs-viewer-interactive-height: 420px" in content_html
    assert 'href="/works/?work=00638"' in content_html
    assert "[[ref:work:638999|commented missing work]]" in content_html
    assert "[[ref:work:638998|commented missing work multiline]]" in content_html
    assert "[[ref:series:26]]" in content_html
    assert "[[ref:moment:dark-sky]]" in content_html
    assert child["viewer_report"] == "semantic_references"
    assert child["viewer_report_subscope"] == "tags"
    assert child["date"] == "2026-06-02"
    assert child["date_display"] == "June 2026"

    assert references_index["header"]["schema"] == "docs_semantic_references_index_v1"
    assert references_index["header"]["count"] == 1
    assert "638999" not in json.dumps(references_index)
    assert "638998" not in json.dumps(references_index)
    assert references_index["targets"][0]["target_key"] == "work:00638"
    assert references_index["targets"][0]["bucket_url"] == "/docs-viewer/generated/docs/studio/references/by-target/work/00638.json"
    assert target_payload["header"]["schema"] == "docs_semantic_references_by_target_v1"
    assert target_payload["target_kind"] == "work"
    assert target_payload["references"][0]["source_doc_id"] == "child"
    assert by_doc["references"][0]["label"] == "three signs"
    assert result["diagnostics"]["docs_emitted"] == 2
    assert result["diagnostics"]["index_tree_changed"] == 1
    assert result["diagnostics"]["recently_added_changed"] == 1


def test_python_docs_builder_excludes_configured_sub_scope_sources() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        config_path = root / "docs-viewer/config/scopes/docs_scopes.json"
        payload = read_json(config_path)
        payload["scopes"][0]["sub_scopes"] = [
            {
                "sub_scope": "tags",
                "source": "docs-viewer/source/studio/tags",
                "output": "docs-viewer/generated/docs/studio/tags",
            }
        ]
        write_json(config_path, payload)
        write_text(
            root / "docs-viewer/source/studio/tags/detail.md",
            """---
doc_id: detail
title: Detail
---
# Detail

Sub-scope detail body.
""",
        )

        config = load_docs_scope_configs(root)["studio"]
        result = build_docs.DocsDataBuilder(repo_root=root, config=config).run(write=True)
        browser_config = build_docs.browser_scope_config_payload(root, [config])

        assert not (root / "docs-viewer/generated/docs/studio/by-id/detail.json").exists()

    assert [doc["doc_id"] for doc in result["index_payload"]["docs"]] == ["parent", "child"]
    assert result["diagnostics"]["source_files_scanned"] == 2
    assert browser_config["scopes"][0]["sub_scopes"] == [
        {
            "sub_scope": "tags",
            "title": "",
            "manifest_url": "/docs-viewer/generated/docs/studio/tags/manifest.json",
            "by_id_url_base": "/docs-viewer/generated/docs/studio/tags/by-id",
        }
    ]


def test_python_docs_builder_writes_sub_scope_payloads_and_minimal_manifest() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        config_path = root / "docs-viewer/config/scopes/docs_scopes.json"
        payload = read_json(config_path)
        payload["scopes"][0]["sub_scopes"] = [
            {
                "sub_scope": "tags",
                "title": "Tags",
                "source": "docs-viewer/source/studio/tags",
                "output": "docs-viewer/generated/docs/studio/tags",
            }
        ]
        write_json(config_path, payload)
        write_text(
            root / "docs-viewer/source/studio/tags-report.md",
            """---
doc_id: tags-report
title: Tags
added_date: 2026-06-20
last_updated: 2026-06-21
parent_id: ""
viewer_report: docs_subscope
viewer_report_subscope: tags
---
# Tags
""",
        )
        write_text(
            root / "docs-viewer/source/studio/tags/detail.md",
            """---
doc_id: detail
title: Detail
added_date: 2026-06-20
last_updated: 2026-06-21
parent_id: ""
---
# Detail

Sub-scope detail body with [related](related.md).
""",
        )
        write_text(
            root / "docs-viewer/source/studio/tags/related.md",
            """---
doc_id: related
title: Related
added_date: 2026-06-22
last_updated: 2026-06-23
parent_id: detail
---
# Related

Related body.
""",
        )
        write_json(root / "docs-viewer/generated/docs/studio/tags/by-id/stale.json", {"doc_id": "stale"})

        exit_code, stdout, stderr = run_cli(root, ["--scope", "studio", "--sub-scope", "tags", "--write", "--diagnostics"])
        manifest = read_json(root / "docs-viewer/generated/docs/studio/tags/manifest.json")
        detail = read_json(root / "docs-viewer/generated/docs/studio/tags/by-id/detail.json")
        related = read_json(root / "docs-viewer/generated/docs/studio/tags/by-id/related.json")

    assert exit_code == 0
    assert stderr == ""
    assert "Docs sub-scope build (write) scope=studio sub_scope=tags" in stdout
    diagnostics = diagnostics_from_stdout(stdout)
    assert diagnostics["build_mode"] == "sub_scope"
    assert diagnostics["sub_scope"] == "tags"
    assert diagnostics["docs_emitted"] == 2
    assert manifest == {"doc_ids": "detail,related"}
    assert detail["doc_id"] == "detail"
    assert detail["title"] == "Detail"
    assert detail["last_updated"] == "2026-06-21"
    assert detail["source_path"] == "detail.md"
    assert detail["viewer_url"] == "/docs/?scope=studio&doc=tags-report&subdoc=detail"
    assert 'href="/docs/?scope=studio&doc=tags-report&subdoc=related"' in detail["content_html"]
    assert related["parent_id"] == "detail"
    assert not (root / "docs-viewer/generated/docs/studio/tags/by-id/stale.json").exists()
    assert not (root / "docs-viewer/generated/docs/studio/tags/index-tree.json").exists()
    assert not (root / "docs-viewer/generated/docs/studio/tags/recently-added.json").exists()


def test_python_docs_builder_rejects_comma_doc_ids_for_sub_scope_manifest() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        config_path = root / "docs-viewer/config/scopes/docs_scopes.json"
        payload = read_json(config_path)
        payload["scopes"][0]["sub_scopes"] = [
            {
                "sub_scope": "tags",
                "title": "Tags",
                "source": "docs-viewer/source/studio/tags",
                "output": "docs-viewer/generated/docs/studio/tags",
            }
        ]
        write_json(config_path, payload)
        write_text(
            root / "docs-viewer/source/studio/tags/bad.md",
            """---
doc_id: bad,id
title: Bad
---
# Bad
""",
        )

        try:
            run_cli(root, ["--scope", "studio", "--sub-scope", "tags", "--write"])
        except RuntimeError as exc:
            message = str(exc)
        else:
            raise AssertionError("Expected comma doc_id to be rejected")

    assert "must not contain commas" in message


def test_python_docs_builder_public_sub_scope_uses_publish_url_base() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        write_site_tools_config(root, media_base="")
        write_public_scope_config(root)
        write_public_source_docs(root)
        config_path = root / "docs-viewer/config/scopes/docs_scopes.json"
        payload = read_json(config_path)
        payload["scopes"][0]["sub_scopes"] = [
            {
                "sub_scope": "tags",
                "title": "Tags",
                "source": "docs-viewer/source/library/tags",
                "output": "docs-viewer/generated/docs/library/tags",
                "publish_output": "site/assets/data/docs/scopes/library/tags",
            }
        ]
        write_json(config_path, payload)
        write_text(
            root / "docs-viewer/source/library/tags/detail.md",
            """---
doc_id: detail
title: Detail
added_date: 2026-06-20
last_updated: 2026-06-21
---
# Detail
""",
        )

        exit_code, _stdout, stderr = run_cli(root, ["--scope", "library", "--sub-scope", "tags", "--write"])
        detail = read_json(root / "docs-viewer/generated/docs/library/tags/by-id/detail.json")
        browser_config = build_docs.browser_scope_config_payload(root, [load_docs_scope_configs(root)["library"]])

    assert exit_code == 0
    assert stderr == ""
    assert detail["doc_id"] == "detail"
    assert browser_config["scopes"][0]["sub_scopes"] == [
        {
            "sub_scope": "tags",
            "title": "Tags",
            "manifest_url": "/assets/data/docs/scopes/library/tags/manifest.json",
            "by_id_url_base": "/assets/data/docs/scopes/library/tags/by-id",
        }
    ]


def test_python_docs_builder_public_generated_payloads_include_manage_rows() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        write_site_tools_config(root, media_base="")
        write_public_scope_config(root)
        write_public_source_docs(root)
        config = load_docs_scope_configs(root)["library"]
        result = build_docs.DocsDataBuilder(repo_root=root, config=config).run(write=True)
        index_tree = read_json(root / "docs-viewer/generated/docs/library/index-tree.json")
        recently_added = read_json(root / "docs-viewer/generated/docs/library/recently-added.json")
        child_payload = read_json(root / "docs-viewer/generated/docs/library/by-id/child.json")
        hidden_payload = read_json(root / "docs-viewer/generated/docs/library/by-id/hidden.json")
        browser_config = build_docs.browser_scope_config_payload(root, [config])

    assert result["diagnostics"]["docs_emitted"] == 6
    public_tree_forbidden_keys = {
        "summary",
        "date",
        "date_display",
        "added_date",
        "last_updated",
        "source_path",
        "viewer_url",
        "content_text_length",
        "viewer_report",
        "viewer_report_scope",
        "viewer_report_access",
        "viewer_report_preset",
        "viewer_report_subscope",
    }
    public_recent_forbidden_keys = {
        "summary",
        "date",
        "date_display",
        "last_updated",
        "source_path",
        "viewer_url",
        "content_text_length",
        "viewer_report",
        "viewer_report_scope",
        "viewer_report_access",
        "viewer_report_preset",
        "viewer_report_subscope",
        "viewable",
        "ui_status",
    }
    public_by_id_forbidden_keys = {
        "doc_id",
        "added_date",
        "parent_id",
        "source_path",
        "viewer_url",
        "ui_status",
        "viewable",
        "content_text_length",
        "viewer_report",
        "viewer_report_scope",
        "viewer_report_access",
        "viewer_report_preset",
        "viewer_report_subscope",
    }

    assert index_tree["schema"] == "docs_index_tree_v1"
    assert [doc["doc_id"] for doc in index_tree["docs"]] == ["manage-root", "parent"]
    assert [doc["doc_id"] for doc in index_tree["docs"][0]["children"]] == ["manage-child"]
    assert [doc["doc_id"] for doc in index_tree["docs"][1]["children"]] == ["child", "hidden"]
    assert [doc["doc_id"] for doc in index_tree["docs"][1]["children"][1]["children"]] == ["hidden-child"]
    flattened_tree_docs = [
        index_tree["docs"][0],
        *index_tree["docs"][0]["children"],
        index_tree["docs"][1],
        *index_tree["docs"][1]["children"],
        *index_tree["docs"][1]["children"][1]["children"],
    ]
    assert all("parent_id" not in doc for doc in flattened_tree_docs)
    assert index_tree["docs"][1]["children"][1]["viewable"] is False
    assert all(public_tree_forbidden_keys.isdisjoint(doc) for doc in flattened_tree_docs)
    assert recently_added["schema"] == "docs_recently_added_v1"
    assert recently_added["limit"] == 2
    assert [doc["doc_id"] for doc in recently_added["docs"]] == ["manage-child", "hidden-child"]
    assert recently_added["docs"][0]["parent_title"] == "Manage Root"
    assert all(public_recent_forbidden_keys.isdisjoint(doc) for doc in recently_added["docs"])
    assert set(child_payload) == {"content_html", "date", "date_display", "last_updated", "summary", "title"}
    assert child_payload["title"] == "Child"
    assert child_payload["date"] == "2026-06-02"
    assert child_payload["date_display"] == "June 2026"
    assert child_payload["summary"] == "Child summary"
    assert child_payload["last_updated"] == "2026-06-03"
    assert "content_html" in child_payload
    assert public_by_id_forbidden_keys.isdisjoint(child_payload)
    assert hidden_payload["title"] == "Hidden"
    assert browser_config["scopes"][0]["index_tree_url"] == "/assets/data/docs/scopes/library/index-tree.json"
    assert browser_config["scopes"][0]["recently_added_url"] == "/assets/data/docs/scopes/library/recently-added.json"
    assert index_tree["docs"][1]["content_url"] == "/assets/data/docs/scopes/library/by-id/parent.json"


def test_python_docs_builder_public_payloads_include_promoted_report_metadata() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        write_site_tools_config(root, media_base="")
        write_public_scope_config(root)
        write_public_source_docs(root)
        write_text(
            root / "docs-viewer/source/library/report.md",
            """---
doc_id: report
title: Report
added_date: 2026-06-24
last_updated: 2026-06-24
parent_id: parent
viewer_report: docs_subscope
viewer_report_access: public
viewer_report_subscope: tags
---
# Report
""",
        )
        config = load_docs_scope_configs(root)["library"]

        build_docs.DocsDataBuilder(repo_root=root, config=config).run(write=True)
        report_payload = read_json(root / "docs-viewer/generated/docs/library/by-id/report.json")
        index_tree = read_json(root / "docs-viewer/generated/docs/library/index-tree.json")

    assert report_payload["viewer_report"] == "docs_subscope"
    assert report_payload["viewer_report_access"] == "public"
    assert report_payload["viewer_report_subscope"] == "tags"
    report_row = index_tree["docs"][1]["children"][2]
    assert report_row["doc_id"] == "report"
    assert "viewer_report" not in report_row
    assert "viewer_report_access" not in report_row
    assert "viewer_report_subscope" not in report_row


def test_python_docs_builder_preserves_existing_payloads_for_targeted_builds() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        run_builder(root)
        parent_before = read_json(root / "docs-viewer/generated/docs/studio/by-id/parent.json")
        write_source_docs(root, child_body_suffix="Updated targeted body.")
        result = run_builder(root, only_doc_ids=["child"])
        parent_after = read_json(root / "docs-viewer/generated/docs/studio/by-id/parent.json")
        child_after = read_json(root / "docs-viewer/generated/docs/studio/by-id/child.json")

    assert parent_after == parent_before
    assert "Updated targeted body." in child_after["content_html"]
    assert result["diagnostics"]["build_mode"] == "targeted"
    assert result["diagnostics"]["only_doc_ids"] == ["child"]
    assert "parent" not in result["write_plan"]["changed_item_ids"]


def test_python_docs_builder_registry_backed_references_do_not_validate_target_existence() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        write_source_docs(root, child_body_suffix="Missing target [[ref:work:99999|still links]].")
        result = run_builder(root)
        child = read_json(root / "docs-viewer/generated/docs/studio/by-id/child.json")
        missing_target = read_json(root / "docs-viewer/generated/docs/studio/references/by-target/work/99999.json")

    assert result["diagnostics"]["warning_count"] == 0
    assert 'href="/works/?work=99999"' in child["content_html"]
    assert missing_target["target_kind"] == "work"
    assert missing_target["target_id"] == "99999"
    assert missing_target["target_status"] == "rendered"
    assert missing_target["references"][0]["label"] == "still links"


def test_python_docs_builder_writes_browser_configs_on_cli_write() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        exit_code, _, _ = run_cli(root, ["--scope", "studio", "--write"])

        assert exit_code == 0
        browser_config = read_json(root / "docs-viewer/config/defaults/docs-viewer-config.json")
        public_config = read_json(root / "docs-viewer/config/defaults/docs-viewer-public-config.json")
        site_public_config = read_json(root / "site/docs-viewer/config/defaults/docs-viewer-public-config.json")

    assert browser_config["schema_version"] == "docs_viewer_config_v1"
    assert browser_config["scopes"][0]["scope_id"] == "studio"
    assert browser_config["scopes"][0]["index_tree_url"] == "/docs-viewer/generated/docs/studio/index-tree.json"
    assert browser_config["scopes"][0]["recently_added_url"] == "/docs-viewer/generated/docs/studio/recently-added.json"
    assert browser_config["docs_viewer"]["ui_statuses_by_scope"] == {"studio": [{"ui_status": "done", "label": "Done"}]}
    assert public_config["scopes"] == []
    assert site_public_config == public_config


def test_python_docs_builder_writes_site_public_browser_config_on_cli_write() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        write_site_tools_config(root, media_base="")
        write_public_scope_config(root)
        write_public_source_docs(root)
        exit_code, _, _ = run_cli(root, ["--scope", "library", "--write"])

        assert exit_code == 0
        public_config = read_json(root / "docs-viewer/config/defaults/docs-viewer-public-config.json")
        site_public_config = read_json(root / "site/docs-viewer/config/defaults/docs-viewer-public-config.json")

    assert site_public_config == public_config
    assert [scope["scope_id"] for scope in site_public_config["scopes"]] == ["library"]
    assert site_public_config["scopes"][0]["viewer_base_url"] == "/library/"


def test_python_docs_builder_cli_dry_run_does_not_write_outputs() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        exit_code, stdout, stderr = run_cli(root, ["--scope", "studio", "--diagnostics"])

        assert exit_code == 0
        assert stderr == ""
        assert "Docs build (dry-run) scope=studio" in stdout
        assert "docs total: 2" in stdout
        assert "docs would write: 2" in stdout
        assert "warnings: 0" in stdout
        assert diagnostics_from_stdout(stdout)["doc_payloads_changed"] == 2
        assert not (root / "docs-viewer/generated/docs/studio/references/index.json").exists()
        assert not (root / "docs-viewer/config/defaults/docs-viewer-config.json").exists()
        assert not (root / "docs-viewer/config/defaults/docs-viewer-public-config.json").exists()


def test_python_docs_builder_cli_omits_diagnostics_by_default() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        exit_code, stdout, stderr = run_cli(root, ["--scope", "studio"])

    assert exit_code == 0
    assert stderr == ""
    assert "Docs build (dry-run) scope=studio" in stdout
    assert "Docs builder diagnostics:" not in stdout


def test_python_docs_builder_cli_reports_unchanged_second_write() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        first_exit, _, _ = run_cli(root, ["--scope", "studio", "--write"])
        second_exit, stdout, stderr = run_cli(root, ["--scope", "studio", "--write", "--diagnostics"])

        diagnostics = diagnostics_from_stdout(stdout)

    assert first_exit == 0
    assert second_exit == 0
    assert stderr == ""
    assert "Docs Viewer browser config: unchanged" in stdout
    assert "Docs Viewer public browser config: unchanged" in stdout
    assert "Docs build (write) scope=studio" in stdout
    assert "docs wrote: 0" in stdout
    assert "references wrote: 0" in stdout
    assert diagnostics["doc_payloads_changed"] == 0
    assert diagnostics["reference_index_changed"] == 0
    assert diagnostics["reference_by_doc_payloads_changed"] == 0
    assert diagnostics["reference_by_target_payloads_changed"] == 0


def test_python_docs_builder_cli_targeted_write_updates_selected_doc_only() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        run_cli(root, ["--scope", "studio", "--write"])
        parent_before = read_json(root / "docs-viewer/generated/docs/studio/by-id/parent.json")
        write_source_docs(root, child_body_suffix="CLI targeted update.")

        exit_code, stdout, stderr = run_cli(root, ["--scope", "studio", "--only-doc-ids", "child", "--write", "--diagnostics"])
        parent_after = read_json(root / "docs-viewer/generated/docs/studio/by-id/parent.json")
        child_after = read_json(root / "docs-viewer/generated/docs/studio/by-id/child.json")
        diagnostics = diagnostics_from_stdout(stdout)

    assert exit_code == 0
    assert stderr == ""
    assert parent_after == parent_before
    assert "CLI targeted update." in child_after["content_html"]
    assert "Docs build (write) scope=studio" in stdout
    assert "docs wrote: 1" in stdout
    assert diagnostics["build_mode"] == "targeted"
    assert diagnostics["only_doc_ids"] == ["child"]
    assert diagnostics["doc_payloads_changed"] == 1


def test_python_docs_builder_script_reports_front_matter_errors_without_traceback() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        write_text(
            root / "docs-viewer/source/studio/bad.md",
            """---
doc_id: bad
invalid front matter
---
# Bad
""",
        )
        completed = subprocess.run(
            [sys.executable, str(BUILD_DIR / "build_docs.py"), "--scope", "studio", "--write"],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )

    assert completed.returncode == 1
    assert "problem with front-matter on doc" in completed.stderr
    assert "Traceback" not in completed.stderr


def test_python_docs_builder_writes_external_local_scope_outputs() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        projects_root = (root.parent / f"{root.name}-external").resolve()
        external_root = projects_root / "docs-viewer"
        external_root.mkdir(parents=True)
        old_projects_base = os.environ.get("DOTLINEFORM_PROJECTS_BASE_DIR")
        os.environ["DOTLINEFORM_PROJECTS_BASE_DIR"] = projects_root.as_posix()
        write_site_tools_config(root)
        write_catalogue_records(root)
        write_external_scope_config(root, external_root)
        write_text(
            external_root / "source/private/private.md",
            """---
doc_id: private
title: Private
added_date: 2026-06-01
last_updated: 2026-06-01
---
# Private

External body.
""",
        )
        try:
            exit_code, stdout, stderr = run_cli(root, ["--scope", "private", "--write"])
            index_tree = read_json(external_root / "generated/docs/private/index-tree.json")
            payload = read_json(external_root / "generated/docs/private/by-id/private.json")
        finally:
            if old_projects_base is None:
                os.environ.pop("DOTLINEFORM_PROJECTS_BASE_DIR", None)
            else:
                os.environ["DOTLINEFORM_PROJECTS_BASE_DIR"] = old_projects_base

    assert exit_code == 0
    assert stderr == ""
    assert "scope=private" in stdout
    assert index_tree["docs"][0]["content_url"] == "/docs/generated/payload?scope=private&doc_id=private"
    assert payload["doc_id"] == "private"


def main() -> None:
    test_python_docs_builder_writes_docs_payloads_and_references()
    test_python_docs_builder_public_generated_payloads_include_manage_rows()
    test_python_docs_builder_preserves_existing_payloads_for_targeted_builds()
    test_python_docs_builder_writes_browser_configs_on_cli_write()
    test_python_docs_builder_cli_dry_run_does_not_write_outputs()
    test_python_docs_builder_cli_reports_unchanged_second_write()
    test_python_docs_builder_cli_targeted_write_updates_selected_doc_only()
    test_python_docs_builder_script_reports_front_matter_errors_without_traceback()
    test_python_docs_builder_writes_external_local_scope_outputs()
    print("Python Docs Viewer builder tests OK")


if __name__ == "__main__":
    main()
