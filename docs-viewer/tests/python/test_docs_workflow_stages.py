"""Exact workflow stage storage and authoring boundaries."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import json
import subprocess
import sys

import pytest

from docs_management_test_support import docs_scope_config as scopes
from repo_factory import docs_scope_record, docs_sub_scope_record, write_json
from docs_management_document_target import resolve_managed_document_target
from docs_management_mutations import plan_create, plan_delete_apply
from docs_generated_reads import read_generated_doc_payload
from build_docs_test_support import prepare_repo, run_cli


DOC_ID = "d-20260906-170000-a1b2c3"


@pytest.fixture
def stage_repo(tmp_path: Path) -> Path:
    prepare_repo(tmp_path)
    analysis = docs_scope_record("analysis", scope_type="public", viewer_base_url="/analysis/", include_scope_param=False)
    analysis["stages"] = {
        stage: {
            "media_namespace": namespace,
            "media": deepcopy(analysis["media"]),
            "sub_scopes": [docs_sub_scope_record("analysis", collection, scope_type="public" if stage == "pre-publish" else "local")],
        }
        for stage, namespace, collection in (
            ("working", "dotlineform", "works"),
            ("pre-publish", "analysis", "works"),
        )
    }
    write_json(tmp_path / scopes.CONFIG_REL_PATH, {
        "schema_version": scopes.SCHEMA_VERSION,
        "scopes": [analysis, docs_scope_record("studio")],
    })
    for stage, collection in (("working", "works"), ("pre-publish", "works")):
        config = scopes.load_docs_scope_stage(tmp_path, "analysis", stage)
        for owner in (config, config.sub_scopes[0]):
            root = tmp_path / scopes.document_source_path(owner)
            root.mkdir(parents=True)
            (root / f"{DOC_ID}.md").write_text(
                f"---\ndoc_id: {DOC_ID}\ntitle: {stage}\n---\n# {stage}\n",
                encoding="utf-8",
            )
        output = tmp_path / scopes.generated_documents_path(config)
        write_json(output / "index-tree.json", {"docs": [{"doc_id": DOC_ID, "content_url": "/docs/doc"}]})
        write_json(output / "by-id" / f"{DOC_ID}.json", {"doc_id": DOC_ID, "title": stage})
    return tmp_path


def test_service_can_import_with_unselected_workflow_parent(stage_repo: Path) -> None:
    services = Path(scopes.__file__).parent
    result = subprocess.run(
        [sys.executable, "-c", "\n".join((
            "import sys",
            "from pathlib import Path",
            f"sys.path.insert(0, {str(services)!r})",
            "import docs_scope_config as scopes",
            f"scopes.DOCS_SCOPE_CONFIGS = scopes.load_docs_scope_configs(Path({str(stage_repo)!r}))",
            "import docs_viewer_service",
        ))],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_stage_storage_retains_scope_owned_snapshot_and_media_identity(stage_repo: Path) -> None:
    working = scopes.load_docs_scope_stage(stage_repo, "analysis", "working")
    pre_publish = scopes.load_docs_scope_stage(stage_repo, "analysis", "pre-publish")
    assert working.scope_id == pre_publish.scope_id == "analysis"
    assert working.published == pre_publish.published
    assert scopes.published_documents_path(working) == Path("docs-viewer/scopes/analysis/published/documents")
    assert scopes.document_source_path(working.sub_scopes[0]) == Path(
        "docs-viewer/scopes/analysis/working/source/documents/sub-scopes/works/documents"
    )
    assert working.media.types["img"].reference_prefix == Path("docs/dotlineform/img")
    assert working.media.types["img"].served_path_prefix == "/docs/media/analysis/working/img"
    assert scopes.document_source_path(scopes.load_docs_scope_stage(stage_repo, "studio")) == Path(
        "docs-viewer/scopes/studio/source/documents"
    )


@pytest.mark.parametrize("stage", [None, "published", "", "WORKING"])
def test_workflow_scope_requires_exact_stage(stage_repo: Path, stage: str | None) -> None:
    with pytest.raises(ValueError, match="requires stage"):
        scopes.load_docs_scope_stage(stage_repo, "analysis", stage)


def test_same_document_id_is_read_only_from_requested_stage(stage_repo: Path) -> None:
    for stage in ("working", "pre-publish"):
        target = {"scope": "analysis", "stage": stage, "doc_id": DOC_ID}
        resolved = resolve_managed_document_target(stage_repo, target)
        assert resolved.request_target() == target
        assert resolved.document.title == stage
        assert read_generated_doc_payload(stage_repo, "analysis", DOC_ID, stage)["title"] == stage
    with pytest.raises(ValueError, match="unknown sub_scope"):
        resolve_managed_document_target(stage_repo, {
            "scope": "analysis", "stage": "pre-publish", "sub_scope": "projects", "doc_id": DOC_ID,
        })


def test_working_child_preserves_publishability_without_public_projection(stage_repo: Path) -> None:
    import docs_source_model as source_model

    config = scopes.load_docs_scope_stage(stage_repo, "analysis", "working")
    child = config.sub_scopes[0]
    assert child.stage == "working" and child.public_projection is None
    path = stage_repo / scopes.document_source_path(child) / f"{DOC_ID}.md"
    path.write_text(f"---\ndoc_id: {DOC_ID}\ntitle: Private work\npublishable: false\n---\n# Private work\n")
    documents = source_model.load_document_collection_docs_for_config(stage_repo, config, child)
    assert documents[0].publishable is False
    code, _stdout, stderr = run_cli(stage_repo, [
        "--scope", "analysis", "--stage", "working", "--sub-scope", "works",
        "--write", "--skip-browser-config", "--skip-media-builds",
    ])
    assert code == 0, stderr
    output = stage_repo / scopes.generated_documents_path(child)
    assert json.loads((output / "manage-manifest.json").read_text())["docs"][0]["publishable"] is False
    assert json.loads((output / "by-id" / f"{DOC_ID}.json").read_text())["publishable"] is False


@pytest.mark.parametrize("sub_scope", [None, "works"])
def test_pre_publish_create_rejected_before_source_changes(stage_repo: Path, sub_scope: str | None) -> None:
    request = {"scope": "analysis", "stage": "pre-publish", "title": "Forbidden"}
    if sub_scope:
        request["sub_scope"] = sub_scope
    with pytest.raises(ValueError, match="authoring is unavailable"):
        plan_create(stage_repo, request)


def test_working_create_and_delete_plan_keep_exact_owner(stage_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import docs_management_mutations as mutations

    def forbidden_cleanup(*args: object, **kwargs: object) -> None:
        pytest.fail("Working Delete must not plan public cleanup")

    monkeypatch.setattr(mutations.public_delete_cleanup, "plan_public_document_delete_cleanup", forbidden_cleanup)
    create = plan_create(stage_repo, {"scope": "analysis", "stage": "working", "title": "New"})
    assert create.stage == "working"
    assert create.response["target"]["stage"] == "working"
    delete = plan_delete_apply(stage_repo, {
        "scope": "analysis", "stage": "working", "doc_ids": [DOC_ID], "confirm": True,
    })
    assert delete.stage == "working"
    assert delete.public_delete_cleanup is None
    assert all("/working/source/" in str(item.path) for item in delete.source_deletes)


def test_stage_build_writes_exact_parent_and_report_payloads(stage_repo: Path) -> None:
    for stage, collection in (("working", "works"), ("pre-publish", "works")):
        config = scopes.load_docs_scope_stage(stage_repo, "analysis", stage)
        root = stage_repo / scopes.document_source_path(config)
        source = root / f"{DOC_ID}.md"
        source.write_text(source.read_text() + f"\n:::report\nid: docs_subscope\naccess: public\nsub_scope: {collection}\n:::\n", encoding="utf-8")
        code, stdout, stderr = run_cli(stage_repo, ["--scope", "analysis", "--stage", stage, "--write", "--skip-media-builds"])
        assert code == 0, stdout + stderr
        output = stage_repo / scopes.generated_documents_path(config)
        index = json.loads((output / "index-tree.json").read_text())
        assert len(index["docs"]) == 1  # Child source is never absorbed by the ordinary tree.
        code, stdout, stderr = run_cli(stage_repo, ["--scope", "analysis", "--stage", stage, "--sub-scope", collection, "--write", "--skip-media-builds"])
        assert code == 0, stdout + stderr
        child_root = stage_repo / scopes.generated_documents_path(config.sub_scopes[0])
        manifest = json.loads((child_root / "manage-manifest.json").read_text())
        assert manifest["docs"][0]["doc_id"] == DOC_ID
        child = json.loads((child_root / "by-id" / f"{DOC_ID}.json").read_text())
        assert f"stage={stage}" in child["viewer_url"]
        assert f"subdoc={DOC_ID}" in child["viewer_url"]


@pytest.mark.parametrize("stage", ["working", "pre-publish"])
def test_rendered_links_preserve_explicit_stage_and_child_targets(stage_repo: Path, stage: str) -> None:
    from docs_builder.pipeline import DocsDataBuilder
    from markdown_renderer import render_markdown_to_html

    builder = DocsDataBuilder(
        repo_root=stage_repo,
        config=scopes.load_docs_scope_stage(stage_repo, "analysis", stage),
        skip_media_builds=True,
    )
    documents = builder.load_docs()
    for target_stage in ("working", "pre-publish"):
        for query in (
            f"doc={DOC_ID}&scope=analysis&stage={target_stage}",
            f"scope=analysis&stage={target_stage}&doc={DOC_ID}",
        ):
            href = f"/docs/?{query}&subdoc={DOC_ID}#detail"
            rendered = render_markdown_to_html(f"[Exact target]({href})")
            assert builder.rewrite_doc_links(
                rendered, current_doc=documents[0], docs=documents,
            ) == rendered


@pytest.mark.parametrize("delete_ancestor", [False, True])
def test_working_default_delete_updates_only_local_browser_config(
    stage_repo: Path, monkeypatch: pytest.MonkeyPatch, delete_ancestor: bool,
) -> None:
    from docs_builder.browser_config import write_browser_config
    import docs_management_service as service
    import docs_management_mutation_service as mutation_service
    import docs_write_rebuild as rebuild

    parent_id = "d-20260906-170001-b2c3d4"
    survivor_id = "d-20260906-170002-c3d4e5"
    config_path = stage_repo / scopes.CONFIG_REL_PATH
    raw = json.loads(config_path.read_text())
    raw["scopes"][0]["stages"]["working"]["default_doc_id"] = DOC_ID
    write_json(config_path, raw)
    configs = scopes.load_docs_scope_configs(stage_repo)
    working = scopes.select_scope_stage(configs["analysis"], "working")
    source = stage_repo / scopes.document_source_path(working)
    if delete_ancestor:
        (source / f"{parent_id}.md").write_text(f"---\ndoc_id: {parent_id}\ntitle: Parent\n---\n# Parent\n")
        (source / f"{DOC_ID}.md").write_text(f"---\ndoc_id: {DOC_ID}\ntitle: Default child\nparent_id: {parent_id}\n---\n# Default\n")
    (source / f"{survivor_id}.md").write_text(f"---\ndoc_id: {survivor_id}\ntitle: Retained\n---\n# Retained\n")
    browser_path = Path("docs-viewer/config/defaults/docs-viewer-config.json")
    write_browser_config(stage_repo, list(configs.values()), path=browser_path, label="Fixture local config")
    before_browser = json.loads((stage_repo / browser_path).read_text())
    protected_paths = [
        Path("docs-viewer/config/defaults/docs-viewer-public-config.json"),
        Path("site/docs-viewer/config/defaults/docs-viewer-public-config.json"),
        Path("docs-viewer/scopes/analysis/published/documents/accepted.json"),
    ]
    for path in protected_paths:
        write_json(stage_repo / path, {"frozen": path.as_posix()})
    protected_paths.extend(
        path.relative_to(stage_repo)
        for path in (stage_repo / "docs-viewer/scopes/analysis/pre-publish").rglob("*")
        if path.is_file()
    )
    before_protected = {path: (stage_repo / path).read_bytes() for path in protected_paths}

    def fixture_build(command, repo):
        assert "--stage" in command and "--skip-media-builds" in command
        code, stdout, stderr = run_cli(repo, command[2:])
        return {"returncode": code, "stdout": stdout, "stderr": stderr, "command": " ".join(command), "elapsed_seconds": 0}

    monkeypatch.setattr(rebuild, "run_rebuild_command", fixture_build)
    monkeypatch.setattr(mutation_service, "log_event", lambda *args, **kwargs: None)
    _, result = service.docs_management_post_response(stage_repo, "/docs/delete-apply", {
        "scope": "analysis", "stage": "working",
        "doc_ids": [parent_id if delete_ancestor else DOC_ID], "confirm": True,
    })
    assert result["ok"] is True and result["default_doc_id_changed"] is True
    assert set(result["deleted_doc_ids"]) == ({DOC_ID, parent_id} if delete_ancestor else {DOC_ID})
    assert scopes.load_docs_scope_stage(stage_repo, "analysis", "working").default_doc_id == ""
    assert not (source / f"{DOC_ID}.md").exists()
    assert (source / f"{survivor_id}.md").is_file()
    expected_browser = deepcopy(before_browser)
    analysis = next(record for record in expected_browser["scopes"] if record["scope_id"] == "analysis")
    next(record for record in analysis["stages"] if record["stage"] == "working")["default_doc_id"] = ""
    assert json.loads((stage_repo / browser_path).read_text()) == expected_browser
    assert all((stage_repo / path).read_bytes() == value for path, value in before_protected.items())


def test_working_write_rebuild_and_delete_preserve_other_owners(stage_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import docs_write_rebuild as rebuild
    import docs_management_service as service
    import docs_management_source_service as source_service
    import docs_management_mutation_service as mutation_service

    def forbidden_follow_through(*args, **kwargs):
        pytest.fail("Working Delete must not run public cleanup or lineage")

    monkeypatch.setattr(mutation_service.public_delete_cleanup, "apply_public_document_delete_cleanup", forbidden_follow_through)
    monkeypatch.setattr(mutation_service.publication_lineage, "apply_document_deletes", forbidden_follow_through)
    monkeypatch.setattr(mutation_service, "log_event", lambda *args, **kwargs: None)
    monkeypatch.setattr(source_service, "log_event", lambda *args, **kwargs: None)
    commands = []

    def fixture_build(command, repo):
        assert "--stage" in command and command[command.index("--stage") + 1] == "working"
        assert "--skip-media-builds" in command
        assert "build_search.py" not in " ".join(command)
        commands.append(command)
        code, stdout, stderr = run_cli(repo, command[2:])
        return {"returncode": code, "stdout": stdout, "stderr": stderr, "command": " ".join(command), "elapsed_seconds": 0}

    monkeypatch.setattr(rebuild, "run_rebuild_command", fixture_build)
    protected = stage_repo / "docs-viewer/scopes/analysis/pre-publish"
    before = {path: path.read_bytes() for path in protected.rglob("*") if path.is_file()}
    for relative in ("docs-viewer/scopes/analysis/published/documents/accepted.json", "site/assets/data/docs/scopes/analysis/accepted.json"):
        sentinel = stage_repo / relative
        sentinel.parent.mkdir(parents=True, exist_ok=True)
        sentinel.write_text("accepted\n")
        before[sentinel] = sentinel.read_bytes()
    for sub_scope in (None, "works"):
        collection = {"scope": "analysis", "stage": "working"}
        if sub_scope:
            collection["sub_scope"] = sub_scope
        _, created = service.docs_management_post_response(stage_repo, "/docs/create", {**collection, "title": "Stage test"})
        target = created["target"]
        params = {key: [value] for key, value in target.items()}
        read = source_service.read_source_body(stage_repo, params)
        body = "# Edited\n\n[[media:docs/dotlineform/img/retained.jpg]]\n"
        _, saved = service.docs_management_post_response(stage_repo, "/docs/source/rebuild", {
            **target, "source_body": body, "source_revision": read["source_revision"],
        })
        assert saved["stage"] == "working"
        assert source_service.read_source_body(stage_repo, params)["source_body"] == body
        resolved = resolve_managed_document_target(stage_repo, target)
        output = stage_repo / scopes.generated_documents_path(resolved.document_config)
        assert "Edited" in json.loads((output / "by-id" / f"{target['doc_id']}.json").read_text())["content_html"]
        if sub_scope:
            _, preview = service.docs_management_post_response(stage_repo, "/docs/delete-preview", target)
            delete_body = {**target, "source_revision": preview["source_revision"], "confirm": True}
        else:
            delete_body = {**collection, "doc_ids": [target["doc_id"]], "confirm": True}
        _, deleted = service.docs_management_post_response(stage_repo, "/docs/delete-apply", delete_body)
        assert deleted["stage"] == "working"
        assert not resolved.document.path.exists()
        assert not (output / "by-id" / f"{target['doc_id']}.json").exists()
    assert len(commands) == 6
    assert all(path.read_bytes() == value for path, value in before.items())


@pytest.mark.parametrize("path", ["/docs/create", "/docs/update-metadata", "/docs/source/rebuild", "/docs/delete-preview", "/docs/delete-apply", "/docs/publish/apply", "/docs/document-transfer-preview"])
def test_pre_publish_services_reject_before_writes(stage_repo: Path, path: str) -> None:
    import docs_management_service as service
    before = {p: p.read_bytes() for p in stage_repo.rglob("*.md")}
    with pytest.raises(ValueError, match="unavailable"):
        service.docs_management_post_response(stage_repo, path, {"scope": "analysis", "stage": "pre-publish", "doc_id": DOC_ID})
    assert all(p.read_bytes() == value for p, value in before.items())


def test_watcher_owns_working_collections_only(stage_repo: Path) -> None:
    import docs_live_rebuild_watcher as watcher
    from docs_watch_suppression import watch_suppression_owner
    configs = scopes.load_docs_scope_configs(stage_repo)
    specs = watcher.desired_watch_state_specs(stage_repo, configs)
    assert "analysis" not in specs
    assert "analysis/working" in specs and "analysis/working/works" in specs
    assert not any("pre-publish" in key for key in specs)
    state = specs["analysis/working"]
    assert list(watcher.state_snapshot(state)) == [f"{DOC_ID}.md"]
    assert watch_suppression_owner("analysis", "projects", stage="working") != watch_suppression_owner("analysis", "projects", stage="pre-publish")


def test_external_stage_urls_and_media_use_selected_owner(stage_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from docs_generated_reads import external_sub_scope_payload_path
    from docs_media_storage import local_media_path_from_route
    from docs_media_inventory import source_media_references
    from docs_builder.browser_config import browser_scope_record

    monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(stage_repo / "external"))
    (stage_repo / "external/docs-viewer").mkdir(parents=True)
    raw = json.loads((stage_repo / scopes.CONFIG_REL_PATH).read_text())
    analysis = raw["scopes"][0]
    analysis["scope_root"] = {"provider": "external_local", "path": "$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/scopes/analysis"}
    write_json(stage_repo / scopes.CONFIG_REL_PATH, raw)
    for stage, collection in (("working", "works"), ("pre-publish", "works")):
        config = scopes.load_docs_scope_stage(stage_repo, "analysis", stage)
        parent = scopes.document_source_path(config)
        parent.mkdir(parents=True)
        (parent / f"{DOC_ID}.md").write_text(f"---\ndoc_id: {DOC_ID}\ntitle: {stage}\n---\n:::report\nid: docs_subscope\naccess: public\nsub_scope: {collection}\n:::\n")
        child = scopes.document_source_path(config.sub_scopes[0])
        child.mkdir(parents=True)
        (child / f"{DOC_ID}.md").write_text(f"---\ndoc_id: {DOC_ID}\ntitle: {stage}\n---\n# Child\n")
        generated = scopes.generated_documents_path(config)
        generated.mkdir(parents=True)
        for extra in ([], ["--sub-scope", collection]):
            code, stdout, stderr = run_cli(stage_repo, ["--scope", "analysis", "--stage", stage, "--write", "--skip-media-builds", *extra])
            assert code == 0, stdout + stderr
        record = read_generated_doc_payload(stage_repo, "analysis", DOC_ID, stage)
        assert record["title"] == stage
        record_config = browser_scope_record(stage_repo, {"analysis": analysis}, config)
        assert f"stage={stage}" in record_config["index_tree_url"]
        manifest_url = record_config["sub_scopes"][0]["manifest_url"]
        assert f"/analysis/{stage}/{collection}/" in manifest_url
        assert external_sub_scope_payload_path(stage_repo, manifest_url).parent == scopes.generated_documents_path(config.sub_scopes[0])
        media = config.media.types["img"]
        media.generated_location.path.mkdir(parents=True)
        picture = media.generated_location.path / "same.jpg"
        picture.write_bytes(stage.encode())
        path, kind = local_media_path_from_route(stage_repo, f"/docs/media/analysis/{stage}/img/same.jpg")
        assert kind == "img" and path.read_bytes() == stage.encode()
        token = f"[[media:{media.reference_prefix}/same.jpg]]"
        assert source_media_references(config, token, doc_id=DOC_ID)[0].logical_path.endswith("same.jpg")
    with pytest.raises(ValueError, match="requires stage"):
        local_media_path_from_route(stage_repo, "/docs/media/analysis/img/same.jpg")
    with pytest.raises(ValueError, match="unknown Docs Viewer scope"):
        local_media_path_from_route(stage_repo, "/docs/media/dotlineform/img/same.jpg")


def test_scope_manifest_records_stages_without_retired_source_paths(stage_repo: Path) -> None:
    from docs_scope_manifest import backfilled_scope_record
    config = scopes.load_docs_scope_configs(stage_repo)["analysis"]
    record = backfilled_scope_record(stage_repo, config)
    roles = {item["kind"] for item in record["files"]}
    assert "working/source_documents_root" in roles
    assert "pre-publish/source_documents_root" in roles
    assert "source_documents_root" not in roles
    assert "published_docs_root" in roles
