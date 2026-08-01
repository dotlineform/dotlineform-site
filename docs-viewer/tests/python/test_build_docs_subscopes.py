#!/usr/bin/env python3
"""Python Docs Viewer builder sub-scope tests."""

from __future__ import annotations

import tempfile
from pathlib import Path

import build_docs
import pytest
from docs_scope_config import load_docs_scope_configs

from build_docs_test_support import (
    CHILD_DOC_ID,
    PARENT_DOC_ID,
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
from repo_factory import docs_scope_record, docs_sub_scope_record


TAGS_REPORT_DOC_ID = "d-20260620-000000-000011"
DETAIL_DOC_ID = "d-20260620-000000-000012"
RELATED_DOC_ID = "d-20260622-000000-000013"
HIDDEN_DOC_ID = "d-20260622-000000-000014"

def test_python_docs_builder_excludes_configured_sub_scope_sources() -> None:
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
            root / f"docs-viewer/scopes/studio/source/sub-scopes/tags/documents/{DETAIL_DOC_ID}.md",
            f"""---
doc_id: {DETAIL_DOC_ID}
title: Detail
---
# Detail

Sub-scope detail body.
""",
        )

        config = load_docs_scope_configs(root)["studio"]
        result = build_docs.DocsDataBuilder(repo_root=root, config=config).run(write=True)
        browser_config = build_docs.browser_scope_config_payload(root, [config])

        assert not (root / f"docs-viewer/scopes/studio/published/documents/by-id/{DETAIL_DOC_ID}.json").exists()

    assert [doc["doc_id"] for doc in result["index_payload"]["docs"]] == [PARENT_DOC_ID, CHILD_DOC_ID]
    assert result["diagnostics"]["source_files_scanned"] == 2
    assert browser_config["scopes"][0]["sub_scopes"] == [
        {
            "sub_scope": "tags",
            "title": "",
            "manifest_url": "/docs-viewer/scopes/studio/published/documents/sub-scopes/tags/manage-manifest.json",
            "by_id_url_base": "/docs-viewer/scopes/studio/published/documents/sub-scopes/tags/by-id",
        }
    ]


def test_python_docs_builder_writes_empty_sub_scope_manifest_pair() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        config_path = root / "docs-viewer/config/scopes/docs_scopes.json"
        payload = read_json(config_path)
        payload["scopes"][0]["sub_scopes"] = [
            docs_sub_scope_record("studio", "tags", title="Tags")
        ]
        write_json(config_path, payload)
        (
            root
            / "docs-viewer/scopes/studio/source/sub-scopes/tags/documents"
        ).mkdir(parents=True)

        exit_code, stdout, stderr = run_cli(
            root,
            ["--scope", "studio", "--sub-scope", "tags", "--write"],
        )
        manifest = read_json(
            root
            / "docs-viewer/scopes/studio/published/documents/sub-scopes/tags/manifest.json"
        )
        manage_manifest = read_json(
            root
            / "docs-viewer/scopes/studio/published/documents/sub-scopes/tags/manage-manifest.json"
        )

    assert exit_code == 0
    assert stderr == ""
    assert "docs total: 0" in stdout
    assert manifest == {"docs": []}
    assert manage_manifest == {"docs": []}


