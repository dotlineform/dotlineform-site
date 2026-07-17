#!/usr/bin/env python3
"""Python Docs Viewer builder CLI tests."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from build_docs_test_support import (
    BUILD_DIR,
    CHILD_DOC_ID,
    PARENT_DOC_ID,
    diagnostics_from_stdout,
    prepare_repo,
    read_json,
    run_cli,
    write_public_scope_config,
    write_public_source_docs,
    write_site_tools_config,
    write_source_docs,
    write_text,
)

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
    assert browser_config["scopes"][0]["index_tree_url"] == "/docs-viewer/published/docs/studio/index-tree.json"
    assert browser_config["scopes"][0]["recent_url"] == "/docs-viewer/published/docs/studio/recent.json"
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
        assert not (root / "docs-viewer/published/docs/studio/references/index.json").exists()
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
        parent_before = read_json(root / f"docs-viewer/published/docs/studio/by-id/{PARENT_DOC_ID}.json")
        write_source_docs(root, child_body_suffix="CLI targeted update.")

        exit_code, stdout, stderr = run_cli(
            root,
            ["--scope", "studio", "--only-doc-ids", CHILD_DOC_ID, "--write", "--diagnostics"],
        )
        parent_after = read_json(root / f"docs-viewer/published/docs/studio/by-id/{PARENT_DOC_ID}.json")
        child_after = read_json(root / f"docs-viewer/published/docs/studio/by-id/{CHILD_DOC_ID}.json")
        diagnostics = diagnostics_from_stdout(stdout)

    assert exit_code == 0
    assert stderr == ""
    assert parent_after == parent_before
    assert "CLI targeted update." in child_after["content_html"]
    assert "Docs build (write) scope=studio" in stdout
    assert "docs wrote: 1" in stdout
    assert diagnostics["build_mode"] == "targeted"
    assert diagnostics["only_doc_ids"] == [CHILD_DOC_ID]
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


def test_python_docs_builder_script_requires_doc_id_without_traceback() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        write_text(
            root / "docs-viewer/source/studio/missing-doc-id.md",
            """---
title: Missing Doc Id
---
# Missing Doc Id
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
    assert "Missing required doc_id in missing-doc-id.md" in completed.stderr
    assert "Traceback" not in completed.stderr


def test_python_docs_builder_script_rejects_legacy_doc_id_without_traceback() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        write_text(
            root / "docs-viewer/source/studio/legacy.md",
            """---
doc_id: legacy
title: Legacy
---
# Legacy
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
    assert "doc_id must use the immutable document ID format in legacy.md" in completed.stderr
    assert "Traceback" not in completed.stderr
