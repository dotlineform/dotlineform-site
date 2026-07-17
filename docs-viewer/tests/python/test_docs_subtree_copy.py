#!/usr/bin/env python3
"""Focused checks for write-free subtree-copy planning."""

from __future__ import annotations

import json
import os
import re
import sys
from collections.abc import Iterator
from dataclasses import replace
from http import HTTPStatus
from pathlib import Path

from repo_factory import docs_scope_record

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
DOCS_BUILD_DIR = REPO_ROOT / "docs-viewer" / "build"
for module_path in (DOCS_BUILD_DIR, DOCS_SERVICES_DIR):
    if str(module_path) not in sys.path:
        sys.path.insert(0, str(module_path))

import build_docs  # noqa: E402
import build_search  # noqa: E402
import docs_source_model as source_model  # noqa: E402
import docs_management_service  # noqa: E402
import docs_subtree_copy as subtree_copy  # noqa: E402
import docs_subtree_copy_apply as subtree_copy_apply  # noqa: E402
from build_docs_test_support import (  # noqa: E402
    write_route_config,
    write_semantic_reference_registry,
    write_site_tools_config,
)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def scope_config(scope: str, *, scope_type: str = "local") -> dict[str, object]:
    return docs_scope_record(
        scope,
        scope_type=scope_type,
        viewer_base_url=f"/{scope}/" if scope_type == "public" else "/docs/",
        include_scope_param=scope_type != "public",
    )


def external_scope_config(scope: str) -> dict[str, object]:
    return docs_scope_record(scope, scope_type="local_external")


def write_doc(
    repo_root: Path,
    scope: str,
    filename: str,
    *,
    doc_id: str,
    title: str,
    parent_id: str = "",
    body: str | None = None,
    extra_front_matter: dict[str, object] | None = None,
) -> None:
    root = repo_root / "docs-viewer/source" / scope / "documents"
    root.mkdir(parents=True, exist_ok=True)
    front_matter: dict[str, object] = {
        "doc_id": doc_id,
        "title": title,
        "parent_id": parent_id,
        "viewable": True,
    }
    front_matter.update(extra_front_matter or {})
    (root / filename).write_text(
        source_model.format_source(front_matter, body if body is not None else f"# {title}\n"),
        encoding="utf-8",
    )


def make_repo(
    tmp_path: Path,
    *,
    source_type: str = "local",
    target_type: str = "local",
) -> Path:
    repo_root = tmp_path / "repo"
    write_json(
        repo_root / "docs-viewer/config/scopes/docs_scopes.json",
        {
            "schema_version": "docs_scopes_v2",
            "scopes": [
                scope_config("source", scope_type=source_type),
                scope_config("target", scope_type=target_type),
            ],
        },
    )
    write_doc(repo_root, "source", "root.md", doc_id="root", title="Root")
    write_doc(repo_root, "source", "beta.md", doc_id="beta", title="Beta", parent_id="root")
    write_doc(repo_root, "source", "alpha.md", doc_id="alpha", title="Alpha", parent_id="root")
    write_doc(repo_root, "source", "grand.md", doc_id="grand", title="Grand", parent_id="alpha")
    write_doc(repo_root, "source", "other.md", doc_id="other", title="Other")
    write_doc(
        repo_root,
        "target",
        "existing.md",
        doc_id="d-20260716-200000-aaaaaa",
        title="Existing",
    )
    return repo_root


def sequential_tokens(*tokens: str) -> subtree_copy.IdentityTokenFactory:
    iterator: Iterator[str] = iter(tokens)
    return lambda _size: next(iterator)


def source_snapshot(repo_root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(repo_root).as_posix(): path.read_bytes()
        for path in sorted((repo_root / "docs-viewer/source").glob("**/*"))
        if path.is_file()
    }


def scope_snapshot(repo_root: Path, scope: str) -> dict[str, bytes]:
    root = repo_root / "docs-viewer/source" / scope / "documents"
    return {
        path.name: path.read_bytes()
        for path in sorted(root.glob("*.md"))
    }


