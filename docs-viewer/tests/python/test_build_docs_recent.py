"""Recent covers exact stage-local collections and is owned by full scope builds."""

from copy import deepcopy
from pathlib import Path

import pytest

from build_docs_test_support import prepare_repo, read_json, write_json, write_route_config, write_text
import build_docs
from docs_builder.sub_scope import SubScopeDocsBuilder
from docs_scope_config import SCHEMA_VERSION, document_source_path, generated_documents_path, load_docs_scope_stage
from repo_factory import docs_scope_record, docs_sub_scope_record


HOST = "d-20260914-100000-000001"
ORDINARY = "d-20260914-100000-000002"
CHILDREN = [f"d-20260914-100000-{index:06x}" for index in range(10, 32)]


def prepare_recent_scope(root: Path, scope: str = "studio") -> None:
    prepare_repo(root)
    record = docs_scope_record(scope)
    record["stages"] = {
        stage: {"default_doc_id": HOST, "media": deepcopy(record["media"]),
                "sub_scopes": [docs_sub_scope_record(scope, "references", title="References")]}
        for stage in ("working", "pre-publish")
    }
    write_json(root / "docs-viewer/config/scopes/docs_scopes.json", {
        "schema_version": SCHEMA_VERSION, "scopes": [record], "docs_viewer": {"recent_limit": 20},
    })
    for stage, date in (("working", "2026-09-14"), ("pre-publish", "2026-09-13")):
        config = load_docs_scope_stage(root, scope, stage)
        ordinary_root = root / document_source_path(config)
        child_root = root / document_source_path(config.sub_scopes[0])
        for doc_id, title, directory, time, body in (
            (HOST, "References", ordinary_root, "08:00:00", ":::report\nid: docs_subscope\nsub_scope: references\n:::\n"),
            (ORDINARY, "Newest ordinary", ordinary_root, "12:00:00", "Text"),
            *((doc_id, f"Reference {index:02}", child_root, f"10:{index:02}:00", "Text")
              for index, doc_id in enumerate(CHILDREN)),
        ):
            write_text(directory / f"{doc_id}.md", (
                f'---\ndoc_id: {doc_id}\ntitle: {title}\nadded_date: "{date} {time}"\n'
                f'last_updated: "{date} {time}"\ndraft: true\n---\n{body}\n'
            ))
        write_json(ordinary_root / "unpublishable.json", [ORDINARY])


@pytest.mark.parametrize("scope", ["studio", "processing"])
@pytest.mark.parametrize("stage", ["working", "pre-publish"])
def test_recent_combines_complete_stage_before_limiting(tmp_path: Path, scope: str, stage: str) -> None:
    prepare_recent_scope(tmp_path, scope)
    config = load_docs_scope_stage(tmp_path, scope, stage)
    builder = build_docs.DocsDataBuilder(repo_root=tmp_path, config=config, skip_media_builds=True)
    child_path = tmp_path / document_source_path(config.sub_scopes[0]) / f"{CHILDREN[-1]}.md"
    child_path.write_text(child_path.read_text().replace("title: Reference 21", "title:").replace("\nText\n", "\n# Heading title\n"))
    result = builder.run(write=True)
    output = tmp_path / generated_documents_path(config)
    recent = read_json(output / "recent.json")
    assert recent["limit"] == 20
    assert [row["doc_id"] for row in recent["docs"]] == [ORDINARY, *reversed(CHILDREN[-19:])]
    child = recent["docs"][1]
    assert child["title"] == "Heading title"
    assert child["sub_scope"] == "references"
    assert child["report_doc_id"] == HOST
    assert child["collection_title"] == "References"
    assert "/references/" in child["content_url"]
    assert all(row["timestamp"].startswith("2026-09-14" if stage == "working" else "2026-09-13") for row in recent["docs"])
    assert "draft" not in child and "last_updated" not in child
    assert [row["doc_id"] for row in result["index_payload"]["docs"]] == [ORDINARY, HOST]
    (tmp_path / document_source_path(config.sub_scopes[0]) / f"{CHILDREN[-1]}.md").unlink()
    builder.run(write=True)
    assert [row["doc_id"] for row in read_json(output / "recent.json")["docs"]] == [ORDINARY, *reversed(CHILDREN[-20:-1])]


