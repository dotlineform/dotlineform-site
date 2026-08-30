#!/usr/bin/env python3
"""Focused checks for target-first multi-document Move apply."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
DOCS_BUILD_DIR = REPO_ROOT / "docs-viewer" / "build"
for _path in (DOCS_SERVICES_DIR, DOCS_BUILD_DIR):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import build_docs  # noqa: E402
import build_search  # noqa: E402
import docs_artifact_locations as artifact_locations  # noqa: E402
import docs_document_move_apply as move_apply  # noqa: E402
import docs_document_transfer as transfer  # noqa: E402
import docs_source_model as source_model  # noqa: E402
import docs_scope_config  # noqa: E402
from test_docs_document_transfer_apply import (  # noqa: E402
    COPY_TIMESTAMP,
    add_mermaid_build,
    base_scope,
    build_source_path,
    local_documents_root,
    make_repo,
    media_path,
    write_bytes,
    write_doc,
    write_route_config,
    write_semantic_token_contract,
    write_site_tools_config,
)


def plan_move(
    repo_root: Path,
    requested_doc_ids: list[str],
) -> transfer.DocumentTransferPlan:
    plan = transfer.plan_document_transfer(
        repo_root,
        source_scope="source",
        requested_doc_ids=requested_doc_ids,
        target_scope="target",
        transfer_mode="move",
        include_descendants=False,
        operation_timestamp=COPY_TIMESTAMP,
    )
    assert plan.ok, plan.blockers
    return plan


def recording_rebuild(
    calls: list[dict[str, object]],
    *,
    before_write=None,
):
    def perform(
        _repo_root: Path,
        scope: str,
        changed_paths: list[Path],
        write_operation,
        **kwargs,
    ) -> dict[str, object]:
        if before_write is not None:
            before_write(scope)
        write_operation()
        calls.append(
            {
                "scope": scope,
                "changed_paths": list(changed_paths),
                "kwargs": kwargs,
            }
        )
        return {"ok": True, "scope": scope}

    return perform


def test_transform_move_preserves_identity_timestamps_and_forces_descendants(
    tmp_path: Path,
) -> None:
    repo_root = make_repo(tmp_path)
    source_root = local_documents_root(repo_root, "source")
    inline_mermaid = """```mermaid
flowchart LR
  accTitle: Move proof
  accDescr: Runtime Mermaid remains canonical source
  A --> B
```"""
    write_doc(
        source_root,
        doc_id="alpha",
        title="Alpha",
        parent_id="root",
        body=(
            "# Alpha\n\n"
            "[Grand](/docs/?scope=source&doc=grand#detail)\n"
            "[Outside](/docs/?scope=source&doc=beta)\n"
            "[[media:docs/source/img/photo.png Photo]]\n\n"
            f"{inline_mermaid}\n"
        ),
    )
    write_bytes(media_path(repo_root, "source", "img", "photo.png"), b"photo")

    plan = plan_move(repo_root, ["alpha"])
    transformed = move_apply.transform_document_move(plan)
    transformed_by_id = {
        item.planned_document.source_doc.doc_id: item
        for item in transformed.documents
    }

    assert plan.descendants_forced is True
    assert [item.source_doc.doc_id for item in plan.documents] == ["alpha", "grand"]
    assert plan.id_map == {"alpha": "alpha", "grand": "grand"}
    alpha_front_matter, alpha_body = source_model.parse_source_text(
        transformed_by_id["alpha"].source_text
    )
    grand_front_matter, _grand_body = source_model.parse_source_text(
        transformed_by_id["grand"].source_text
    )
    assert alpha_front_matter["doc_id"] == "alpha"
    assert alpha_front_matter["added_date"] == "2026-07-01 10:00:00"
    assert alpha_front_matter["last_updated"] == "2026-07-02 11:00:00"
    assert alpha_front_matter["parent_id"] == ""
    assert "publishable" not in alpha_front_matter
    assert grand_front_matter["parent_id"] == "alpha"
    assert "/docs/?scope=target&doc=grand#detail" in alpha_body
    assert "/docs/?scope=source&doc=beta" in alpha_body
    assert "[[media:docs/target/img/photo.png Photo]]" in alpha_body
    assert inline_mermaid in alpha_body
    assert transformed.viewer_link_rewrites == 1
    assert transformed.media_link_rewrites == 1


def test_apply_move_finishes_target_before_source_rebuild_and_exclusive_cleanup(
    tmp_path: Path,
) -> None:
    repo_root = make_repo(tmp_path)
    source_root = local_documents_root(repo_root, "source")
    write_doc(
        source_root,
        doc_id="alpha",
        title="Alpha",
        parent_id="root",
        body="# Alpha\n\n[[media:docs/source/img/photo.png Photo]]\n",
    )
    write_bytes(media_path(repo_root, "source", "img", "photo.png"), b"photo")
    plan = plan_move(repo_root, ["alpha"])
    calls: list[dict[str, object]] = []
    event_calls: list[tuple[object, ...]] = []

    def before_write(scope: str) -> None:
        if scope == "target":
            assert media_path(
                repo_root,
                "target",
                "img",
                "photo.png",
            ).read_bytes() == b"photo"
            assert (source_root / "alpha.md").is_file()
            assert not (local_documents_root(repo_root, "target") / "alpha.md").exists()
        else:
            assert (local_documents_root(repo_root, "target") / "alpha.md").is_file()
            assert (local_documents_root(repo_root, "target") / "grand.md").is_file()
            assert (source_root / "alpha.md").is_file()

    result = move_apply.apply_document_move(
        repo_root,
        plan,
        confirm=True,
        perform_source_write_and_rebuild=recording_rebuild(
            calls,
            before_write=before_write,
        ),
        event_logger=lambda *args, **_kwargs: event_calls.append(args),
    )

    assert [call["scope"] for call in calls] == ["target", "source"]
    assert all(call["kwargs"]["skip_media_builds"] is True for call in calls)
    assert result["moved_doc_ids"] == ["alpha", "grand"]
    assert all(
        call["kwargs"]["docs_doc_ids"] == result["moved_doc_ids"]
        for call in calls
    )
    assert calls[1]["kwargs"]["written_paths"] == []
    assert result["target_media_counts"] == {
        "created": 1,
        "reused": 0,
        "produced": 0,
    }
    assert result["removed_source_media"] == [
        {"media_type": "img", "identity": "photo.png"}
    ]
    assert result["retained_shared_source_media"] == []
    assert not (source_root / "alpha.md").exists()
    assert not (source_root / "grand.md").exists()
    assert not media_path(repo_root, "source", "img", "photo.png").exists()
    assert media_path(repo_root, "target", "img", "photo.png").is_file()
    assert len(event_calls) == 1


def test_apply_move_retains_source_media_referenced_outside_moved_set(
    tmp_path: Path,
) -> None:
    repo_root = make_repo(tmp_path)
    source_root = local_documents_root(repo_root, "source")
    token = "[[media:docs/source/img/shared.png Shared]]"
    write_doc(
        source_root,
        doc_id="alpha",
        title="Alpha",
        parent_id="root",
        body=f"# Alpha\n\n{token}\n",
    )
    write_doc(
        source_root,
        doc_id="other",
        title="Other",
        body=f"# Other\n\n{token}\n",
    )
    write_bytes(media_path(repo_root, "source", "img", "shared.png"), b"shared")
    plan = plan_move(repo_root, ["alpha"])
    assert plan.media[0].shared_outside_document_ids == ("other",)

    result = move_apply.apply_document_move(
        repo_root,
        plan,
        confirm=True,
        perform_source_write_and_rebuild=recording_rebuild([]),
        event_logger=lambda *_args, **_kwargs: None,
    )

    assert media_path(repo_root, "source", "img", "shared.png").is_file()
    assert media_path(repo_root, "target", "img", "shared.png").is_file()
    assert result["removed_source_media"] == []
    assert result["retained_shared_source_media"] == [
        {
            "media_type": "img",
            "identity": "shared.png",
            "outside_document_ids": ["other"],
        }
    ]


def test_apply_move_rechecks_remaining_references_before_media_cleanup(
    tmp_path: Path,
) -> None:
    repo_root = make_repo(tmp_path)
    source_root = local_documents_root(repo_root, "source")
    token = "[[media:docs/source/img/shared.png Shared]]"
    write_doc(
        source_root,
        doc_id="alpha",
        title="Alpha",
        parent_id="root",
        body=f"# Alpha\n\n{token}\n",
    )
    write_bytes(media_path(repo_root, "source", "img", "shared.png"), b"shared")
    plan = plan_move(repo_root, ["alpha"])
    assert plan.media[0].shared_outside_document_ids == ()

    def rebuild_with_concurrent_reference(
        _repo_root: Path,
        scope: str,
        _changed_paths: list[Path],
        write_operation,
        **_kwargs,
    ) -> dict[str, object]:
        write_operation()
        if scope == "source":
            write_doc(
                source_root,
                doc_id="other",
                title="Other",
                body=f"# Other\n\n{token}\n",
            )
        return {"ok": True, "scope": scope}

    result = move_apply.apply_document_move(
        repo_root,
        plan,
        confirm=True,
        perform_source_write_and_rebuild=rebuild_with_concurrent_reference,
        event_logger=lambda *_args, **_kwargs: None,
    )

    assert media_path(repo_root, "source", "img", "shared.png").is_file()
    assert result["retained_shared_source_media"] == [
        {
            "media_type": "img",
            "identity": "shared.png",
            "outside_document_ids": ["other"],
        }
    ]


def test_apply_move_target_rebuild_failure_leaves_source_complete(
    tmp_path: Path,
) -> None:
    repo_root = make_repo(tmp_path)
    source_root = local_documents_root(repo_root, "source")
    write_doc(
        source_root,
        doc_id="alpha",
        title="Alpha",
        parent_id="root",
        body="# Alpha\n\n[[media:docs/source/img/photo.png Photo]]\n",
    )
    write_bytes(media_path(repo_root, "source", "img", "photo.png"), b"photo")
    plan = plan_move(repo_root, ["alpha"])
    event_calls: list[tuple[object, ...]] = []

    def fail_target_rebuild(
        _repo_root: Path,
        _scope: str,
        _changed_paths: list[Path],
        write_operation,
        **_kwargs,
    ) -> dict[str, object]:
        write_operation()
        raise RuntimeError("simulated target rebuild failure")

    with pytest.raises(
        move_apply.DocumentMoveApplyError,
        match="target_documents_and_rebuild",
    ) as captured:
        move_apply.apply_document_move(
            repo_root,
            plan,
            confirm=True,
            perform_source_write_and_rebuild=fail_target_rebuild,
            event_logger=lambda *args, **_kwargs: event_calls.append(args),
        )

    failure = captured.value.result
    assert failure["target_media_complete"] is True
    assert failure["target_rebuild_complete"] is False
    assert failure["source_rebuild_complete"] is False
    assert [item["state"] for item in failure["target_state"]["documents"]] == [
        "exact",
        "exact",
    ]
    assert [item["state"] for item in failure["source_state"]["documents"]] == [
        "exact",
        "exact",
    ]
    assert failure["source_state"]["media"][0]["state"] == "exact"
    assert event_calls == []


def test_apply_move_source_rebuild_failure_reports_both_canonical_copies(
    tmp_path: Path,
) -> None:
    repo_root = make_repo(tmp_path)
    source_root = local_documents_root(repo_root, "source")
    write_doc(
        source_root,
        doc_id="alpha",
        title="Alpha",
        parent_id="root",
        body="# Alpha\n\n[[media:docs/source/img/photo.png Photo]]\n",
    )
    write_bytes(media_path(repo_root, "source", "img", "photo.png"), b"photo")
    plan = plan_move(repo_root, ["alpha"])
    call_count = 0

    def fail_source_rebuild(
        _repo_root: Path,
        _scope: str,
        _changed_paths: list[Path],
        write_operation,
        **_kwargs,
    ) -> dict[str, object]:
        nonlocal call_count
        call_count += 1
        write_operation()
        if call_count == 2:
            raise RuntimeError("simulated source rebuild failure")
        return {"ok": True}

    with pytest.raises(
        move_apply.DocumentMoveApplyError,
        match="source_documents_and_rebuild",
    ) as captured:
        move_apply.apply_document_move(
            repo_root,
            plan,
            confirm=True,
            perform_source_write_and_rebuild=fail_source_rebuild,
            event_logger=lambda *_args, **_kwargs: None,
        )

    failure = captured.value.result
    assert failure["target_rebuild_complete"] is True
    assert failure["source_rebuild_complete"] is False
    assert [item["state"] for item in failure["target_state"]["documents"]] == [
        "exact",
        "exact",
    ]
    assert [item["state"] for item in failure["source_state"]["documents"]] == [
        "missing",
        "missing",
    ]
    assert failure["source_state"]["media"][0]["state"] == "exact"


def test_apply_move_media_cleanup_failure_reports_partial_source_cleanup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = make_repo(tmp_path)
    source_root = local_documents_root(repo_root, "source")
    write_doc(
        source_root,
        doc_id="alpha",
        title="Alpha",
        parent_id="root",
        body=(
            "# Alpha\n\n"
            "[[media:docs/source/img/one.png One]]\n"
            "[[media:docs/source/img/two.png Two]]\n"
        ),
    )
    write_bytes(media_path(repo_root, "source", "img", "one.png"), b"one")
    write_bytes(media_path(repo_root, "source", "img", "two.png"), b"two")
    plan = plan_move(repo_root, ["alpha"])
    original_delete = artifact_locations.FilesystemArtifactLocationAdapter.delete

    def fail_second_cleanup(self, identity) -> None:
        if str(identity) == "two.png":
            raise RuntimeError("simulated media cleanup failure")
        original_delete(self, identity)

    monkeypatch.setattr(
        artifact_locations.FilesystemArtifactLocationAdapter,
        "delete",
        fail_second_cleanup,
    )

    with pytest.raises(
        move_apply.DocumentMoveApplyError,
        match="source_media_cleanup",
    ) as captured:
        move_apply.apply_document_move(
            repo_root,
            plan,
            confirm=True,
            perform_source_write_and_rebuild=recording_rebuild([]),
            event_logger=lambda *_args, **_kwargs: None,
        )

    failure = captured.value.result
    assert failure["target_rebuild_complete"] is True
    assert failure["source_rebuild_complete"] is True
    assert failure["source_media_cleanup_complete"] is False
    assert [item["state"] for item in failure["source_state"]["documents"]] == [
        "missing",
        "missing",
    ]
    assert [
        (item["identity"], item["state"])
        for item in failure["source_state"]["media"]
    ] == [("one.png", "missing"), ("two.png", "exact")]
    assert all(
        item["state"] == "exact"
        for item in failure["target_state"]["media"]
    )


def test_apply_move_removes_exclusive_mermaid_source_and_output_after_rebuild(
    tmp_path: Path,
) -> None:
    source_scope = base_scope("source", media_types=("svg",))
    target_scope = base_scope("target", media_types=("svg",))
    add_mermaid_build(source_scope)
    add_mermaid_build(target_scope)
    repo_root = make_repo(
        tmp_path,
        source_scope=source_scope,
        target_scope=target_scope,
    )
    inline_mermaid = """```mermaid
flowchart LR
  accTitle: Inline source
  accDescr: Runtime Mermaid remains source text
  A --> B
```"""
    write_doc(
        local_documents_root(repo_root, "source"),
        doc_id="alpha",
        title="Alpha",
        parent_id="root",
        body=(
            "# Alpha\n\n"
            "[[media:docs/source/svg/diagram.svg Diagram]]\n\n"
            f"{inline_mermaid}\n"
        ),
    )
    write_bytes(
        build_source_path(repo_root, "source", "mermaid", "diagram.mmd"),
        b"flowchart LR\n  A --> B\n",
    )
    write_bytes(media_path(repo_root, "source", "svg", "diagram.svg"), b"source-svg")
    plan = plan_move(repo_root, ["alpha"])

    def media_builder(
        _repo_root: Path,
        config,
        **kwargs,
    ) -> list[dict[str, object]]:
        assert config.scope_id == "target"
        assert kwargs["replace_existing"] is False
        write_bytes(
            media_path(repo_root, "target", "svg", "diagram.svg"),
            b"produced-svg",
        )
        return [{"build_type": "mermaid", "output_identities": ["diagram.svg"]}]

    result = move_apply.apply_document_move(
        repo_root,
        plan,
        confirm=True,
        media_builder=media_builder,
        perform_source_write_and_rebuild=recording_rebuild([]),
        event_logger=lambda *_args, **_kwargs: None,
    )

    target_doc = local_documents_root(repo_root, "target") / "alpha.md"
    _front_matter, target_body = source_model.parse_source(target_doc)
    assert "[[media:docs/target/svg/diagram.svg Diagram]]" in target_body
    assert inline_mermaid in target_body
    assert result["target_media_counts"] == {
        "created": 0,
        "reused": 0,
        "produced": 1,
    }
    assert result["removed_source_build_sources"] == [
        {"build_type": "mermaid", "identity": "diagram.mmd"}
    ]
    assert not build_source_path(
        repo_root,
        "source",
        "mermaid",
        "diagram.mmd",
    ).exists()
    assert not media_path(repo_root, "source", "svg", "diagram.svg").exists()
    assert build_source_path(
        repo_root,
        "target",
        "mermaid",
        "diagram.mmd",
    ).is_file()


def test_apply_move_rebuilds_loadable_target_and_removes_source_outputs(
    tmp_path: Path,
) -> None:
    repo_root = make_repo(tmp_path)
    write_site_tools_config(repo_root)
    write_semantic_token_contract(repo_root)
    write_route_config(repo_root)
    source_root = local_documents_root(repo_root, "source")
    for path in source_root.glob("*.md"):
        path.unlink()
    root_id = "d-20260701-100000-aaaaaa"
    alpha_id = "d-20260701-100001-bbbbbb"
    grand_id = "d-20260701-100002-cccccc"
    write_doc(source_root, doc_id=root_id, title="Root")
    write_doc(
        source_root,
        doc_id=alpha_id,
        title="Alpha",
        parent_id=root_id,
    )
    write_doc(
        source_root,
        doc_id=grand_id,
        title="Grand",
        parent_id=alpha_id,
    )
    plan = plan_move(repo_root, [alpha_id])
    configs = docs_scope_config.load_docs_scope_configs(repo_root)
    build_docs.DocsDataBuilder(
        repo_root=repo_root,
        config=configs["source"],
        skip_media_builds=True,
    ).run(write=True)
    build_search.DocsViewerSearchDataBuilder(
        repo_root=repo_root,
        scope="source",
    ).run(write=True, force=True)
    rebuild_scopes: list[str] = []

    def build_scope(
        _repo_root: Path,
        scope: str,
        _changed_paths: list[Path],
        write_operation,
        **kwargs,
    ) -> dict[str, object]:
        assert kwargs["skip_media_builds"] is True
        write_operation()
        current_config = docs_scope_config.load_docs_scope_configs(repo_root)[scope]
        docs_result = build_docs.DocsDataBuilder(
            repo_root=repo_root,
            config=current_config,
            skip_media_builds=True,
        ).run(write=True)
        search_result = build_search.DocsViewerSearchDataBuilder(
            repo_root=repo_root,
            scope=scope,
        ).run(write=True, force=True)
        rebuild_scopes.append(scope)
        return {
            "ok": True,
            "docs_count": len(docs_result["index_payload"]["docs"]),
            "search_count": search_result["header"]["count"],
        }

    result = move_apply.apply_document_move(
        repo_root,
        plan,
        confirm=True,
        perform_source_write_and_rebuild=build_scope,
        event_logger=lambda *_args, **_kwargs: None,
    )

    moved_ids = set(result["moved_doc_ids"])
    target_output = repo_root / "docs-viewer/scopes/target/generated/documents"
    source_output = repo_root / "docs-viewer/scopes/source/generated/documents"
    target_search = json.loads(
        (
            repo_root / "docs-viewer/scopes/target/generated/search/index.json"
        ).read_text(encoding="utf-8")
    )
    source_search = json.loads(
        (
            repo_root / "docs-viewer/scopes/source/generated/search/index.json"
        ).read_text(encoding="utf-8")
    )

    assert rebuild_scopes == ["target", "source"]
    assert all(
        (target_output / f"by-id/{doc_id}.json").is_file()
        for doc_id in moved_ids
    )
    assert all(
        not (source_output / f"by-id/{doc_id}.json").exists()
        for doc_id in moved_ids
    )
    assert moved_ids <= {
        str(document["id"]) for document in target_search["docs"]
    }
    assert moved_ids.isdisjoint(
        {str(document["id"]) for document in source_search["docs"]}
    )


def test_apply_move_writes_external_local_target_then_cleans_repository_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    projects_base = tmp_path / "Projects"
    monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(projects_base))
    repo_root = make_repo(
        tmp_path,
        source_scope=base_scope("source", media_types=("img",)),
        target_scope=base_scope(
            "target",
            scope_type="local_external",
            scope_root_provider="external_local",
            media_types=("img",),
        ),
    )
    external_root = projects_base / "docs-viewer/scopes/target"
    (external_root / "source/documents").mkdir(parents=True, exist_ok=True)
    write_doc(
        local_documents_root(repo_root, "source"),
        doc_id="alpha",
        title="Alpha",
        parent_id="root",
        body="# Alpha\n\n[[media:docs/source/img/photo.png Photo]]\n",
    )
    write_bytes(media_path(repo_root, "source", "img", "photo.png"), b"photo")
    plan = plan_move(repo_root, ["alpha"])

    result = move_apply.apply_document_move(
        repo_root,
        plan,
        confirm=True,
        perform_source_write_and_rebuild=recording_rebuild([]),
        event_logger=lambda *_args, **_kwargs: None,
    )

    assert result["moved_doc_ids"] == ["alpha", "grand"]
    assert (external_root / "source/documents/alpha.md").is_file()
    assert (external_root / "source/documents/grand.md").is_file()
    assert (
        projects_base / "docs-viewer/scopes/target/source/media/img/photo.png"
    ).read_bytes() == b"photo"
    assert not (
        local_documents_root(repo_root, "source") / "alpha.md"
    ).exists()