def test_python_docs_builder_projects_folder_paths_only_into_manage_manifest() -> None:
    first_doc_id = "d-20260801-101500-a1b2c3"
    second_doc_id = "d-20260801-101501-b2c3d4"
    pathless_doc_id = "d-20260801-101502-c3d4e5"
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        write_json(
            root / "docs-viewer/config/scopes/docs_scopes.json",
            {
                "schema_version": "docs_scopes_v3",
                "scopes": [
                    docs_scope_record(
                        "dotlineform",
                        sub_scopes=[
                            docs_sub_scope_record(
                                "dotlineform",
                                "projects",
                                title="Projects",
                                report_customisation={
                                    "id": "dotlineform_projects",
                                    "settings": {},
                                },
                            )
                        ],
                    )
                ],
            },
        )
        source_root = root / (
            "docs-viewer/scopes/dotlineform/source/sub-scopes/"
            "projects/documents"
        )
        write_text(
            source_root / f"{first_doc_id}.md",
            f"""---
doc_id: {first_doc_id}
title: Architecture
folder_path: projects/architecture
---
# Architecture
""",
        )
        write_text(
            source_root / f"{second_doc_id}.md",
            f"""---
doc_id: {second_doc_id}
title: Architecture notes
folder_path: projects/architecture
---
# Architecture notes
""",
        )
        write_text(
            source_root / f"{pathless_doc_id}.md",
            f"""---
doc_id: {pathless_doc_id}
title: Pathless
---
# Pathless
""",
        )

        exit_code, _stdout, stderr = run_cli(
            root,
            ["--scope", "dotlineform", "--sub-scope", "projects", "--write"],
        )
        manifest = read_json(
            root / (
                "docs-viewer/scopes/dotlineform/published/documents/"
                "sub-scopes/projects/manifest.json"
            )
        )
        manage_manifest = read_json(
            root / (
                "docs-viewer/scopes/dotlineform/published/documents/"
                "sub-scopes/projects/manage-manifest.json"
            )
        )

    assert exit_code == 0
    assert stderr == ""
    assert manifest == {
        "docs": [
            {"doc_id": first_doc_id, "title": "Architecture"},
            {"doc_id": second_doc_id, "title": "Architecture notes"},
            {"doc_id": pathless_doc_id, "title": "Pathless"},
        ]
    }
    assert manage_manifest == {
        "customisation": {"id": "dotlineform_projects", "data": {}},
        "docs": [
            {
                "doc_id": first_doc_id,
                "title": "Architecture",
                "ui_status": "",
                "viewable": True,
                "last_updated": "",
                "customisation": {"folder_path": "projects/architecture"},
            },
            {
                "doc_id": second_doc_id,
                "title": "Architecture notes",
                "ui_status": "",
                "viewable": True,
                "last_updated": "",
                "customisation": {"folder_path": "projects/architecture"},
            },
            {
                "doc_id": pathless_doc_id,
                "title": "Pathless",
                "ui_status": "",
                "viewable": True,
                "last_updated": "",
            },
        ],
    }

