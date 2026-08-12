#!/usr/bin/env python3
"""Focused checks for generalized, write-free document transfer planning."""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest

from repo_factory import docs_scope_record, docs_sub_scope_record


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
if str(DOCS_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(DOCS_SERVICES_DIR))

import docs_document_transfer as transfer  # noqa: E402
import docs_media_source_evidence as media_source_evidence  # noqa: E402
import docs_source_model as source_model  # noqa: E402


def write_json(path: Path, payload: object) -> None:
    if path.name == "docs_scopes.json" and isinstance(payload, dict):
        payload = {
            **payload,
            "schema_version": "docs_scopes_v4",
            "media_workspace": {
                "location": {
                    "provider": "external_local",
                    "path": "$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/media",
                }
            },
        }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if path.name == "docs_scopes.json":
        registry_path = path.parents[1] / "reports/reports.json"
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry_path.write_text(
            (REPO_ROOT / "docs-viewer/config/reports/reports.json").read_text(
                encoding="utf-8"
            ),
            encoding="utf-8",
        )


def report_body(title: str, sub_scope: str) -> str:
    return (
        f"# {title}\n\n"
        ":::report\n"
        "id: docs_subscope\n"
        "access: local\n"
        f"sub_scope: {sub_scope}\n"
        ":::\n"
    )


def write_doc(
    documents_root: Path,
    *,
    doc_id: str,
    title: str,
    parent_id: str = "",
    body: str = "",
    extra_front_matter: dict[str, object] | None = None,
) -> None:
    documents_root.mkdir(parents=True, exist_ok=True)
    front_matter = {
        "doc_id": doc_id,
        "title": title,
        "added_date": "2026-07-01 10:00:00",
        "last_updated": "2026-07-02 11:00:00",
        "parent_id": parent_id,
    }
    front_matter.update(extra_front_matter or {})
    (documents_root / f"{doc_id}.md").write_text(
        source_model.format_source(front_matter, body or f"# {title}\n"),
        encoding="utf-8",
    )


def local_documents_root(repo_root: Path, scope: str) -> Path:
    return repo_root / "docs-viewer/scopes" / scope / "source/documents"


def media_path(repo_root: Path, scope: str, media_type: str, identity: str) -> Path:
    del repo_root
    return Path(os.environ["DOTLINEFORM_PROJECTS_BASE_DIR"]) / "docs-viewer/media" / scope / media_type / identity


def build_source_path(repo_root: Path, scope: str, build_type: str, identity: str) -> Path:
    del repo_root
    return (
        Path(os.environ["DOTLINEFORM_PROJECTS_BASE_DIR"])
        / "docs-viewer/media"
        / scope
        / "build-source"
        / build_type
        / identity
    )


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def base_scope(scope: str, **kwargs: object) -> dict[str, object]:
    return docs_scope_record(
        scope,
        viewer_base_url="/docs/",
        include_scope_param=True,
        **kwargs,
    )


def add_mermaid_build(scope: dict[str, object]) -> None:
    media = scope["media"]
    assert isinstance(media, dict)
    types = media["types"]
    assert isinstance(types, dict)
    svg = types["svg"]
    assert isinstance(svg, dict)
    media["build_sources"] = {
        "mermaid": {
            "producer": "mermaid",
            "publishes_to": "svg",
        }
    }
    svg["build_inputs"] = ["mermaid"]


@pytest.fixture(autouse=True)
def isolated_media_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    projects = tmp_path / "projects"
    (projects / "docs-viewer/media").mkdir(parents=True)
    monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(projects))


def make_repo(
    tmp_path: Path,
    *,
    source_scope: dict[str, object] | None = None,
    target_scope: dict[str, object] | None = None,
) -> Path:
    repo_root = tmp_path / "repo"
    write_json(
        repo_root / "docs-viewer/config/scopes/docs_scopes.json",
        {
            "schema_version": "docs_scopes_v4",
            "scopes": [
                source_scope or base_scope("source"),
                target_scope or base_scope("target"),
            ],
        },
    )
    source_root = local_documents_root(repo_root, "source")
    target_root = local_documents_root(repo_root, "target")
    write_doc(source_root, doc_id="root", title="Root")
    write_doc(source_root, doc_id="alpha", title="Alpha", parent_id="root")
    write_doc(source_root, doc_id="grand", title="Grand", parent_id="alpha")
    write_doc(source_root, doc_id="beta", title="Beta", parent_id="root")
    write_doc(source_root, doc_id="other", title="Other")
    target_root.mkdir(parents=True, exist_ok=True)
    return repo_root


def sub_scope_documents_root(repo_root: Path, scope: str, sub_scope: str) -> Path:
    return (
        repo_root
        / "docs-viewer/scopes"
        / scope
        / "source/sub-scopes"
        / sub_scope
        / "documents"
    )


