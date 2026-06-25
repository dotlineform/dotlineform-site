"""Shared fixtures for Python Docs Viewer builder tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

from repo_factory import (
    read_json,
    write_docs_scope_config,
    write_json,
    write_site_tools_config as write_fixture_site_tools_config,
    write_text,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
BUILD_DIR = REPO_ROOT / "docs-viewer" / "build"
SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
for path in (BUILD_DIR, SERVICES_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import build_docs  # noqa: E402
from docs_scope_config import load_docs_scope_configs  # noqa: E402

EXTERNAL_DATA_ROOT_MARKER = "$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer"


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


def write_site_tools_config(root: Path, *, media_base: str = "https://media.example.test") -> None:
    write_fixture_site_tools_config(root, media_base=media_base)


def write_scope_config(root: Path) -> None:
    write_docs_scope_config(
        root,
        [
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
        {
            "recently_added_limit": 10,
            "ui_statuses_by_scope": {
                "studio": [{"ui_status": "done", "label": "Done"}],
                "library": [{"ui_status": "draft", "label": "Draft"}],
            },
        },
    )


def write_external_scope_config(root: Path, external_root: Path) -> None:
    del external_root
    write_docs_scope_config(
        root,
        [
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
    )


def write_public_scope_config(root: Path) -> None:
    write_docs_scope_config(
        root,
        [
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
        {"recently_added_limit": 2},
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