def test_python_docs_builder_writes_sub_scope_payloads_and_minimal_manifest() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        config_path = root / "docs-viewer/config/scopes/docs_scopes.json"
        payload = read_json(config_path)
        payload["scopes"][0]["sub_scopes"] = [
            docs_sub_scope_record(
                "studio",
                "tags",
                title="Tags",
                analysis_tag_groups=["subject", "domain", "form", "theme"],
            )
        ]
        write_json(config_path, payload)
        write_text(
            root / f"docs-viewer/scopes/studio/source/documents/{TAGS_REPORT_DOC_ID}.md",
            f"""---
doc_id: {TAGS_REPORT_DOC_ID}
title: Tags
added_date: 2026-06-20
last_updated: 2026-06-21
parent_id: ""
group: subject
viewer_report: docs_subscope
viewer_report_subscope: tags
---
# Tags
""",
        )
        write_text(
            root / f"docs-viewer/scopes/studio/source/sub-scopes/tags/documents/{DETAIL_DOC_ID}.md",
            f"""---
doc_id: {DETAIL_DOC_ID}
title: Detail
added_date: 2026-06-20
last_updated: 2026-06-21
parent_id: ""
ui_status: draft
group: subject
---
# Detail

Sub-scope detail body with [related](related.md).
""",
        )
        write_text(
            root / f"docs-viewer/scopes/studio/source/sub-scopes/tags/documents/{RELATED_DOC_ID}.md",
            f"""---
doc_id: {RELATED_DOC_ID}
title: Related
added_date: 2026-06-22
last_updated: 2026-06-23
parent_id: {DETAIL_DOC_ID}
---
# Related

Related body.
""",
        )
        write_json(root / "docs-viewer/scopes/studio/published/documents/sub-scopes/tags/by-id/stale.json", {"doc_id": "stale"})

        exit_code, stdout, stderr = run_cli(root, ["--scope", "studio", "--sub-scope", "tags", "--write", "--diagnostics"])
        manifest = read_json(root / "docs-viewer/scopes/studio/published/documents/sub-scopes/tags/manifest.json")
        manage_manifest = read_json(
            root
            / "docs-viewer/scopes/studio/published/documents/sub-scopes/tags/manage-manifest.json"
        )
        detail = read_json(root / f"docs-viewer/scopes/studio/published/documents/sub-scopes/tags/by-id/{DETAIL_DOC_ID}.json")
        related = read_json(root / f"docs-viewer/scopes/studio/published/documents/sub-scopes/tags/by-id/{RELATED_DOC_ID}.json")

    assert exit_code == 0
    assert stderr == ""
    assert "Docs sub-scope build (write) scope=studio sub_scope=tags" in stdout
    diagnostics = diagnostics_from_stdout(stdout)
    assert diagnostics["build_mode"] == "sub_scope"
    assert diagnostics["sub_scope"] == "tags"
    assert diagnostics["docs_emitted"] == 2
    assert manifest == {
        "docs": [
            {"doc_id": DETAIL_DOC_ID, "title": "Detail"},
            {"doc_id": RELATED_DOC_ID, "title": "Related"},
        ]
    }
    assert manage_manifest == {
        "customisation": {
            "id": "analysis_tags",
            "data": {
                "groups": ["subject", "domain", "form", "theme"],
            },
        },
        "docs": [
            {
                "doc_id": DETAIL_DOC_ID,
                "title": "Detail",
                "ui_status": "draft",
                "viewable": True,
                "last_updated": "2026-06-21",
                "customisation": {"group": "subject"},
            },
            {
                "doc_id": RELATED_DOC_ID,
                "title": "Related",
                "ui_status": "",
                "viewable": True,
                "last_updated": "2026-06-23",
            },
        ],
    }
    assert detail["doc_id"] == DETAIL_DOC_ID
    assert detail["title"] == "Detail"
    assert detail["last_updated"] == "2026-06-21"
    assert "source_path" not in detail
    assert "group" not in detail
    assert detail["viewer_url"] == f"/docs/?scope=studio&doc={TAGS_REPORT_DOC_ID}&subdoc={DETAIL_DOC_ID}"
    assert 'href="related.md"' in detail["content_html"]
    assert related["parent_id"] == DETAIL_DOC_ID
    assert not (root / "docs-viewer/scopes/studio/published/documents/sub-scopes/tags/by-id/stale.json").exists()
    assert not (root / "docs-viewer/scopes/studio/published/documents/sub-scopes/tags/index-tree.json").exists()
    assert not (root / "docs-viewer/scopes/studio/published/documents/sub-scopes/tags/recent.json").exists()


@pytest.mark.parametrize(
    ("group", "error"),
    [
        ("unknown", "Unknown group"),
        ("[subject, theme]", "Unknown group"),
    ],
)
def test_python_docs_builder_rejects_invalid_sub_scope_group(
    group: str,
    error: str,
) -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        config_path = root / "docs-viewer/config/scopes/docs_scopes.json"
        payload = read_json(config_path)
        payload["scopes"][0]["sub_scopes"] = [
            docs_sub_scope_record(
                "studio",
                "tags",
                analysis_tag_groups=["subject", "domain", "form", "theme"],
            )
        ]
        write_json(config_path, payload)
        write_text(
            root
            / f"docs-viewer/scopes/studio/source/sub-scopes/tags/documents/{DETAIL_DOC_ID}.md",
            f"""---
doc_id: {DETAIL_DOC_ID}
title: Detail
group: {group}
---
# Detail
""",
        )

        with pytest.raises(RuntimeError, match=error):
            run_cli(
                root,
                ["--scope", "studio", "--sub-scope", "tags"],
            )