def make_collection_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    source_sub_scopes = [
        docs_sub_scope_record(
            "source",
            "tags",
            title="Tags",
            analysis_tag_groups=["subject", "domain"],
        ),
        docs_sub_scope_record(
            "source",
            "works",
            title="Works",
            sub_scope_customisation={"id": "analysis_works", "settings": {}},
        ),
    ]
    target_sub_scopes = [
        docs_sub_scope_record(
            "target",
            "tags",
            title="Tags",
            analysis_tag_groups=["subject"],
        ),
        docs_sub_scope_record(
            "target",
            "works",
            title="Works",
            sub_scope_customisation={"id": "analysis_works", "settings": {}},
        ),
    ]
    write_json(
        repo_root / "docs-viewer/config/scopes/docs_scopes.json",
        {
            "schema_version": "docs_scopes_v4",
            "scopes": [
                base_scope("source", sub_scopes=source_sub_scopes),
                base_scope("target", sub_scopes=target_sub_scopes),
            ],
        },
    )
    source_root = local_documents_root(repo_root, "source")
    target_root = local_documents_root(repo_root, "target")
    write_doc(source_root, doc_id="parent-a", title="Parent A")
    write_doc(source_root, doc_id="parent-b", title="Parent B")
    target_root.mkdir(parents=True, exist_ok=True)
    report_ids = {
        ("source", "tags"): "d-20260701-100000-aaaaaa",
        ("source", "works"): "d-20260701-100001-bbbbbb",
        ("target", "tags"): "d-20260701-100002-cccccc",
        ("target", "works"): "d-20260701-100003-dddddd",
    }
    for (scope, sub_scope), report_id in report_ids.items():
        write_doc(
            local_documents_root(repo_root, scope),
            doc_id=report_id,
            title=f"{scope.title()} {sub_scope.title()}",
            body=report_body(f"{scope.title()} {sub_scope.title()}", sub_scope),
        )
        sub_scope_documents_root(repo_root, scope, sub_scope).mkdir(
            parents=True,
            exist_ok=True,
        )
    write_doc(
        sub_scope_documents_root(repo_root, "source", "tags"),
        doc_id="tag-a",
        title="Tag A",
        body=(
            "# Tag A\n\n"
            "[Tag B](/docs/?scope=source&doc="
            f"{report_ids[('source', 'tags')]}&subdoc=tag-b)\n\n"
            "[[media:docs/source/img/photo.png Photo]]\n"
        ),
        extra_front_matter={"group": "subject", "work_id": "00123"},
    )
    write_doc(
        sub_scope_documents_root(repo_root, "source", "tags"),
        doc_id="tag-b",
        title="Tag B",
        extra_front_matter={"group": "domain"},
    )
    write_doc(
        sub_scope_documents_root(repo_root, "source", "works"),
        doc_id="work-a",
        title="Work A",
        extra_front_matter={"folder_path": "2026/work-a"},
    )
    write_bytes(media_path(repo_root, "source", "img", "photo.png"), b"photo")
    return repo_root


def make_lineage_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    source_id = "d-20260801-100000-aaaaaa"
    target_id = "d-20260802-110000-bbbbbb"
    second_target_id = "d-20260802-120000-cccccc"
    missing_target_id = "d-20260802-130000-dddddd"
    source_sub_scope = docs_sub_scope_record(
        "dotlineform",
        "projects",
        title="Projects",
        sub_scope_customisation={"id": "dotlineform_projects", "settings": {}},
        lifecycle={
            "tool_id": "docs-viewer-scope-lifecycle",
            "report_host_doc_id": "d-20260801-090000-eeeeee",
            "report_host_source_revision": "sha256:" + "1" * 64,
        },
    )
    target_sub_scope = docs_sub_scope_record(
        "analysis",
        "works",
        title="Works",
        scope_type="public",
        sub_scope_customisation={"id": "analysis_works", "settings": {}},
        lifecycle={
            "tool_id": "docs-viewer-scope-lifecycle",
            "report_host_doc_id": "d-20260802-090000-ffffff",
            "report_host_source_revision": "sha256:" + "2" * 64,
        },
    )
    write_json(
        repo_root / "docs-viewer/config/scopes/docs_scopes.json",
        {
            "schema_version": "docs_scopes_v4",
            "scopes": [
                base_scope("dotlineform", sub_scopes=[source_sub_scope]),
                docs_scope_record(
                    "analysis",
                    scope_type="public",
                    viewer_base_url="/analysis/",
                    include_scope_param=False,
                    sub_scopes=[target_sub_scope],
                ),
            ],
        },
    )
    local_documents_root(repo_root, "dotlineform").mkdir(parents=True, exist_ok=True)
    local_documents_root(repo_root, "analysis").mkdir(parents=True, exist_ok=True)
    write_doc(
        local_documents_root(repo_root, "dotlineform"),
        doc_id="d-20260801-090000-eeeeee",
        title="Projects Report",
        body=report_body("Projects Report", "projects"),
    )
    write_doc(
        local_documents_root(repo_root, "analysis"),
        doc_id="d-20260802-090000-ffffff",
        title="Works Report",
        body=report_body("Works Report", "works"),
    )
    source_root = sub_scope_documents_root(repo_root, "dotlineform", "projects")
    target_root = sub_scope_documents_root(repo_root, "analysis", "works")
    write_doc(
        source_root,
        doc_id=source_id,
        title="Working A",
        body="# Working A\n\nCurrent working body.\n",
        extra_front_matter={"folder_path": "2026/working-a", "work_id": "00123"},
    )
    write_doc(
        source_root,
        doc_id="d-20260801-101000-999999",
        title="Working Without Editorial",
        body="# Working Without Editorial\n",
        extra_front_matter={"folder_path": "2026/working-new"},
    )
    write_doc(
        target_root,
        doc_id=target_id,
        title="Editorial B One",
        body="# Editorial B One\n\nEditorial body one.\n",
        extra_front_matter={"publishable": False},
    )
    write_doc(
        target_root,
        doc_id=second_target_id,
        title="Editorial B Two",
        body="# Editorial B Two\n\nEditorial body two.\n",
    )
    write_json(
        repo_root / "docs-viewer/data/canonical/document-publication-lineage.json",
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
                    "working_doc_id": source_id,
                    "editorials": [
                        {
                            "doc_id": editorial_id,
                            "created_at": "2026-08-07T20:00:00Z",
                            "last_copied_at": "2026-08-07T20:00:00Z",
                            "published_url": None,
                        }
                        for editorial_id in (
                            target_id,
                            second_target_id,
                            missing_target_id,
                        )
                    ],
                }
            ],
        },
    )
    return repo_root


def sequential_tokens(*values: str) -> transfer.IdentityTokenFactory:
    iterator: Iterator[str] = iter(values)
    return lambda _size: next(iterator)


def snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def blocker_codes(plan: transfer.DocumentTransferPlan) -> set[str]:
    return {blocker.code for blocker in plan.blockers}


def test_report_host_document_is_not_transferable(tmp_path: Path) -> None:
    repo_root = make_collection_repo(tmp_path)
    report_id = "d-20260701-100000-aaaaaa"

    plan = transfer.plan_document_transfer(
        repo_root,
        source_scope="source",
        requested_doc_ids=[report_id],
        target_scope="target",
        transfer_mode="copy",
        operation_timestamp="2026-07-24 09:10:11",
        token_factory=sequential_tokens("ffffff"),
    )

    assert not plan.ok
    assert blocker_codes(plan) == {"source_report_host_forbidden"}
    assert plan.blockers[0].document_ids == (report_id,)


