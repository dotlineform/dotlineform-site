"""Working promotion, complete rebuilds, and revision-bound staged publication."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from build_docs_test_support import prepare_repo, run_cli
from repo_factory import docs_scope_record, docs_sub_scope_record, write_json, write_text
import docs_pre_publish as promotion
import docs_scope_publish as publication
import docs_write_rebuild as rebuild
from docs_scope_config import SCHEMA_VERSION, load_docs_scope_stage, document_source_path, generated_documents_path


ROOT = "d-20260911-100000-000001"
HOST = "d-20260911-100000-000002"
CHILD = "d-20260911-100000-000003"
DRAFT = "d-20260911-100000-000004"
DESCENDANT = "d-20260911-100000-000005"
WORKING = {"scope": "analysis", "stage": "working"}
PREPARED = {"scope": "analysis", "stage": "pre-publish"}


def source(root, doc_id, *, fields="", body="Ready text"):
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{doc_id}.md"
    path.write_text(f'---\ndoc_id: {doc_id}\ntitle: {doc_id}\nadded_date: "2026-09-11 10:00:00"\nlast_updated: "2026-09-11 10:00:00"\n{fields}---\n{body}\n')
    return path


@pytest.fixture
def repo(tmp_path, monkeypatch):
    prepare_repo(tmp_path)
    analysis = docs_scope_record("analysis", scope_type="public", viewer_base_url="/analysis/", include_scope_param=False, media_types=("img", "svg", "files", "html"))
    analysis["stages"] = {
        stage: {"default_doc_id": ROOT, "media": deepcopy(analysis["media"]),
                "sub_scopes": [docs_sub_scope_record("analysis", "works", title="Works", scope_type="public" if stage == "pre-publish" else "local")]}
        for stage in ("working", "pre-publish")
    }
    write_json(tmp_path / "docs-viewer/config/scopes/docs_scopes.json", {"schema_version": SCHEMA_VERSION, "scopes": [analysis]})
    for stage in ("working", "pre-publish"):
        config = load_docs_scope_stage(tmp_path, "analysis", stage)
        for collection in (config, *config.sub_scopes):
            (tmp_path / document_source_path(collection)).mkdir(parents=True, exist_ok=True)
        (tmp_path / generated_documents_path(config)).mkdir(parents=True, exist_ok=True)
    (tmp_path / analysis["scope_root"]["path"] / "published").mkdir(parents=True, exist_ok=True)
    working = load_docs_scope_stage(tmp_path, "analysis", "working")
    ordinary = tmp_path / document_source_path(working)
    source(ordinary, ROOT, fields="draft: false\n", body=f"[Work](/docs/?scope=analysis&stage=working&doc={HOST}&subdoc={CHILD}#part)\n\n![Diagram]([[media:docs/analysis/svg/example.svg]])\n\n[Local](dlf-local:private/folder)")
    write_text(ordinary.parent / "media/svg/example.svg", '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"></svg>')
    source(ordinary, HOST, fields="draft: false\n", body=":::report\nid: docs_subscope\naccess: local\nsub_scope: works\n:::\n")
    source(ordinary, DRAFT, fields="draft: true\n")
    source(ordinary, DESCENDANT, fields=f"draft: false\nparent_id: {DRAFT}\n")
    source(tmp_path / document_source_path(working.sub_scopes[0]), CHILD, fields='draft: false\nwork_id: "00123"\n')

    # Run the production docs/Search builders in-process against this isolated repo.
    def command(command, repo_root):
        if "build_docs.py" in command[1]:
            code, stdout, stderr = run_cli(repo_root, command[2:])
        else:
            from build_search import DocsViewerSearchDataBuilder
            DocsViewerSearchDataBuilder(repo_root=repo_root, scope="analysis", stage="pre-publish").run(write=True, force=False)
            code, stdout, stderr = 0, "", ""
        return {"returncode": code, "stdout": stdout, "stderr": stderr, "elapsed_seconds": 0}
    monkeypatch.setattr(rebuild, "run_rebuild_command", command)
    return tmp_path


def apply(repo):
    preview = promotion.preview_pre_publish(repo, WORKING)
    return promotion.apply_pre_publish(repo, {**WORKING, "confirm": True, "plan_revision": preview["plan_revision"]})


def test_rebuild_and_publish_replace_stale_derivatives_without_changing_working(repo):
    working = load_docs_scope_stage(repo, "analysis", "working")
    source_root = repo / working.stage_root.path / "source"
    before = promotion._files_from_root(source_root)
    target = load_docs_scope_stage(repo, "analysis", "pre-publish")
    stale = source(repo / document_source_path(target), "d-20260911-100000-ffffff")
    result = apply(repo)
    assert result["document_count"] == 3
    assert result["excluded_doc_ids"] == [DRAFT, DESCENDANT]
    assert not stale.exists()
    assert promotion._files_from_root(source_root) == before
    generated = repo / generated_documents_path(target)
    host = json.loads((generated / "by-id" / f"{HOST}.json").read_text())
    assert host["report"]["access"] == "public"
    root_payload = json.loads((generated / "by-id" / f"{ROOT}.json").read_text())
    assert "stage=working" not in root_payload["content_html"]
    assert "stage=pre-publish" in root_payload["content_html"]
    assert "private/folder" not in root_payload["content_html"]
    child_root = repo / generated_documents_path(target.sub_scopes[0])
    child = json.loads((child_root / "by-id" / f"{CHILD}.json").read_text())
    assert child["subject"] == {"kind": "work", "key": "00123"}
    search = (generated.parent / "search/index.json").read_text()
    assert CHILD in search and DRAFT not in search and DESCENDANT not in search
    preview = publication.preview_scope_publish(repo, PREPARED)
    published = publication.apply_scope_publish(repo, {**PREPARED, "confirm": True, "plan_revision": preview["plan_revision"], "target_published_revision": preview["target_published_revision"]})
    assert published["document_count"] == 3
    _, _, files = publication.validate_published_snapshot(repo, "analysis")
    assert json.loads(files[Path("sub-scopes/works/documents/by-id") / f"{CHILD}.json"])["subject"] == child["subject"]
    assert all(path.name != "manage-manifest.json" for path in files)
    assert files[Path("media/svg/example.svg")] == before[Path("media/svg/example.svg")]


def test_excluded_host_omits_collection_and_next_rebuild_removes_deleted_content(repo):
    apply(repo)
    working = load_docs_scope_stage(repo, "analysis", "working")
    source(repo / document_source_path(working), HOST, fields="draft: true\n", body=":::report\nid: docs_subscope\naccess: local\nsub_scope: works\n:::\n")
    result = apply(repo)
    assert result["collections"]["works"] == 0
    target = load_docs_scope_stage(repo, "analysis", "pre-publish")
    assert not (repo / generated_documents_path(target.sub_scopes[0]) / "by-id" / f"{CHILD}.json").exists()


def test_stale_preview_and_wrong_stage_cannot_write(repo):
    preview = promotion.preview_pre_publish(repo, WORKING)
    working = load_docs_scope_stage(repo, "analysis", "working")
    source(repo / document_source_path(working), DRAFT, fields="draft: false\n")
    with pytest.raises(ValueError, match="stale"):
        promotion.apply_pre_publish(repo, {**WORKING, "confirm": True, "plan_revision": preview["plan_revision"]})
    with pytest.raises(ValueError, match="Analysis Working"):
        promotion.preview_pre_publish(repo, PREPARED)
    with pytest.raises(ValueError, match="Pre-publish stage"):
        publication.preview_scope_publish(repo, WORKING)


def test_failed_build_cannot_publish_previous_snapshot(repo, monkeypatch):
    apply(repo)
    def fail(*args, **kwargs):
        raise RuntimeError("fixture build failure")
    monkeypatch.setattr(promotion, "rebuild_scope_outputs", fail)
    with pytest.raises(RuntimeError, match="fixture build failure"):
        apply(repo)
    with pytest.raises(FileNotFoundError, match="incomplete"):
        publication.preview_scope_publish(repo, PREPARED)


@pytest.mark.parametrize("fields", ["draft: true\n", "draft: false\npublishable: false\n", ""])
def test_readiness_and_intent_exclude_descendants(repo, fields):
    working = load_docs_scope_stage(repo, "analysis", "working")
    source(repo / document_source_path(working), DRAFT, fields=fields)
    assert promotion.preview_pre_publish(repo, WORKING)["excluded_doc_ids"] == [DRAFT, DESCENDANT]


def test_read_only_status_and_stage_manifest_identity(repo):
    from docs_management_read_service import docs_management_get_payload
    apply(repo)
    status = docs_management_get_payload(repo, "/docs/publish/status", {"scope": ["analysis"], "stage": ["pre-publish"]})
    assert status["stage"] == "pre-publish" and status["document_count"] == 3
    config = load_docs_scope_stage(repo, "analysis", "pre-publish")
    path = repo / generated_documents_path(config) / "../build-manifest.json"
    manifest = json.loads(path.read_text())
    manifest["stage"] = "working"
    write_json(path, manifest)
    with pytest.raises(RuntimeError, match="stage identity"):
        publication.preview_scope_publish(repo, PREPARED)