def test_python_docs_builder_can_confine_sub_scope_write_from_browser_configs() -> None:
    browser_config_paths = (
        Path("docs-viewer/config/defaults/docs-viewer-config.json"),
        Path("docs-viewer/config/defaults/docs-viewer-public-config.json"),
        Path("site/docs-viewer/config/defaults/docs-viewer-public-config.json"),
    )
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
            root
            / f"docs-viewer/scopes/studio/source/sub-scopes/tags/documents/{DETAIL_DOC_ID}.md",
            f"""---
doc_id: {DETAIL_DOC_ID}
title: Detail
---
# Detail
""",
        )
        for path in browser_config_paths:
            write_text(root / path, f"sentinel:{path.as_posix()}\n")
        before = {
            path: (root / path).read_bytes()
            for path in browser_config_paths
        }

        exit_code, stdout, stderr = run_cli(
            root,
            [
                "--scope",
                "studio",
                "--sub-scope",
                "tags",
                "--write",
                "--skip-browser-config",
            ],
        )

        after = {
            path: (root / path).read_bytes()
            for path in browser_config_paths
        }
        manifest_exists = (
            root
            / "docs-viewer/scopes/studio/published/documents/sub-scopes/tags/manifest.json"
        ).is_file()

    assert exit_code == 0
    assert stderr == ""
    assert "Docs sub-scope build (write)" in stdout
    assert manifest_exists is True
    assert after == before


def test_python_docs_builder_rejects_browser_config_suppression_outside_sub_scope() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)

        with pytest.raises(
            RuntimeError,
            match="--skip-browser-config requires --sub-scope",
        ):
            run_cli(
                root,
                ["--scope", "studio", "--write", "--skip-browser-config"],
            )


def test_python_docs_builder_keeps_non_viewable_docs_out_of_public_manifest() -> None:
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
            root / f"docs-viewer/scopes/studio/source/sub-scopes/tags/documents/{DETAIL_DOC_ID}.md",
            f"""---
doc_id: {DETAIL_DOC_ID}
title: Detail
---
# Detail
""",
        )
        write_text(
            root / f"docs-viewer/scopes/studio/source/sub-scopes/tags/documents/{HIDDEN_DOC_ID}.md",
            f"""---
doc_id: {HIDDEN_DOC_ID}
title: Hidden
viewable: false
---
# Hidden
""",
        )

        exit_code, _stdout, stderr = run_cli(
            root,
            ["--scope", "studio", "--sub-scope", "tags", "--write"],
        )
        manifest = read_json(
            root / "docs-viewer/scopes/studio/published/documents/sub-scopes/tags/manifest.json"
        )
        manage_manifest = read_json(
            root
            / "docs-viewer/scopes/studio/published/documents/sub-scopes/tags/manage-manifest.json"
        )
        visible_payload = read_json(
            root
            / f"docs-viewer/scopes/studio/published/documents/sub-scopes/tags/by-id/{DETAIL_DOC_ID}.json"
        )
        hidden_payload_path = (
            root
            / f"docs-viewer/scopes/studio/published/documents/sub-scopes/tags/by-id/{HIDDEN_DOC_ID}.json"
        )
        hidden_payload_exists = hidden_payload_path.is_file()

    assert exit_code == 0
    assert stderr == ""
    assert manifest == {"docs": [{"doc_id": DETAIL_DOC_ID, "title": "Detail"}]}
    assert manage_manifest == {
        "docs": [
            {
                "doc_id": DETAIL_DOC_ID,
                "title": "Detail",
                "ui_status": "",
                "viewable": True,
                "last_updated": "",
            },
            {
                "doc_id": HIDDEN_DOC_ID,
                "title": "Hidden",
                "ui_status": "",
                "viewable": False,
                "last_updated": "",
            },
        ]
    }
    assert set(visible_payload) >= {"doc_id", "title", "content_html"}
    assert hidden_payload_exists


