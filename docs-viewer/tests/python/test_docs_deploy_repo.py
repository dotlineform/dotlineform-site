#!/usr/bin/env python3
"""Focused checks for the accepted-snapshot Deploy Repo boundary."""

from __future__ import annotations

import json
import sys
from http import HTTPStatus
from pathlib import Path

import pytest

from repo_factory import docs_scope_record, docs_sub_scope_record, write_docs_scope_config


REPO_ROOT = Path(__file__).resolve().parents[3]
SERVICES = REPO_ROOT / "docs-viewer/services"
if str(SERVICES) not in sys.path:
    sys.path.insert(0, str(SERVICES))

import docs_deploy_repo  # noqa: E402
import docs_document_publication_lineage as publication_lineage  # noqa: E402
import docs_management_routes  # noqa: E402
import docs_management_service  # noqa: E402
import docs_scope_publish  # noqa: E402


TAG_HOST = "d-20260801-100000-aaaaaa"
WORK_HOST = "d-20260801-100001-bbbbbb"
TAG_DOC = "d-20260801-100002-cccccc"
WORK_DOC = "d-20260801-100003-dddddd"
PROJECTS_LINEAGE_CONTRACT = "dotlineform_projects_to_analysis_works"
PROCESSING_LINEAGE_CONTRACT = "dotlineform_processing_to_analysis_works"


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_config(root: Path, *, media_provider: str = "repository") -> None:
    sub_scopes = [
        docs_sub_scope_record(
            "analysis",
            "tags",
            title="Tags",
            public_title="Concepts",
            scope_type="public",
            analysis_tag_groups=["subject"],
        ),
        docs_sub_scope_record(
            "analysis",
            "works",
            title="Works",
            scope_type="public",
            sub_scope_customisation={"id": "analysis_works", "settings": {}},
            lifecycle={
                "tool_id": "docs-viewer-scope-lifecycle",
                "report_host_doc_id": WORK_HOST,
                "report_host_source_revision": "sha256:" + "1" * 64,
            },
        ),
    ]
    write_docs_scope_config(
        root,
        [
            docs_scope_record(
                "dotlineform",
                sub_scopes=[
                    docs_sub_scope_record(
                        "dotlineform",
                        "projects",
                        sub_scope_customisation={
                            "id": "dotlineform_projects",
                            "settings": {},
                        },
                    ),
                    docs_sub_scope_record(
                        "dotlineform",
                        "processing",
                        sub_scope_customisation={
                            "id": "dotlineform_processing",
                            "settings": {},
                        },
                    ),
                ],
            ),
            docs_scope_record(
                "analysis",
                scope_type="public",
                viewer_base_url="/analysis/",
                include_scope_param=False,
                default_doc_id=TAG_HOST,
                media_provider=media_provider,
                media_types=("img",),
                sub_scopes=sub_scopes,
            )
        ],
    )


def document_payload(doc_id: str, title: str, content_html: str) -> dict[str, object]:
    return {
        "doc_id": doc_id,
        "title": title,
        "content_html": content_html,
    }