def warning_codes(plan: transfer.DocumentTransferPlan) -> set[str]:
    return {warning.code for warning in plan.warnings}


def test_lineage_copy_requires_explicit_new_or_exact_replace_and_lists_unavailable(
    tmp_path: Path,
) -> None:
    repo_root = make_lineage_repo(tmp_path)
    source_id = "d-20260801-100000-aaaaaa"
    target_id = "d-20260802-110000-bbbbbb"
    second_target_id = "d-20260802-120000-cccccc"
    missing_target_id = "d-20260802-130000-dddddd"
    common = {
        "source_scope": "dotlineform",
        "source_sub_scope": "projects",
        "requested_doc_ids": [source_id],
        "target_scope": "analysis",
        "target_sub_scope": "works",
        "transfer_mode": "copy",
        "operation_timestamp": "2026-08-08 10:00:00",
    }

    no_existing = transfer.plan_document_transfer(
        repo_root,
        **{
            **common,
            "requested_doc_ids": ["d-20260801-101000-999999"],
        },
        token_factory=sequential_tokens("999999"),
    )
    assert no_existing.ok
    assert no_existing.lineage is not None
    assert no_existing.lineage.decisions[0].action == transfer.COPY_ACTION_NEW
    assert no_existing.lineage.decisions[0].existing_editorials == ()

    undecided = transfer.plan_document_transfer(repo_root, **common)
    assert not undecided.ok
    assert blocker_codes(undecided) == {"lineage_copy_action_required"}
    assert undecided.preview_payload()["apply_plan"] is None
    lineage_payload = undecided.preview_payload()["lineage"]
    assert lineage_payload["choice_required"] is True
    assert lineage_payload["sources"] == [
        {
            "source_doc_id": source_id,
            "title": "Working A",
            "action": "",
            "replace_target_doc_id": "",
            "existing_editorials": [
                {
                    "editorial_doc_id": target_id,
                    "title": "Editorial B One",
                    "available": True,
                },
                {
                    "editorial_doc_id": second_target_id,
                    "title": "Editorial B Two",
                    "available": True,
                },
                {
                    "editorial_doc_id": missing_target_id,
                    "title": "",
                    "available": False,
                },
            ],
        }
    ]
    with pytest.raises(ValueError, match="must not be empty"):
        transfer.plan_document_transfer(
            repo_root,
            **common,
            copy_lineage_actions=[],
        )

    new_plan = transfer.plan_document_transfer(
        repo_root,
        **common,
        copy_lineage_actions=[
            {
                "source_doc_id": source_id,
                "action": "new",
                "replace_target_doc_id": "",
            }
        ],
        token_factory=sequential_tokens("eeeeee"),
    )
    assert new_plan.ok
    assert new_plan.documents[0].copy_action == transfer.COPY_ACTION_NEW
    assert new_plan.documents[0].target_doc_id == "d-20260808-100000-eeeeee"

    replace_plan = transfer.plan_document_transfer(
        repo_root,
        **common,
        copy_lineage_actions=[
            {
                "source_doc_id": source_id,
                "action": "replace",
                "replace_target_doc_id": target_id,
            }
        ],
    )
    assert replace_plan.ok
    assert replace_plan.documents[0].target_doc_id == target_id
    assert replace_plan.documents[0].target_path.name == f"{target_id}.md"
    assert replace_plan.apply_plan_payload()["lineage"]["decisions"] == [
        {
            "source_doc_id": source_id,
            "action": "replace",
            "replace_target_doc_id": target_id,
        }
    ]

    with pytest.raises(ValueError, match="not an available Editorial child"):
        transfer.plan_document_transfer(
            repo_root,
            **common,
            copy_lineage_actions=[
                {
                    "source_doc_id": source_id,
                    "action": "replace",
                    "replace_target_doc_id": missing_target_id,
                }
            ],
        )


def test_lineage_replace_receipt_keeps_exact_target_after_target_edit(tmp_path: Path) -> None:
    repo_root = make_lineage_repo(tmp_path)
    source_id = "d-20260801-100000-aaaaaa"
    target_id = "d-20260802-110000-bbbbbb"
    plan = transfer.plan_document_transfer(
        repo_root,
        source_scope="dotlineform",
        source_sub_scope="projects",
        requested_doc_ids=[source_id],
        target_scope="analysis",
        target_sub_scope="works",
        transfer_mode="copy",
        operation_timestamp="2026-08-08 10:00:00",
        copy_lineage_actions=[
            {
                "source_doc_id": source_id,
                "action": "replace",
                "replace_target_doc_id": target_id,
            }
        ],
    )
    target_path = sub_scope_documents_root(
        repo_root,
        "analysis",
        "works",
    ) / f"{target_id}.md"
    target_path.write_text(
        target_path.read_text(encoding="utf-8") + "\nChanged after preview.\n",
        encoding="utf-8",
    )

    restored = transfer.restore_document_transfer_apply_plan(
        repo_root,
        plan.apply_plan_payload(),
    )

    assert restored.documents[0].target_doc_id == target_id
    assert restored.documents[0].replacement_doc is not None
    assert restored.documents[0].replacement_doc.source_text.endswith(
        "Changed after preview.\n"
    )


def test_copy_selection_is_deterministic_deduplicated_and_write_free(tmp_path: Path) -> None:
    repo_root = make_repo(tmp_path)
    before = snapshot(repo_root)

    exact = transfer.plan_document_transfer(
        repo_root,
        source_scope="source",
        requested_doc_ids=["beta", "alpha", "alpha"],
        target_scope="target",
        transfer_mode="copy",
        include_descendants=False,
        operation_timestamp="2026-07-24 09:10:11",
        token_factory=sequential_tokens("aaaaaa", "bbbbbb"),
    )
    repeated = transfer.plan_document_transfer(
        repo_root,
        source_scope="source",
        requested_doc_ids=["beta", "alpha", "alpha"],
        target_scope="target",
        transfer_mode="copy",
        include_descendants=False,
        operation_timestamp="2026-07-24 09:10:11",
        token_factory=sequential_tokens("aaaaaa", "bbbbbb"),
    )

    assert snapshot(repo_root) == before
    assert exact == repeated
    assert exact.ok
    assert exact.requested_doc_ids == ("alpha", "beta")
    assert [item.source_doc.doc_id for item in exact.documents] == ["alpha", "beta"]
    assert [item.target_parent_id for item in exact.documents] == ["", ""]
    assert exact.preview_payload()["requested_count"] == 2
    assert exact.preview_payload()["effective_root_count"] == 2
    assert exact.preview_payload()["descendant_count"] == 0
    assert exact.preview_payload()["apply_plan"]["schema_version"] == (
            "docs_document_transfer_apply_plan_v4"
    )
    serialized = json.dumps(exact.preview_payload()["apply_plan"])
    assert str(repo_root) not in serialized
    assert "# Alpha" not in serialized


