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


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, object]:
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
                    "meta": "local management",
                    "source": "docs-viewer/source/studio",
                    "media_path_prefix": "docs/studio",
                    "output": "docs-viewer/generated/docs/studio",
                    "search_output": "docs-viewer/generated/search/studio/index.json",
                    "viewer_base_url": "/docs/",
                    "include_scope_param": True,
                    "default_doc_id": "parent",
                    "allow_nested_source": False,
                    "non_loadable_doc_ids": [],
                    "manage_only_tree_root_ids": ["change-history-reports"],
                    "show_updated_date": True,
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
added_date: 2026-06-01
last_updated: 2026-06-01
summary: Child summary
ui_status: done
parent_id: parent
viewer_report: semantic_references
---
# Child

Intro with [parent](parent.md), ![Diagram]([[media:docs/studio/diagram.png]]), and [[ref:work:638|three signs]].

`[[ref:series:26]]`

```text
[[ref:moment:dark-sky]]
```

[[interactive-html:chart.html height=420]]

<img src="/image.jpg" alt="Alt text">

{child_body_suffix}
""",
    )


def prepare_repo(root: Path) -> None:
    write_text(root / "_config.yml", "media_base: https://media.example.test\n")
    write_scope_config(root)
    write_catalogue_records(root)
    write_text(root / "assets/docs/interactive/studio/chart.html", "<!doctype html><title>Chart</title>")
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

        index = read_json(root / "docs-viewer/generated/docs/studio/index.json")
        child = read_json(root / "docs-viewer/generated/docs/studio/by-id/child.json")
        references_index = read_json(root / "docs-viewer/generated/docs/studio/references/index.json")
        target_payload = read_json(root / "docs-viewer/generated/docs/studio/references/by-target/work/00638.json")
        by_doc = read_json(root / "docs-viewer/generated/docs/studio/references/by-doc/child.json")

    docs = index["docs"]
    assert [doc["doc_id"] for doc in docs] == ["parent", "child"]
    assert docs[1]["summary"] == "Child summary"
    assert docs[1]["ui_status"] == "done"
    assert docs[1]["content_url"] == "/docs-viewer/generated/docs/studio/by-id/child.json"
    assert isinstance(docs[1]["content_text_length"], int)

    content_html = child["content_html"]
    assert 'href="/docs/?scope=studio&doc=parent"' in content_html
    assert 'src="https://media.example.test/docs/studio/diagram.png"' in content_html
    assert 'title="Alt text"' in content_html
    assert 'class="docsViewer__interactiveFrame"' in content_html
    assert "--docs-viewer-interactive-height: 420px" in content_html
    assert 'href="/works/?work=00638"' in content_html
    assert "[[ref:series:26]]" in content_html
    assert "[[ref:moment:dark-sky]]" in content_html
    assert child["viewer_report"] == "semantic_references"

    assert references_index["header"]["schema"] == "docs_semantic_references_index_v1"
    assert references_index["header"]["count"] == 1
    assert references_index["targets"][0]["target_key"] == "work:00638"
    assert references_index["targets"][0]["bucket_url"] == "/docs-viewer/generated/docs/studio/references/by-target/work/00638.json"
    assert target_payload["header"]["schema"] == "docs_semantic_references_by_target_v1"
    assert target_payload["target_kind"] == "work"
    assert target_payload["references"][0]["source_doc_id"] == "child"
    assert by_doc["references"][0]["label"] == "three signs"
    assert result["diagnostics"]["docs_emitted"] == 2


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


def test_python_docs_builder_writes_browser_configs_on_cli_write() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        exit_code, _, _ = run_cli(root, ["--scope", "studio", "--write"])

        assert exit_code == 0
        browser_config = read_json(root / "docs-viewer/config/defaults/docs-viewer-config.json")
        public_config = read_json(root / "docs-viewer/config/defaults/docs-viewer-public-config.json")

    assert browser_config["schema_version"] == "docs_viewer_config_v1"
    assert browser_config["scopes"][0]["scope_id"] == "studio"
    assert browser_config["docs_viewer"]["ui_statuses_by_scope"] == {"studio": [{"ui_status": "done", "label": "Done"}]}
    assert public_config["scopes"] == []


def test_python_docs_builder_cli_dry_run_does_not_write_outputs() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        exit_code, stdout, stderr = run_cli(root, ["--scope", "studio"])

        assert exit_code == 0
        assert stderr == ""
        assert "Dry run:" in stdout
        assert "would write doc payloads: 2" in stdout
        assert diagnostics_from_stdout(stdout)["doc_payloads_changed"] == 2
        assert not (root / "docs-viewer/generated/docs/studio/index.json").exists()
        assert not (root / "docs-viewer/generated/docs/studio/references/index.json").exists()
        assert not (root / "docs-viewer/config/defaults/docs-viewer-config.json").exists()
        assert not (root / "docs-viewer/config/defaults/docs-viewer-public-config.json").exists()


def test_python_docs_builder_cli_reports_unchanged_second_write() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        first_exit, _, _ = run_cli(root, ["--scope", "studio", "--write"])
        second_exit, stdout, stderr = run_cli(root, ["--scope", "studio", "--write"])

        diagnostics = diagnostics_from_stdout(stdout)

    assert first_exit == 0
    assert second_exit == 0
    assert stderr == ""
    assert "Docs Viewer browser config unchanged:" in stdout
    assert "Docs Viewer public browser config unchanged:" in stdout
    assert "Doc payloads wrote: 0." in stdout
    assert "Reference by-doc payloads wrote: 0." in stdout
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

        exit_code, stdout, stderr = run_cli(root, ["--scope", "studio", "--only-doc-ids", "child", "--write"])
        parent_after = read_json(root / "docs-viewer/generated/docs/studio/by-id/parent.json")
        child_after = read_json(root / "docs-viewer/generated/docs/studio/by-id/child.json")
        diagnostics = diagnostics_from_stdout(stdout)

    assert exit_code == 0
    assert stderr == ""
    assert parent_after == parent_before
    assert "CLI targeted update." in child_after["content_html"]
    assert "Doc payloads wrote: 1." in stdout
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


def main() -> None:
    test_python_docs_builder_writes_docs_payloads_and_references()
    test_python_docs_builder_preserves_existing_payloads_for_targeted_builds()
    test_python_docs_builder_writes_browser_configs_on_cli_write()
    test_python_docs_builder_cli_dry_run_does_not_write_outputs()
    test_python_docs_builder_cli_reports_unchanged_second_write()
    test_python_docs_builder_cli_targeted_write_updates_selected_doc_only()
    test_python_docs_builder_script_reports_front_matter_errors_without_traceback()
    print("Python Docs Viewer builder tests OK")


if __name__ == "__main__":
    main()