def test_plan_copy_subtree_is_complete_ordered_and_write_free(tmp_path: Path) -> None:
    repo_root = make_repo(tmp_path)
    before = source_snapshot(repo_root)

    plan = subtree_copy.plan_copy_subtree(
        repo_root,
        source_scope="source",
        source_doc_id="root",
        target_scope="target",
        copy_timestamp="2026-07-16 20:00:00",
        token_factory=sequential_tokens("aaaaaa", "bbbbbb", "cccccc", "dddddd", "eeeeee"),
    )

    assert source_snapshot(repo_root) == before
    assert plan.copy_timestamp == "2026-07-16 20:00:00"
    assert [document.source_doc.doc_id for document in plan.documents] == [
        "root",
        "alpha",
        "grand",
        "beta",
    ]
    assert [document.target_doc_id for document in plan.documents] == [
        "d-20260716-200000-bbbbbb",
        "d-20260716-200000-cccccc",
        "d-20260716-200000-dddddd",
        "d-20260716-200000-eeeeee",
    ]
    assert [document.target_parent_id for document in plan.documents] == [
        "",
        "d-20260716-200000-bbbbbb",
        "d-20260716-200000-cccccc",
        "d-20260716-200000-bbbbbb",
    ]
    assert all(
        document.target_path.name == f"{document.target_doc_id}.md"
        for document in plan.documents
    )
    assert len({document.target_path for document in plan.documents}) == 4
    preview = plan.preview_payload()
    apply_plan = preview.pop("apply_plan")
    assert preview == {
        "schema_version": "docs_copy_subtree_preview_v1",
        "ok": True,
        "source": {"scope": "source", "doc_id": "root", "title": "Root"},
        "target": {"scope": "target", "placement": "scope_root"},
        "document_count": 4,
        "descendant_count": 3,
    }
    assert apply_plan == plan.apply_plan_payload()
    assert apply_plan["schema_version"] == "docs_copy_subtree_apply_plan_v1"
    assert apply_plan["source_scope"] == "source"
    assert apply_plan["source_doc_id"] == "root"
    assert apply_plan["target_scope"] == "target"
    assert apply_plan["copy_timestamp"] == "2026-07-16 20:00:00"
    assert len(apply_plan["source_config_sha256"]) == 64
    assert len(apply_plan["target_config_sha256"]) == 64
    assert [record["source_doc_id"] for record in apply_plan["documents"]] == [
        "root",
        "alpha",
        "grand",
        "beta",
    ]
    assert [record["target_doc_id"] for record in apply_plan["documents"]] == [
        document.target_doc_id for document in plan.documents
    ]
    assert all(len(record["source_sha256"]) == 64 for record in apply_plan["documents"])
    serialized_apply_plan = json.dumps(apply_plan)
    assert str(repo_root) not in serialized_apply_plan
    assert "# Root" not in serialized_apply_plan


def test_plan_copy_subtree_handles_leaf_and_duplicate_titles(tmp_path: Path) -> None:
    repo_root = make_repo(tmp_path)
    write_doc(
        repo_root,
        "source",
        "beta.md",
        doc_id="beta",
        title="Alpha",
        parent_id="root",
    )

    tree_plan = subtree_copy.plan_copy_subtree(
        repo_root,
        source_scope="source",
        source_doc_id="root",
        target_scope="target",
        copy_timestamp="2026-07-16 20:00:00",
        token_factory=sequential_tokens("bbbbbb", "cccccc", "dddddd", "eeeeee"),
    )
    leaf_plan = subtree_copy.plan_copy_subtree(
        repo_root,
        source_scope="source",
        source_doc_id="grand",
        target_scope="target",
        copy_timestamp="2026-07-16 20:01:00",
        token_factory=sequential_tokens("aaaaaa"),
    )

    assert [document.source_doc.title for document in tree_plan.documents].count("Alpha") == 2
    assert len(set(tree_plan.id_map.values())) == len(tree_plan.documents) == 4
    assert [document.source_doc.doc_id for document in leaf_plan.documents] == ["grand"]
    assert leaf_plan.root.target_parent_id == ""
    assert leaf_plan.preview_payload()["descendant_count"] == 0


def test_plan_copy_subtree_rejects_public_target(tmp_path: Path) -> None:
    repo_root = make_repo(tmp_path, target_type="public")

    with pytest.raises(
        ValueError,
        match="public target scope 'target' is not available for subtree copy",
    ):
        subtree_copy.plan_copy_subtree(
            repo_root,
            source_scope="source",
            source_doc_id="root",
            target_scope="target",
        )