def test_copy_optional_descendants_unions_overlapping_checked_subtrees(tmp_path: Path) -> None:
    repo_root = make_repo(tmp_path)
    plan = transfer.plan_document_transfer(
        repo_root,
        source_scope="source",
        requested_doc_ids=["alpha", "root"],
        target_scope="target",
        transfer_mode="copy",
        include_descendants=True,
        operation_timestamp="2026-07-24 09:10:11",
        token_factory=sequential_tokens("aaaaaa", "bbbbbb", "cccccc", "dddddd"),
    )

    assert plan.requested_doc_ids == ("root", "alpha")
    assert [item.source_doc.doc_id for item in plan.documents] == [
        "root",
        "alpha",
        "grand",
        "beta",
    ]
    assert plan.descendant_count == 2
    assert plan.effective_root_count == 1
    assert [item.target_parent_id for item in plan.documents] == [
        "",
        plan.documents[0].target_doc_id,
        plan.documents[1].target_doc_id,
        plan.documents[0].target_doc_id,
    ]


@pytest.mark.parametrize(
    (
        "source_sub_scope",
        "requested_doc_ids",
        "target_sub_scope",
        "expected_source",
        "expected_target",
    ),
    [
        ("", ["parent-a"], "", {"scope": "source"}, {"scope": "target"}),
        (
            "",
            ["parent-a"],
            "works",
            {"scope": "source"},
            {"scope": "target", "sub_scope": "works"},
        ),
        (
            "tags",
            ["tag-a"],
            "",
            {"scope": "source", "sub_scope": "tags"},
            {"scope": "target"},
        ),
        (
            "tags",
            ["tag-a"],
            "works",
            {"scope": "source", "sub_scope": "tags"},
            {"scope": "target", "sub_scope": "works"},
        ),
    ],
)
def test_copy_plans_all_exact_parent_and_child_collection_shapes(
    tmp_path: Path,
    source_sub_scope: str,
    requested_doc_ids: list[str],
    target_sub_scope: str,
    expected_source: dict[str, str],
    expected_target: dict[str, str],
) -> None:
    repo_root = make_collection_repo(tmp_path)

    plan = transfer.plan_document_transfer(
        repo_root,
        source_scope="source",
        source_sub_scope=source_sub_scope or None,
        requested_doc_ids=requested_doc_ids,
        target_scope="target",
        target_sub_scope=target_sub_scope or None,
        transfer_mode="copy",
        operation_timestamp="2026-07-24 09:10:11",
        token_factory=sequential_tokens("aaaaaa"),
    )

    assert plan.ok
    assert plan.source_collection.request_target() == expected_source
    assert plan.target_collection.request_target() == expected_target
    assert plan.documents[0].target_path.parent == plan.target_collection.source_root
    assert plan.preview_payload()["source"] == expected_source
    assert {
        key: value
        for key, value in plan.preview_payload()["target"].items()
        if key != "placement"
    } == expected_target


def test_child_copy_receipt_freezes_collections_metadata_links_and_owners(
    tmp_path: Path,
) -> None:
    repo_root = make_collection_repo(tmp_path)
    before = snapshot(repo_root)
    plan = transfer.plan_document_transfer(
        repo_root,
        source_scope="source",
        source_sub_scope="tags",
        requested_doc_ids=["tag-a", "tag-b"],
        target_scope="target",
        target_sub_scope="works",
        transfer_mode="copy",
        operation_timestamp="2026-07-24 09:10:11",
        token_factory=sequential_tokens("aaaaaa", "bbbbbb"),
    )

    assert plan.ok
    assert snapshot(repo_root) == before
    preview = plan.preview_payload()
    assert preview["target"] == {
        "scope": "target",
        "sub_scope": "works",
        "placement": "sub_scope_root",
    }
    assert "target_default_publishable" not in preview
    assert preview["custom_metadata"]["retained"] == []
    assert preview["custom_metadata"]["rejected"] == []
    assert {
        (item["source_doc_id"], item["field_name"], item["status"])
        for item in preview["custom_metadata"]["omitted"]
    } == {
        ("tag-a", "group", "omitted"),
        ("tag-b", "group", "omitted"),
    }
    assert {item.field_name for item in plan.custom_metadata} == {"group"}
    assert plan.link_decisions == (
        transfer.TransferLinkDecision(
            source_doc_id="tag-a",
            referenced_doc_id="tag-b",
            target_doc_id=plan.id_map["tag-b"],
            status="remap",
            occurrence_count=1,
        ),
    )
    receipt = plan.apply_plan_payload()
    assert receipt["source"] == {"scope": "source", "sub_scope": "tags"}
    assert receipt["target"] == {"scope": "target", "sub_scope": "works"}
    assert receipt["media_owners"] == {
        "source": {"scope": "source"},
        "target": {"scope": "target"},
    }
    assert len(plan.media) == 1
    assert plan.media[0].source_reference == "docs/source/img/photo.png"
    assert plan.media[0].target_reference == "docs/target/img/photo.png"
    assert plan.media[0].target_status == "create"
    assert receipt["target_rebuild_owner"] == {
        "scope": "target",
        "sub_scope": "works",
    }
    assert "target_default_publishable" not in receipt
    restored = transfer.restore_document_transfer_apply_plan(repo_root, receipt)
    assert restored == plan
    assert snapshot(repo_root) == before


