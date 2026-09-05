#!/usr/bin/env python3
"""Python Docs Viewer builder sub-scope tests."""

from __future__ import annotations

import tempfile
from pathlib import Path

import build_docs
import docs_subscope_customisations as customisations
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
    write_route_config,
    write_site_tools_config,
    write_text,
)
from repo_factory import docs_scope_record, docs_sub_scope_record


TAGS_REPORT_DOC_ID = "d-20260620-000000-000011"
DETAIL_DOC_ID = "d-20260620-000000-000012"
RELATED_DOC_ID = "d-20260622-000000-000013"
HIDDEN_DOC_ID = "d-20260622-000000-000014"


def test_child_report_preserves_descriptor_and_authored_host(tmp_path: Path) -> None:
    prepare_repo(tmp_path)
    config_path = tmp_path / "docs-viewer/config/scopes/docs_scopes.json"
    payload = read_json(config_path)
    payload["scopes"][0]["sub_scopes"] = [docs_sub_scope_record("studio", "works")]
    write_json(config_path, payload)
    write_text(
        tmp_path / f"docs-viewer/scopes/studio/source/sub-scopes/works/documents/{DETAIL_DOC_ID}.md",
        f'''---
doc_id: {DETAIL_DOC_ID}
title: Child report
---
Before report.

:::report
id: reports_list
access: public
:::

After report with **formatted text**.
''',
    )
    exit_code, _, stderr = run_cli(
        tmp_path, ["--scope", "studio", "--sub-scope", "works", "--write", "--skip-media-builds"],
    )
    assert exit_code == 0, stderr
    child = read_json(tmp_path / f"docs-viewer/scopes/studio/generated/documents/sub-scopes/works/by-id/{DETAIL_DOC_ID}.json")
    assert child["doc_id"] == DETAIL_DOC_ID
    assert child["report"]["id"] == "reports_list"
    assert child["report"]["access"] == "public"
    html = child["content_html"]
    assert html.count("data-docs-viewer-report-host") == 1
    assert html.index("Before report") < html.index("data-docs-viewer-report-host") < html.index("After report")
    assert "<p>After report with <strong>formatted text</strong>.</p>" in html


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

        assert not (root / f"docs-viewer/scopes/studio/generated/documents/by-id/{DETAIL_DOC_ID}.json").exists()

    assert [doc["doc_id"] for doc in result["index_payload"]["docs"]] == [PARENT_DOC_ID, CHILD_DOC_ID]
    assert result["diagnostics"]["source_files_scanned"] == 2
    assert browser_config["scopes"][0]["sub_scopes"] == [
        {
            "sub_scope": "tags",
            "title": "",
            "manifest_url": "/docs-viewer/scopes/studio/generated/documents/sub-scopes/tags/manage-manifest.json",
            "by_id_url_base": "/docs-viewer/scopes/studio/generated/documents/sub-scopes/tags/by-id",
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
            / "docs-viewer/scopes/studio/generated/documents/sub-scopes/tags/manifest.json"
        )
        manage_manifest = read_json(
            root
            / "docs-viewer/scopes/studio/generated/documents/sub-scopes/tags/manage-manifest.json"
        )

    assert exit_code == 0
    assert stderr == ""
    assert "docs total: 0" in stdout
    assert manifest == {"docs": []}
    assert manage_manifest == {"docs": []}


def test_python_docs_builder_projects_empty_processing_collection_report(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    prepare_repo(root)
    config_path = root / "docs-viewer/config/scopes/docs_scopes.json"
    payload = read_json(config_path)
    payload["scopes"][0]["sub_scopes"] = [
        docs_sub_scope_record(
            "studio",
            "processing",
            title="Processing",
            sub_scope_customisation={
                "id": "dotlineform_processing",
                "settings": {},
            },
        ),
        docs_sub_scope_record(
            "studio",
            "projects",
            title="Projects",
            sub_scope_customisation={
                "id": "dotlineform_projects",
                "settings": {},
            },
        ),
    ]
    payload["scopes"].append(
        docs_scope_record(
            "analysis",
            scope_type="public",
            viewer_base_url="/analysis/",
            include_scope_param=False,
            sub_scopes=[
                docs_sub_scope_record(
                    "analysis",
                    "works",
                    scope_type="public",
                    sub_scope_customisation={
                        "id": "analysis_works",
                        "settings": {},
                    },
                )
            ],
        )
    )
    write_json(config_path, payload)
    (
        root
        / "docs-viewer/scopes/studio/source/sub-scopes/processing/documents"
    ).mkdir(parents=True)

    exit_code, _stdout, stderr = run_cli(
        root,
        ["--scope", "studio", "--sub-scope", "processing", "--write"],
    )
    manifest = read_json(
        root
        / "docs-viewer/scopes/studio/generated/documents/sub-scopes/processing/manifest.json"
    )
    manage_manifest = read_json(
        root
        / "docs-viewer/scopes/studio/generated/documents/sub-scopes/processing/manage-manifest.json"
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
    assert manifest == {"docs": []}
    assert manage_manifest == {
        "customisation": {
            "id": "dotlineform_processing",
            "data": {},
        },
        "subject_generation": manage_manifest["subject_generation"],
        "docs": [],
    }
    assert browser_config["scopes"][0]["sub_scopes"][0][
        "sub_scope_customisation"
    ] == {
        "id": "dotlineform_processing",
        "capabilities": {
            "assignable_field_groups": ["authoring_subject"],
            "lineage_copy": {
                "contract_id": "dotlineform_processing_to_analysis_works",
                "target": {"scope": "analysis", "sub_scope": "works"},
                "action_label": "Copy to Analysis",
                "modal_title": "Copy to analysis/works",
            },
        },
    }
    assert "sub_scope_customisation" not in public_browser_config["scopes"][0][
        "sub_scopes"
    ][0]


def test_python_docs_builder_projects_subjects_into_private_products() -> None:
    first_doc_id = "d-20260801-101500-a1b2c3"
    second_doc_id = "d-20260801-101501-b2c3d4"
    pathless_doc_id = "d-20260801-101502-c3d4e5"
    pre_publish_doc_id = "d-20260802-101500-d4e5f6"
    published_doc_id = "d-20260802-101501-e5f6a7"
    unavailable_doc_id = "d-20260802-101502-f6a7b8"
    analysis_report_doc_id = "d-20260802-090000-abcdef"
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        write_json(
            root / "docs-viewer/config/scopes/docs_scopes.json",
            {
                "schema_version": "docs_scopes_v5",
                "scopes": [
                    docs_scope_record(
                        "dotlineform",
                        sub_scopes=[
                            docs_sub_scope_record(
                                "dotlineform",
                                "projects",
                                title="Projects",
                                sub_scope_customisation={
                                    "id": "dotlineform_projects",
                                    "settings": {},
                                },
                            ),
                            docs_sub_scope_record(
                                "dotlineform",
                                "processing",
                                title="Processing",
                                sub_scope_customisation={
                                    "id": "dotlineform_processing",
                                    "settings": {},
                                },
                            ),
                        ],
                    ),
                    docs_scope_record(
                        "analysis",
                        scope_type="public",
                        viewer_base_url="/analysis/",
                        include_scope_param=False,
                        sub_scopes=[
                            docs_sub_scope_record(
                                "analysis",
                                "works",
                                title="Works",
                                scope_type="public",
                                sub_scope_customisation={
                                    "id": "analysis_works",
                                    "settings": {},
                                },
                            )
                        ],
                    ),
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
        target_root = root / (
            "docs-viewer/scopes/analysis/generated/documents/"
            "sub-scopes/works/by-id"
        )
        pre_publish_url = (
            f"/docs/?scope=analysis&doc={analysis_report_doc_id}"
            f"&subdoc={pre_publish_doc_id}"
        )
        published_url = (
            f"/docs/?scope=analysis&doc={analysis_report_doc_id}"
            f"&subdoc={published_doc_id}"
        )
        write_text(
            root / (
                "docs-viewer/scopes/analysis/source/documents/"
                f"{analysis_report_doc_id}.md"
            ),
            f"""---
doc_id: {analysis_report_doc_id}
title: Works
---
# Works

:::report
id: docs_subscope
access: public
sub_scope: works
:::
""",
        )
        write_json(
            target_root / f"{pre_publish_doc_id}.json",
            {
                "doc_id": pre_publish_doc_id,
                "title": "Editorial draft",
                "viewer_url": pre_publish_url,
            },
        )
        write_json(
            target_root / f"{published_doc_id}.json",
            {
                "doc_id": published_doc_id,
                "title": "Published editorial",
                "viewer_url": published_url,
            },
        )
        write_json(
            root
            / "docs-viewer/scopes/dotlineform/source/sub-scopes/projects/data/document-publication-lineage.json",
            {
                "schema_version": "docs_document_publication_lineage_v3",
                "working_collection": {
                    "scope": "dotlineform",
                    "sub_scope": "projects",
                },
                "editorial_collection": {
                    "scope": "analysis",
                    "sub_scope": "works",
                },
                "records": [
                    {
                        "working_doc_id": first_doc_id,
                        "editorials": [
                            {
                                "doc_id": pre_publish_doc_id,
                                "created_at": "2026-08-08T10:00:00Z",
                                "last_copied_at": "2026-08-08T10:00:00Z",
                                "published_url": None,
                            },
                            {
                                "doc_id": published_doc_id,
                                "created_at": "2026-08-08T11:00:00Z",
                                "last_copied_at": "2026-08-08T11:00:00Z",
                                "published_url": "/analysis/published",
                            },
                        ],
                    },
                    {
                        "working_doc_id": pathless_doc_id,
                        "editorials": [
                            {
                                "doc_id": unavailable_doc_id,
                                "created_at": "2026-08-08T12:00:00Z",
                                "last_copied_at": "2026-08-08T12:00:00Z",
                                "published_url": None,
                            }
                        ],
                    },
                ],
            },
        )

        exit_code, _stdout, stderr = run_cli(
            root,
            ["--scope", "dotlineform", "--sub-scope", "projects", "--write"],
        )
        manifest = read_json(
            root / (
                "docs-viewer/scopes/dotlineform/generated/documents/"
                "sub-scopes/projects/manifest.json"
            )
        )
        config = load_docs_scope_configs(root)["dotlineform"]
        browser_config = build_docs.browser_scope_config_payload(root, [config])
        public_browser_config = build_docs.browser_scope_config_payload(
            root,
            [config],
            published=True,
        )
        manage_manifest = read_json(
            root / (
                "docs-viewer/scopes/dotlineform/generated/documents/"
                "sub-scopes/projects/manage-manifest.json"
            )
        )
        subject_associations = read_json(
            root / (
                "docs-viewer/scopes/dotlineform/generated/documents/"
                "sub-scopes/projects/subject-associations.json"
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
        "subject_generation": manage_manifest["subject_generation"],
        "docs": [
            {
                "doc_id": first_doc_id,
                "title": "Architecture",
                "ui_status": "",
                "last_updated": "",
                "authoring_subject": {
                    "state": "valid",
                    "kind": "folder",
                    "key": "projects/architecture",
                    "fields": ["folder_path"],
                },
                "customisation": {
                    "folder_path": "projects/architecture",
                    "publication_targets": [
                        {
                            "editorial": {
                                "scope": "analysis",
                                "sub_scope": "works",
                                "doc_id": pre_publish_doc_id,
                            },
                            "available": True,
                            "title": "Editorial draft",
                            "viewer_url": pre_publish_url,
                            "publication": None,
                        },
                        {
                            "editorial": {
                                "scope": "analysis",
                                "sub_scope": "works",
                                "doc_id": published_doc_id,
                            },
                            "available": True,
                            "title": "Published editorial",
                            "viewer_url": published_url,
                            "publication": {"public_url": "/analysis/published"},
                        },
                    ],
                },
            },
            {
                "doc_id": second_doc_id,
                "title": "Architecture notes",
                "ui_status": "",
                "last_updated": "",
                "authoring_subject": {
                    "state": "valid",
                    "kind": "folder",
                    "key": "projects/architecture",
                    "fields": ["folder_path"],
                },
                "customisation": {"folder_path": "projects/architecture"},
            },
            {
                "doc_id": pathless_doc_id,
                "title": "Pathless",
                "ui_status": "",
                "last_updated": "",
                "authoring_subject": {
                    "state": "none",
                    "kind": "none",
                    "key": "",
                    "fields": [],
                },
                "customisation": {
                    "publication_targets": [
                        {
                            "editorial": {
                                "scope": "analysis",
                                "sub_scope": "works",
                                "doc_id": unavailable_doc_id,
                            },
                            "available": False,
                            "title": "",
                            "viewer_url": "",
                            "publication": None,
                        }
                    ]
                },
            },
        ],
    }
    assert subject_associations == {
        "schema_version": "docs_subject_associations_v1",
        "scope": "dotlineform",
        "sub_scope": "projects",
        "subject_generation": manage_manifest["subject_generation"],
        "associations": [
            {
                "subject": {
                    "kind": "folder",
                    "key": "projects/architecture",
                },
                "documents": [
                    {
                        "target": {
                            "scope": "dotlineform",
                            "sub_scope": "projects",
                            "doc_id": first_doc_id,
                        },
                        "locations": [
                            {
                                "access": "manage",
                                "url": f"/docs/?scope=dotlineform&doc={first_doc_id}",
                            }
                        ],
                    },
                    {
                        "target": {
                            "scope": "dotlineform",
                            "sub_scope": "projects",
                            "doc_id": second_doc_id,
                        },
                        "locations": [
                            {
                                "access": "manage",
                                "url": f"/docs/?scope=dotlineform&doc={second_doc_id}",
                            }
                        ],
                    },
                ],
            }
        ],
    }
    assert browser_config["scopes"][0]["sub_scopes"][0][
        "sub_scope_customisation"
    ] == {
        "id": "dotlineform_projects",
        "capabilities": {
            "assignable_field_groups": ["authoring_subject"],
            "lineage_copy": {
                "contract_id": "dotlineform_projects_to_analysis_works",
                "target": {"scope": "analysis", "sub_scope": "works"},
                "action_label": "Copy to Analysis",
                "modal_title": "Copy to analysis/works",
            },
        },
    }
    assert "sub_scope_customisation" not in public_browser_config["scopes"][0][
        "sub_scopes"
    ][0]


def test_private_builder_reads_work_and_series_subjects_without_customisation() -> None:
    work_doc_id = "d-20260801-111500-a1b2c3"
    series_doc_id = "d-20260801-111501-b2c3d4"
    malformed_doc_id = "d-20260801-111502-c3d4e5"
    conflicting_doc_id = "d-20260801-111503-d4e5f6"
    none_doc_id = "d-20260801-111504-e5f6a7"
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        config_path = root / "docs-viewer/config/scopes/docs_scopes.json"
        payload = read_json(config_path)
        payload["scopes"][0]["sub_scopes"] = [
            docs_sub_scope_record("studio", "works", title="Works")
        ]
        write_json(config_path, payload)
        source_root = root / (
            "docs-viewer/scopes/studio/source/sub-scopes/works/documents"
        )
        fixtures = {
            work_doc_id: 'work_id: "00123"',
            series_doc_id: 'series_id: "026"',
            malformed_doc_id: "work_id: 00123",
            conflicting_doc_id: 'work_id: "00123"\nseries_id: "026"',
            none_doc_id: "",
        }
        for doc_id, subject_source in fixtures.items():
            write_text(
                source_root / f"{doc_id}.md",
                f"""---
doc_id: {doc_id}
title: {doc_id}
{subject_source}
---
# {doc_id}
""",
            )

        exit_code, _stdout, stderr = run_cli(
            root,
            ["--scope", "studio", "--sub-scope", "works", "--write"],
        )
        output_root = root / (
            "docs-viewer/scopes/studio/generated/documents/sub-scopes/works"
        )
        manage_manifest = read_json(output_root / "manage-manifest.json")
        associations = read_json(output_root / "subject-associations.json")
        write_text(
            source_root / f"{work_doc_id}.md",
            f"""---
doc_id: {work_doc_id}
title: {work_doc_id}
---
# {work_doc_id}
""",
        )
        rerun_exit_code, _rerun_stdout, rerun_stderr = run_cli(
            root,
            ["--scope", "studio", "--sub-scope", "works", "--write"],
        )
        cleared_manifest = read_json(output_root / "manage-manifest.json")
        cleared_associations = read_json(output_root / "subject-associations.json")
        for doc_id in fixtures:
            write_text(
                source_root / f"{doc_id}.md",
                f"""---
doc_id: {doc_id}
title: {doc_id}
---
# {doc_id}
""",
            )
        empty_exit_code, _empty_stdout, empty_stderr = run_cli(
            root,
            ["--scope", "studio", "--sub-scope", "works", "--write"],
        )
        empty_manifest = read_json(output_root / "manage-manifest.json")
        empty_associations = read_json(output_root / "subject-associations.json")

    assert exit_code == 0
    assert stderr == ""
    subjects_by_id = {
        row["doc_id"]: row["authoring_subject"]
        for row in manage_manifest["docs"]
    }
    assert subjects_by_id == {
        work_doc_id: {
            "state": "valid", "kind": "work", "key": "00123", "fields": ["work_id"]
        },
        series_doc_id: {
            "state": "valid", "kind": "series", "key": "026", "fields": ["series_id"]
        },
        malformed_doc_id: {
            "state": "malformed",
            "kind": "work",
            "key": "",
            "fields": ["work_id"],
            "evidence": {"work_id": 123},
        },
        conflicting_doc_id: {
            "state": "conflicting",
            "kind": "conflict",
            "key": "",
            "fields": ["work_id", "series_id"],
            "evidence": {"work_id": "00123", "series_id": "026"},
        },
        none_doc_id: {
            "state": "none", "kind": "none", "key": "", "fields": []
        },
    }
    assert associations["subject_generation"] == manage_manifest["subject_generation"]
    assert [record["subject"] for record in associations["associations"]] == [
        {"kind": "series", "key": "026"},
        {"kind": "work", "key": "00123"},
    ]
    assert [
        record["documents"][0]["target"]["doc_id"]
        for record in associations["associations"]
    ] == [series_doc_id, work_doc_id]
    assert rerun_exit_code == 0
    assert rerun_stderr == ""
    cleared_subjects_by_id = {
        row["doc_id"]: row["authoring_subject"]
        for row in cleared_manifest["docs"]
    }
    assert cleared_subjects_by_id[work_doc_id] == {
        "state": "none",
        "kind": "none",
        "key": "",
        "fields": [],
    }
    assert cleared_associations["subject_generation"] == cleared_manifest[
        "subject_generation"
    ]
    assert cleared_associations["associations"] == [
        {
            "subject": {"kind": "series", "key": "026"},
            "documents": associations["associations"][0]["documents"],
        }
    ]
    assert empty_exit_code == 0
    assert empty_stderr == ""
    assert {
        row["authoring_subject"]["state"]
        for row in empty_manifest["docs"]
    } == {"none"}
    assert empty_associations == {
        "schema_version": "docs_subject_associations_v1",
        "scope": "studio",
        "sub_scope": "works",
        "subject_generation": empty_manifest["subject_generation"],
        "associations": [],
    }


def test_subject_association_uses_composed_sub_scope_manage_location() -> None:
    report_doc_id = "d-20260801-121500-a1b2c3"
    work_doc_id = "d-20260801-121501-b2c3d4"
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        config_path = root / "docs-viewer/config/scopes/docs_scopes.json"
        payload = read_json(config_path)
        payload["scopes"][0]["sub_scopes"] = [
            docs_sub_scope_record("studio", "works", title="Works")
        ]
        write_json(config_path, payload)
        write_text(
            root / f"docs-viewer/scopes/studio/source/documents/{report_doc_id}.md",
            f"""---
doc_id: {report_doc_id}
title: Works
---
# Works

:::report
id: docs_subscope
access: local
sub_scope: works
:::
""",
        )
        write_text(
            root / f"docs-viewer/scopes/studio/source/sub-scopes/works/documents/{work_doc_id}.md",
            f"""---
doc_id: {work_doc_id}
title: Work note
work_id: "00123"
---
# Work note
""",
        )

        exit_code, _stdout, stderr = run_cli(
            root,
            ["--scope", "studio", "--sub-scope", "works", "--write"],
        )
        associations = read_json(
            root / (
                "docs-viewer/scopes/studio/generated/documents/sub-scopes/"
                "works/subject-associations.json"
            )
        )

    assert exit_code == 0
    assert stderr == ""
    assert associations["associations"][0]["documents"][0]["locations"] == [
        {
            "access": "manage",
            "url": (
                f"/docs/?scope=studio&doc={report_doc_id}&subdoc={work_doc_id}"
            ),
        }
    ]

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
---
# Tags

:::report
id: docs_subscope
access: local
sub_scope: tags
:::
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
tag_id: absence
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
tag_id: absence
---
# Related

Related body.
""",
        )
        write_json(root / "docs-viewer/scopes/studio/generated/documents/sub-scopes/tags/by-id/stale.json", {"doc_id": "stale"})

        exit_code, stdout, stderr = run_cli(root, ["--scope", "studio", "--sub-scope", "tags", "--write", "--diagnostics"])
        manifest = read_json(root / "docs-viewer/scopes/studio/generated/documents/sub-scopes/tags/manifest.json")
        manage_manifest = read_json(
            root
            / "docs-viewer/scopes/studio/generated/documents/sub-scopes/tags/manage-manifest.json"
        )
        detail = read_json(root / f"docs-viewer/scopes/studio/generated/documents/sub-scopes/tags/by-id/{DETAIL_DOC_ID}.json")
        related = read_json(root / f"docs-viewer/scopes/studio/generated/documents/sub-scopes/tags/by-id/{RELATED_DOC_ID}.json")
        tag_associations = read_json(
            root
            / "docs-viewer/scopes/studio/generated/documents/sub-scopes/tags/tag-associations.json"
        )
        related_source_path = (
            root
            / f"docs-viewer/scopes/studio/source/sub-scopes/tags/documents/{RELATED_DOC_ID}.md"
        )
        related_source_path.write_text(
            related_source_path.read_text(encoding="utf-8").replace(
                "tag_id: absence",
                "tag_id: presence",
            ),
            encoding="utf-8",
        )
        reassigned_exit_code, _reassigned_stdout, reassigned_stderr = run_cli(
            root,
            ["--scope", "studio", "--sub-scope", "tags", "--write"],
        )
        reassigned_associations = read_json(
            root
            / "docs-viewer/scopes/studio/generated/documents/sub-scopes/tags/tag-associations.json"
        )
        related_source_path.unlink()
        deleted_exit_code, _deleted_stdout, deleted_stderr = run_cli(
            root,
            ["--scope", "studio", "--sub-scope", "tags", "--write"],
        )
        deleted_associations = read_json(
            root
            / "docs-viewer/scopes/studio/generated/documents/sub-scopes/tags/tag-associations.json"
        )

    assert exit_code == 0
    assert stderr == ""
    assert reassigned_exit_code == 0
    assert reassigned_stderr == ""
    assert deleted_exit_code == 0
    assert deleted_stderr == ""
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
                "last_updated": "2026-06-21",
                "customisation": {"group": "subject", "tag_id": "absence"},
            },
            {
                "doc_id": RELATED_DOC_ID,
                "title": "Related",
                "ui_status": "",
                "last_updated": "2026-06-23",
                "customisation": {"tag_id": "absence"},
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
    assert tag_associations["schema_version"] == "docs_tag_associations_v1"
    assert tag_associations["scope"] == "studio"
    assert tag_associations["sub_scope"] == "tags"
    assert [
        document["target"]["doc_id"]
        for document in tag_associations["associations"][0]["documents"]
    ] == sorted([DETAIL_DOC_ID, RELATED_DOC_ID])
    assert tag_associations["associations"][0]["tag_id"] == "absence"
    assert all(
        [location["access"] for location in document["locations"]] == ["manage"]
        for document in tag_associations["associations"][0]["documents"]
    )
    assert {
        document["target"]["doc_id"]: document["locations"][0]["url"]
        for document in tag_associations["associations"][0]["documents"]
    } == {
        DETAIL_DOC_ID: (
            f"/docs/?scope=studio&doc={TAGS_REPORT_DOC_ID}"
            f"&subdoc={DETAIL_DOC_ID}"
        ),
        RELATED_DOC_ID: (
            f"/docs/?scope=studio&doc={TAGS_REPORT_DOC_ID}"
            f"&subdoc={RELATED_DOC_ID}"
        ),
    }
    assert [
        (
            association["tag_id"],
            [document["target"]["doc_id"] for document in association["documents"]],
        )
        for association in reassigned_associations["associations"]
    ] == [
        ("absence", [DETAIL_DOC_ID]),
        ("presence", [RELATED_DOC_ID]),
    ]
    assert [
        (
            association["tag_id"],
            [document["target"]["doc_id"] for document in association["documents"]],
        )
        for association in deleted_associations["associations"]
    ] == [("absence", [DETAIL_DOC_ID])]
    assert not (root / "docs-viewer/scopes/studio/generated/documents/sub-scopes/tags/by-id/stale.json").exists()
    assert not (root / "docs-viewer/scopes/studio/generated/documents/sub-scopes/tags/index-tree.json").exists()
    assert not (root / "docs-viewer/scopes/studio/generated/documents/sub-scopes/tags/recent.json").exists()


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
            / "docs-viewer/scopes/studio/generated/documents/sub-scopes/tags/manifest.json"
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


def test_python_docs_builder_keeps_non_publishable_docs_out_of_public_manifest() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        write_route_config(root, public_scope="studio", public_basis="edited")
        config_path = root / "docs-viewer/config/scopes/docs_scopes.json"
        payload = read_json(config_path)
        payload["scopes"][0] = docs_scope_record(
            "studio",
            scope_type="public",
            viewer_base_url="/studio/",
            include_scope_param=False,
            default_doc_id=PARENT_DOC_ID,
            sub_scopes=[
                docs_sub_scope_record(
                    "studio",
                    "tags",
                    scope_type="public",
                )
            ],
        )
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
publishable: false
---
# Hidden
""",
        )

        exit_code, _stdout, stderr = run_cli(
            root,
            ["--scope", "studio", "--sub-scope", "tags", "--write"],
        )
        manifest = read_json(
            root / "docs-viewer/scopes/studio/generated/documents/sub-scopes/tags/manifest.json"
        )
        manage_manifest = read_json(
            root
            / "docs-viewer/scopes/studio/generated/documents/sub-scopes/tags/manage-manifest.json"
        )
        visible_payload = read_json(
            root
            / f"docs-viewer/scopes/studio/generated/documents/sub-scopes/tags/by-id/{DETAIL_DOC_ID}.json"
        )
        hidden_payload_path = (
            root
            / f"docs-viewer/scopes/studio/generated/documents/sub-scopes/tags/by-id/{HIDDEN_DOC_ID}.json"
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
                "last_updated": "",
            },
            {
                "doc_id": HIDDEN_DOC_ID,
                "title": "Hidden",
                "ui_status": "",
                "publishable": False,
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
                sub_scope_customisation={
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
---
# Tags

:::report
id: docs_subscope
access: local
sub_scope: tags
:::
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
            root / "docs-viewer/scopes/studio/generated/documents/sub-scopes/tags/manifest.json"
        )
        manage_manifest = read_json(
            root
            / "docs-viewer/scopes/studio/generated/documents/sub-scopes/tags/manage-manifest.json"
        )
        detail = read_json(
            root
            / f"docs-viewer/scopes/studio/generated/documents/sub-scopes/tags/by-id/{DETAIL_DOC_ID}.json"
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
                "last_updated": "2026-06-21",
                "customisation": {"group": "subject"},
            }
        ],
    }
    assert detail["viewer_url"] == (
        f"/docs/?scope=studio&doc={TAGS_REPORT_DOC_ID}&subdoc={DETAIL_DOC_ID}"
    )
    assert browser_config["scopes"][0]["sub_scopes"][0]["sub_scope_customisation"] == {
        "id": "analysis_tags",
        "capabilities": {
            "assignable_field_groups": ["tag_fields"],
        },
    }
    assert "sub_scope_customisation" not in public_browser_config["scopes"][0]["sub_scopes"][0]


def test_browser_config_projects_assignable_group_for_exact_configured_collection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def normalize_settings(raw: object, field: str) -> dict[str, object]:
        if raw != {}:
            raise ValueError(f"{field} must be empty")
        return {}

    def project_manifest(
        settings: object,
        documents: object,
        repo_root: Path,
        scope: str,
        sub_scope: str,
    ) -> dict[str, object]:
        assert settings == {}
        assert documents == ()
        assert repo_root
        assert scope == "studio"
        assert sub_scope == "project-notes"
        return {
            "root": {"id": "synthetic_fields", "data": {}},
            "rows": {},
        }

    monkeypatch.setitem(
        customisations.SUB_SCOPE_CUSTOMISATION_DEFINITIONS,
        "synthetic_fields",
        customisations.DocsSubScopeCustomisationDefinition(
            customisation_id="synthetic_fields",
            normalize_settings=normalize_settings,
            manifest_projection=customisations.DocsSubScopeManifestProjectionAspect(
                project=project_manifest,
            ),
            browser_composition=customisations.DocsSubScopeBrowserCompositionAspect(
                accesses=frozenset({"manage"}),
            ),
            assignable_field_groups=(
                customisations.DocsSubScopeAssignableFieldGroup(
                    group_id="authoring_subject",
                    field_names=("folder_path",),
                ),
            ),
        ),
    )
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        config_path = root / "docs-viewer/config/scopes/docs_scopes.json"
        payload = read_json(config_path)
        payload["scopes"][0]["sub_scopes"] = [
            docs_sub_scope_record(
                "studio",
                "project-notes",
                title="Project notes",
                sub_scope_customisation={
                    "id": "synthetic_fields",
                    "settings": {},
                },
            ),
            docs_sub_scope_record("studio", "default", title="Default"),
        ]
        write_json(config_path, payload)
        config = load_docs_scope_configs(root)["studio"]
        manage = build_docs.browser_scope_config_payload(root, [config])
        public = build_docs.browser_scope_config_payload(
            root,
            [config],
            published=True,
        )

    manage_records = manage["scopes"][0]["sub_scopes"]
    public_records = public["scopes"][0]["sub_scopes"]
    assert manage_records[0]["sub_scope_customisation"] == {
        "id": "synthetic_fields",
        "capabilities": {
            "assignable_field_groups": ["authoring_subject"],
        },
    }
    assert "sub_scope_customisation" not in manage_records[1]
    assert all("sub_scope_customisation" not in record for record in public_records)


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
                "example",
                "tags",
                title="Tags",
                public_title="Concepts",
                scope_type="public",
            )
        ]
        write_json(config_path, payload)
        write_text(
            root / f"docs-viewer/scopes/example/source/sub-scopes/tags/documents/{DETAIL_DOC_ID}.md",
            f"""---
doc_id: {DETAIL_DOC_ID}
title: Detail
added_date: 2026-06-20
last_updated: 2026-06-21
work_id: "00123"
---
# Detail
""",
        )

        exit_code, _stdout, stderr = run_cli(root, ["--scope", "example", "--sub-scope", "tags", "--write"])
        detail = read_json(root / f"docs-viewer/scopes/example/generated/documents/sub-scopes/tags/by-id/{DETAIL_DOC_ID}.json")
        output_root = root / "docs-viewer/scopes/example/generated/documents/sub-scopes/tags"
        manifest = read_json(output_root / "manifest.json")
        manage_manifest = read_json(output_root / "manage-manifest.json")
        output_names = sorted(path.name for path in output_root.iterdir())
        config = load_docs_scope_configs(root)["example"]
        browser_config = build_docs.browser_scope_config_payload(root, [config])
        public_browser_config = build_docs.browser_scope_config_payload(
            root,
            [config],
            published=True,
        )

    assert exit_code == 0
    assert stderr == ""
    assert detail["doc_id"] == DETAIL_DOC_ID
    assert manifest == {"docs": [{"doc_id": DETAIL_DOC_ID, "title": "Detail"}]}
    assert manage_manifest == {
        "docs": [
            {
                "doc_id": DETAIL_DOC_ID,
                "title": "Detail",
                "ui_status": "",
                "last_updated": "2026-06-21",
            }
        ]
    }
    assert output_names == ["by-id", "manage-manifest.json", "manifest.json"]
    assert browser_config["scopes"][0]["sub_scopes"] == [
        {
            "sub_scope": "tags",
            "title": "Tags",
            "manifest_url": "/docs-viewer/scopes/example/generated/documents/sub-scopes/tags/manage-manifest.json",
            "by_id_url_base": "/docs-viewer/scopes/example/generated/documents/sub-scopes/tags/by-id",
        }
    ]
    assert public_browser_config["scopes"][0]["sub_scopes"] == [
        {
            "sub_scope": "tags",
            "title": "Concepts",
            "manifest_url": "/assets/data/docs/scopes/example/tags/manifest.json",
            "by_id_url_base": "/assets/data/docs/scopes/example/tags/by-id",
        }
    ]


def test_public_authoring_subject_collection_emits_deployment_metadata() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        write_site_tools_config(root, media_base="")
        write_public_scope_config(root)
        write_public_source_docs(root)
        config_path = root / "docs-viewer/config/scopes/docs_scopes.json"
        payload = read_json(config_path)
        payload["scopes"][0]["sub_scopes"] = [
            docs_sub_scope_record(
                "example",
                "works",
                title="Works",
                scope_type="public",
                sub_scope_customisation={"id": "analysis_works", "settings": {}},
            )
        ]
        payload["scopes"].append(
            docs_scope_record(
                "dotlineform",
                sub_scopes=[
                    docs_sub_scope_record(
                        "dotlineform",
                        "projects",
                        sub_scope_customisation={
                            "id": "dotlineform_projects",
                            "settings": {},
                        },
                    ),
                    docs_sub_scope_record(
                        "dotlineform",
                        "processing",
                        sub_scope_customisation={
                            "id": "dotlineform_processing",
                            "settings": {},
                        },
                    ),
                ],
            )
        )
        write_json(config_path, payload)
        write_text(
            root
            / f"docs-viewer/scopes/example/source/sub-scopes/works/documents/{DETAIL_DOC_ID}.md",
            f"""---
doc_id: {DETAIL_DOC_ID}
title: Work note
work_id: "00123"
---
# Work note
""",
        )

        exit_code, _stdout, stderr = run_cli(
            root,
            ["--scope", "example", "--sub-scope", "works", "--write"],
        )
        associations = read_json(
            root
            / "docs-viewer/scopes/example/generated/documents/sub-scopes/works/subject-associations.json"
        )

    assert exit_code == 0
    assert stderr == ""
    assert associations["scope"] == "example"
    assert associations["sub_scope"] == "works"
    assert associations["associations"][0]["subject"] == {
        "kind": "work",
        "key": "00123",
    }
    assert associations["associations"][0]["documents"][0]["target"] == {
        "scope": "example",
        "sub_scope": "works",
        "doc_id": DETAIL_DOC_ID,
    }
