#!/usr/bin/env python3
"""Focused route checks for generalized document Copy and Move."""

from __future__ import annotations

import json
import sys
from http import HTTPStatus
from pathlib import Path

import pytest

from repo_factory import docs_scope_record, docs_sub_scope_record


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
if str(DOCS_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(DOCS_SERVICES_DIR))

import docs_management_service  # noqa: E402
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


def report_body(title: str) -> str:
    return (
        f"# {title}\n\n"
        ":::report\n"
        "id: docs_subscope\n"
        "access: local\n"
        "sub_scope: works\n"
        ":::\n"
    )


def write_doc(
    documents_root: Path,
    *,
    doc_id: str,
    title: str,
    parent_id: str = "",
    body: str | None = None,
    extra_front_matter: dict[str, object] | None = None,
) -> None:
    documents_root.mkdir(parents=True, exist_ok=True)
    front_matter = {
        "doc_id": doc_id,
        "title": title,
        "parent_id": parent_id,
    }
    front_matter.update(extra_front_matter or {})
    (documents_root / f"{doc_id}.md").write_text(
        source_model.format_source(front_matter, body or f"# {title}\n"),
        encoding="utf-8",
    )


def make_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    write_json(
        repo_root / "docs-viewer/config/scopes/docs_scopes.json",
        {
            "schema_version": "docs_scopes_v4",
            "scopes": [
                docs_scope_record(
                    "source",
                    viewer_base_url="/docs/",
                    include_scope_param=True,
                    sub_scopes=[
                        docs_sub_scope_record("source", "works", title="Works"),
                    ],
                ),
                docs_scope_record(
                    "target",
                    viewer_base_url="/docs/",
                    include_scope_param=True,
                    sub_scopes=[
                        docs_sub_scope_record("target", "works", title="Works"),
                    ],
                ),
            ],
        },
    )
    source_root = repo_root / "docs-viewer/scopes/source/source/documents"
    target_root = repo_root / "docs-viewer/scopes/target/source/documents"
    source_works_root = (
        repo_root
        / "docs-viewer/scopes/source/source/sub-scopes/works/documents"
    )
    target_works_root = (
        repo_root
        / "docs-viewer/scopes/target/source/sub-scopes/works/documents"
    )
    write_doc(source_root, doc_id="root", title="Root")
    write_doc(source_root, doc_id="alpha", title="Alpha", parent_id="root")
    write_doc(source_root, doc_id="grand", title="Grand", parent_id="alpha")
    write_doc(source_root, doc_id="beta", title="Beta", parent_id="root")
    write_doc(
        source_root,
        doc_id="source-works-report",
        title="Source Works",
        body=report_body("Source Works"),
    )
    write_doc(
        target_root,
        doc_id="target-works-report",
        title="Target Works",
        body=report_body("Target Works"),
    )
    write_doc(source_works_root, doc_id="work-a", title="Work A")
    target_root.mkdir(parents=True, exist_ok=True)
    target_works_root.mkdir(parents=True, exist_ok=True)
    return repo_root


@pytest.fixture(autouse=True)
def isolated_media_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    projects = tmp_path / "projects"
    (projects / "docs-viewer/media").mkdir(parents=True)
    monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(projects))