def test_custom_metadata_contract_retains_omits_and_rejects_by_target_settings(
    tmp_path: Path,
) -> None:
    repo_root = make_collection_repo(tmp_path)
    retained = transfer.plan_document_transfer(
        repo_root,
        source_scope="source",
        source_sub_scope="tags",
        requested_doc_ids=["tag-a"],
        target_scope="target",
        target_sub_scope="tags",
        transfer_mode="copy",
        operation_timestamp="2026-07-24 09:10:11",
        token_factory=sequential_tokens("aaaaaa"),
    )
    omitted = transfer.plan_document_transfer(
        repo_root,
        source_scope="source",
        source_sub_scope="tags",
        requested_doc_ids=["tag-a"],
        target_scope="target",
        target_sub_scope="works",
        transfer_mode="copy",
        operation_timestamp="2026-07-24 09:10:11",
        token_factory=sequential_tokens("bbbbbb"),
    )
    rejected = transfer.plan_document_transfer(
        repo_root,
        source_scope="source",
        source_sub_scope="tags",
        requested_doc_ids=["tag-b"],
        target_scope="target",
        target_sub_scope="tags",
        transfer_mode="copy",
        operation_timestamp="2026-07-24 09:10:11",
        token_factory=sequential_tokens("cccccc"),
    )

    assert retained.ok
    assert retained.custom_metadata[0].status == "retained"
    assert omitted.ok
    assert omitted.custom_metadata[0].status == "omitted"
    assert not rejected.ok
    assert rejected.custom_metadata[0].status == "rejected"
    assert blocker_codes(rejected) == {"target_custom_metadata_rejected"}
    assert rejected.preview_payload()["apply_plan"] is None


def test_child_flatness_and_move_boundaries_are_explicit(tmp_path: Path) -> None:
    repo_root = make_collection_repo(tmp_path)
    with pytest.raises(ValueError, match="does not support descendant"):
        transfer.plan_document_transfer(
            repo_root,
            source_scope="source",
            source_sub_scope="tags",
            requested_doc_ids=["tag-a"],
            target_scope="target",
            transfer_mode="copy",
            include_descendants=True,
        )
    with pytest.raises(ValueError, match="parent-scope collections only"):
        transfer.plan_document_transfer(
            repo_root,
            source_scope="source",
            source_sub_scope="tags",
            requested_doc_ids=["tag-a"],
            target_scope="target",
            transfer_mode="move",
        )
    write_doc(
        sub_scope_documents_root(repo_root, "source", "tags"),
        doc_id="tag-child",
        title="Tag Child",
        parent_id="tag-a",
        extra_front_matter={"group": "subject"},
    )
    with pytest.raises(ValueError, match="contains a parent/child relationship"):
        transfer.plan_document_transfer(
            repo_root,
            source_scope="source",
            source_sub_scope="tags",
            requested_doc_ids=["tag-a", "tag-child"],
            target_scope="target",
            target_sub_scope="works",
            transfer_mode="copy",
        )

    write_doc(
        local_documents_root(repo_root, "source"),
        doc_id="parent-child",
        title="Parent Child",
        parent_id="parent-a",
    )
    blocked = transfer.plan_document_transfer(
        repo_root,
        source_scope="source",
        requested_doc_ids=["parent-a", "parent-child"],
        target_scope="target",
        target_sub_scope="works",
        transfer_mode="copy",
        operation_timestamp="2026-07-24 09:10:11",
        token_factory=sequential_tokens("aaaaaa", "bbbbbb"),
    )
    assert blocker_codes(blocked) == {"flat_target_hierarchy"}
    assert blocked.preview_payload()["apply_plan"] is None


def test_same_parent_different_child_copy_is_valid(tmp_path: Path) -> None:
    repo_root = make_collection_repo(tmp_path)
    plan = transfer.plan_document_transfer(
        repo_root,
        source_scope="source",
        source_sub_scope="tags",
        requested_doc_ids=["tag-a"],
        target_scope="source",
        target_sub_scope="works",
        transfer_mode="copy",
        operation_timestamp="2026-07-24 09:10:11",
        token_factory=sequential_tokens("aaaaaa"),
    )

    assert plan.ok
    assert plan.source_scope == plan.target_scope == "source"
    assert plan.source_sub_scope == "tags"
    assert plan.target_sub_scope == "works"


def test_move_forces_descendants_preserves_identity_and_reports_shared_media(
    tmp_path: Path,
) -> None:
    repo_root = make_repo(tmp_path)
    source_root = local_documents_root(repo_root, "source")
    media_reference = "[[media:docs/source/img/shared.png Shared]]\n"
    write_doc(
        source_root,
        doc_id="root",
        title="Root",
        body=f"# Root\n\n{media_reference}",
    )
    write_doc(
        source_root,
        doc_id="other",
        title="Other",
        body=f"# Other\n\n{media_reference}",
    )
    write_bytes(media_path(repo_root, "source", "img", "shared.png"), b"shared")

    plan = transfer.plan_document_transfer(
        repo_root,
        source_scope="source",
        requested_doc_ids=["root"],
        target_scope="target",
        transfer_mode="move",
        include_descendants=False,
        operation_timestamp="2026-07-24 09:10:11",
    )

    assert plan.ok
    assert plan.include_descendants is True
    assert plan.descendants_forced is True
    assert [item.source_doc.doc_id for item in plan.documents] == [
        "root",
        "alpha",
        "grand",
        "beta",
    ]
    assert [item.target_doc_id for item in plan.documents] == [
        "root",
        "alpha",
        "grand",
        "beta",
    ]
    assert plan.documents[0].source_doc.front_matter["added_date"] == "2026-07-01 10:00:00"
    assert plan.media[0].shared_outside_document_ids == ("other",)
    assert plan.media[0].target_status == "create"


