#!/usr/bin/env python3
"""Focused checks for selection-aware document Copy apply."""

from __future__ import annotations

import json
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

from repo_factory import docs_scope_record, docs_sub_scope_record


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
DOCS_BUILD_DIR = REPO_ROOT / "docs-viewer" / "build"
for _path in (DOCS_SERVICES_DIR, DOCS_BUILD_DIR):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import docs_document_transfer as transfer  # noqa: E402
import docs_document_transfer_apply as transfer_apply  # noqa: E402
import docs_artifact_locations as artifact_locations  # noqa: E402
import docs_source_model as source_model  # noqa: E402
import docs_scope_config  # noqa: E402
import build_docs  # noqa: E402
import build_search  # noqa: E402
from build_docs_test_support import (  # noqa: E402
    write_route_config,
    write_semantic_token_contract,
    write_site_tools_config,
)
from test_docs_document_transfer import (  # noqa: E402
    make_collection_repo,
    sub_scope_documents_root,
)


COPY_TIMESTAMP = "2026-07-24 14:00:00"


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_doc(
    documents_root: Path,
    *,
    doc_id: str,
    title: str,
    parent_id: str = "",
    body: str = "",
) -> Path:
    documents_root.mkdir(parents=True, exist_ok=True)
    path = documents_root / f"{doc_id}.md"
    path.write_text(
        source_model.format_source(
            {
                "doc_id": doc_id,
                "title": title,
                "added_date": "2026-07-01 10:00:00",
                "last_updated": "2026-07-02 11:00:00",
                "parent_id": parent_id,
            },
            body or f"# {title}\n",
        ),
        encoding="utf-8",
    )
    return path


def local_documents_root(repo_root: Path, scope: str) -> Path:
    return repo_root / "docs-viewer/scopes" / scope / "source/documents"


def media_path(
    repo_root: Path,
    scope: str,
    media_type: str,
    identity: str,
) -> Path:
    return (
        repo_root
        / "docs-viewer/scopes"
        / scope
        / "published/media"
        / media_type
        / identity
    )


def build_source_path(
    repo_root: Path,
    scope: str,
    build_type: str,
    identity: str,
) -> Path:
    return (
        repo_root
        / "docs-viewer/scopes"
        / scope
        / "source/media"
        / build_type
        / identity
    )


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def base_scope(
    scope: str,
    *,
    scope_type: str = "local",
    media_types: tuple[str, ...] = ("img", "svg", "files"),
) -> dict[str, object]:
    return docs_scope_record(
        scope,
        scope_type=scope_type,
        viewer_base_url="/docs/",
        include_scope_param=True,
        media_types=media_types,
    )


def add_mermaid_build(scope: dict[str, object]) -> None:
    source = scope["source"]
    published = scope["published"]
    assert isinstance(source, dict)
    assert isinstance(published, dict)
    media = published["media"]
    assert isinstance(media, dict)
    svg = media["svg"]
    assert isinstance(svg, dict)
    source["build_media"] = {
        "mermaid": {
            "path": "media/mermaid",
            "producer": "mermaid",
            "publishes_to": "svg",
        }
    }
    svg["build_inputs"] = ["mermaid"]


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
            "schema_version": "docs_scopes_v3",
            "scopes": [
                source_scope or base_scope("source"),
                target_scope or base_scope("target"),
            ],
        },
    )
    source_root = local_documents_root(repo_root, "source")
    write_doc(source_root, doc_id="root", title="Root")
    write_doc(source_root, doc_id="alpha", title="Alpha", parent_id="root")
    write_doc(source_root, doc_id="grand", title="Grand", parent_id="alpha")
    write_doc(source_root, doc_id="beta", title="Beta", parent_id="root")
    write_doc(source_root, doc_id="other", title="Other")
    local_documents_root(repo_root, "target").mkdir(parents=True, exist_ok=True)
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


