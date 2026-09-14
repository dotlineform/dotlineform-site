"""Exact file reads and the confined local editor action for publication exclusions."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from docs_management_test_support import docs_scope_config as scopes
from docs_management_read_service import docs_management_get_payload
from docs_management_routes import UNPUBLISHABLE_REPORT_PATH
from docs_management_source_service import open_publication_ignore
from docs_publication_ignore import publication_ignore_path, read_publication_ignore_ids
from docs_unpublishable_report import build_unpublishable_report
from repo_factory import docs_scope_record, write_docs_scope_config, write_site_tools_config

EXCLUDED_ID = "d-20260909-160000-000001"
INCLUDED_ID = "d-20260909-160000-000002"


@pytest.fixture
def report_repo(tmp_path: Path) -> Path:
    write_site_tools_config(tmp_path)
    analysis = docs_scope_record("analysis", scope_type="public", viewer_base_url="/analysis/", include_scope_param=False)
    analysis["stages"] = {
        stage: {"media": deepcopy(analysis["media"]), "sub_scopes": []}
        for stage in ("working", "pre-publish")
    }
    write_docs_scope_config(tmp_path, [analysis])
    path = publication_ignore_path(tmp_path, "analysis")
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps([EXCLUDED_ID, EXCLUDED_ID]))
    return tmp_path


def test_refresh_preserves_ids_without_source_or_generated_index(report_repo):
    payload = docs_management_get_payload(report_repo, UNPUBLISHABLE_REPORT_PATH, {"scope": ["analysis"], "stage": ["working"]})
    assert payload == {"ok": True, "schema_version": "docs_unpublishable_report_v3", "scope": "analysis", "stage": "working", "documents": [{"doc_id": EXCLUDED_ID, "title": None}]}
    path = publication_ignore_path(report_repo, "analysis")
    path.write_text(json.dumps([INCLUDED_ID]))
    assert read_publication_ignore_ids(report_repo, "analysis") == {INCLUDED_ID}
    path.write_text("[]")
    assert build_unpublishable_report(report_repo, scope="analysis", stage="working")["documents"] == []


def test_titles_read_only_listed_canonical_sources_and_refresh(report_repo):
    root = publication_ignore_path(report_repo, "analysis").parent
    source = root / f"{EXCLUDED_ID}.md"
    source.write_text(f"---\ndoc_id: {EXCLUDED_ID}\ntitle: First title\n---\n")
    (root / "unrelated.md").write_text("---\ninvalid: [\n---\n")
    assert build_unpublishable_report(report_repo, scope="analysis", stage="working")["documents"] == [{"doc_id": EXCLUDED_ID, "title": "First title"}]
    source.write_text(f"---\ndoc_id: {EXCLUDED_ID}\ntitle: Updated title\n---\n")
    assert build_unpublishable_report(report_repo, scope="analysis", stage="working")["documents"] == [{"doc_id": EXCLUDED_ID, "title": "Updated title"}]
    source.write_text(f"---\ndoc_id: {INCLUDED_ID}\ntitle: Wrong document\n---\n")
    with pytest.raises(ValueError):
        build_unpublishable_report(report_repo, scope="analysis", stage="working")


@pytest.mark.parametrize("content", ["{}", "[1]", '["invalid"]', '["../document.md"]', '[" d-20260909-160000-000001"]', "[", "null"])
def test_invalid_list_fails_instead_of_reusing_previous_values(report_repo, content):
    assert read_publication_ignore_ids(report_repo, "analysis") == {EXCLUDED_ID}
    publication_ignore_path(report_repo, "analysis").write_text(content)
    with pytest.raises(ValueError, match="unpublishable.json"):
        read_publication_ignore_ids(report_repo, "analysis")


def test_missing_file_does_not_read_another_stage_or_create_a_replacement(report_repo):
    path = publication_ignore_path(report_repo, "analysis")
    path.unlink()
    config = scopes.load_docs_scope_stage(report_repo, "analysis", "pre-publish")
    other = scopes.resolve_scope_path(report_repo, scopes.document_source_path(config)) / "unpublishable.json"
    other.parent.mkdir(parents=True)
    other.write_text("[]")
    with pytest.raises(FileNotFoundError):
        read_publication_ignore_ids(report_repo, "analysis")
    assert not path.exists()


def test_symlink_is_not_an_alternate_policy_file(report_repo):
    path = publication_ignore_path(report_repo, "analysis")
    path.unlink()
    substitute = report_repo / "substitute.json"
    substitute.write_text("[]")
    path.symlink_to(substitute)
    with pytest.raises(ValueError, match="configured source directory"):
        read_publication_ignore_ids(report_repo, "analysis")


def test_editor_opens_only_configured_file_even_when_json_needs_repair(report_repo, monkeypatch):
    import docs_management_source_service as service
    path = publication_ignore_path(report_repo, "analysis")
    path.write_text("[")
    opened = []
    monkeypatch.setattr(service, "open_source_path", lambda repo, target, **options: opened.append((repo, target, options)))
    result = open_publication_ignore(report_repo, {"scope": "analysis", "stage": "working"}, True)
    assert result["ok"] is True
    assert opened == [(report_repo, path, {"editor": "vscode", "dry_run": True})]
    with pytest.raises(ValueError, match="only scope and Working"):
        open_publication_ignore(report_repo, {"scope": "analysis", "stage": "working", "path": "/unrelated"}, True)
    assert len(opened) == 1


@pytest.mark.parametrize("scope,stage", [("studio", ""), ("analysis", ""), ("analysis", "pre-publish")])
def test_rejects_other_report_owners(report_repo, scope, stage):
    with pytest.raises(ValueError, match="only in Working"):
        build_unpublishable_report(report_repo, scope=scope, stage=stage)