def test_media_is_deduplicated_and_exact_target_bytes_are_reused(tmp_path: Path) -> None:
    repo_root = make_repo(tmp_path)
    reference = "[[media:docs/source/files/guide.pdf Guide]]\n"
    write_doc(
        local_documents_root(repo_root, "source"),
        doc_id="root",
        title="Root",
        body=f"# Root\n\n{reference}",
    )
    write_doc(
        local_documents_root(repo_root, "source"),
        doc_id="alpha",
        title="Alpha",
        parent_id="root",
        body=f"# Alpha\n\n{reference}",
    )
    write_bytes(media_path(repo_root, "source", "files", "guide.pdf"), b"same")
    write_bytes(media_path(repo_root, "target", "files", "guide.pdf"), b"same")

    plan = transfer.plan_document_transfer(
        repo_root,
        source_scope="source",
        requested_doc_ids=["root"],
        target_scope="target",
        transfer_mode="copy",
        include_descendants=True,
        operation_timestamp="2026-07-24 09:10:11",
        token_factory=sequential_tokens("aaaaaa", "bbbbbb", "cccccc", "dddddd"),
    )

    assert plan.ok
    assert len(plan.media) == 1
    assert plan.media[0].document_ids == ("alpha", "root")
    assert plan.media[0].source_reference == "docs/source/files/guide.pdf"
    assert plan.media[0].target_reference == "docs/target/files/guide.pdf"
    assert plan.media[0].target_status == "reuse"


def test_copy_plans_exact_media_source_evidence_without_inference(
    tmp_path: Path,
) -> None:
    repo_root = make_repo(tmp_path)
    write_doc(
        local_documents_root(repo_root, "source"),
        doc_id="root",
        title="Root",
        body=(
            "# Root\n\n"
            "[[media:docs/source/files/guide.pdf Guide]]\n"
            "[[media:docs/source/img/photo.png Photo]]\n"
        ),
    )
    write_bytes(media_path(repo_root, "source", "files", "guide.pdf"), b"guide")
    write_bytes(media_path(repo_root, "source", "img", "photo.png"), b"photo")
    media_source_evidence.record_media_source_evidence(
        repo_root,
        "source",
        media_type="files",
        identity="guide.pdf",
        source_root="analysis",
        source_path="analysis/guides/guide.pdf",
    )

    plan = transfer.plan_document_transfer(
        repo_root,
        source_scope="source",
        requested_doc_ids=["root"],
        target_scope="target",
        transfer_mode="copy",
        operation_timestamp="2026-07-24 09:10:11",
        token_factory=sequential_tokens("aaaaaa"),
    )
    receipt = plan.apply_plan_payload()
    planned = {
        (item.media_type, item.identity): item.source_evidence
        for item in plan.media
    }

    assert planned[("files", "guide.pdf")] == (
        transfer.TransferMediaSourceEvidencePlan(
            status="copy",
            source_root="analysis",
            source_path="analysis/guides/guide.pdf",
        )
    )
    assert planned[("img", "photo.png")] == (
        transfer.TransferMediaSourceEvidencePlan(status="unrecorded")
    )

    media_source_evidence.record_media_source_evidence(
        repo_root,
        "target",
        media_type="files",
        identity="guide.pdf",
        source_root="analysis",
        source_path="analysis/target-owned/guide.pdf",
    )
    with pytest.raises(ValueError, match="document transfer preview is stale"):
        transfer.restore_document_transfer_apply_plan(repo_root, receipt)

    retained = transfer.plan_document_transfer(
        repo_root,
        source_scope="source",
        requested_doc_ids=["root"],
        target_scope="target",
        transfer_mode="copy",
        operation_timestamp="2026-07-24 09:10:11",
        token_factory=sequential_tokens("aaaaaa"),
    )
    retained_guide = next(
        item
        for item in retained.media
        if (item.media_type, item.identity) == ("files", "guide.pdf")
    )
    assert retained_guide.source_evidence == (
        transfer.TransferMediaSourceEvidencePlan(
            status="retain",
            source_root="analysis",
            source_path="analysis/target-owned/guide.pdf",
        )
    )


@pytest.mark.parametrize(
    ("source_bytes", "target_bytes", "expected_code"),
    [
        (None, None, "source_media_unavailable"),
        (b"source", b"different", "target_media_collision"),
    ],
)
def test_missing_media_and_differing_target_bytes_block_apply(
    tmp_path: Path,
    source_bytes: bytes | None,
    target_bytes: bytes | None,
    expected_code: str,
) -> None:
    repo_root = make_repo(tmp_path)
    write_doc(
        local_documents_root(repo_root, "source"),
        doc_id="root",
        title="Root",
        body="# Root\n\n[[media:docs/source/img/photo.png Photo]]\n",
    )
    if source_bytes is not None:
        write_bytes(media_path(repo_root, "source", "img", "photo.png"), source_bytes)
    if target_bytes is not None:
        write_bytes(media_path(repo_root, "target", "img", "photo.png"), target_bytes)

    plan = transfer.plan_document_transfer(
        repo_root,
        source_scope="source",
        requested_doc_ids=["root"],
        target_scope="target",
        transfer_mode="copy",
        operation_timestamp="2026-07-24 09:10:11",
        token_factory=sequential_tokens("aaaaaa"),
    )

    assert not plan.ok
    assert expected_code in blocker_codes(plan)
    assert plan.preview_payload()["apply_plan"] is None
    with pytest.raises(ValueError, match="blocked document transfer"):
        plan.apply_plan_payload()


def test_mermaid_svg_includes_canonical_build_source_but_inline_mermaid_does_not(
    tmp_path: Path,
) -> None:
    source_scope = base_scope("source")
    target_scope = base_scope("target")
    add_mermaid_build(source_scope)
    add_mermaid_build(target_scope)
    repo_root = make_repo(
        tmp_path,
        source_scope=source_scope,
        target_scope=target_scope,
    )
    write_doc(
        local_documents_root(repo_root, "source"),
        doc_id="root",
        title="Root",
        body=(
            "# Root\n\n"
            "[[media:docs/source/svg/diagram.svg Diagram]]\n\n"
            "```mermaid\nflowchart LR\n  A --> B\n```\n"
        ),
    )
    write_bytes(media_path(repo_root, "source", "svg", "diagram.svg"), b"<svg/>")
    write_bytes(
        build_source_path(repo_root, "source", "mermaid", "diagram.mmd"),
        b"flowchart LR\n  A --> B\n",
    )
    before = snapshot(repo_root)

    plan = transfer.plan_document_transfer(
        repo_root,
        source_scope="source",
        requested_doc_ids=["root"],
        target_scope="target",
        transfer_mode="copy",
        operation_timestamp="2026-07-24 09:10:11",
        token_factory=sequential_tokens("aaaaaa"),
    )

    assert snapshot(repo_root) == before
    assert plan.ok
    assert len(plan.media) == 1
    assert plan.media[0].identity == "diagram.svg"
    assert len(plan.media[0].build_sources) == 1
    build = plan.media[0].build_sources[0]
    assert build.source_identity == "diagram.mmd"
    assert build.producer == "mermaid"
    assert build.target_status == "create"
    assert plan.media[0].target_status == "produce"
    assert "```mermaid" in plan.documents[0].source_doc.source_text


