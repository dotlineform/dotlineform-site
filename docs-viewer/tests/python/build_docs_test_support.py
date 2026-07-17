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
    docs_scope_record,
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
PARENT_DOC_ID = "d-20260601-000000-000001"
CHILD_DOC_ID = "d-20260601-000000-000002"
HIDDEN_DOC_ID = "d-20260601-000000-000003"
HIDDEN_CHILD_DOC_ID = "d-20260601-000000-000004"
MANAGE_ROOT_DOC_ID = "d-20260601-000000-000005"
MANAGE_CHILD_DOC_ID = "d-20260601-000000-000006"
PRIVATE_DOC_ID = "d-20260601-000000-000007"


def write_semantic_reference_registry(root: Path) -> None:
    write_json(
        root / "docs-viewer/config/semantic-references/registry.json",
        {
            "schema_version": "docs_semantic_reference_registry_v1",
            "target_lookup_url": "/docs-viewer/published/semantic-references/target-lookup.json",
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


def write_route_config(root: Path, *, public_scope: str = "", public_basis: str = "edited") -> None:
    routes = [
        {
            "route_id": "docs-manage",
            "app_kind": "manage",
            "default_scope_id": "studio",
            "features": ["recent"],
            "recent_basis": "edited",
        }
    ]
    if public_scope:
        routes.append(
            {
                "route_id": public_scope,
                "app_kind": "public",
                "default_scope_id": public_scope,
                "features": ["recent"],
                "recent_basis": public_basis,
            }
        )
    write_json(
        root / "docs-viewer/config/routes/docs-viewer-routes.json",
        {"schema_version": "docs_viewer_routes_v1", "routes": routes},
    )


def write_scope_config(root: Path) -> None:
    write_route_config(root)
    studio = docs_scope_record(
        "studio",
        meta="local management",
        default_doc_id=PARENT_DOC_ID,
    )
    studio["published"]["media"]["html"] = {  # type: ignore[index]
        "reference_prefix": "docs/studio/html",
        "location": {
            "provider": "repository",
            "path": "site/assets/data/docs/scopes/studio/media/html",
        },
        "served_path_prefix": "/assets/data/docs/scopes/studio/media/html",
        "build_inputs": [],
    }
    write_docs_scope_config(
        root,
        [studio],
        {
            "recent_limit": 10,
            "ui_statuses_by_scope": {
                "studio": [{"ui_status": "done", "label": "Done"}],
                "library": [{"ui_status": "draft", "label": "Draft"}],
            },
        },
    )


def write_external_scope_config(root: Path, external_root: Path) -> None:
    del external_root
    write_route_config(root)
    write_docs_scope_config(
        root,
        [
            docs_scope_record(
                "private",
                scope_type="local_external",
                meta="external local",
                default_doc_id=PRIVATE_DOC_ID,
            )
        ],
    )


def write_public_scope_config(root: Path) -> None:
    write_route_config(root, public_scope="library", public_basis="edited")
    write_docs_scope_config(
        root,
        [
            docs_scope_record(
                "library",
                scope_type="public",
                meta="public scope",
                viewer_base_url="/library/",
                include_scope_param=False,
                default_doc_id=PARENT_DOC_ID,
                manage_only_tree_root_ids=[MANAGE_ROOT_DOC_ID],
            )
        ],
        {"recent_limit": 2},
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
        root / f"docs-viewer/source/studio/documents/{PARENT_DOC_ID}.md",
        f"""---
doc_id: {PARENT_DOC_ID}
title: Parent
added_date: 2026-06-01
last_updated: 2026-06-01 10:00:00
parent_id: ""
---
# Parent

Parent body.
""",
    )
    write_text(
        root / f"docs-viewer/source/studio/documents/{CHILD_DOC_ID}.md",
        f"""---
doc_id: {CHILD_DOC_ID}
title: Child
date: 2026-06-02
date_display: June 2026
added_date: 2026-06-01
last_updated: 2026-06-02 10:00:00
summary: Child summary
ui_status: done
parent_id: {PARENT_DOC_ID}
viewer_report: semantic_references
viewer_report_subscope: tags
---
# Child

Intro with [parent](/docs/?scope=studio&doc={PARENT_DOC_ID}), ![Diagram]([[media:docs/studio/img/diagram.png]]), and [[ref:work:638|three signs]].

![Measured diagram]([[media:docs/studio/img/measured-diagram.png width=800 height=600]])

<!-- [[ref:work:638999|commented missing work]] -->

<!--
[[ref:work:638998|commented missing work multiline]]
-->

`[[ref:series:26]]`

```text
[[ref:moment:dark-sky]]
```

[[html-media:docs/studio/html/chart.html height=420]]

<img src="/image.jpg" alt="Alt text">

{child_body_suffix}
""",
    )


def write_public_source_docs(root: Path) -> None:
    rows = [
        (PARENT_DOC_ID, "Parent", "2026-06-01", "2026-06-01 10:00:00", "", True),
        (CHILD_DOC_ID, "Child", "2026-06-03", "2026-06-03 10:00:00", PARENT_DOC_ID, True),
        (HIDDEN_DOC_ID, "Hidden", "2026-06-04", "2026-06-04 10:00:00", PARENT_DOC_ID, False),
        (HIDDEN_CHILD_DOC_ID, "Hidden Child", "2026-06-05", "2026-06-05 10:00:00", HIDDEN_DOC_ID, True),
        (MANAGE_ROOT_DOC_ID, "Manage Root", "2026-06-05", "2026-06-05 10:00:00", "", True),
        (MANAGE_CHILD_DOC_ID, "Manage Child", "2026-06-06", "2026-06-06 10:00:00", MANAGE_ROOT_DOC_ID, True),
    ]
    for doc_id, title, added_date, last_updated, parent_id, viewable in rows:
        viewable_line = "" if viewable else "viewable: false\n"
        parent_line = f"parent_id: {parent_id}\n" if parent_id else ""
        date_lines = "date: 2026-06-02\ndate_display: June 2026\n" if doc_id == CHILD_DOC_ID else ""
        write_text(
            root / f"docs-viewer/source/library/documents/{doc_id}.md",
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
    write_text(
        root / "site/assets/data/docs/scopes/studio/media/html/chart.html",
        "<!doctype html><title>Chart</title>",
    )
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