def test_transform_copy_subtree_preserves_content_and_rewrites_only_copied_links(
    tmp_path: Path,
) -> None:
    repo_root = make_repo(tmp_path)
    root_body = (
        "# Root\n\n"
        "[Copied child](/docs/?scope=source&doc=alpha#details)\n"
        "[Outside subtree](/docs/?scope=source&doc=other#keep)\n"
        "[Existing target](/target/?doc=d-20260716-200000-aaaaaa)\n"
        "[External host](https://example.com/docs/?scope=source&doc=alpha)\n"
        "[[ref:source:alpha]]\n"
        "[[media:docs/source/image.webp]]\n"
        "![Image](/assets/docs/source/image.webp)\n"
        "[Download](/downloads/source.zip)\n"
        "<script src=\"/interactive/source.js\"></script>\n"
    )
    alpha_body = (
        "# Alpha\n\n"
        "[Copied root](/docs/?doc=root&scope=source&mode=outline#top)\n"
    )
    write_doc(
        repo_root,
        "source",
        "root.md",
        doc_id="root",
        title="Root",
        body=root_body,
        extra_front_matter={
            "date": "2026-07-01",
            "summary": "Preserve this summary",
            "sort_order": 7,
            "ui_status": "ready",
            "custom_field": "kept",
        },
    )
    write_doc(
        repo_root,
        "source",
        "alpha.md",
        doc_id="alpha",
        title="Alpha",
        parent_id="root",
        body=alpha_body,
        extra_front_matter={"viewable": False},
    )
    before = source_snapshot(repo_root)
    plan = subtree_copy.plan_copy_subtree(
        repo_root,
        source_scope="source",
        source_doc_id="root",
        target_scope="target",
        copy_timestamp="2026-07-16 20:00:00",
        token_factory=sequential_tokens("bbbbbb", "cccccc", "dddddd", "eeeeee"),
    )

    result = subtree_copy.transform_copy_subtree(plan)

    assert source_snapshot(repo_root) == before
    assert result.viewer_link_rewrites == 2
    assert len(result.documents) == 4
    by_source_id = {
        document.planned_document.source_doc.doc_id: document
        for document in result.documents
    }
    root = by_source_id["root"]
    alpha = by_source_id["alpha"]
    root_front_matter, rewritten_root_body = source_model.parse_source_text(root.source_text)
    alpha_front_matter, rewritten_alpha_body = source_model.parse_source_text(alpha.source_text)

    assert root.target_path.name == f"{plan.id_map['root']}.md"
    assert root_front_matter == {
        "doc_id": plan.id_map["root"],
        "title": "Root",
        "date": "2026-07-01",
        "added_date": "2026-07-16 20:00:00",
        "last_updated": "2026-07-16 20:00:00",
        "summary": "Preserve this summary",
        "ui_status": "ready",
        "parent_id": "",
        "custom_field": "kept",
        "sort_order": 7,
    }
    assert alpha_front_matter["doc_id"] == plan.id_map["alpha"]
    assert alpha_front_matter["parent_id"] == plan.id_map["root"]
    assert alpha_front_matter["added_date"] == "2026-07-16 20:00:00"
    assert alpha_front_matter["last_updated"] == "2026-07-16 20:00:00"
    assert "viewable" not in alpha_front_matter
    assert "copied_from" not in root_front_matter
    assert (
        f"[Copied child](/docs/?scope=target&doc={plan.id_map['alpha']}#details)"
        in rewritten_root_body
    )
    assert "[Outside subtree](/docs/?scope=source&doc=other#keep)" in rewritten_root_body
    assert "[Existing target](/target/?doc=d-20260716-200000-aaaaaa)" in rewritten_root_body
    assert "[External host](https://example.com/docs/?scope=source&doc=alpha)" in rewritten_root_body
    assert "[[ref:source:alpha]]" in rewritten_root_body
    assert "[[media:docs/source/image.webp]]" in rewritten_root_body
    assert "![Image](/assets/docs/source/image.webp)" in rewritten_root_body
    assert "[Download](/downloads/source.zip)" in rewritten_root_body
    assert '<script src="/interactive/source.js"></script>' in rewritten_root_body
    assert (
        f"[Copied root](/docs/?doc={plan.id_map['root']}&scope=target&mode=outline#top)"
        in rewritten_alpha_body
    )
    for document in result.documents:
        front_matter, _body = source_model.parse_source_text(document.source_text)
        assert front_matter["doc_id"] == document.planned_document.target_doc_id
        assert source_model.doc_is_viewable(front_matter) is True


def test_restore_copy_subtree_apply_plan_round_trips_previewed_plan(tmp_path: Path) -> None:
    repo_root = make_repo(tmp_path)
    plan = subtree_copy.plan_copy_subtree(
        repo_root,
        source_scope="source",
        source_doc_id="root",
        target_scope="target",
        copy_timestamp="2026-07-16 20:00:00",
        token_factory=sequential_tokens("bbbbbb", "cccccc", "dddddd", "eeeeee"),
    )

    restored = subtree_copy.restore_copy_subtree_apply_plan(
        repo_root,
        plan.apply_plan_payload(),
    )

    assert restored.source_scope == plan.source_scope
    assert restored.target_scope == plan.target_scope
    assert restored.copy_timestamp == plan.copy_timestamp
    assert [document.source_doc.doc_id for document in restored.documents] == [
        document.source_doc.doc_id for document in plan.documents
    ]
    assert restored.id_map == plan.id_map
    assert [document.target_parent_id for document in restored.documents] == [
        document.target_parent_id for document in plan.documents
    ]


