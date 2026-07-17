#!/usr/bin/env python3
"""Python Docs Viewer external scope builder tests."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from build_docs_test_support import (
    PRIVATE_DOC_ID,
    read_json,
    run_cli,
    write_catalogue_records,
    write_external_scope_config,
    write_site_tools_config,
    write_text,
)

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
            external_root / f"source/private/{PRIVATE_DOC_ID}.md",
            f"""---
doc_id: {PRIVATE_DOC_ID}
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
            index_tree = read_json(external_root / "published/docs/private/index-tree.json")
            payload = read_json(external_root / f"published/docs/private/by-id/{PRIVATE_DOC_ID}.json")
        finally:
            if old_projects_base is None:
                os.environ.pop("DOTLINEFORM_PROJECTS_BASE_DIR", None)
            else:
                os.environ["DOTLINEFORM_PROJECTS_BASE_DIR"] = old_projects_base

    assert exit_code == 0
    assert stderr == ""
    assert "scope=private" in stdout
    assert index_tree["docs"][0]["content_url"] == f"/docs/doc?scope=private&doc_id={PRIVATE_DOC_ID}"
    assert payload["doc_id"] == PRIVATE_DOC_ID
