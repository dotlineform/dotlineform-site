#!/usr/bin/env python3
"""Focused managed-document target and sub-scope inventory contracts."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

from repo_factory import (
    docs_scope_record,
    docs_sub_scope_record,
    write_docs_scope_config,
    write_site_tools_config,
    write_text,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))

import docs_management_document_target as target_service  # noqa: E402
import docs_management_routes as routes  # noqa: E402
import docs_management_service as management_service  # noqa: E402
import docs_management_source_service as source_service  # noqa: E402


def write_source_doc(
    scope_root: Path,
    doc_id: str,
    *,
    source_doc_id: str | None = None,
    title: str = "",
    ui_status: str = "",
    group: str = "",
    viewable: bool = True,
    sub_scope: str = "",
) -> Path:
    documents_root = (
        scope_root / "source/sub-scopes" / sub_scope / "documents"
        if sub_scope
        else scope_root / "source/documents"
    )
    front_matter = [
        "---",
        f"doc_id: {source_doc_id if source_doc_id is not None else doc_id}",
        f"title: {title or doc_id.title()}",
    ]
    if ui_status:
        front_matter.append(f"ui_status: {ui_status}")
    if group:
        front_matter.append(f"group: {group}")
    if not viewable:
        front_matter.append("viewable: false")
    front_matter.extend(["---", "", f"# {title or doc_id.title()}", "", "Body.", ""])
    path = documents_root / f"{doc_id}.md"
    write_text(path, "\n".join(front_matter))
    return path


def prepare_repo(
    repo_root: Path,
    *,
    scope_type: str = "local",
    projects_base: Path | None = None,
) -> Path:
    write_site_tools_config(repo_root)
    write_docs_scope_config(
        repo_root,
        [
            docs_scope_record(
                "analysis",
                scope_type=scope_type,
                sub_scopes=[
                    docs_sub_scope_record(
                        "analysis",
                        "tags",
                        title="Tags",
                        document_groups=["subject", "domain", "form", "theme"],
                    )
                ],
            )
        ],
    )
    if scope_type == "local_external":
        if projects_base is None:
            raise AssertionError("projects_base is required for an external-local fixture")
        scope_root = projects_base / "docs-viewer/scopes/analysis"
    else:
        scope_root = repo_root / "docs-viewer/scopes/analysis"
    write_source_doc(scope_root, "parent-report", title="Parent Report")
    write_source_doc(
        scope_root,
        "detail-doc",
        title="Detail",
        ui_status="draft",
        sub_scope="tags",
    )
    write_source_doc(
        scope_root,
        "hidden-doc",
        title="Hidden",
        viewable=False,
        sub_scope="tags",
    )
    return scope_root


def test_resolver_accepts_only_exact_parent_and_sub_scope_targets(tmp_path: Path) -> None:
    scope_root = prepare_repo(tmp_path)
    (scope_root / "source/documents/parent-report.md").rename(
        scope_root / "source/documents/parent-source.md"
    )

    parent = target_service.resolve_managed_document_target(
        tmp_path,
        {"scope": " ANALYSIS ", "doc_id": "parent-report"},
    )
    detail = target_service.resolve_managed_document_target(
        tmp_path,
        {"scope": "analysis", "sub_scope": "TAGS", "doc_id": "detail-doc"},
    )

    assert parent.request_target() == {"scope": "analysis", "doc_id": "parent-report"}
    assert parent.document.path == (scope_root / "source/documents/parent-source.md").resolve()
    assert detail.request_target() == {
        "scope": "analysis",
        "sub_scope": "tags",
        "doc_id": "detail-doc",
    }
    assert detail.document.path == (
        scope_root / "source/sub-scopes/tags/documents/detail-doc.md"
    ).resolve()
    assert detail.parent_config.scope_id == "analysis"
    assert detail.document_config.sub_scope == "tags"

    with pytest.raises(ValueError, match="contain exactly"):
        target_service.resolve_managed_document_target(
            tmp_path,
            {"scope": "analysis", "doc_id": "detail-doc", "displayed_doc": "fallback"},
        )


@pytest.mark.parametrize(
    ("target", "message"),
    [
        ({"scope": "", "doc_id": "parent-report"}, "scope is required"),
        ({"scope": "analysis", "doc_id": ""}, "doc_id is required"),
        ({"scope": "unknown", "doc_id": "parent-report"}, "unknown Docs Viewer scope"),
        (
            {"scope": "analysis", "sub_scope": "", "doc_id": "detail-doc"},
            "sub_scope is required",
        ),
        (
            {"scope": "analysis", "sub_scope": "unknown", "doc_id": "detail-doc"},
            "unknown sub_scope",
        ),
        (
            {"scope": "analysis", "sub_scope": "tags/nested", "doc_id": "detail-doc"},
            "one configured child",
        ),
        (
            {"scope": "analysis", "sub_scope": "tags", "doc_id": "../detail-doc"},
            "direct-child",
        ),
    ],
)
def test_resolver_rejects_blank_unknown_nested_and_path_targets(
    tmp_path: Path,
    target: dict[str, str],
    message: str,
) -> None:
    prepare_repo(tmp_path)

    with pytest.raises(ValueError, match=message):
        target_service.resolve_managed_document_target(tmp_path, target)


def test_resolver_rejects_unlisted_mismatched_and_escaping_sources(tmp_path: Path) -> None:
    scope_root = prepare_repo(tmp_path)
    sub_scope_root = scope_root / "source/sub-scopes/tags/documents"

    with pytest.raises(FileNotFoundError, match="was not found"):
        target_service.resolve_managed_document_target(
            tmp_path,
            {"scope": "analysis", "sub_scope": "tags", "doc_id": "missing-doc"},
        )

    write_source_doc(
        scope_root,
        "mismatch",
        source_doc_id="different-doc",
        sub_scope="tags",
    )
    with pytest.raises(ValueError, match="does not match requested doc_id"):
        target_service.resolve_managed_document_target(
            tmp_path,
            {"scope": "analysis", "sub_scope": "tags", "doc_id": "mismatch"},
        )

    outside = tmp_path / "outside.md"
    outside.write_text("---\ndoc_id: escape\n---\n", encoding="utf-8")
    (sub_scope_root / "escape.md").symlink_to(outside)
    with pytest.raises(ValueError, match="escapes configured document root"):
        target_service.resolve_managed_document_target(
            tmp_path,
            {"scope": "analysis", "sub_scope": "tags", "doc_id": "escape"},
        )

    outside_parent = tmp_path / "outside-parent.md"
    outside_parent.write_text("---\ndoc_id: escaped-parent\n---\n", encoding="utf-8")
    (scope_root / "source/documents/escaped-parent.md").symlink_to(outside_parent)
    with pytest.raises(ValueError, match="escapes configured document root"):
        target_service.resolve_managed_document_target(
            tmp_path,
            {"scope": "analysis", "doc_id": "escaped-parent"},
        )


def test_inventory_route_includes_non_viewable_docs_without_mutating_public_payloads(
    tmp_path: Path,
) -> None:
    scope_root = prepare_repo(tmp_path)
    published_root = scope_root / "published/documents/sub-scopes/tags"
    manifest_path = published_root / "manifest.json"
    detail_path = published_root / "by-id/detail-doc.json"
    write_text(
        manifest_path,
        '{\n  "docs": [\n    {"doc_id": "detail-doc", "title": "Detail"}\n  ]\n}\n',
    )
    write_text(detail_path, '{"doc_id":"detail-doc","title":"Detail"}\n')
    before = {
        manifest_path: manifest_path.read_bytes(),
        detail_path: detail_path.read_bytes(),
    }

    payload = management_service.docs_management_get_payload(
        tmp_path,
        routes.SUB_SCOPE_DOCUMENTS_PATH,
        {"scope": ["analysis"], "sub_scope": ["tags"]},
    )

    assert payload == {
        "ok": True,
        "scope": "analysis",
        "sub_scope": "tags",
        "documents": [
            {
                "doc_id": "detail-doc",
                "title": "Detail",
                "ui_status": "draft",
                "viewable": True,
            },
            {
                "doc_id": "hidden-doc",
                "title": "Hidden",
                "ui_status": "",
                "viewable": False,
            },
        ],
    }
    assert {path: path.read_bytes() for path in before} == before


def test_metadata_route_hydrates_parent_and_sub_scope_records_from_source(
    tmp_path: Path,
) -> None:
    scope_root = prepare_repo(tmp_path)
    detail_path = (
        scope_root
        / "source/sub-scopes/tags/documents/detail-doc.md"
    )
    detail_path.write_text(
        """---