def test_preview_and_copy_apply_routes_share_apply_plan(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = make_repo(tmp_path)
    status, preview = docs_management_service.docs_management_post_response(
        repo_root,
        docs_management_service.routes.DOCUMENT_TRANSFER_PREVIEW_PATH,
        {
            "scope": "source",
            "doc_ids": ["root"],
            "target_scope": "target",
            "transfer_mode": "copy",
            "include_descendants": True,
        },
    )

    assert status == HTTPStatus.OK
    assert preview["ok"] is True
    assert preview["dry_run"] is True
    assert preview["source"] == {"scope": "source"}
    assert preview["target"] == {"scope": "target", "placement": "scope_root"}
    assert preview["mode"] == "copy"
    assert preview["requested_count"] == 1
    assert preview["document_count"] == 4
    assert preview["descendant_count"] == 3
    apply_plan = preview["apply_plan"]
    captured: dict[str, object] = {}

    def fake_apply(
        actual_repo_root: Path,
        plan,
        *,
        confirm: bool,
    ) -> dict[str, object]:
        captured.update(
            {
                "repo_root": actual_repo_root,
                "source_scope": plan.source_scope,
                "target_scope": plan.target_scope,
                "source_doc_ids": [
                    document.source_doc.doc_id for document in plan.documents
                ],
                "target_doc_ids": [
                    document.target_doc_id for document in plan.documents
                ],
                "confirm": confirm,
            }
        )
        return {
            "ok": True,
            "target_viewer_url": "/docs/?scope=target&doc=copied",
        }

    monkeypatch.setattr(
        docs_management_service.docs_document_transfer_apply,
        "apply_document_copy",
        fake_apply,
    )
    status, applied = docs_management_service.docs_management_post_response(
        repo_root,
        docs_management_service.routes.DOCUMENT_TRANSFER_APPLY_PATH,
        {
            "scope": "source",
            "apply_plan": apply_plan,
            "confirm": True,
        },
    )

    assert status == HTTPStatus.OK
    assert applied == {
        "ok": True,
        "target_viewer_url": "/docs/?scope=target&doc=copied",
    }
    assert captured == {
        "repo_root": repo_root,
        "source_scope": "source",
        "target_scope": "target",
        "source_doc_ids": ["root", "alpha", "grand", "beta"],
        "target_doc_ids": [
            record["target_doc_id"] for record in apply_plan["documents"]
        ],
        "confirm": True,
    }

    with pytest.raises(ValueError, match="source collection does not match request"):
        docs_management_service.docs_management_post_response(
            repo_root,
            docs_management_service.routes.DOCUMENT_TRANSFER_APPLY_PATH,
            {
                "scope": "target",
                "apply_plan": apply_plan,
                "confirm": True,
            },
        )


def test_preview_and_apply_routes_preserve_exact_child_collections(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = make_repo(tmp_path)
    status, preview = docs_management_service.docs_management_post_response(
        repo_root,
        docs_management_service.routes.DOCUMENT_TRANSFER_PREVIEW_PATH,
        {
            "scope": "source",
            "sub_scope": "works",
            "doc_ids": ["work-a"],
            "target_scope": "target",
            "target_sub_scope": "works",
            "transfer_mode": "copy",
            "include_descendants": False,
        },
    )

    assert status == HTTPStatus.OK
    assert preview["source"] == {"scope": "source", "sub_scope": "works"}
    assert preview["target"] == {
        "scope": "target",
        "sub_scope": "works",
        "placement": "sub_scope_root",
    }
    captured: dict[str, object] = {}

    def fake_apply(actual_repo_root: Path, plan, *, confirm: bool) -> dict[str, object]:
        captured.update(
            {
                "repo_root": actual_repo_root,
                "source": plan.source_collection.request_target(),
                "target": plan.target_collection.request_target(),
                "confirm": confirm,
            }
        )
        return {"ok": True}

    monkeypatch.setattr(
        docs_management_service.docs_document_transfer_apply,
        "apply_document_copy",
        fake_apply,
    )
    status, applied = docs_management_service.docs_management_post_response(
        repo_root,
        docs_management_service.routes.DOCUMENT_TRANSFER_APPLY_PATH,
        {
            "scope": "source",
            "sub_scope": "works",
            "apply_plan": preview["apply_plan"],
            "confirm": True,
        },
    )

    assert status == HTTPStatus.OK
    assert applied == {"ok": True}
    assert captured == {
        "repo_root": repo_root,
        "source": {"scope": "source", "sub_scope": "works"},
        "target": {"scope": "target", "sub_scope": "works"},
        "confirm": True,
    }
    with pytest.raises(ValueError, match="source collection does not match request"):
        docs_management_service.docs_management_post_response(
            repo_root,
            docs_management_service.routes.DOCUMENT_TRANSFER_APPLY_PATH,
            {
                "scope": "source",
                "apply_plan": preview["apply_plan"],
                "confirm": True,
            },
        )


def test_preview_forces_move_descendants_and_apply_dispatches_move(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = make_repo(tmp_path)
    status, preview = docs_management_service.docs_management_post_response(
        repo_root,
        docs_management_service.routes.DOCUMENT_TRANSFER_PREVIEW_PATH,
        {
            "scope": "source",
            "doc_ids": ["alpha"],
            "target_scope": "target",
            "transfer_mode": "move",
            "include_descendants": False,
        },
    )

    assert status == HTTPStatus.OK
    assert preview["mode"] == "move"
    assert preview["include_descendants"] is True
    assert preview["descendants_forced"] is True
    assert [item["source_doc_id"] for item in preview["documents"]] == [
        "alpha",
        "grand",
    ]
    captured: dict[str, object] = {}

    def fake_move(actual_repo_root: Path, plan, *, confirm: bool) -> dict[str, object]:
        captured.update(
            {
                "repo_root": actual_repo_root,
                "mode": plan.mode,
                "doc_ids": [
                    document.source_doc.doc_id for document in plan.documents
                ],
                "confirm": confirm,
            }
        )
        return {
            "ok": True,
            "effective_roots": [
                {"target_viewer_url": "/docs/?scope=target&doc=alpha"}
            ],
        }

    monkeypatch.setattr(
        docs_management_service.docs_document_move_apply,
        "apply_document_move",
        fake_move,
    )
    status, applied = docs_management_service.docs_management_post_response(
        repo_root,
        docs_management_service.routes.DOCUMENT_TRANSFER_APPLY_PATH,
        {
            "scope": "source",
            "apply_plan": preview["apply_plan"],
            "confirm": True,
        },
    )

    assert status == HTTPStatus.OK
    assert applied["effective_roots"][0]["target_viewer_url"].endswith("doc=alpha")
    assert captured == {
        "repo_root": repo_root,
        "mode": "move",
        "doc_ids": ["alpha", "grand"],
        "confirm": True,
    }


def test_apply_route_preserves_failure_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = make_repo(tmp_path)
    _status, preview = docs_management_service.docs_management_post_response(
        repo_root,
        docs_management_service.routes.DOCUMENT_TRANSFER_PREVIEW_PATH,
        {
            "scope": "source",
            "doc_ids": ["root"],
            "target_scope": "target",
            "transfer_mode": "copy",
            "include_descendants": False,
        },
    )
    evidence = {
        "ok": False,
        "phase": "target_rebuild",
        "target": {"state": "present"},
    }

    def fail_apply(*_args, **_kwargs):
        raise docs_management_service.docs_document_transfer_apply.DocumentTransferApplyError(
            "target rebuild failed",
            evidence,
        )

    monkeypatch.setattr(
        docs_management_service.docs_document_transfer_apply,
        "apply_document_copy",
        fail_apply,
    )
    status, payload = docs_management_service.docs_management_post_response(
        repo_root,
        docs_management_service.routes.DOCUMENT_TRANSFER_APPLY_PATH,
        {
            "scope": "source",
            "apply_plan": preview["apply_plan"],
            "confirm": True,
        },
    )

    assert status == HTTPStatus.CONFLICT
    assert payload == {
        **evidence,
        "error": "target rebuild failed",
    }