@pytest.mark.parametrize("missing", [False, True])
def test_targeted_and_child_builds_never_generate_or_touch_recent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, missing: bool) -> None:
    prepare_recent_scope(tmp_path)
    config = load_docs_scope_stage(tmp_path, "studio", "working")
    build_docs.DocsDataBuilder(repo_root=tmp_path, config=config, skip_media_builds=True).run(write=True)
    output = tmp_path / generated_documents_path(config)
    recent_paths = [output / "recent.json", output / ".publish/recent.json"]
    write_json(recent_paths[1], {"docs": [{"doc_id": CHILDREN[-1], "sub_scope": "references"}]})
    if missing:
        for path in recent_paths:
            path.unlink()
    before = [(path.read_bytes(), path.stat().st_mtime_ns) if path.exists() else None for path in recent_paths]

    def forbidden(*_args, **_kwargs):
        pytest.fail("A targeted or child-only build must not generate Recent")

    monkeypatch.setattr(build_docs.DocsDataBuilder, "recent_candidates", forbidden)
    monkeypatch.setattr(build_docs.DocsDataBuilder, "recent_payload", forbidden)
    ordinary_path = tmp_path / document_source_path(config) / f"{ORDINARY}.md"
    ordinary_path.write_text(ordinary_path.read_text().replace("12:00:00", "13:00:00"))
    result = build_docs.DocsDataBuilder(
        repo_root=tmp_path, config=config, only_doc_ids=[ORDINARY], skip_media_builds=True,
    ).run(write=True)
    SubScopeDocsBuilder(
        repo_root=tmp_path, config=config, sub_scope=config.sub_scopes[0], skip_media_builds=True,
    ).run(write=True)
    assert result["recent_payload"] is None
    assert result["diagnostics"]["recent_changed"] == 0
    assert [(path.read_bytes(), path.stat().st_mtime_ns) if path.exists() else None for path in recent_paths] == before
    child_output = tmp_path / generated_documents_path(config.sub_scopes[0])
    assert not (child_output / "recent.json").exists()


@pytest.mark.parametrize("ambiguous", [False, True])
def test_recent_requires_exact_host_in_same_stage(tmp_path: Path, ambiguous: bool) -> None:
    prepare_recent_scope(tmp_path)
    config = load_docs_scope_stage(tmp_path, "studio", "pre-publish")
    root = tmp_path / document_source_path(config)
    host = root / f"{HOST}.md"
    if ambiguous:
        write_text(root / f"{ORDINARY}.md", host.read_text().replace(HOST, ORDINARY))
    else:
        host.unlink()
    builder = build_docs.DocsDataBuilder(repo_root=tmp_path, config=config, skip_media_builds=True)
    with pytest.raises(ValueError, match="exactly one report host"):
        builder.recent_candidates(builder.load_docs())


def test_scope_without_children_and_route_projection_use_all_stage_documents(tmp_path: Path) -> None:
    prepare_recent_scope(tmp_path)
    config_path = tmp_path / "docs-viewer/config/scopes/docs_scopes.json"
    settings = read_json(config_path)
    working = settings["scopes"][0]["stages"]["working"]
    working["sub_scopes"] = []
    working["manage_only_tree_root_ids"] = [ORDINARY]
    write_json(config_path, settings)
    write_route_config(tmp_path, public_scope="studio")
    config = load_docs_scope_stage(tmp_path, "studio", "working")
    host_path = tmp_path / document_source_path(config) / f"{HOST}.md"
    host_path.write_text(host_path.read_text().replace(":::report\nid: docs_subscope\nsub_scope: references\n:::", "Ordinary text"))
    result = build_docs.DocsDataBuilder(repo_root=tmp_path, config=config, skip_media_builds=True).run(write=True)
    assert [row["doc_id"] for row in result["recent_payload"]["docs"]] == [ORDINARY, HOST]
    assert result["publication_recent_payload"]["docs"] == result["recent_payload"]["docs"]