def test_python_docs_builder_projects_registered_manage_customisation_only() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        config_path = root / "docs-viewer/config/scopes/docs_scopes.json"
        payload = read_json(config_path)
        payload["scopes"][0]["sub_scopes"] = [
            docs_sub_scope_record(
                "studio",
                "tags",
                title="Tags",
                report_customisation={
                    "id": "analysis_tags",
                    "settings": {"groups": ["subject", "theme"]},
                },
            )
        ]
        write_json(config_path, payload)
        write_text(
            root / f"docs-viewer/scopes/studio/source/documents/{TAGS_REPORT_DOC_ID}.md",
            f"""---
doc_id: {TAGS_REPORT_DOC_ID}
title: Tags
viewer_report: docs_subscope
viewer_report_access: local
viewer_report_subscope: tags
---
# Tags
""",
        )
        write_text(
            root / f"docs-viewer/scopes/studio/source/sub-scopes/tags/documents/{DETAIL_DOC_ID}.md",
            f"""---
doc_id: {DETAIL_DOC_ID}
title: Detail
last_updated: 2026-06-21
group: subject
---
# Detail
""",
        )

        exit_code, _stdout, stderr = run_cli(
            root,
            ["--scope", "studio", "--sub-scope", "tags", "--write"],
        )
        manifest = read_json(
            root / "docs-viewer/scopes/studio/published/documents/sub-scopes/tags/manifest.json"
        )
        manage_manifest = read_json(
            root
            / "docs-viewer/scopes/studio/published/documents/sub-scopes/tags/manage-manifest.json"
        )
        detail = read_json(
            root
            / f"docs-viewer/scopes/studio/published/documents/sub-scopes/tags/by-id/{DETAIL_DOC_ID}.json"
        )
        config = load_docs_scope_configs(root)["studio"]
        browser_config = build_docs.browser_scope_config_payload(root, [config])
        public_browser_config = build_docs.browser_scope_config_payload(
            root,
            [config],
            published=True,
        )

    assert exit_code == 0
    assert stderr == ""
    assert manifest == {"docs": [{"doc_id": DETAIL_DOC_ID, "title": "Detail"}]}
    assert manage_manifest == {
        "customisation": {
            "id": "analysis_tags",
            "data": {"groups": ["subject", "theme"]},
        },
        "docs": [
            {
                "doc_id": DETAIL_DOC_ID,
                "title": "Detail",
                "ui_status": "",
                "viewable": True,
                "last_updated": "2026-06-21",
                "customisation": {"group": "subject"},
            }
        ],
    }
    assert detail["viewer_url"] == (
        f"/docs/?scope=studio&doc={TAGS_REPORT_DOC_ID}&subdoc={DETAIL_DOC_ID}"
    )
    assert browser_config["scopes"][0]["sub_scopes"][0]["report_customisation"] == {
        "id": "analysis_tags"
    }
    assert "report_customisation" not in public_browser_config["scopes"][0]["sub_scopes"][0]


def test_python_docs_builder_public_sub_scope_separates_manage_and_public_url_bases() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        write_site_tools_config(root, media_base="")
        write_public_scope_config(root)
        write_public_source_docs(root)
        config_path = root / "docs-viewer/config/scopes/docs_scopes.json"
        payload = read_json(config_path)
        payload["scopes"][0]["sub_scopes"] = [
            docs_sub_scope_record(
                "library",
                "tags",
                title="Tags",
                public_title="Concepts",
                scope_type="public",
            )
        ]
        write_json(config_path, payload)
        write_text(
            root / f"docs-viewer/scopes/library/source/sub-scopes/tags/documents/{DETAIL_DOC_ID}.md",
            f"""---
doc_id: {DETAIL_DOC_ID}
title: Detail
added_date: 2026-06-20
last_updated: 2026-06-21
---
# Detail
""",
        )

        exit_code, _stdout, stderr = run_cli(root, ["--scope", "library", "--sub-scope", "tags", "--write"])
        detail = read_json(root / f"docs-viewer/scopes/library/published/documents/sub-scopes/tags/by-id/{DETAIL_DOC_ID}.json")
        config = load_docs_scope_configs(root)["library"]
        browser_config = build_docs.browser_scope_config_payload(root, [config])
        public_browser_config = build_docs.browser_scope_config_payload(
            root,
            [config],
            published=True,
        )

    assert exit_code == 0
    assert stderr == ""
    assert detail["doc_id"] == DETAIL_DOC_ID
    assert browser_config["scopes"][0]["sub_scopes"] == [
        {
            "sub_scope": "tags",
            "title": "Tags",
            "manifest_url": "/docs-viewer/scopes/library/published/documents/sub-scopes/tags/manage-manifest.json",
            "by_id_url_base": "/docs-viewer/scopes/library/published/documents/sub-scopes/tags/by-id",
        }
    ]
    assert public_browser_config["scopes"][0]["sub_scopes"] == [
        {
            "sub_scope": "tags",
            "title": "Concepts",
            "manifest_url": "/assets/data/docs/scopes/library/tags/manifest.json",
            "by_id_url_base": "/assets/data/docs/scopes/library/tags/by-id",
        }
    ]
