"""Prepared-record aggregation and its full Working rebuild completion boundary."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

import docs_write_rebuild as rebuild
from docs_scope_config import load_docs_scope_stage, generated_documents_path, document_source_path
from docs_scope_links import write_scope_links
from docs_generated_reads import read_generated_scope_links
from docs_management_read_service import docs_management_get_payload
from docs_management_routes import GENERATED_SCOPE_LINKS_PATH, GET_PATHS
from repo_factory import docs_scope_record, docs_sub_scope_record, write_docs_scope_config, write_json


@pytest.fixture
def working(tmp_path):
    scope = docs_scope_record("analysis", scope_type="public", viewer_base_url="/analysis/", include_scope_param=False)
    scope["stages"] = {
        stage: {"media": deepcopy(scope["media"]), "sub_scopes": [docs_sub_scope_record("analysis", "works", scope_type="local" if stage == "working" else "public")]}
        for stage in ("working", "pre-publish")
    }
    write_docs_scope_config(tmp_path, [scope])
    config = load_docs_scope_stage(tmp_path, "analysis", "working")
    output = tmp_path / generated_documents_path(config)
    (output / "links-by-id").mkdir(parents=True)
    (tmp_path / document_source_path(config)).mkdir(parents=True)
    return tmp_path, config, output


def test_aggregate_preserves_records_omits_isolated_and_replaces_removed(working):
    root, config, output = working
    incoming = {"incoming": [{"document": {"title": "Source"}}], "outgoing": [], "counts": {"incoming_occurrences": 2}}
    outgoing = {"incoming": [], "outgoing": [{"occurrences": [{"label": "one"}, {"label": "two"}]}], "self": {"subject": {"kind": "work"}}}
    write_json(output / "links-by-id/b.json", outgoing)
    write_json(output / "links-by-id/a.json", incoming)
    write_json(output / "links-by-id/c.json", {"incoming": [], "outgoing": []})
    assert write_scope_links(root, config) == {"documents": 2, "changed": True}
    assert json.loads((output / "links.json").read_text()) == {
        "schema_version": 1, "scope": "analysis", "stage": "working", "documents": [incoming, outgoing],
    }
    assert write_scope_links(root, config)["changed"] is False
    (output / "links-by-id/a.json").unlink()
    (output / "links-by-id/b.json").unlink()
    assert write_scope_links(root, config)["documents"] == 0
    assert json.loads((output / "links.json").read_text())["documents"] == []


@pytest.mark.parametrize("failure", ["invalid_json", "missing_list", "symlink", "missing_directory"])
def test_unreadable_inputs_preserve_previous_aggregate(working, failure):
    root, config, output = working
    target = output / "links.json"
    target.write_text("previous completed aggregate")
    path = output / "links-by-id/a.json"
    if failure == "invalid_json":
        path.write_text("{")
    elif failure == "missing_list":
        write_json(path, {"outgoing": []})
    elif failure == "symlink":
        path.symlink_to(target)
    else:
        path.parent.rmdir()
    with pytest.raises((ValueError, FileNotFoundError)):
        write_scope_links(root, config)
    assert target.read_text() == "previous completed aggregate"


def test_full_working_rebuild_aggregates_completed_children_before_manifest(working, monkeypatch):
    root, config, output = working
    calls = []
    record = {"incoming": [{"document": {"title": "Neighbour"}}], "outgoing": []}

    def run(command, _root):
        calls.append(command)
        if "--sub-scope" in command:
            write_json(output / "links-by-id/child.json", record)
        return {"command": command, "returncode": 0, "stdout": "", "stderr": "", "elapsed_seconds": 0}

    monkeypatch.setattr(rebuild, "run_rebuild_command", run)
    result = rebuild.rebuild_scope_outputs(root, "analysis", stage="working", include_search=True)
    assert [Path(command[1]).name for command in calls] == ["build_docs.py", "build_docs.py", "build_search.py"]
    assert all(command[command.index("--stage") + 1] == "working" for command in calls)
    assert calls[1][calls[1].index("--sub-scope") + 1] == "works"
    assert result["links"] == {"documents": 1, "changed": True}
    assert json.loads((output / "links.json").read_text())["documents"] == [record]
    assert "documents/links.json" in {row["path"] for row in result["build_manifest"]["files"]}
    before = (output / "links.json").read_bytes()
    rebuild.rebuild_scope_outputs(root, "analysis", stage="working", docs_doc_ids=["single-document"])
    assert (output / "links.json").read_bytes() == before


def test_aggregation_failure_prevents_scope_rebuild_completion(working, monkeypatch):
    root, config, output = working
    (output / "links-by-id/broken.json").write_text("{")
    monkeypatch.setattr(rebuild, "run_rebuild_command", lambda *_args: {
        "returncode": 0, "stdout": "", "stderr": "", "elapsed_seconds": 0,
    })
    with pytest.raises(ValueError, match="invalid JSON"):
        rebuild.rebuild_scope_outputs(root, "analysis", stage="working", include_search=True)
    assert not (output.parent / "build-manifest.json").exists()


def test_scope_read_returns_the_completed_snapshot_without_consulting_inputs(working):
    root, config, output = working
    write_scope_links(root, config)
    path = output / "links.json"
    before = path.read_bytes()
    (output / "links-by-id/unreadable.json").write_text("{")
    assert GENERATED_SCOPE_LINKS_PATH in GET_PATHS
    payload = docs_management_get_payload(root, GENERATED_SCOPE_LINKS_PATH, {"scope": ["analysis"], "stage": ["working"]})
    assert payload == json.loads(before)
    assert path.read_bytes() == before


@pytest.mark.parametrize("scope,stage", [("analysis", None), ("analysis", "pre-publish"), ("studio", "working")])
def test_scope_read_requires_exact_working_owner(working, scope, stage):
    with pytest.raises(ValueError, match="only in Analysis Working"):
        read_generated_scope_links(working[0], scope, stage)


def test_scope_read_distinguishes_missing_invalid_and_wrong_snapshot(working):
    root, _config, output = working
    path = output / "links.json"
    with pytest.raises(FileNotFoundError):
        read_generated_scope_links(root, "analysis", "working")
    path.write_text("{")
    with pytest.raises(RuntimeError, match="not valid JSON"):
        read_generated_scope_links(root, "analysis", "working")
    write_json(path, {"schema_version": 1, "scope": "analysis", "stage": "pre-publish", "documents": []})
    with pytest.raises(ValueError, match="does not match"):
        read_generated_scope_links(root, "analysis", "working")
