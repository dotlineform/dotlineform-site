"""Exact source eligibility and document links for the local Unpublishable report."""

from copy import deepcopy
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

from docs_management_test_support import docs_scope_config as scopes
from docs_management_read_service import docs_management_get_payload
from docs_management_routes import GET_PATHS, UNPUBLISHABLE_REPORT_PATH
from docs_source_model import format_source
from docs_unpublishable_report import build_unpublishable_report
from repo_factory import docs_scope_record, docs_sub_scope_record, write_docs_scope_config, write_site_tools_config


EXCLUDED_ID = "d-20260909-160000-000001"
INCLUDED_ID = "d-20260909-160000-000002"


@pytest.fixture
def report_repo(tmp_path: Path) -> Path:
    write_site_tools_config(tmp_path)
    analysis = docs_scope_record("analysis", scope_type="public", viewer_base_url="/analysis/", include_scope_param=False)
    analysis["stages"] = {
        stage: {
            "media": deepcopy(analysis["media"]),
            "sub_scopes": [
                docs_sub_scope_record("analysis", name, title=name.title(), scope_type="public" if stage == "pre-publish" else "local")
                for name in ("works", "concepts")
            ],
        }
        for stage in ("working", "pre-publish")
    }
    write_docs_scope_config(tmp_path, [analysis])
    for stage in ("working", "pre-publish"):
        config = scopes.load_docs_scope_stage(tmp_path, "analysis", stage)
        for sub_scope, collection in [("", config), *[(child.sub_scope, child) for child in config.sub_scopes]]:
            source = scopes.resolve_scope_path(tmp_path, scopes.document_source_path(collection))
            source.mkdir(parents=True)
            for doc_id, included in ((EXCLUDED_ID, False), (INCLUDED_ID, True)):
                fields = {"doc_id": doc_id, "title": "Repeated title"}
                if not included:
                    fields["publishable"] = False
                elif not sub_scope:
                    fields["parent_id"] = EXCLUDED_ID
                (source / f"{doc_id}.md").write_text(format_source(fields, "# Document\n", sub_scope=sub_scope))
        parent = scopes.resolve_scope_path(tmp_path, scopes.document_source_path(config))
        for index, child in enumerate(config.sub_scopes, start=3):
            host_id = f"d-20260909-160000-{index:06d}"
            (parent / f"{host_id}.md").write_text(format_source(
                {"doc_id": host_id, "title": child.title},
                f":::report\nid: docs_subscope\naccess: local\nsub_scope: {child.sub_scope}\n:::\n",
            ))
    return tmp_path


def test_reads_only_ordinary_working_explicit_false(report_repo: Path) -> None:
    assert UNPUBLISHABLE_REPORT_PATH in GET_PATHS
    payload = docs_management_get_payload(report_repo, UNPUBLISHABLE_REPORT_PATH, {"scope": ["analysis"], "stage": ["working"]})
    assert payload["ok"] is True and payload["stage"] == "working"
    rows = payload["rows"]
    assert [(row["target"]["sub_scope"], row["target"]["doc_id"]) for row in rows] == [
        ("", EXCLUDED_ID),
    ]
    for row in rows:
        target = row["target"]
        query = parse_qs(urlparse(row["href"]).query)
        assert target["scope"] == "analysis" and target["stage"] == "working"
        assert query["scope"] == ["analysis"] and query["stage"] == ["working"]
        assert query["subdoc" if target["sub_scope"] else "doc"] == [EXCLUDED_ID]
        if target["sub_scope"]:
            host_index = 3 if target["sub_scope"] == "works" else 4
            assert query["doc"] == [f"d-20260909-160000-{host_index:06d}"]

    # Refresh reads source again, even without a generated document index.
    config = scopes.load_docs_scope_stage(report_repo, "analysis", "working")
    for collection in (config, *config.sub_scopes):
        path = scopes.resolve_scope_path(report_repo, scopes.document_source_path(collection)) / f"{EXCLUDED_ID}.md"
        path.write_text(path.read_text().replace("publishable: false\n", ""))
    assert build_unpublishable_report(report_repo, scope="analysis", stage="working")["rows"] == []


@pytest.mark.parametrize("scope,stage", [("studio", ""), ("analysis", ""), ("analysis", "pre-publish")])
def test_rejects_other_report_owners(report_repo: Path, scope: str, stage: str) -> None:
    with pytest.raises(ValueError, match="only in Analysis Working"):
        build_unpublishable_report(report_repo, scope=scope, stage=stage)