doc_id: detail-doc
title: Detail
summary: Full local summary
date: 2026-07-27
date_display: July 2026
ui_status: draft
group: theme
viewable: false
parent_id: retained-sub-scope-parent
---
# Detail
""",
        encoding="utf-8",
    )

    parent = management_service.docs_management_get_payload(
        tmp_path,
        routes.METADATA_PATH,
        {"scope": ["analysis"], "doc_id": ["parent-report"]},
    )
    detail = management_service.docs_management_get_payload(
        tmp_path,
        routes.METADATA_PATH,
        {
            "scope": ["analysis"],
            "sub_scope": ["tags"],
            "doc_id": ["detail-doc"],
        },
    )

    assert parent == {
        "ok": True,
        "scope": "analysis",
        "doc_id": "parent-report",
        "record": {
            "doc_id": "parent-report",
            "title": "Parent Report",
            "summary": "",
            "date": "",
            "date_display": "",
            "ui_status": "",
            "viewable": True,
            "parent_id": "",
        },
    }
    assert detail == {
        "ok": True,
        "scope": "analysis",
        "sub_scope": "tags",
        "doc_id": "detail-doc",
        "source_revision": target_service.source_model.source_revision(
            detail_path.read_bytes()
        ),
        "choices": {
            "ui_status": ["draft", "done"],
            "group": ["subject", "domain", "form", "theme"],
        },
        "record": {
            "doc_id": "detail-doc",
            "title": "Detail",
            "summary": "Full local summary",
            "date": "2026-07-27",
            "date_display": "July 2026",
            "ui_status": "draft",
            "viewable": False,
            "group": "theme",
        },
    }


def test_source_read_uses_exact_target_and_retires_doc_alias(tmp_path: Path) -> None:
    prepare_repo(tmp_path)

    payload = source_service.read_source_body(
        tmp_path,
        {
            "scope": ["analysis"],
            "sub_scope": ["tags"],
            "doc_id": ["detail-doc"],
        },
    )

    assert payload["scope"] == "analysis"
    assert payload["sub_scope"] == "tags"
    assert payload["doc_id"] == "detail-doc"
    assert payload["source_body"].endswith("# Detail\n\nBody.\n")

    with pytest.raises(ValueError, match="doc_id is required"):
        source_service.read_source_body(
            tmp_path,
            {"scope": ["analysis"], "doc": ["parent-report"]},
        )


def test_external_local_target_and_inventory_use_configured_workspace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = tmp_path / "repo"
    projects_base = tmp_path / "projects"
    monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(projects_base))
    scope_root = prepare_repo(
        repo_root,
        scope_type="local_external",
        projects_base=projects_base,
    )

    resolved = target_service.resolve_managed_document_target(
        repo_root,
        {"scope": "analysis", "sub_scope": "tags", "doc_id": "detail-doc"},
    )
    inventory = management_service.docs_management_get_payload(
        repo_root,
        routes.SUB_SCOPE_DOCUMENTS_PATH,
        {"scope": ["analysis"], "sub_scope": ["tags"]},
    )

    assert resolved.source_root == (
        scope_root / "source/sub-scopes/tags/documents"
    ).resolve()
    assert [record["doc_id"] for record in inventory["documents"]] == [
        "detail-doc",
        "hidden-doc",
    ]