def test_unsupported_target_role_and_build_are_blockers(tmp_path: Path) -> None:
    source_scope = base_scope("source")
    add_mermaid_build(source_scope)
    target_scope = base_scope("target", media_types=("img", "files"))
    repo_root = make_repo(
        tmp_path,
        source_scope=source_scope,
        target_scope=target_scope,
    )
    write_doc(
        local_documents_root(repo_root, "source"),
        doc_id="root",
        title="Root",
        body="# Root\n\n[[media:docs/source/svg/diagram.svg Diagram]]\n",
    )
    write_bytes(media_path(repo_root, "source", "svg", "diagram.svg"), b"<svg/>")
    write_bytes(
        build_source_path(repo_root, "source", "mermaid", "diagram.mmd"),
        b"flowchart LR\n  A --> B\n",
    )

    plan = transfer.plan_document_transfer(
        repo_root,
        source_scope="source",
        requested_doc_ids=["root"],
        target_scope="target",
        transfer_mode="copy",
        operation_timestamp="2026-07-24 09:10:11",
        token_factory=sequential_tokens("aaaaaa"),
    )

    assert {
        "unsupported_target_media_role",
        "unsupported_target_media_build",
    }.issubset(blocker_codes(plan))


def test_external_and_other_scope_media_are_retained_dependencies(tmp_path: Path) -> None:
    repo_root = make_repo(tmp_path)
    write_doc(
        local_documents_root(repo_root, "source"),
        doc_id="root",
        title="Root",
        body=(
            "# Root\n\n"
            "[[media:docs/archive/img/old.png Old]]\n\n"
            "![Hosted](https://cdn.example.test/hosted.png)\n"
        ),
    )

    plan = transfer.plan_document_transfer(
        repo_root,
        source_scope="source",
        requested_doc_ids=["root"],
        target_scope="target",
        transfer_mode="copy",
        operation_timestamp="2026-07-24 09:10:11",
        token_factory=sequential_tokens("aaaaaa"),
    )

    assert plan.ok
    assert {
        (item.kind, item.reference)
        for item in plan.retained_external_dependencies
    } == {
        ("external_url", "https://cdn.example.test/hosted.png"),
        ("other_scope_media", "docs/archive/img/old.png"),
    }


def test_move_document_collision_blocks_apply(
    tmp_path: Path,
) -> None:
    repo_root = make_repo(tmp_path)
    write_doc(
        local_documents_root(repo_root, "target"),
        doc_id="root",
        title="Existing root",
    )

    plan = transfer.plan_document_transfer(
        repo_root,
        source_scope="source",
        requested_doc_ids=["root"],
        target_scope="target",
        transfer_mode="move",
        operation_timestamp="2026-07-24 09:10:11",
    )

    assert blocker_codes(plan) == {"target_document_collision"}
    assert plan.preview_payload()["apply_plan"] is None


def test_move_inbound_viewer_link_warns_with_titles_without_blocking(
    tmp_path: Path,
) -> None:
    repo_root = make_repo(tmp_path)
    write_doc(
        local_documents_root(repo_root, "source"),
        doc_id="other",
        title="Outside Document",
        body="# Other\n\n[Root](/docs/?scope=source&doc=root)\n",
    )

    plan = transfer.plan_document_transfer(
        repo_root,
        source_scope="source",
        requested_doc_ids=["root"],
        target_scope="target",
        transfer_mode="move",
        operation_timestamp="2026-07-24 09:10:11",
    )

    assert plan.ok
    assert blocker_codes(plan) == set()
    assert warning_codes(plan) == {"inbound_viewer_link"}
    assert plan.warnings[0].message == (
        "“Outside Document” links to “Root”. That link will remain pointed at "
        "the “source” scope after the move; change it to “target” if it should "
        "follow the document."
    )
    preview = plan.preview_payload()
    assert preview["warnings"] == [
        {
            "code": "inbound_viewer_link",
            "message": plan.warnings[0].message,
            "document_ids": ("other", "root"),
        }
    ]
    assert preview["apply_plan"] is not None


@dataclass(frozen=True)
class RemoteStat:
    key: str
    size: int
    etag: str = ""


class FakeR2Client:
    def __init__(self, objects: dict[str, bytes]) -> None:
        self.objects = dict(objects)

    def list_objects(self, prefix: str) -> list[RemoteStat]:
        return [
            RemoteStat(key=key, size=len(value))
            for key, value in sorted(self.objects.items())
            if key.startswith(prefix)
        ]

    def get_object(self, key: str) -> bytes:
        return self.objects[key]

    def head_object(self, key: str) -> RemoteStat | None:
        value = self.objects.get(key)
        return None if value is None else RemoteStat(key=key, size=len(value))

    def put_object(self, key: str, path: Path, content_type: str) -> None:
        del content_type
        self.objects[key] = path.read_bytes()

    def delete_object(self, key: str) -> None:
        del self.objects[key]