def prepare_published(root: Path, *, include_subjects: bool = True) -> str:
    published = root / "docs-viewer/scopes/analysis/published"
    report_html = '<section class="docsViewerReport" data-docs-viewer-report-host aria-label="Document report"></section>'
    files: dict[Path, bytes] = {}

    def add(relative: str, payload: object) -> None:
        files[Path(relative)] = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")

    add(
        "documents/index-tree.json",
        {
            "schema": "docs_index_tree_v1",
            "docs": [
                {"doc_id": TAG_HOST, "title": "Concepts", "content_url": f"/docs/doc?scope=analysis&doc_id={TAG_HOST}"},
                {"doc_id": WORK_HOST, "title": "Works", "content_url": f"/docs/doc?scope=analysis&doc_id={WORK_HOST}"},
            ],
        },
    )
    add(
        "documents/recent.json",
        {
            "schema": "docs_recent_v1",
            "docs": [
                {"doc_id": WORK_HOST, "title": "Works", "content_url": f"/docs/doc?scope=analysis&doc_id={WORK_HOST}"}
            ],
        },
    )
    add(
        f"documents/by-id/{TAG_HOST}.json",
        {
            **document_payload(TAG_HOST, "Concepts", f"<h1>Concepts</h1>{report_html}"),
            "report": {"id": "docs_subscope", "access": "public", "sub_scope": "tags"},
        },
    )
    add(
        f"documents/by-id/{WORK_HOST}.json",
        {
            **document_payload(WORK_HOST, "Works", f"<h1>Works</h1>{report_html}"),
            "report": {"id": "docs_subscope", "access": "public", "sub_scope": "works"},
        },
    )
    add(
        "documents/sub-scopes/tags/manifest.json",
        {"schema": "docs_sub_scope_manifest_v1", "docs": [{"doc_id": TAG_DOC, "title": "tag"}]},
    )
    add(
        f"documents/sub-scopes/tags/by-id/{TAG_DOC}.json",
        document_payload(TAG_DOC, "tag", "<h1>tag</h1>"),
    )
    add(
        "documents/sub-scopes/tags/tag-associations.json",
        {"schema_version": "docs_tag_associations_v1", "associations": []},
    )
    add(
        "documents/sub-scopes/works/manifest.json",
        {"schema": "docs_sub_scope_manifest_v1", "docs": [{"doc_id": WORK_DOC, "title": "Work note"}]},
    )
    add(
        f"documents/sub-scopes/works/by-id/{WORK_DOC}.json",
        document_payload(
            WORK_DOC,
            "Work note",
            '<p><img src="/docs/published/media/analysis/img/picture.png">'
            '<a href="dlf-local:projects/private">private folder</a></p>',
        ),
    )
    if include_subjects:
        add(
            "documents/sub-scopes/works/subject-associations.json",
            {
                "schema_version": "docs_subject_associations_v1",
                "scope": "analysis",
                "sub_scope": "works",
                "subject_generation": "sha256:" + "0" * 64,
                "associations": [
                    {
                        "subject": {"kind": "work", "key": "00638"},
                        "documents": [
                            {
                                "target": {"scope": "analysis", "sub_scope": "works", "doc_id": WORK_DOC},
                                "title": "Work note",
                                "locations": [],
                            }
                        ],
                    }
                ],
            },
        )
    search_docs = [
        {"id": TAG_HOST, "title": "Concepts", "href": f"/analysis/?doc={TAG_HOST}"},
        {"id": WORK_HOST, "title": "Works", "href": f"/analysis/?doc={WORK_HOST}"},
        {
            "id": TAG_DOC,
            "title": "tag",
            "href": f"/analysis/?doc={TAG_HOST}&subdoc={TAG_DOC}",
            "sub_scope": "tags",
            "report_doc_id": TAG_HOST,
            "collection_title": "Tags",
            "display_meta": "2026-08-01 • Tags",
        },
        {
            "id": WORK_DOC,
            "title": "Work note",
            "href": f"/analysis/?doc={WORK_HOST}&subdoc={WORK_DOC}",
            "sub_scope": "works",
            "report_doc_id": WORK_HOST,
        },
    ]
    add(
        "search/index.json",
        {
            "header": {"schema": "docs_viewer_search_index_v2", "scope": "analysis", "version": "accepted", "count": 4},
            "docs": search_docs,
            "terms": {},
        },
    )
    files[Path("media/img/picture.png")] = b"accepted-picture"
    for relative, data in files.items():
        path = published / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    manifest = docs_scope_publish._publish_manifest_payload(
        "analysis",
        "sha256:" + "2" * 64,
        files,
    )
    write_json(published / docs_scope_publish.PUBLISH_MANIFEST_FILENAME, manifest)
    return str(manifest["published_revision"])


def prepare_repo(root: Path) -> str:
    write_config(root)
    revision = prepare_published(root)
    write_json(
        root / "site/assets/works/index/00638.json",
        {
            "header": {
                "schema": "work_record_v4",
                "version": "fixture",
                "generated_at_utc": "2026-08-01T00:00:00Z",
                "work_id": "00638",
                "count": 0,
            },
            "work": {"work_id": "00638", "title": "Fixture Work", "doc_url": []},
            "sections": [],
        },
    )
    write_json(root / "site/assets/data/docs/scopes/analysis/by-id/stale.json", {"title": "stale"})
    (root / "site/assets/data/docs/scopes/analysis/media/img/stale.png").parent.mkdir(parents=True, exist_ok=True)
    (root / "site/assets/data/docs/scopes/analysis/media/img/stale.png").write_bytes(b"stale")
    (root / "site/unrelated.txt").parent.mkdir(parents=True, exist_ok=True)
    (root / "site/unrelated.txt").write_text("keep", encoding="utf-8")
    return revision


