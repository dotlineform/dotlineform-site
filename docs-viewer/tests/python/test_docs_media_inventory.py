#!/usr/bin/env python3
"""Typed Docs media inventory checks."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
for _path in (REPO_ROOT / "docs-viewer/build", REPO_ROOT / "docs-viewer/services"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))


from docs_media_inventory import inventory_scope_media
from docs_scope_config import load_docs_scope_configs
from repo_factory import docs_scope_record, write_docs_scope_config, write_site_tools_config


def write_config(repo_root: Path, record: dict[str, object]) -> None:
    write_docs_scope_config(repo_root, [record])


@pytest.fixture(autouse=True)
def isolated_media_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    projects_base = tmp_path / "projects"
    projects_base.mkdir(parents=True)
    monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(projects_base))


def test_inventory_lists_unreferenced_owned_media_and_reports_missing_references(tmp_path: Path) -> None:
    write_site_tools_config(tmp_path, media_base="https://media.example.test")
    record = docs_scope_record(
        "example",
        scope_type="public",
        viewer_base_url="/example/",
        include_scope_param=False,
        default_doc_id="example",
        media_types=("img", "svg", "files", "html"),
    )
    write_config(tmp_path, record)
    source = tmp_path / "docs-viewer/scopes/example/source/documents/example.md"
    source.parent.mkdir(parents=True)
    source.write_text(
        """---
doc_id: example
title: Example
---
![Used]([[media:docs/example/img/used.png]])
[[html-media:docs/example/html/widget.html height=320]]
[Missing]([[media:docs/example/files/missing.pdf]])
[Direct route](/assets/data/docs/scopes/example/media/html/widget.html)
""",
        encoding="utf-8",
    )
    media_root = tmp_path / "docs-viewer/scopes/example/source/media"
    html = media_root / "html/widget.html"
    html.parent.mkdir(parents=True)
    html.write_text("<!doctype html><title>Widget</title>", encoding="utf-8")
    (media_root / "img").mkdir(parents=True)
    (media_root / "img/used.png").write_bytes(b"used")
    (media_root / "img/unreferenced.png").write_bytes(b"owned but unreferenced")

    inventory = inventory_scope_media(
        tmp_path,
        load_docs_scope_configs(tmp_path)["example"],
    )

    by_identity = {(item.media_type, item.identity): item for item in inventory.items}
    assert by_identity[("img", "used.png")].document_ids == ("example",)
    assert by_identity[("img", "unreferenced.png")].document_ids == ()
    assert by_identity[("html", "widget.html")].served_path.endswith("/html/widget.html")
    assert [(item.media_type, item.identity) for item in inventory.missing_references] == [
        ("files", "missing.pdf")
    ]
