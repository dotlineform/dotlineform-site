#!/usr/bin/env python3
"""Python Docs Viewer builder sub-scope tests."""

from __future__ import annotations

import tempfile
from pathlib import Path

import build_docs
from docs_scope_config import load_docs_scope_configs

from build_docs_test_support import (
    diagnostics_from_stdout,
    prepare_repo,
    read_json,
    run_cli,
    write_json,
    write_public_scope_config,
    write_public_source_docs,
    write_site_tools_config,
    write_text,
)

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
    assert manifest == {
        "docs": [
            {"doc_id": "detail", "title": "Detail"},
            {"doc_id": "related", "title": "Related"},
        ]
    }
    assert detail["doc_id"] == "detail"
    assert detail["title"] == "Detail"
    assert detail["last_updated"] == "2026-06-21"
    assert "source_path" not in detail
    assert detail["viewer_url"] == "/docs/?scope=studio&doc=tags-report&subdoc=detail"
    assert 'href="related.md"' in detail["content_html"]
    assert related["parent_id"] == "detail"
    assert not (root / "docs-viewer/generated/docs/studio/tags/by-id/stale.json").exists()
    assert not (root / "docs-viewer/generated/docs/studio/tags/index-tree.json").exists()
    assert not (root / "docs-viewer/generated/docs/studio/tags/recently-added.json").exists()

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
