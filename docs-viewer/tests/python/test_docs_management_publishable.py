"""Ordinary Working selection validation and atomic publication-intent writes."""

from copy import deepcopy
from pathlib import Path

import pytest

import docs_management_publishable as service
import docs_source_model as source_model
from docs_scope_config import document_source_path, load_docs_scope_stage
from repo_factory import docs_scope_record, write_docs_scope_config, write_site_tools_config


@pytest.fixture
def working_repo(tmp_path: Path) -> tuple[Path, Path, list[str]]:
    write_site_tools_config(tmp_path)
    scope = docs_scope_record("analysis", scope_type="public", viewer_base_url="/analysis/", include_scope_param=False)
    scope["stages"] = {stage: {"media": deepcopy(scope["media"]), "sub_scopes": []} for stage in ("working", "pre-publish")}
    write_docs_scope_config(tmp_path, [scope])
    config = load_docs_scope_stage(tmp_path, "analysis", "working")
    root = tmp_path / document_source_path(config)
    root.mkdir(parents=True)
    ids = [f"d-20260909-180000-{index:06d}" for index in (1, 2)]
    for doc_id in ids:
        fields = {"doc_id": doc_id, "title": doc_id, "draft": True, "ui_status": "review"}
        (root / f"{doc_id}.md").write_text(source_model.format_source(fields, "# Body\n"))
    return tmp_path, root, ids


def request(ids: list[str], **changes: object) -> dict[str, object]:
    return {"scope": "analysis", "stage": "working", "doc_ids": ids, "publishable": False, "confirm": True, **changes}


def test_complete_selection_prevalidated_and_one_rebuild(working_repo, monkeypatch) -> None:
    repo, root, ids = working_repo
    before = {path: path.read_bytes() for path in root.glob("*.md")}
    with pytest.raises(FileNotFoundError):
        service.plan_set_publishable(repo, request([*ids, "missing"]))
    assert all(path.read_bytes() == content for path, content in before.items())
    rebuilds = []
    monkeypatch.setattr(service.write_rebuild, "rebuild_scope_outputs", lambda _root, scope, **options: rebuilds.append((scope, options["stage"], options["docs_doc_ids"])) or {"ok": True})
    result = service.set_publishable(repo, request(ids))
    assert result["updated_doc_ids"] == ids
    assert result["target"] == {"scope": "analysis", "stage": "working"}
    assert rebuilds == [("analysis", "working", ids)]
    for doc_id in ids:
        fields, body = source_model.parse_source(root / f"{doc_id}.md")
        assert fields["publishable"] is False and fields["draft"] is True and fields["ui_status"] == "review"
        assert body == "# Body\n"
    assert service.set_publishable(repo, request(ids))["updated_count"] == 0
    assert len(rebuilds) == 1
    service.set_publishable(repo, request(ids, publishable=True))
    assert all("publishable" not in source_model.parse_source(path)[0] for path in before)


@pytest.mark.parametrize("changes", [{"doc_ids": []}, {"doc_ids": ["same", "same"]}, {"sub_scope": "works"}, {"confirm": False}, {"publishable": "false"}, {"stage": "pre-publish"}])
def test_invalid_target_or_selection_never_writes(working_repo, changes) -> None:
    repo, root, ids = working_repo
    before = {path: path.read_bytes() for path in root.glob("*.md")}
    with pytest.raises(ValueError):
        service.plan_set_publishable(repo, request(ids, **changes))
    assert all(path.read_bytes() == content for path, content in before.items())


def test_stale_batch_snapshot_does_not_write_other_documents(working_repo) -> None:
    repo, root, ids = working_repo
    plan = service.plan_set_publishable(repo, request(ids))
    first, second = [root / f"{doc_id}.md" for doc_id in ids]
    second_before = second.read_bytes()
    first.write_text(first.read_text() + "\nNew authored text.\n")
    first_before = first.read_bytes()
    with pytest.raises(service.PublishableSelectionConflict):
        service.apply_set_publishable_plan(repo, plan)
    assert first.read_bytes() == first_before and second.read_bytes() == second_before