def test_public_scope_managed_source_to_external_local_target_is_provider_neutral(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    projects_base = tmp_path / "Projects"
    (projects_base / "docs-viewer/media").mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(projects_base))
    source_scope = docs_scope_record(
        "source",
        scope_type="public",
        viewer_base_url="/source/",
        include_scope_param=False,
        media_types=("img",),
    )
    target_scope = docs_scope_record(
        "target",
        scope_type="local_external",
        viewer_base_url="/docs/",
        include_scope_param=True,
        media_types=("img",),
    )
    repo_root = tmp_path / "repo"
    write_json(
        repo_root / "docs-viewer/config/scopes/docs_scopes.json",
        {
            "schema_version": "docs_scopes_v4",
            "scopes": [source_scope, target_scope],
        },
    )
    write_doc(
        local_documents_root(repo_root, "source"),
        doc_id="root",
        title="Root",
        body="# Root\n\n[[media:docs/source/img/photo.png Photo]]\n",
    )
    external_documents = (
        projects_base / "docs-viewer/scopes/target/source/documents"
    )
    external_documents.mkdir(parents=True, exist_ok=True)
    write_bytes(media_path(repo_root, "source", "img", "photo.png"), b"managed")

    plan = transfer.plan_document_transfer(
        repo_root,
        source_scope="source",
        requested_doc_ids=["root"],
        target_scope="target",
        transfer_mode="copy",
        operation_timestamp="2026-07-24 09:10:11",
        token_factory=sequential_tokens("aaaaaa"),
    )

    assert plan.ok
    assert plan.media[0].source_provider == "external_local"
    assert plan.media[0].target_provider == "external_local"
    assert plan.media[0].target_status == "create"


def test_external_local_source_can_plan_move_to_local_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    projects_base = tmp_path / "Projects"
    (projects_base / "docs-viewer/media").mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(projects_base))
    source_scope = docs_scope_record(
        "source",
        scope_type="local_external",
        viewer_base_url="/docs/",
        include_scope_param=True,
        media_types=("img",),
    )
    target_scope = base_scope("target", media_types=("img",))
    repo_root = tmp_path / "repo"
    write_json(
        repo_root / "docs-viewer/config/scopes/docs_scopes.json",
        {
            "schema_version": "docs_scopes_v4",
            "scopes": [source_scope, target_scope],
        },
    )
    external_scope_root = projects_base / "docs-viewer/scopes/source"
    write_doc(
        external_scope_root / "source/documents",
        doc_id="root",
        title="Root",
        body="# Root\n\n[[media:docs/source/img/photo.png Photo]]\n",
    )
    write_bytes(
        media_path(repo_root, "source", "img", "photo.png"),
        b"external",
    )
    local_documents_root(repo_root, "target").mkdir(parents=True, exist_ok=True)

    plan = transfer.plan_document_transfer(
        repo_root,
        source_scope="source",
        requested_doc_ids=["root"],
        target_scope="target",
        transfer_mode="move",
        operation_timestamp="2026-07-24 09:10:11",
    )

    assert plan.ok
    assert plan.media[0].source_provider == "external_local"
    assert plan.media[0].target_provider == "external_local"
    assert plan.media[0].target_status == "create"


def test_public_copy_target_is_allowed_but_public_moves_are_rejected(
    tmp_path: Path,
) -> None:
    public_source = docs_scope_record(
        "source",
        scope_type="public",
        viewer_base_url="/source/",
        include_scope_param=False,
    )
    public_target = docs_scope_record(
        "target",
        scope_type="public",
        viewer_base_url="/target/",
        include_scope_param=False,
    )
    repo_root = make_repo(
        tmp_path,
        source_scope=public_source,
        target_scope=public_target,
    )
    plan = transfer.plan_document_transfer(
        repo_root,
        source_scope="source",
        requested_doc_ids=["root"],
        target_scope="target",
        transfer_mode="copy",
        operation_timestamp="2026-07-24 09:10:11",
        token_factory=sequential_tokens("aaaaaa"),
    )

    assert plan.ok
    assert plan.preview_payload()["target_default_publishable"] is True

    with pytest.raises(ValueError, match="public source scopes cannot be moved"):
        transfer.plan_document_transfer(
            repo_root,
            source_scope="source",
            requested_doc_ids=["root"],
            target_scope="target",
            transfer_mode="move",
        )

    target_move_repo = make_repo(
        tmp_path / "target-move",
        target_scope=public_target,
    )
    with pytest.raises(ValueError, match="public target scope"):
        transfer.plan_document_transfer(
            target_move_repo,
            source_scope="source",
            requested_doc_ids=["root"],
            target_scope="target",
            transfer_mode="move",
        )


def test_public_parent_and_child_can_accept_copy(
    tmp_path: Path,
) -> None:
    public_target = docs_scope_record(
        "target",
        scope_type="public",
        viewer_base_url="/target/",
        include_scope_param=False,
        sub_scopes=[
            docs_sub_scope_record(
                "target",
                "works",
                title="Works",
                scope_type="public",
                sub_scope_customisation={
                    "id": "analysis_works",
                    "settings": {},
                },
            )
        ],
    )
    repo_root = make_repo(tmp_path, target_scope=public_target)
    report_id = "d-20260701-100003-dddddd"
    write_doc(
        local_documents_root(repo_root, "target"),
        doc_id=report_id,
        title="Works",
        body=report_body("Works", "works"),
    )
    sub_scope_documents_root(repo_root, "target", "works").mkdir(
        parents=True,
        exist_ok=True,
    )

    child_plan = transfer.plan_document_transfer(
        repo_root,
        source_scope="source",
        requested_doc_ids=["other"],
        target_scope="target",
        target_sub_scope="works",
        transfer_mode="copy",
        operation_timestamp="2026-07-24 09:10:11",
        token_factory=sequential_tokens("aaaaaa"),
    )
    capabilities = transfer.document_transfer_collection_capabilities(
        child_plan.target_collection
    )

    assert child_plan.ok
    assert child_plan.preview_payload()["target_default_publishable"] is True
    assert capabilities == {
        "copy_source": True,
        "move_source": False,
        "copy_target": True,
        "move_target": False,
    }
    parent_plan = transfer.plan_document_transfer(
        repo_root,
        source_scope="source",
        requested_doc_ids=["other"],
        target_scope="target",
        transfer_mode="copy",
        operation_timestamp="2026-07-24 09:10:12",
        token_factory=sequential_tokens("bbbbbb"),
    )
    parent_capabilities = transfer.document_transfer_collection_capabilities(
        parent_plan.target_collection
    )

    assert parent_plan.ok
    assert parent_plan.preview_payload()["target_default_publishable"] is True
    assert parent_capabilities == {
        "copy_source": True,
        "move_source": False,
        "copy_target": True,
        "move_target": False,
    }