def test_restore_copy_subtree_apply_plan_rejects_changed_source_and_config(tmp_path: Path) -> None:
    repo_root = make_repo(tmp_path)
    plan = subtree_copy.plan_copy_subtree(
        repo_root,
        source_scope="source",
        source_doc_id="root",
        target_scope="target",
    )
    apply_plan = plan.apply_plan_payload()
    root_path = repo_root / "docs-viewer/source/source/documents/root.md"
    root_path.write_text(root_path.read_text(encoding="utf-8") + "Changed.\n", encoding="utf-8")

    with pytest.raises(ValueError, match="source content changed for 'root'"):
        subtree_copy.restore_copy_subtree_apply_plan(repo_root, apply_plan)

    root_path.write_text(plan.root.source_doc.source_text, encoding="utf-8")
    config_path = repo_root / "docs-viewer/config/scopes/docs_scopes.json"
    config_payload = json.loads(config_path.read_text(encoding="utf-8"))
    config_payload["scopes"][1]["default_doc_id"] = "d-20260716-200000-aaaaaa"
    write_json(config_path, config_payload)

    with pytest.raises(ValueError, match="target scope 'target' configuration changed"):
        subtree_copy.restore_copy_subtree_apply_plan(repo_root, apply_plan)


def test_management_copy_subtree_preview_and_apply_routes_share_apply_plan(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = make_repo(tmp_path)
    status, preview = docs_management_service.docs_management_post_response(
        repo_root,
        docs_management_service.routes.COPY_SUBTREE_PREVIEW_PATH,
        {
            "scope": "source",
            "source_doc_id": "root",
            "target_scope": "target",
        },
    )

    assert status == HTTPStatus.OK
    assert preview["ok"] is True
    assert preview["dry_run"] is True
    assert preview["source"] == {"scope": "source", "doc_id": "root", "title": "Root"}
    assert preview["target"] == {"scope": "target", "placement": "scope_root"}
    assert preview["document_count"] == 4
    assert preview["descendant_count"] == 3
    apply_plan = preview["apply_plan"]
    captured: dict[str, object] = {}

    def fake_apply(
        actual_repo_root: Path,
        plan: subtree_copy.CopySubtreePlan,
        *,
        confirm: bool,
    ) -> dict[str, object]:
        captured.update({
            "repo_root": actual_repo_root,
            "source_scope": plan.source_scope,
            "target_scope": plan.target_scope,
            "source_doc_ids": [document.source_doc.doc_id for document in plan.documents],
            "target_doc_ids": [document.target_doc_id for document in plan.documents],
            "confirm": confirm,
        })
        return {"ok": True, "target_viewer_url": "/docs/?scope=target&doc=copied"}

    monkeypatch.setattr(
        docs_management_service.docs_subtree_copy_apply,
        "apply_copy_subtree",
        fake_apply,
    )
    status, applied = docs_management_service.docs_management_post_response(
        repo_root,
        docs_management_service.routes.COPY_SUBTREE_APPLY_PATH,
        {
            "scope": "source",
            "apply_plan": apply_plan,
            "confirm": True,
        },
    )

    assert status == HTTPStatus.OK
    assert applied == {"ok": True, "target_viewer_url": "/docs/?scope=target&doc=copied"}
    assert captured == {
        "repo_root": repo_root,
        "source_scope": "source",
        "target_scope": "target",
        "source_doc_ids": ["root", "alpha", "grand", "beta"],
        "target_doc_ids": [record["target_doc_id"] for record in apply_plan["documents"]],
        "confirm": True,
    }

    with pytest.raises(ValueError, match="source scope does not match request scope"):
        docs_management_service.docs_management_post_response(
            repo_root,
            docs_management_service.routes.COPY_SUBTREE_APPLY_PATH,
            {
                "scope": "target",
                "apply_plan": apply_plan,
                "confirm": True,
            },
        )


def test_transform_copy_subtree_adds_scope_for_local_target_and_uses_create_viewability(
    tmp_path: Path,
) -> None:
    repo_root = make_repo(tmp_path, source_type="public")
    write_doc(
        repo_root,
        "source",
        "root.md",
        doc_id="root",
        title="Root",
        body="# Root\n\n[Self](/source/?doc=root#details)\n",
        extra_front_matter={"viewable": False},
    )
    plan = subtree_copy.plan_copy_subtree(
        repo_root,
        source_scope="source",
        source_doc_id="root",
        target_scope="target",
        copy_timestamp="2026-07-16 20:00:00",
        token_factory=sequential_tokens("bbbbbb", "cccccc", "dddddd", "eeeeee"),
    )

    result = subtree_copy.transform_copy_subtree(plan)
    root = result.documents[0]
    front_matter, body = source_model.parse_source_text(root.source_text)

    assert "viewable" not in front_matter
    assert source_model.doc_is_viewable(front_matter) is True
    assert f"[Self](/docs/?scope=target&doc={plan.id_map['root']}#details)" in body


def test_copy_subtree_supports_external_local_target_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    projects_root = tmp_path / "projects"
    external_docs_root = projects_root / "docs-viewer"
    target_root = external_docs_root / "source/target/documents"
    target_root.mkdir(parents=True)
    monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", projects_root.as_posix())
    repo_root = make_repo(tmp_path)
    config_path = repo_root / "docs-viewer/config/scopes/docs_scopes.json"
    config_payload = json.loads(config_path.read_text(encoding="utf-8"))
    config_payload["scopes"][1] = external_scope_config("target")
    write_json(config_path, config_payload)
    write_doc(
        projects_root,
        "target",
        "existing.md",
        doc_id="d-20260716-200000-aaaaaa",
        title="Existing",
    )
    source_before = scope_snapshot(repo_root, "source")

    plan = subtree_copy.plan_copy_subtree(
        repo_root,
        source_scope="source",
        source_doc_id="root",
        target_scope="target",
        copy_timestamp="2026-07-16 20:00:00",
        token_factory=sequential_tokens("bbbbbb", "cccccc", "dddddd", "eeeeee"),
    )
    transformed = subtree_copy.transform_copy_subtree(plan)
    result = subtree_copy_apply.apply_copy_subtree(
        repo_root,
        plan,
        confirm=True,
        perform_source_write_and_rebuild=lambda _root, _scope, _paths, write, **_kwargs: (
            write() or {"ok": True}
        ),
        activity_logger=lambda *_args, **_kwargs: None,
    )

    assert all(document.target_path.parent == target_root for document in plan.documents)
    assert all(
        source_model.doc_is_viewable(source_model.parse_source_text(document.source_text)[0]) is True
        for document in transformed.documents
    )
    assert set(result["created_doc_ids"]) == {
        path.stem for path in target_root.glob("*.md") if path.name != "existing.md"
    }
    assert scope_snapshot(repo_root, "source") == source_before


def test_apply_copy_subtree_writes_only_target_and_coordinates_one_rebuild(
    tmp_path: Path,
) -> None:
    repo_root = make_repo(tmp_path)
    source_before = scope_snapshot(repo_root, "source")
    plan = subtree_copy.plan_copy_subtree(
        repo_root,
        source_scope="source",
        source_doc_id="root",
        target_scope="target",
        copy_timestamp="2026-07-16 20:00:00",
        token_factory=sequential_tokens("bbbbbb", "cccccc", "dddddd", "eeeeee"),
    )
    rebuild_calls: list[dict[str, object]] = []
    activity_calls: list[tuple[str, dict[str, object]]] = []

    def fake_rebuild(
        _repo_root: Path,
        scope: str,
        changed_paths: list[Path],
        write_operation,
        **kwargs,
    ) -> dict[str, object]:
        write_operation()
        rebuild_calls.append({
            "scope": scope,
            "changed_paths": list(changed_paths),
            **kwargs,
            "written_paths": list(kwargs["written_paths"]),
        })
        return {"ok": True, "mode": "test"}

    def fake_activity(_repo_root: Path, event: str, details: dict[str, object]) -> None:
        activity_calls.append((event, dict(details)))

    result = subtree_copy_apply.apply_copy_subtree(
        repo_root,
        plan,
        confirm=True,
        perform_source_write_and_rebuild=fake_rebuild,
        activity_logger=fake_activity,
    )

    assert scope_snapshot(repo_root, "source") == source_before
    assert result == {
        "schema_version": "docs_copy_subtree_apply_v1",
        "ok": True,
        "source_scope": "source",
        "source_root_doc_id": "root",
        "target_scope": "target",
        "new_root_doc_id": plan.id_map["root"],
        "created_doc_ids": list(plan.id_map.values()),
        "document_count": 4,
        "copy_timestamp": "2026-07-16 20:00:00",
        "target_viewer_url": f"/docs/?scope=target&doc={plan.id_map['root']}",
        "viewer_link_rewrites": 0,
        "rebuild": {"ok": True, "mode": "test"},
        "summary_text": "Copied 4 documents from source to target.",
    }
    assert len(rebuild_calls) == 1
    rebuild_call = rebuild_calls[0]
    assert rebuild_call["scope"] == "target"
    assert rebuild_call["changed_paths"] == [document.target_path for document in plan.documents]
    assert rebuild_call["written_paths"] == [document.target_path for document in plan.documents]
    assert rebuild_call["docs_doc_ids"] == list(plan.id_map.values())
    assert rebuild_call["search_doc_ids"] == list(plan.id_map.values())
    assert rebuild_call["include_search"] is True
    assert rebuild_call["suppression_reason"] == "docs-copy-subtree"
    assert activity_calls == [
        (
            "docs-copy-subtree",
            {
                "source_scope": "source",
                "source_doc_id": "root",
                "target_scope": "target",
                "new_root_doc_id": plan.id_map["root"],
                "created_count": 4,
            },
        )
    ]
    target_front_matter = {
        path.stem: source_model.parse_source(path)[0]
        for path in (repo_root / "docs-viewer/source/target/documents").glob("*.md")
        if path.stem in set(plan.id_map.values())
    }
    assert set(target_front_matter) == set(plan.id_map.values())
    assert target_front_matter[plan.id_map["root"]]["parent_id"] == ""
    assert target_front_matter[plan.id_map["alpha"]]["parent_id"] == plan.id_map["root"]
    assert target_front_matter[plan.id_map["grand"]]["parent_id"] == plan.id_map["alpha"]
    assert target_front_matter[plan.id_map["beta"]]["parent_id"] == plan.id_map["root"]

    target_after = scope_snapshot(repo_root, "target")
    with pytest.raises(
        subtree_copy_apply.CopySubtreeTargetCollisionError,
        match="copy subtree target collision",
    ):
        subtree_copy_apply.apply_copy_subtree(
            repo_root,
            plan,
            confirm=True,
            perform_source_write_and_rebuild=lambda *_args, **_kwargs: pytest.fail(
                "collision must fail before coordinated write"
            ),
            activity_logger=lambda *_args, **_kwargs: pytest.fail(
                "collision must not log activity"
            ),
        )
    assert scope_snapshot(repo_root, "target") == target_after


def test_repeated_copy_subtree_is_additive(tmp_path: Path) -> None:
    repo_root = make_repo(tmp_path)
    source_before = scope_snapshot(repo_root, "source")

    def write_without_rebuild(_root, _scope, _paths, write, **_kwargs):
        write()
        return {"ok": True}

    first_plan = subtree_copy.plan_copy_subtree(
        repo_root,
        source_scope="source",
        source_doc_id="root",
        target_scope="target",
        copy_timestamp="2026-07-16 20:00:00",
        token_factory=sequential_tokens("bbbbbb", "cccccc", "dddddd", "eeeeee"),
    )
    first = subtree_copy_apply.apply_copy_subtree(
        repo_root,
        first_plan,
        confirm=True,
        perform_source_write_and_rebuild=write_without_rebuild,
        activity_logger=lambda *_args, **_kwargs: None,
    )
    second_plan = subtree_copy.plan_copy_subtree(
        repo_root,
        source_scope="source",
        source_doc_id="root",
        target_scope="target",
        copy_timestamp="2026-07-16 20:01:00",
        token_factory=sequential_tokens("aaaaaa", "bbbbbb", "cccccc", "dddddd"),
    )
    second = subtree_copy_apply.apply_copy_subtree(
        repo_root,
        second_plan,
        confirm=True,
        perform_source_write_and_rebuild=write_without_rebuild,
        activity_logger=lambda *_args, **_kwargs: None,
    )

    created_ids = [*first["created_doc_ids"], *second["created_doc_ids"]]
    assert len(created_ids) == len(set(created_ids)) == 8
    assert all((repo_root / f"docs-viewer/source/target/documents/{doc_id}.md").exists() for doc_id in created_ids)
    assert scope_snapshot(repo_root, "source") == source_before


def test_apply_copy_subtree_reports_rebuild_failure_without_activity(tmp_path: Path) -> None:
    repo_root = make_repo(tmp_path)
    plan = subtree_copy.plan_copy_subtree(
        repo_root,
        source_scope="source",
        source_doc_id="root",
        target_scope="target",
    )
    activity_calls: list[object] = []

    def failing_rebuild(_root, _scope, _paths, write, **_kwargs):
        write()
        raise RuntimeError("rebuild failed for target: simulated failure")

    with pytest.raises(RuntimeError, match="rebuild failed for target: simulated failure"):
        subtree_copy_apply.apply_copy_subtree(
            repo_root,
            plan,
            confirm=True,
            perform_source_write_and_rebuild=failing_rebuild,
            activity_logger=lambda *args, **_kwargs: activity_calls.append(args),
        )

    assert all(document.target_path.exists() for document in plan.documents)
    assert activity_calls == []


def test_apply_copy_subtree_builds_loadable_and_searchable_target_outputs(tmp_path: Path) -> None:
    repo_root = make_repo(tmp_path)
    write_site_tools_config(repo_root)
    write_semantic_reference_registry(repo_root)
    write_route_config(repo_root)
    plan = subtree_copy.plan_copy_subtree(
        repo_root,
        source_scope="source",
        source_doc_id="root",
        target_scope="target",
        copy_timestamp="2026-07-16 20:00:00",
        token_factory=sequential_tokens("bbbbbb", "cccccc", "dddddd", "eeeeee"),
    )

    def build_target(_root, scope, _paths, write, **_kwargs):
        write()
        config = subtree_copy.load_docs_scope_configs(repo_root)[scope]
        docs_result = build_docs.DocsDataBuilder(repo_root=repo_root, config=config).run(write=True)
        search_result = build_search.DocsViewerSearchDataBuilder(
            repo_root=repo_root,
            scope=scope,
        ).run(write=True, force=True)
        return {
            "ok": True,
            "docs_count": len(docs_result["index_payload"]["docs"]),
            "search_count": search_result["header"]["count"],
        }

    result = subtree_copy_apply.apply_copy_subtree(
        repo_root,
        plan,
        confirm=True,
        perform_source_write_and_rebuild=build_target,
        activity_logger=lambda *_args, **_kwargs: None,
    )

    output_root = repo_root / "docs-viewer/published/docs/target"
    tree_payload = json.loads((output_root / "index-tree.json").read_text(encoding="utf-8"))
    search_payload = json.loads(
        (repo_root / "docs-viewer/published/search/target/index.json").read_text(encoding="utf-8")
    )

    def tree_ids(records: list[dict[str, object]]) -> set[str]:
        ids: set[str] = set()
        for record in records:
            ids.add(str(record.get("doc_id") or ""))
            children = record.get("children")
            if isinstance(children, list):
                ids.update(tree_ids(children))
        return ids

    created_ids = set(result["created_doc_ids"])
    assert created_ids <= tree_ids(tree_payload["docs"])
    assert created_ids <= {str(entry["id"]) for entry in search_payload["entries"]}
    assert all((output_root / f"by-id/{doc_id}.json").exists() for doc_id in created_ids)
    assert result["rebuild"] == {"ok": True, "docs_count": 5, "search_count": 5}


def test_apply_copy_subtree_requires_confirmation_before_revalidation(tmp_path: Path) -> None:
    repo_root = make_repo(tmp_path)
    plan = subtree_copy.plan_copy_subtree(
        repo_root,
        source_scope="source",
        source_doc_id="root",
        target_scope="target",
    )

    with pytest.raises(ValueError, match="confirm must be true"):
        subtree_copy_apply.apply_copy_subtree(
            repo_root,
            plan,
            confirm=False,
            perform_source_write_and_rebuild=lambda *_args, **_kwargs: pytest.fail(
                "unconfirmed apply must not write"
            ),
            activity_logger=lambda *_args, **_kwargs: pytest.fail(
                "unconfirmed apply must not log"
            ),
        )


def test_apply_copy_subtree_rejects_changed_source_before_write(tmp_path: Path) -> None:
    repo_root = make_repo(tmp_path)
    plan = subtree_copy.plan_copy_subtree(
        repo_root,
        source_scope="source",
        source_doc_id="root",
        target_scope="target",
    )
    root_path = repo_root / "docs-viewer/source/source/documents/root.md"
    root_path.write_text(root_path.read_text(encoding="utf-8") + "Changed after preview.\n", encoding="utf-8")
    target_before = scope_snapshot(repo_root, "target")

    with pytest.raises(
        subtree_copy_apply.CopySubtreePlanStaleError,
        match="source content changed",
    ):
        subtree_copy_apply.apply_copy_subtree(
            repo_root,
            plan,
            confirm=True,
            perform_source_write_and_rebuild=lambda *_args, **_kwargs: pytest.fail(
                "stale source must fail before coordinated write"
            ),
            activity_logger=lambda *_args, **_kwargs: pytest.fail(
                "stale source must not log activity"
            ),
        )
    assert scope_snapshot(repo_root, "target") == target_before


def test_apply_copy_subtree_rejects_changed_descendant_set_before_write(tmp_path: Path) -> None:
    repo_root = make_repo(tmp_path)
    plan = subtree_copy.plan_copy_subtree(
        repo_root,
        source_scope="source",
        source_doc_id="root",
        target_scope="target",
    )
    write_doc(
        repo_root,
        "source",
        "new-child.md",
        doc_id="new-child",
        title="New Child",
        parent_id="root",
    )

    with pytest.raises(
        subtree_copy_apply.CopySubtreePlanStaleError,
        match="source subtree membership or order changed",
    ):
        subtree_copy_apply.apply_copy_subtree(
            repo_root,
            plan,
            confirm=True,
            perform_source_write_and_rebuild=lambda *_args, **_kwargs: pytest.fail(
                "changed subtree must fail before coordinated write"
            ),
            activity_logger=lambda *_args, **_kwargs: pytest.fail(
                "changed subtree must not log activity"
            ),
        )


def test_apply_copy_subtree_refuses_target_collision_without_overwrite(tmp_path: Path) -> None:
    repo_root = make_repo(tmp_path)
    plan = subtree_copy.plan_copy_subtree(
        repo_root,
        source_scope="source",
        source_doc_id="root",
        target_scope="target",
    )
    collision_path = plan.documents[0].target_path
    collision_path.write_text("sentinel\n", encoding="utf-8")

    with pytest.raises(
        subtree_copy_apply.CopySubtreeTargetCollisionError,
        match="copy subtree target collision",
    ):
        subtree_copy_apply.apply_copy_subtree(
            repo_root,
            plan,
            confirm=True,
            perform_source_write_and_rebuild=lambda *_args, **_kwargs: pytest.fail(
                "collision must fail before coordinated write"
            ),
            activity_logger=lambda *_args, **_kwargs: pytest.fail(
                "collision must not log activity"
            ),
        )
    assert collision_path.read_text(encoding="utf-8") == "sentinel\n"
    assert all(not document.target_path.exists() for document in plan.documents[1:])


def test_apply_copy_subtree_revalidates_planned_identity_and_filename(tmp_path: Path) -> None:
    repo_root = make_repo(tmp_path)
    plan = subtree_copy.plan_copy_subtree(
        repo_root,
        source_scope="source",
        source_doc_id="root",
        target_scope="target",
    )
    forged_document = replace(
        plan.documents[0],
        target_doc_id="not-an-immutable-id",
        target_path=plan.documents[0].target_path.with_name("not-an-immutable-id.md"),
    )
    forged_plan = replace(plan, documents=(forged_document, *plan.documents[1:]))

    with pytest.raises(
        subtree_copy_apply.CopySubtreePlanStaleError,
        match="planned target identity 'not-an-immutable-id' is invalid",
    ):
        subtree_copy_apply.apply_copy_subtree(
            repo_root,
            forged_plan,
            confirm=True,
            perform_source_write_and_rebuild=lambda *_args, **_kwargs: pytest.fail(
                "invalid identity must fail before coordinated write"
            ),
            activity_logger=lambda *_args, **_kwargs: pytest.fail(
                "invalid identity must not log activity"
            ),
        )


@pytest.mark.parametrize(
    ("source_scope", "source_doc_id", "target_scope", "message"),
    [
        ("missing", "root", "target", "source_scope 'missing' is not a configured Docs Viewer scope"),
        ("source", "root", "missing", "target_scope 'missing' is not a configured Docs Viewer scope"),
        ("source", "root", "source", "target_scope must differ from source_scope"),
        ("source", "", "target", "source_doc_id is required"),
    ],
)
def test_plan_copy_subtree_rejects_invalid_targets(
    tmp_path: Path,
    source_scope: str,
    source_doc_id: str,
    target_scope: str,
    message: str,
) -> None:
    repo_root = make_repo(tmp_path)

    with pytest.raises(ValueError, match=re.escape(message)):
        subtree_copy.plan_copy_subtree(
            repo_root,
            source_scope=source_scope,
            source_doc_id=source_doc_id,
            target_scope=target_scope,
        )


def test_plan_copy_subtree_rejects_missing_source_doc(tmp_path: Path) -> None:
    repo_root = make_repo(tmp_path)

    with pytest.raises(FileNotFoundError, match="doc 'missing' not found in scope source"):
        subtree_copy.plan_copy_subtree(
            repo_root,
            source_scope="source",
            source_doc_id="missing",
            target_scope="target",
        )


def test_plan_copy_subtree_rejects_unavailable_target_root(tmp_path: Path) -> None:
    repo_root = make_repo(tmp_path)
    target_root = repo_root / "docs-viewer/source/target/documents"
    for path in target_root.iterdir():
        path.unlink()
    target_root.rmdir()

    with pytest.raises(ValueError, match="source root for scope 'target' is unavailable"):
        subtree_copy.plan_copy_subtree(
            repo_root,
            source_scope="source",
            source_doc_id="root",
            target_scope="target",
        )


def test_plan_copy_subtree_rejects_unavailable_source_root(tmp_path: Path) -> None:
    repo_root = make_repo(tmp_path)
    source_root = repo_root / "docs-viewer/source/source/documents"
    for path in source_root.iterdir():
        path.unlink()
    source_root.rmdir()

    with pytest.raises(ValueError, match="source root for scope 'source' is unavailable"):
        subtree_copy.plan_copy_subtree(
            repo_root,
            source_scope="source",
            source_doc_id="root",
            target_scope="target",
        )


def test_plan_copy_subtree_rejects_non_writable_target_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = make_repo(tmp_path)
    target_root = (repo_root / "docs-viewer/source/target/documents").resolve()
    real_access = os.access

    def fake_access(path: os.PathLike[str] | str, mode: int) -> bool:
        if Path(path).resolve() == target_root and mode & os.W_OK:
            return False
        return real_access(path, mode)

    monkeypatch.setattr(subtree_copy.os, "access", fake_access)

    with pytest.raises(ValueError, match="target scope 'target' cannot accept managed canonical writes"):
        subtree_copy.plan_copy_subtree(
            repo_root,
            source_scope="source",
            source_doc_id="root",
            target_scope="target",
        )
