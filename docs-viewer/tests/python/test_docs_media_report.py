#!/usr/bin/env python3
"""Focused contract checks for exact Docs Media report rows."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
for _path in (
    REPO_ROOT / "docs-viewer/services",
    REPO_ROOT / "docs-viewer/tests/fixtures",
):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))


from docs_media_report import REPORT_SCHEMA_VERSION, build_docs_media_report  # noqa: E402
from docs_scope_config import document_source_path, load_docs_scope_configs, load_docs_scope_stage, resolve_scope_path  # noqa: E402
from docs_source_model import format_source  # noqa: E402
from repo_factory import (  # noqa: E402
    docs_scope_record,
    docs_sub_scope_record,
    write_docs_scope_config,
    write_site_tools_config,
)


PARENT_DOC_ID = "d-20260101-000000-000001"
OTHER_DOC_ID = "d-20260101-000000-000002"
REPORT_HOST_ID = "d-20260101-000000-000003"
SUBDOC_ID = "d-20260101-000000-000004"


@pytest.fixture(autouse=True)
def isolated_media_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    projects_base = tmp_path / "projects"
    (projects_base / "docs-viewer").mkdir(parents=True)
    monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(projects_base))
    monkeypatch.setenv("DOTLINEFORM_DOCS_BASE_DIR", str(projects_base / "docs-viewer"))


def _write_document(
    root: Path,
    doc_id: str,
    title: str,
    body: str,
    *,
    sub_scope: str = "",
    scope: str = "example",
    stage: str | None = None,
) -> None:
    config = load_docs_scope_stage(root, scope, stage)
    owner = next(item for item in config.sub_scopes if item.sub_scope == sub_scope) if sub_scope else config
    collection = resolve_scope_path(root, document_source_path(owner))
    collection.mkdir(parents=True, exist_ok=True)
    (collection / f"{doc_id}.md").write_text(
        format_source(
            {
                "doc_id": doc_id,
                "title": title,
                "parent_id": "",
            },
            body,
        ),
        encoding="utf-8",
    )


def _build_fixture(root: Path) -> None:
    write_site_tools_config(root)
    record = docs_scope_record(
        "example",
        scope_root_provider="external_local",
        default_doc_id=PARENT_DOC_ID,
        sub_scopes=[docs_sub_scope_record("example", "tags", title="Tags")],
    )
    record["media"]["build_sources"] = {  # type: ignore[index]
        "mermaid": {
            "producer": "mermaid",
            "publishes_to": "svg",
        }
    }
    record["media"]["types"]["svg"]["build_inputs"] = ["mermaid"]  # type: ignore[index]
    write_docs_scope_config(root, [record])

    used = "[[media:docs/example/img/nested/used.png]]"
    _write_document(
        root,
        PARENT_DOC_ID,
        "Repeated title",
        f"# Repeated title\n\n{used}\n\nRepeated: {used}\n",
    )
    _write_document(
        root,
        OTHER_DOC_ID,
        "Other document",
        (
            "# Other document\n\n"
            "[[media:docs/example/svg/diagram.svg]]\n\n"
            "[[media:docs/example/files/missing.pdf]]\n"
        ),
    )
    _write_document(
        root,
        REPORT_HOST_ID,
        "Tags",
        (
            "# Tags\n\n"
            ":::report\n"
            "id: docs_subscope\n"
            "access: local\n"
            "sub_scope: tags\n"
            ":::\n"
        ),
    )
    _write_document(
        root,
        SUBDOC_ID,
        "Repeated title",
        f"# Repeated title\n\n{used}\n",
        sub_scope="tags",
    )

    media_root = load_docs_scope_configs(root)["example"].media.types["img"].source_location.path.parent
    files = {
        "img/nested/used.png": b"used",
        "img/unreferenced.png": b"unreferenced",
        "svg/diagram.svg": b"<svg></svg>",
        "build-source/mermaid/diagram.mmd": b"graph TD; A-->B",
    }
    for relative, content in files.items():
        path = media_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def test_report_rows_join_exact_parent_and_sub_scope_documents(tmp_path: Path) -> None:
    _build_fixture(tmp_path)

    report = build_docs_media_report(
        tmp_path,
        load_docs_scope_configs(tmp_path)["example"],
    )

    assert report["schema_version"] == REPORT_SCHEMA_VERSION
    assert report["scope"] == "example"
    assert [
        (row["media_type"], row["identity"])
        for row in report["rows"]
    ] == [
        ("img", "nested/used.png"),
        ("img", "unreferenced.png"),
        ("mermaid", "diagram.mmd"),
        ("svg", "diagram.svg"),
    ]

    rows = {
        (row["media_type"], row["identity"]): row
        for row in report["rows"]
    }
    used = rows[("img", "nested/used.png")]
    assert used["local_target"] == "docs-viewer/scopes/example/source/media/img/nested/used.png"
    assert used["documents"] == [
        {
            "target": {
                "scope": "example",
                "sub_scope": "",
                "doc_id": PARENT_DOC_ID,
            },
            "title": "Repeated title",
            "href": f"/docs/?scope=example&doc={PARENT_DOC_ID}",
        },
        {
            "target": {
                "scope": "example",
                "sub_scope": "tags",
                "doc_id": SUBDOC_ID,
            },
            "title": "Repeated title",
            "href": (
                f"/docs/?scope=example&doc={REPORT_HOST_ID}"
                f"&subdoc={SUBDOC_ID}"
            ),
        },
    ]
    assert rows[("img", "unreferenced.png")]["documents"] == []
    assert rows[("mermaid", "diagram.mmd")] == {
        "scope": "example",
        "media_type": "mermaid",
        "identity": "diagram.mmd",
        "local_target": "docs-viewer/scopes/example/source/media/build-source/mermaid/diagram.mmd",
        "documents": [],
    }
    assert rows[("svg", "diagram.svg")]["documents"][0]["target"]["doc_id"] == OTHER_DOC_ID


@pytest.mark.parametrize("stage", ["working", "pre-publish"])
def test_report_isolates_stage_media_and_document_targets(tmp_path: Path, stage: str) -> None:
    analysis = docs_scope_record(
        "analysis", scope_type="public", viewer_base_url="/analysis/", include_scope_param=False,
        scope_root_provider="external_local",
    )
    analysis["media"]["build_sources"] = {"mermaid": {"producer": "mermaid", "publishes_to": "svg"}}
    analysis["media"]["types"]["svg"]["build_inputs"] = ["mermaid"]
    analysis["stages"] = {
        name: {
            "media": analysis["media"],
            "sub_scopes": [docs_sub_scope_record(
                "analysis", "works", scope_type="public" if name == "pre-publish" else "local"
            )],
        }
        for name in ("working", "pre-publish")
    }
    write_docs_scope_config(tmp_path, [analysis])
    for name in ("working", "pre-publish"):
        _write_document(tmp_path, PARENT_DOC_ID, name, "[[media:docs/analysis/img/same.png]]", scope="analysis", stage=name)
        _write_document(tmp_path, REPORT_HOST_ID, "Works", ":::report\nid: docs_subscope\naccess: local\nsub_scope: works\n:::\n", scope="analysis", stage=name)
        _write_document(tmp_path, SUBDOC_ID, name, "[[media:docs/analysis/img/same.png]]", scope="analysis", stage=name, sub_scope="works")
        config = load_docs_scope_stage(tmp_path, "analysis", name)
        for location, identity in (
            (config.media.types["img"].source_location, "same.png"),
            (config.media.build_sources["mermaid"].location, "diagram.mmd"),
        ):
            location.path.mkdir(parents=True, exist_ok=True)
            (location.path / identity).write_text(name, encoding="utf-8")
        (config.media.types["img"].source_location.path / f"{name}.png").write_bytes(b"unique")

    report = build_docs_media_report(tmp_path, load_docs_scope_stage(tmp_path, "analysis", stage))

    assert report["stage"] == stage
    assert {row["identity"] for row in report["rows"]} == {"same.png", "diagram.mmd", f"{stage}.png"}
    for row in report["rows"]:
        expected_role = "build-source/mermaid" if row["media_type"] == "mermaid" else "img"
        assert row["local_target"] == f"docs-viewer/scopes/analysis/{stage}/source/media/{expected_role}/{row['identity']}"
        for document in row["documents"]:
            assert document["target"]["stage"] == stage
            assert document["title"] == stage
            assert f"scope=analysis&stage={stage}&" in document["href"]
    used = next(row for row in report["rows"] if row["identity"] == "same.png")
    assert {document["target"]["doc_id"] for document in used["documents"]} == {PARENT_DOC_ID, SUBDOC_ID}


def test_report_omits_missing_references_and_private_inventory_fields(tmp_path: Path) -> None:
    _build_fixture(tmp_path)

    report = build_docs_media_report(
        tmp_path,
        load_docs_scope_configs(tmp_path)["example"],
    )
    serialized = json.dumps(report, sort_keys=True)

    assert "missing.pdf" not in serialized
    assert str(tmp_path / "projects") not in serialized
    for excluded in (
        '"provider"',
        '"size"',
        '"etag"',
        '"served_path"',
        '"producer"',
        '"publishes_to"',
        '"missing_references"',
        '"source_path"',
        '"source_root"',
    ):
        assert excluded not in serialized