def test_capability_exposes_only_writable_analysis_destination(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_config(tmp_path)
    configs = docs_deploy_repo.load_docs_scope_configs(tmp_path)

    assert docs_deploy_repo.deploy_repo_capability(
        tmp_path,
        configs["analysis"],
    ) == {
        "available": True,
        "preview": True,
        "apply": True,
        "reason": "",
    }
    assert docs_deploy_repo.deploy_repo_capability(
        tmp_path,
        configs["dotlineform"],
    ) == {
        "available": False,
        "preview": False,
        "apply": False,
        "reason": "Deploy Repo is available only for Analysis.",
    }

    monkeypatch.setattr(
        docs_deploy_repo,
        "_writable_repository_destination",
        lambda *_args, **_kwargs: False,
    )
    unavailable = docs_deploy_repo.deploy_repo_capability(
        tmp_path,
        configs["analysis"],
    )
    assert unavailable == {
        "available": False,
        "preview": False,
        "apply": False,
        "reason": "The configured repository projection is unavailable.",
    }
    assert "path" not in unavailable


def test_management_capabilities_project_browser_safe_deploy_repo_authority(
    tmp_path: Path,
) -> None:
    write_config(tmp_path)
    (tmp_path / "docs-viewer/scopes/analysis/source/documents").mkdir(
        parents=True,
    )
    payload = docs_management_service.capabilities_payload(tmp_path)

    assert payload["capabilities"]["deploy_repo"] == {
        "preview": True,
        "apply": True,
    }
    assert payload["capabilities"]["scopes"]["analysis"]["deploy_repo"] == {
        "available": True,
        "preview": True,
        "apply": True,
        "reason": "",
    }
    assert payload["capabilities"]["scopes"]["dotlineform"]["deploy_repo"] == {
        "available": False,
        "preview": False,
        "apply": False,
        "reason": "Deploy Repo is available only for Analysis.",
    }


def test_preview_and_apply_use_only_accepted_published_snapshot(tmp_path: Path) -> None:
    revision = prepare_repo(tmp_path)
    preview = docs_deploy_repo.preview_deploy_repo(
        tmp_path,
        {"scope": "analysis", "deployment_timestamp": "2026-08-30T22:00:00Z"},
    )

    assert preview["published_revision"] == revision
    assert preview["document_count"] == 4
    assert "site/assets/data/docs/scopes/analysis/by-id/stale.json" in {
        row["path"] for row in preview["repository"]["changes"] if row["action"] == "remove"
    }
    assert preview["media"]["copy_count"] == 1
    assert preview["media"]["remove_count"] == 1

    result = docs_deploy_repo.apply_deploy_repo(
        tmp_path,
        {
            "scope": "analysis",
            "confirm": True,
            "published_revision": preview["published_revision"],
            "plan_revision": preview["plan_revision"],
            "deployment_timestamp": preview["deployment_timestamp"],
        },
    )

    assert result["complete"] is True
    assert (tmp_path / "site/unrelated.txt").read_text(encoding="utf-8") == "keep"
    assert not (tmp_path / "site/assets/data/docs/scopes/analysis/by-id/stale.json").exists()
    assert not (tmp_path / "site/assets/data/docs/scopes/analysis/works/subject-associations.json").exists()
    assert (tmp_path / "site/assets/data/docs/scopes/analysis/media/img/picture.png").read_bytes() == b"accepted-picture"
    work_payload = json.loads(
        (tmp_path / f"site/assets/data/docs/scopes/analysis/works/by-id/{WORK_DOC}.json").read_text(encoding="utf-8")
    )
    assert "/assets/data/docs/scopes/analysis/media/img/picture.png" in work_payload["content_html"]
    assert "dlf-local:" not in work_payload["content_html"]
    tree = json.loads((tmp_path / "site/assets/data/docs/scopes/analysis/index-tree.json").read_text(encoding="utf-8"))
    assert tree["docs"][0]["content_url"] == f"/assets/data/docs/scopes/analysis/by-id/{TAG_HOST}.json"
    deployed_search = json.loads(
        (tmp_path / "site/assets/data/search/analysis/index.json").read_text(
            encoding="utf-8"
        )
    )
    published_search = json.loads(
        (tmp_path / "docs-viewer/scopes/analysis/published/search/index.json").read_text(
            encoding="utf-8"
        )
    )
    tag_search = next(row for row in deployed_search["docs"] if row["id"] == TAG_DOC)
    assert tag_search["collection_title"] == "Concepts"
    assert tag_search["display_meta"] == "2026-08-01 • Concepts"
    assert deployed_search["terms"] == published_search["terms"]
    catalogue_payload = json.loads(
        (tmp_path / "site/assets/works/index/00638.json").read_text(encoding="utf-8")
    )
    assert catalogue_payload["work"]["doc_url"] == [
        f"/analysis/?doc={WORK_HOST}&subdoc={WORK_DOC}"
    ]


def test_preview_requires_analysis_and_deployment_subject_metadata(tmp_path: Path) -> None:
    write_config(tmp_path)
    prepare_published(tmp_path, include_subjects=False)
    with pytest.raises(FileNotFoundError, match="deployment subject associations"):
        docs_deploy_repo.preview_deploy_repo(tmp_path, {"scope": "analysis"})
    with pytest.raises(ValueError, match="only for the Analysis"):
        docs_deploy_repo.preview_deploy_repo(tmp_path, {"scope": "studio"})


def test_apply_rejects_changed_destination_plan(tmp_path: Path) -> None:
    prepare_repo(tmp_path)
    preview = docs_deploy_repo.preview_deploy_repo(
        tmp_path,
        {"scope": "analysis", "deployment_timestamp": "2026-08-30T22:00:00Z"},
    )
    target = tmp_path / "site/assets/data/docs/scopes/analysis/index-tree.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("changed after preview", encoding="utf-8")
    with pytest.raises(ValueError, match="preview is stale"):
        docs_deploy_repo.apply_deploy_repo(
            tmp_path,
            {
                "scope": "analysis",
                "confirm": True,
                "published_revision": preview["published_revision"],
                "plan_revision": preview["plan_revision"],
                "deployment_timestamp": preview["deployment_timestamp"],
            },
        )


def test_raw_mermaid_requires_accepted_projection_input() -> None:
    payload = {
        "doc_id": WORK_DOC,
        "title": "Diagram",
        "content_html": '<pre><code class="language-mermaid">flowchart LR; A--&gt;B</code></pre>',
    }
    with pytest.raises(RuntimeError, match="accepted Published snapshot"):
        docs_deploy_repo.project_document_payload(
            (json.dumps(payload) + "\n").encode("utf-8"),
            label="accepted diagram",
            media_projection={},
        )


def test_apply_reports_media_failure_after_repository_projection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepare_repo(tmp_path)
    preview = docs_deploy_repo.preview_deploy_repo(
        tmp_path,
        {"scope": "analysis", "deployment_timestamp": "2026-08-30T22:00:00Z"},
    )
    monkeypatch.setattr(
        docs_deploy_repo,
        "apply_public_media_reconciliation",
        lambda *_args, **_kwargs: {
            "operation": "apply",
            "scope": "analysis",
            "copied_count": 0,
            "removed_count": 0,
            "error_count": 1,
            "errors": ["simulated media failure"],
            "types": [],
        },
    )

    result = docs_deploy_repo.apply_deploy_repo(
        tmp_path,
        {
            "scope": "analysis",
            "confirm": True,
            "published_revision": preview["published_revision"],
            "plan_revision": preview["plan_revision"],
            "deployment_timestamp": preview["deployment_timestamp"],
        },
    )

    assert result["applied"] is True
    assert result["complete"] is False
    assert result["error_count"] == 1
    assert (tmp_path / "site/assets/data/docs/scopes/analysis/index-tree.json").is_file()


def test_apply_reconciles_lineage_and_rebuilds_only_working_collection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepare_repo(tmp_path)
    table = publication_lineage.empty_table(
        working_scope="dotlineform",
        working_sub_scope="projects",
        editorial_scope="analysis",
        editorial_sub_scope="works",
    )
    table = publication_lineage.DocumentLineageTable(
        working_collection=table.working_collection,
        editorial_collection=table.editorial_collection,
        records=(
            publication_lineage.DocumentLineageRecord(
                working_doc_id="d-20260801-100010-eeeeee",
                editorials=(
                    publication_lineage.DocumentEditorialChild(
                        doc_id=WORK_DOC,
                        created_at="2026-08-08T10:00:00Z",
                        last_copied_at="2026-08-08T10:00:00Z",
                        published_url=None,
                    ),
                ),
            ),
        ),
    )
    publication_lineage.write_table_atomic(
        tmp_path,
        table,
        contract_id=PROJECTS_LINEAGE_CONTRACT,
    )
    rebuilds: list[tuple[str, str]] = []
    monkeypatch.setattr(
        docs_deploy_repo,
        "rebuild_sub_scope_outputs",
        lambda _root, scope, sub_scope: rebuilds.append((scope, sub_scope)),
    )
    preview = docs_deploy_repo.preview_deploy_repo(
        tmp_path,
        {"scope": "analysis", "deployment_timestamp": "2026-08-30T22:00:00Z"},
    )

    result = docs_deploy_repo.apply_deploy_repo(
        tmp_path,
        {
            "scope": "analysis",
            "confirm": True,
            "published_revision": preview["published_revision"],
            "plan_revision": preview["plan_revision"],
            "deployment_timestamp": preview["deployment_timestamp"],
        },
    )

    assert preview["publication_lineage"]["changed"] is True
    assert result["publication_lineage"]["status"] == "updated"
    projects_result = next(
        record
        for record in result["publication_lineage"]["workflows"]
        if record["contract_id"] == PROJECTS_LINEAGE_CONTRACT
    )
    assert projects_result["working_rebuild"] == {
        "status": "updated",
        "error": "",
    }
    assert rebuilds == [("dotlineform", "projects")]
    reconciled = publication_lineage.load_table(
        tmp_path,
        contract_id=PROJECTS_LINEAGE_CONTRACT,
    )
    assert reconciled is not None
    assert reconciled.records[0].editorials[0].published_url == (
        f"/analysis/?doc={WORK_HOST}&subdoc={WORK_DOC}"
    )


def test_apply_reconciles_every_lineage_workflow_targeting_analysis_works(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepare_repo(tmp_path)
    processing_editorial_id = "d-20260801-100004-eeeeee"
    for contract_id, working_sub_scope, working_doc_id, editorial_doc_id, public_url in (
        (
            PROJECTS_LINEAGE_CONTRACT,
            "projects",
            "d-20260801-100010-eeeeee",
            WORK_DOC,
            None,
        ),
        (
            PROCESSING_LINEAGE_CONTRACT,
            "processing",
            "d-20260801-100011-ffffff",
            processing_editorial_id,
            "/analysis/stale",
        ),
    ):
        table = publication_lineage.empty_table(
            working_scope="dotlineform",
            working_sub_scope=working_sub_scope,
            editorial_scope="analysis",
            editorial_sub_scope="works",
        )
        table = publication_lineage.DocumentLineageTable(
            working_collection=table.working_collection,
            editorial_collection=table.editorial_collection,
            records=(
                publication_lineage.DocumentLineageRecord(
                    working_doc_id=working_doc_id,
                    editorials=(
                        publication_lineage.DocumentEditorialChild(
                            doc_id=editorial_doc_id,
                            created_at="2026-08-08T10:00:00Z",
                            last_copied_at="2026-08-08T10:00:00Z",
                            published_url=public_url,
                        ),
                    ),
                ),
            ),
        )
        publication_lineage.write_table_atomic(
            tmp_path,
            table,
            contract_id=contract_id,
        )

    rebuilds: list[tuple[str, str]] = []
    monkeypatch.setattr(
        docs_deploy_repo,
        "rebuild_sub_scope_outputs",
        lambda _root, scope, sub_scope: rebuilds.append((scope, sub_scope)),
    )
    preview = docs_deploy_repo.preview_deploy_repo(
        tmp_path,
        {"scope": "analysis", "deployment_timestamp": "2026-08-30T22:00:00Z"},
    )

    result = docs_deploy_repo.apply_deploy_repo(
        tmp_path,
        {
            "scope": "analysis",
            "confirm": True,
            "published_revision": preview["published_revision"],
            "plan_revision": preview["plan_revision"],
            "deployment_timestamp": preview["deployment_timestamp"],
        },
    )

    assert preview["publication_lineage"]["changed_count"] == 2
    assert {
        record["contract_id"]
        for record in result["publication_lineage"]["workflows"]
        if record["status"] == "updated"
    } == {PROJECTS_LINEAGE_CONTRACT, PROCESSING_LINEAGE_CONTRACT}
    assert rebuilds == [
        ("dotlineform", "processing"),
        ("dotlineform", "projects"),
    ]
    processing = publication_lineage.load_table(
        tmp_path,
        contract_id=PROCESSING_LINEAGE_CONTRACT,
    )
    assert processing is not None
    assert processing.records[0].editorials[0].published_url is None


def test_apply_reports_projects_rebuild_failure_separately_from_updated_lineage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepare_repo(tmp_path)
    table = publication_lineage.empty_table(
        working_scope="dotlineform",
        working_sub_scope="projects",
        editorial_scope="analysis",
        editorial_sub_scope="works",
    )
    table = publication_lineage.DocumentLineageTable(
        working_collection=table.working_collection,
        editorial_collection=table.editorial_collection,
        records=(
            publication_lineage.DocumentLineageRecord(
                working_doc_id="d-20260801-100010-eeeeee",
                editorials=(
                    publication_lineage.DocumentEditorialChild(
                        doc_id=WORK_DOC,
                        created_at="2026-08-08T10:00:00Z",
                        last_copied_at="2026-08-08T10:00:00Z",
                        published_url=None,
                    ),
                ),
            ),
        ),
    )
    publication_lineage.write_table_atomic(
        tmp_path,
        table,
        contract_id=PROJECTS_LINEAGE_CONTRACT,
    )
    monkeypatch.setattr(
        docs_deploy_repo,
        "rebuild_sub_scope_outputs",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            RuntimeError("simulated Projects rebuild failure")
        ),
    )
    preview = docs_deploy_repo.preview_deploy_repo(
        tmp_path,
        {"scope": "analysis", "deployment_timestamp": "2026-08-30T22:00:00Z"},
    )

    result = docs_deploy_repo.apply_deploy_repo(
        tmp_path,
        {
            "scope": "analysis",
            "confirm": True,
            "published_revision": preview["published_revision"],
            "plan_revision": preview["plan_revision"],
            "deployment_timestamp": preview["deployment_timestamp"],
        },
    )

    assert result["complete"] is False
    assert result["error_count"] == 1
    assert result["publication_lineage"]["status"] == "updated"
    projects_result = next(
        record
        for record in result["publication_lineage"]["workflows"]
        if record["contract_id"] == PROJECTS_LINEAGE_CONTRACT
    )
    assert projects_result["error"] == ""
    assert projects_result["working_rebuild"] == {
        "status": "stale",
        "error": "simulated Projects rebuild failure",
    }
    reconciled = publication_lineage.load_table(
        tmp_path,
        contract_id=PROJECTS_LINEAGE_CONTRACT,
    )
    assert reconciled is not None
    assert reconciled.records[0].editorials[0].published_url == (
        f"/analysis/?doc={WORK_HOST}&subdoc={WORK_DOC}"
    )


def test_management_routes_dispatch_independent_preview_and_apply(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        docs_management_service,
        "refresh_source_model_scope_configs",
        lambda _repo_root: None,
    )
    monkeypatch.setattr(
        docs_management_service.docs_deploy_repo,
        "preview_deploy_repo",
        lambda _repo_root, body: {"operation": "preview", "scope": body["scope"]},
    )
    monkeypatch.setattr(
        docs_management_service.docs_deploy_repo,
        "apply_deploy_repo",
        lambda _repo_root, body: {"operation": "apply", "scope": body["scope"]},
    )

    preview_status, preview = docs_management_service.docs_management_post_response(
        tmp_path,
        docs_management_routes.DEPLOY_REPO_PREVIEW_PATH,
        {"scope": "analysis"},
    )
    apply_status, applied = docs_management_service.docs_management_post_response(
        tmp_path,
        docs_management_routes.DEPLOY_REPO_APPLY_PATH,
        {"scope": "analysis"},
    )

    assert preview_status == HTTPStatus.OK
    assert preview == {"operation": "preview", "scope": "analysis"}
    assert apply_status == HTTPStatus.OK
    assert applied == {"operation": "apply", "scope": "analysis"}
    with pytest.raises(ValueError, match="does not support dry_run"):
        docs_management_service.docs_management_post_response(
            tmp_path,
            docs_management_routes.DEPLOY_REPO_APPLY_PATH,
            {"scope": "analysis"},
            dry_run=True,
        )