def fake_rebuild(
    calls: list[dict[str, object]],
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
            before_write()
        write_operation()
        calls.append(
            {
                "scope": scope,
                "changed_paths": list(changed_paths),
                "kwargs": kwargs,
            }
        )
        return {"ok": True, "call": len(calls)}

    return perform


def fake_sub_scope_rebuild(calls: list[dict[str, object]]):
    def perform(
        _repo_root: Path,
        scope: str,
        sub_scope: str,
        changed_paths: list[Path],
        write_operation,
        **kwargs,
    ) -> dict[str, object]:
        write_operation()
        calls.append(
            {
                "scope": scope,
                "sub_scope": sub_scope,
                "changed_paths": list(changed_paths),
                "kwargs": kwargs,
            }
        )
        return {"ok": True, "mode": "sub_scope", "sub_scope": sub_scope}

    return perform


def test_transform_copy_preserves_selected_hierarchy_and_rewrites_owned_links(
    tmp_path: Path,
) -> None:
    repo_root = make_repo(tmp_path)
    source_root = local_documents_root(repo_root, "source")
    inline_mermaid = """```mermaid
flowchart LR
  accTitle: Copy proof
  accDescr: Inline Mermaid remains canonical source
  A --> B
```"""
    write_doc(
        source_root,
        doc_id="alpha",
        title="Alpha",
        parent_id="root",
        body=f"""# Alpha

[Grand](/docs/?scope=source&doc=grand#detail)
[Beta](/docs/?scope=source&doc=beta)
[Outside](/docs/?scope=source&doc=other)
[[media:docs/source/img/shared.png Shared]]
![Shared](/docs/media/source/img/shared.png?v=1)

{inline_mermaid}
""",
    )
    write_bytes(media_path(repo_root, "source", "img", "shared.png"), b"shared")

    plan = transfer.plan_document_transfer(
        repo_root,
        source_scope="source",
        requested_doc_ids=["beta", "grand", "alpha"],
        target_scope="target",
        transfer_mode="copy",
        operation_timestamp=COPY_TIMESTAMP,
        token_factory=sequential_tokens("aaaaaa", "bbbbbb", "cccccc"),
    )
    transformed = transfer_apply.transform_document_copy(plan)
    transformed_by_source = {
        item.planned_document.source_doc.doc_id: item
        for item in transformed.documents
    }

    assert plan.id_map == {
        "alpha": "d-20260724-140000-aaaaaa",
        "grand": "d-20260724-140000-bbbbbb",
        "beta": "d-20260724-140000-cccccc",
    }
    assert plan.documents[0].target_parent_id == ""
    assert plan.documents[1].target_parent_id == plan.id_map["alpha"]
    assert plan.documents[2].target_parent_id == ""
    alpha = transformed_by_source["alpha"]
    front_matter, body = source_model.parse_source_text(alpha.source_text)
    assert front_matter["doc_id"] == plan.id_map["alpha"]
    assert front_matter["added_date"] == COPY_TIMESTAMP
    assert front_matter["last_updated"] == COPY_TIMESTAMP
    assert "publishable" not in front_matter
    assert (
        f"/docs/?scope=target&doc={plan.id_map['grand']}#detail"
        in body
    )
    assert f"/docs/?scope=target&doc={plan.id_map['beta']}" in body
    assert "/docs/?scope=source&doc=other" in body
    assert "[[media:docs/target/img/shared.png Shared]]" in body
    assert "/docs/media/target/img/shared.png?v=1" in body
    assert inline_mermaid in body
    assert transformed.viewer_link_rewrites == 2
    assert transformed.media_link_rewrites == 2


def test_restore_receipt_revalidates_exact_plan_and_rejects_source_change(
    tmp_path: Path,
) -> None:
    repo_root = make_repo(tmp_path)
    plan = transfer.plan_document_transfer(
        repo_root,
        source_scope="source",
        requested_doc_ids=["alpha"],
        target_scope="target",
        transfer_mode="copy",
        include_descendants=True,
        operation_timestamp=COPY_TIMESTAMP,
        token_factory=sequential_tokens("aaaaaa", "bbbbbb"),
    )
    receipt = plan.apply_plan_payload()

    restored = transfer.restore_document_transfer_apply_plan(repo_root, receipt)
    assert restored.apply_plan_payload() == receipt

    write_doc(
        local_documents_root(repo_root, "source"),
        doc_id="grand",
        title="Grand",
        parent_id="alpha",
        body="# Grand changed\n",
    )
    with pytest.raises(ValueError, match="document transfer preview is stale"):
        transfer.restore_document_transfer_apply_plan(repo_root, receipt)
    assert not any(local_documents_root(repo_root, "target").glob("*.md"))


def test_apply_copy_transfers_shared_media_once_and_repeated_copy_reuses_it(
    tmp_path: Path,
) -> None:
    repo_root = make_repo(tmp_path)
    source_root = local_documents_root(repo_root, "source")
    media_token = "[[media:docs/source/img/shared.png Shared]]"
    write_doc(
        source_root,
        doc_id="alpha",
        title="Alpha",
        parent_id="root",
        body=f"# Alpha\n\n{media_token}\n[Beta](/docs/?scope=source&doc=beta)\n",
    )
    write_doc(
        source_root,
        doc_id="beta",
        title="Beta",
        parent_id="root",
        body=f"# Beta\n\n{media_token}\n",
    )
    write_bytes(media_path(repo_root, "source", "img", "shared.png"), b"shared")
    source_before = snapshot(repo_root / "docs-viewer/scopes/source")
    rebuild_calls: list[dict[str, object]] = []

    plan = transfer.plan_document_transfer(
        repo_root,
        source_scope="source",
        requested_doc_ids=["alpha", "beta"],
        target_scope="target",
        transfer_mode="copy",
        operation_timestamp=COPY_TIMESTAMP,
        token_factory=sequential_tokens("aaaaaa", "bbbbbb"),
    )

    def before_first_write() -> None:
        assert media_path(
            repo_root,
            "target",
            "img",
            "shared.png",
        ).read_bytes() == b"shared"
        assert not any(local_documents_root(repo_root, "target").glob("*.md"))

    result = transfer_apply.apply_document_copy(
        repo_root,
        plan,
        confirm=True,
        perform_source_write_and_rebuild=fake_rebuild(
            rebuild_calls,
            before_first_write,
        ),
        activity_logger=lambda *_args, **_kwargs: None,
    )

    assert result["created_doc_ids"] == [
        "d-20260724-140000-aaaaaa",
        "d-20260724-140000-bbbbbb",
    ]
    assert result["document_count"] == 2
    assert result["unique_media_count"] == 1
    assert result["media_counts"] == {"created": 1, "reused": 0, "produced": 0}
    assert result["viewer_link_rewrites"] == 1
    assert result["media_link_rewrites"] == 2
    assert len(result["effective_roots"]) == 2
    assert rebuild_calls[0]["scope"] == "target"
    assert rebuild_calls[0]["kwargs"]["skip_media_builds"] is True
    assert rebuild_calls[0]["kwargs"]["docs_doc_ids"] == result["created_doc_ids"]
    assert snapshot(repo_root / "docs-viewer/scopes/source") == source_before

    second_plan = transfer.plan_document_transfer(
        repo_root,
        source_scope="source",
        requested_doc_ids=["alpha", "beta"],
        target_scope="target",
        transfer_mode="copy",
        operation_timestamp="2026-07-24 14:00:01",
        token_factory=sequential_tokens("cccccc", "dddddd"),
    )
    second = transfer_apply.apply_document_copy(
        repo_root,
        second_plan,
        confirm=True,
        perform_source_write_and_rebuild=fake_rebuild(rebuild_calls),
        activity_logger=lambda *_args, **_kwargs: None,
    )

    assert second["media_counts"] == {"created": 0, "reused": 1, "produced": 0}
    assert len(list(local_documents_root(repo_root, "target").glob("*.md"))) == 4
    assert media_path(
        repo_root,
        "target",
        "img",
        "shared.png",
    ).read_bytes() == b"shared"
    assert snapshot(repo_root / "docs-viewer/scopes/source") == source_before


def test_apply_copy_builds_loadable_target_documents_and_search_once(
    tmp_path: Path,
) -> None:
    repo_root = make_repo(tmp_path)
    write_site_tools_config(repo_root)
    write_semantic_token_contract(repo_root)
    write_route_config(repo_root)
    write_doc(
        local_documents_root(repo_root, "source"),
        doc_id="alpha",
        title="Alpha",
        parent_id="root",
        body="# Alpha\n\n[Beta](/docs/?scope=source&doc=beta)\n",
    )
    plan = transfer.plan_document_transfer(
        repo_root,
        source_scope="source",
        requested_doc_ids=["alpha", "beta"],
        target_scope="target",
        transfer_mode="copy",
        operation_timestamp=COPY_TIMESTAMP,
        token_factory=sequential_tokens("aaaaaa", "bbbbbb"),
    )
    rebuild_calls = 0

    def build_target(
        _repo_root: Path,
        scope: str,
        _paths: list[Path],
        write_operation,
        **kwargs,
    ) -> dict[str, object]:
        nonlocal rebuild_calls
        rebuild_calls += 1
        assert kwargs["skip_media_builds"] is True
        write_operation()
        config = docs_scope_config.load_docs_scope_configs(repo_root)[scope]
        docs_result = build_docs.DocsDataBuilder(
            repo_root=repo_root,
            config=config,
            skip_media_builds=True,
        ).run(write=True)
        search_result = build_search.DocsViewerSearchDataBuilder(
            repo_root=repo_root,
            scope=scope,
        ).run(write=True, force=True)
        return {
            "ok": True,
            "docs_count": len(docs_result["index_payload"]["docs"]),
            "search_count": search_result["header"]["count"],
        }

    result = transfer_apply.apply_document_copy(
        repo_root,
        plan,
        confirm=True,
        perform_source_write_and_rebuild=build_target,
        activity_logger=lambda *_args, **_kwargs: None,
    )

    output_root = repo_root / "docs-viewer/scopes/target/published/documents"
    tree_payload = json.loads(
        (output_root / "index-tree.json").read_text(encoding="utf-8")
    )
    search_payload = json.loads(
        (
            repo_root
            / "docs-viewer/scopes/target/published/search/index.json"
        ).read_text(encoding="utf-8")
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
    assert rebuild_calls == 1
    assert created_ids <= tree_ids(tree_payload["docs"])
    assert created_ids <= {
        str(entry["id"]) for entry in search_payload["entries"]
    }
    assert all(
        (output_root / f"by-id/{doc_id}.json").is_file()
        for doc_id in created_ids
    )
    assert result["rebuild"] == {
        "ok": True,
        "docs_count": 2,
        "search_count": 2,
    }


def test_apply_copy_preserves_mermaid_source_and_produces_absent_svg_before_docs(
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
  accDescr: Inline source stays in the copied document
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
    source_mermaid = b"""flowchart LR
  accTitle: Built diagram
  accDescr: Canonical build source is copied before production
  A --> B
"""
    write_bytes(
        build_source_path(repo_root, "source", "mermaid", "diagram.mmd"),
        source_mermaid,
    )
    write_bytes(media_path(repo_root, "source", "svg", "diagram.svg"), b"source-svg")
    rebuild_calls: list[dict[str, object]] = []
    media_builder_calls: list[dict[str, object]] = []

    plan = transfer.plan_document_transfer(
        repo_root,
        source_scope="source",
        requested_doc_ids=["alpha"],
        target_scope="target",
        transfer_mode="copy",
        operation_timestamp=COPY_TIMESTAMP,
        token_factory=sequential_tokens("aaaaaa"),
    )
    assert plan.media[0].target_status == "produce"
    assert plan.media[0].build_sources[0].target_status == "create"

    def media_builder(
        _repo_root: Path,
        config,
        **kwargs,
    ) -> list[dict[str, object]]:
        assert config.scope_id == "target"
        assert kwargs["replace_existing"] is False
        assert kwargs["requested_published_identities"] == {
            "mermaid": {"diagram.svg"}
        }
        assert build_source_path(
            repo_root,
            "target",
            "mermaid",
            "diagram.mmd",
        ).read_bytes() == source_mermaid
        assert not any(local_documents_root(repo_root, "target").glob("*.md"))
        write_bytes(
            media_path(repo_root, "target", "svg", "diagram.svg"),
            b"produced-svg",
        )
        media_builder_calls.append(kwargs)
        return [{"build_type": "mermaid", "output_identities": ["diagram.svg"]}]

    def before_document_write() -> None:
        assert media_path(
            repo_root,
            "target",
            "svg",
            "diagram.svg",
        ).read_bytes() == b"produced-svg"

    result = transfer_apply.apply_document_copy(
        repo_root,
        plan,
        confirm=True,
        media_builder=media_builder,
        perform_source_write_and_rebuild=fake_rebuild(
            rebuild_calls,
            before_document_write,
        ),
        activity_logger=lambda *_args, **_kwargs: None,
    )

    assert len(media_builder_calls) == 1
    assert result["media_counts"] == {"created": 0, "reused": 0, "produced": 1}
    assert result["build_source_counts"] == {"created": 1, "reused": 0}
    copied_path = local_documents_root(repo_root, "target") / (
        f"{result['created_doc_ids'][0]}.md"
    )
    _front_matter, copied_body = source_model.parse_source(copied_path)
    assert "[[media:docs/target/svg/diagram.svg Diagram]]" in copied_body
    assert inline_mermaid in copied_body
    assert rebuild_calls[0]["kwargs"]["skip_media_builds"] is True


def test_apply_copy_reports_exact_partial_target_after_document_write_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
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
        doc_id="beta",
        title="Beta",
        parent_id="root",
        body="# Beta\n",
    )
    write_bytes(media_path(repo_root, "source", "img", "shared.png"), b"shared")
    plan = transfer.plan_document_transfer(
        repo_root,
        source_scope="source",
        requested_doc_ids=["alpha", "beta"],
        target_scope="target",
        transfer_mode="copy",
        operation_timestamp=COPY_TIMESTAMP,
        token_factory=sequential_tokens("aaaaaa", "bbbbbb"),
    )
    original_write = transfer_apply.source_model.write_text_atomic_new
    writes = 0

    def fail_second_write(path: Path, text: str) -> None:
        nonlocal writes
        writes += 1
        if writes == 2:
            raise RuntimeError("simulated second document write failure")
        original_write(path, text)

    monkeypatch.setattr(
        transfer_apply.source_model,
        "write_text_atomic_new",
        fail_second_write,
    )
    activity_calls: list[object] = []

    with pytest.raises(
        transfer_apply.DocumentTransferApplyError,
        match="documents_and_rebuild",
    ) as captured:
        transfer_apply.apply_document_copy(
            repo_root,
            plan,
            confirm=True,
            perform_source_write_and_rebuild=fake_rebuild([]),
            activity_logger=lambda *args, **_kwargs: activity_calls.append(args),
        )

    failure = captured.value.result
    assert failure["ok"] is False
    assert failure["phase"] == "documents_and_rebuild"
    assert failure["media_complete"] is True
    assert failure["rebuild_complete"] is False
    assert failure["target_state"]["media"] == [
        {
            "media_type": "img",
            "identity": "shared.png",
            "planned_status": "create",
            "state": "exact",
            "size": 6,
            "sha256": transfer_apply._sha256(b"shared"),
        }
    ]
    assert [
        item["state"] for item in failure["target_state"]["documents"]
    ] == ["exact", "missing"]
    assert activity_calls == []


def test_apply_copy_reports_exact_partial_target_after_media_write_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = make_repo(tmp_path)
    write_doc(
        local_documents_root(repo_root, "source"),
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
    plan = transfer.plan_document_transfer(
        repo_root,
        source_scope="source",
        requested_doc_ids=["alpha"],
        target_scope="target",
        transfer_mode="copy",
        operation_timestamp=COPY_TIMESTAMP,
        token_factory=sequential_tokens("aaaaaa"),
    )
    original_write = artifact_locations.FilesystemArtifactLocationAdapter.write

    def fail_second_media(self, identity, data, *, content_type=""):
        if str(identity) == "two.png":
            raise RuntimeError("simulated media write failure")
        return original_write(self, identity, data, content_type=content_type)

    monkeypatch.setattr(
        artifact_locations.FilesystemArtifactLocationAdapter,
        "write",
        fail_second_media,
    )

    with pytest.raises(
        transfer_apply.DocumentTransferApplyError,
        match="during media",
    ) as captured:
        transfer_apply.apply_document_copy(
            repo_root,
            plan,
            confirm=True,
            perform_source_write_and_rebuild=fake_rebuild([]),
            activity_logger=lambda *_args, **_kwargs: None,
        )

    failure = captured.value.result
    assert failure["media_complete"] is False
    assert [
        (item["identity"], item["state"])
        for item in failure["target_state"]["media"]
    ] == [("one.png", "exact"), ("two.png", "missing")]
    assert failure["target_state"]["documents"][0]["state"] == "missing"


def test_apply_copy_writes_external_local_target_documents_and_media(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    projects_base = tmp_path / "Projects"
    monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(projects_base))
    target_scope = base_scope(
        "target",
        scope_type="local_external",
        media_types=("img",),
    )
    repo_root = make_repo(
        tmp_path,
        source_scope=base_scope("source", media_types=("img",)),
        target_scope=target_scope,
    )
    external_root = projects_base / "docs-viewer/scopes/target"
    external_documents = external_root / "source/documents"
    external_documents.mkdir(parents=True, exist_ok=True)
    write_doc(
        local_documents_root(repo_root, "source"),
        doc_id="alpha",
        title="Alpha",
        parent_id="root",
        body="# Alpha\n\n[[media:docs/source/img/photo.png Photo]]\n",
    )
    write_bytes(media_path(repo_root, "source", "img", "photo.png"), b"photo")
    plan = transfer.plan_document_transfer(
        repo_root,
        source_scope="source",
        requested_doc_ids=["alpha"],
        target_scope="target",
        transfer_mode="copy",
        operation_timestamp=COPY_TIMESTAMP,
        token_factory=sequential_tokens("aaaaaa"),
    )

    result = transfer_apply.apply_document_copy(
        repo_root,
        plan,
        confirm=True,
        perform_source_write_and_rebuild=fake_rebuild([]),
        activity_logger=lambda *_args, **_kwargs: None,
    )

    copied_path = external_documents / f"{result['created_doc_ids'][0]}.md"
    assert copied_path.is_file()
    assert (
        external_root / "published/media/img/photo.png"
    ).read_bytes() == b"photo"
    assert "docs/target/img/photo.png" in copied_path.read_text(encoding="utf-8")


def test_apply_child_to_child_copy_uses_exact_transform_rebuild_and_result(
    tmp_path: Path,
) -> None:
    repo_root = make_collection_repo(tmp_path)
    source_before = snapshot(repo_root / "docs-viewer/scopes/source")
    rebuild_calls: list[dict[str, object]] = []
    activity_calls: list[tuple[Path, str, dict[str, object]]] = []
    plan = transfer.plan_document_transfer(
        repo_root,
        source_scope="source",
        source_sub_scope="tags",
        requested_doc_ids=["tag-a", "tag-b"],
        target_scope="target",
        target_sub_scope="works",
        transfer_mode="copy",
        operation_timestamp=COPY_TIMESTAMP,
        token_factory=sequential_tokens("aaaaaa", "bbbbbb"),
    )

    def reject_parent_rebuild(*_args, **_kwargs):
        raise AssertionError("parent rebuild must not own a child target")

    result = transfer_apply.apply_document_copy(
        repo_root,
        plan,
        confirm=True,
        perform_source_write_and_rebuild=reject_parent_rebuild,
        perform_sub_scope_source_write_and_rebuild=fake_sub_scope_rebuild(
            rebuild_calls
        ),
        activity_logger=lambda root, event, payload: activity_calls.append(
            (root, event, payload)
        ),
    )

    target_ids = result["created_doc_ids"]
    target_root = sub_scope_documents_root(repo_root, "target", "works")
    alpha_front_matter, alpha_body = source_model.parse_source(
        target_root / f"{target_ids[0]}.md"
    )
    beta_front_matter, _beta_body = source_model.parse_source(
        target_root / f"{target_ids[1]}.md"
    )
    target_report_id = "d-20260701-100003-dddddd"

    assert result["schema_version"] == "docs_document_copy_apply_v2"
    assert result["source"] == {"scope": "source", "sub_scope": "tags"}
    assert result["target"] == {"scope": "target", "sub_scope": "works"}
    assert "source_scope" not in result
    assert "target_scope" not in result
    assert alpha_front_matter["work_id"] == "00123"
    assert "group" not in alpha_front_matter
    assert "group" not in beta_front_matter
    assert "publishable" not in alpha_front_matter
    assert alpha_front_matter["parent_id"] == ""
    assert (
        f"/docs/?scope=target&doc={target_report_id}&subdoc={target_ids[1]}"
        in alpha_body
    )
    assert "docs/target/img/photo.png" in alpha_body
    assert media_path(repo_root, "target", "img", "photo.png").read_bytes() == b"photo"
    assert rebuild_calls == [
        {
            "scope": "target",
            "sub_scope": "works",
            "changed_paths": [
                target_root / f"{target_ids[0]}.md",
                target_root / f"{target_ids[1]}.md",
            ],
            "kwargs": {
                "suppression_reason": transfer_apply.DOCUMENT_COPY_SUPPRESSION_REASON
            },
        }
    ]
    assert result["effective_roots"] == [
        {
            "source_doc_id": "tag-a",
            "target_doc_id": target_ids[0],
            "target_viewer_url": (
                f"/docs/?scope=target&doc={target_report_id}"
                f"&subdoc={target_ids[0]}"
            ),
        },
        {
            "source_doc_id": "tag-b",
            "target_doc_id": target_ids[1],
            "target_viewer_url": (
                f"/docs/?scope=target&doc={target_report_id}"
                f"&subdoc={target_ids[1]}"
            ),
        },
    ]
    assert activity_calls[0][1:] == (
        transfer_apply.DOCUMENT_COPY_ACTIVITY_EVENT,
        {
            "source": {"scope": "source", "sub_scope": "tags"},
            "requested_doc_ids": ["tag-a", "tag-b"],
            "target": {"scope": "target", "sub_scope": "works"},
            "effective_roots": result["effective_roots"],
            "created_count": 2,
            "unique_media_count": 1,
        },
    )
    assert snapshot(repo_root / "docs-viewer/scopes/source") == source_before


def test_apply_child_to_parent_copy_rewrites_subdoc_as_doc(
    tmp_path: Path,
) -> None:
    repo_root = make_collection_repo(tmp_path)
    rebuild_calls: list[dict[str, object]] = []
    plan = transfer.plan_document_transfer(
        repo_root,
        source_scope="source",
        source_sub_scope="tags",
        requested_doc_ids=["tag-a", "tag-b"],
        target_scope="target",
        transfer_mode="copy",
        operation_timestamp=COPY_TIMESTAMP,
        token_factory=sequential_tokens("cccccc", "dddddd"),
    )

    result = transfer_apply.apply_document_copy(
        repo_root,
        plan,
        confirm=True,
        perform_source_write_and_rebuild=fake_rebuild(rebuild_calls),
        activity_logger=lambda *_args, **_kwargs: None,
    )

    target_ids = result["created_doc_ids"]
    copied = local_documents_root(repo_root, "target") / f"{target_ids[0]}.md"
    front_matter, body = source_model.parse_source(copied)
    assert result["target"] == {"scope": "target"}
    assert front_matter["work_id"] == "00123"
    assert "group" not in front_matter
    assert f"/docs/?scope=target&doc={target_ids[1]}" in body
    assert "subdoc=" not in body
    assert rebuild_calls[0]["scope"] == "target"
    assert rebuild_calls[0]["kwargs"]["docs_doc_ids"] == target_ids


def test_apply_parent_to_public_child_uses_omitted_true_default_and_subdoc_links(
    tmp_path: Path,
) -> None:
    target_scope = docs_scope_record(
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
    repo_root = make_repo(tmp_path, target_scope=target_scope)
    target_report_id = "d-20260701-100003-dddddd"
    write_doc(
        local_documents_root(repo_root, "target"),
        doc_id=target_report_id,
        title="Target Works",
        body="# Target Works\n",
    )
    report_path = local_documents_root(repo_root, "target") / f"{target_report_id}.md"
    report_front_matter, report_body = source_model.parse_source(report_path)
    report_front_matter.update(
        {
            "viewer_report": "docs_subscope",
            "viewer_report_access": "local",
            "viewer_report_subscope": "works",
        }
    )
    report_path.write_text(
        source_model.format_source(report_front_matter, report_body),
        encoding="utf-8",
    )
    target_root = sub_scope_documents_root(repo_root, "target", "works")
    target_root.mkdir(parents=True, exist_ok=True)
    write_doc(
        local_documents_root(repo_root, "source"),
        doc_id="alpha",
        title="Alpha",
        parent_id="root",
        body="# Alpha\n\n[Beta](/docs/?scope=source&doc=beta#detail)\n",
    )
    plan = transfer.plan_document_transfer(
        repo_root,
        source_scope="source",
        requested_doc_ids=["alpha", "beta"],
        target_scope="target",
        target_sub_scope="works",
        transfer_mode="copy",
        operation_timestamp=COPY_TIMESTAMP,
        token_factory=sequential_tokens("eeeeee", "ffffff"),
    )

    result = transfer_apply.apply_document_copy(
        repo_root,
        plan,
        confirm=True,
        perform_sub_scope_source_write_and_rebuild=fake_sub_scope_rebuild([]),
        activity_logger=lambda *_args, **_kwargs: None,
    )

    target_ids = result["created_doc_ids"]
    front_matter, body = source_model.parse_source(
        target_root / f"{target_ids[0]}.md"
    )
    assert "publishable" not in front_matter
    assert front_matter["parent_id"] == ""
    assert f"/target/?doc={target_report_id}&subdoc={target_ids[1]}#detail" in body
    assert result["effective_roots"][0]["target_viewer_url"] == (
        f"/docs/?scope=target&doc={target_report_id}&subdoc={target_ids[0]}"
    )


def test_child_copy_stale_target_fails_before_media_or_document_writes(
    tmp_path: Path,
) -> None:
    repo_root = make_collection_repo(tmp_path)
    plan = transfer.plan_document_transfer(
        repo_root,
        source_scope="source",
        source_sub_scope="tags",
        requested_doc_ids=["tag-a"],
        target_scope="target",
        target_sub_scope="works",
        transfer_mode="copy",
        operation_timestamp=COPY_TIMESTAMP,
        token_factory=sequential_tokens("aaaaaa"),
    )
    target_path = plan.documents[0].target_path
    write_doc(
        target_path.parent,
        doc_id=plan.documents[0].target_doc_id,
        title="Concurrent target",
    )
    media_before = snapshot(repo_root / "docs-viewer/scopes/target/published")

    with pytest.raises(
        transfer_apply.DocumentTransferPlanStaleError,
        match="document transfer preview is stale",
    ):
        transfer_apply.apply_document_copy(
            repo_root,
            plan,
            confirm=True,
            perform_sub_scope_source_write_and_rebuild=fake_sub_scope_rebuild([]),
            activity_logger=lambda *_args, **_kwargs: None,
        )

    assert target_path.read_text(encoding="utf-8").find("Concurrent target") >= 0
    assert snapshot(repo_root / "docs-viewer/scopes/target/published") == media_before


def test_apply_child_copy_retains_matching_custom_metadata(
    tmp_path: Path,
) -> None:
    repo_root = make_collection_repo(tmp_path)
    plan = transfer.plan_document_transfer(
        repo_root,
        source_scope="source",
        source_sub_scope="tags",
        requested_doc_ids=["tag-a"],
        target_scope="target",
        target_sub_scope="tags",
        transfer_mode="copy",
        operation_timestamp=COPY_TIMESTAMP,
        token_factory=sequential_tokens("aaaaaa"),
    )

    result = transfer_apply.apply_document_copy(
        repo_root,
        plan,
        confirm=True,
        perform_sub_scope_source_write_and_rebuild=fake_sub_scope_rebuild([]),
        activity_logger=lambda *_args, **_kwargs: None,
    )

    front_matter, body = source_model.parse_source(
        sub_scope_documents_root(repo_root, "target", "tags")
        / f"{result['created_doc_ids'][0]}.md"
    )
    assert front_matter["group"] == "subject"
    assert front_matter["work_id"] == "00123"
    assert "scope=source" in body
    assert "subdoc=tag-b" in body


@pytest.mark.parametrize("stale_fact", ["collection_config", "metadata", "media"])
def test_child_copy_revalidates_complete_collection_receipt_before_writes(
    tmp_path: Path,
    stale_fact: str,
) -> None:
    repo_root = make_collection_repo(tmp_path)
    plan = transfer.plan_document_transfer(
        repo_root,
        source_scope="source",
        source_sub_scope="tags",
        requested_doc_ids=["tag-a"],
        target_scope="target",
        target_sub_scope="works",
        transfer_mode="copy",
        operation_timestamp=COPY_TIMESTAMP,
        token_factory=sequential_tokens("aaaaaa"),
    )
    if stale_fact == "collection_config":
        config_path = repo_root / "docs-viewer/config/scopes/docs_scopes.json"
        config_payload = json.loads(config_path.read_text(encoding="utf-8"))
        config_payload["scopes"][1]["sub_scopes"][1]["title"] = "Changed Works"
        write_json(config_path, config_payload)
    elif stale_fact == "metadata":
        source_path = (
            sub_scope_documents_root(repo_root, "source", "tags") / "tag-a.md"
        )
        front_matter, body = source_model.parse_source(source_path)
        front_matter["group"] = "domain"
        source_path.write_text(
            source_model.format_source(front_matter, body),
            encoding="utf-8",
        )
    else:
        write_bytes(media_path(repo_root, "source", "img", "photo.png"), b"changed")

    with pytest.raises(
        transfer_apply.DocumentTransferPlanStaleError,
        match="document transfer preview is stale",
    ):
        transfer_apply.apply_document_copy(
            repo_root,
            plan,
            confirm=True,
            perform_sub_scope_source_write_and_rebuild=fake_sub_scope_rebuild([]),
            activity_logger=lambda *_args, **_kwargs: None,
        )

    assert not any(
        sub_scope_documents_root(repo_root, "target", "works").glob("*.md")
    )
    assert not media_path(repo_root, "target", "img", "photo.png").exists()


def test_copy_revalidates_registered_build_source_before_writes(
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
    write_doc(
        local_documents_root(repo_root, "source"),
        doc_id="alpha",
        title="Alpha",
        parent_id="root",
        body="# Alpha\n\n[[media:docs/source/svg/diagram.svg Diagram]]\n",
    )
    source_build = build_source_path(
        repo_root,
        "source",
        "mermaid",
        "diagram.mmd",
    )
    write_bytes(source_build, b"flowchart LR\n  A --> B\n")
    write_bytes(media_path(repo_root, "source", "svg", "diagram.svg"), b"source-svg")
    plan = transfer.plan_document_transfer(
        repo_root,
        source_scope="source",
        requested_doc_ids=["alpha"],
        target_scope="target",
        transfer_mode="copy",
        operation_timestamp=COPY_TIMESTAMP,
        token_factory=sequential_tokens("aaaaaa"),
    )
    write_bytes(source_build, b"flowchart LR\n  A --> Changed\n")

    with pytest.raises(
        transfer_apply.DocumentTransferPlanStaleError,
        match="document transfer preview is stale",
    ):
        transfer_apply.apply_document_copy(
            repo_root,
            plan,
            confirm=True,
            perform_source_write_and_rebuild=fake_rebuild([]),
            activity_logger=lambda *_args, **_kwargs: None,
        )

    assert not any(local_documents_root(repo_root, "target").glob("*.md"))
    assert not build_source_path(
        repo_root,
        "target",
        "mermaid",
        "diagram.mmd",
    ).exists()


def test_child_copy_failure_reports_only_the_exact_target_collection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = make_collection_repo(tmp_path)
    parent_target_before = snapshot(
        local_documents_root(repo_root, "target")
    )
    plan = transfer.plan_document_transfer(
        repo_root,
        source_scope="source",
        source_sub_scope="tags",
        requested_doc_ids=["tag-a", "tag-b"],
        target_scope="target",
        target_sub_scope="works",
        transfer_mode="copy",
        operation_timestamp=COPY_TIMESTAMP,
        token_factory=sequential_tokens("aaaaaa", "bbbbbb"),
    )
    original_write = transfer_apply.source_model.write_text_atomic_new
    writes = 0

    def fail_second_write(path: Path, text: str) -> None:
        nonlocal writes
        writes += 1
        if writes == 2:
            raise RuntimeError("simulated child document write failure")
        original_write(path, text)

    monkeypatch.setattr(
        transfer_apply.source_model,
        "write_text_atomic_new",
        fail_second_write,
    )

    with pytest.raises(
        transfer_apply.DocumentTransferApplyError,
        match="documents_and_rebuild",
    ) as captured:
        transfer_apply.apply_document_copy(
            repo_root,
            plan,
            confirm=True,
            perform_sub_scope_source_write_and_rebuild=fake_sub_scope_rebuild([]),
            activity_logger=lambda *_args, **_kwargs: None,
        )

    failure = captured.value.result
    assert failure["source"] == {"scope": "source", "sub_scope": "tags"}
    assert failure["target"] == {"scope": "target", "sub_scope": "works"}
    assert [
        item["state"] for item in failure["target_state"]["documents"]
    ] == ["exact", "missing"]
    assert snapshot(local_documents_root(repo_root, "target")) == parent_target_before
