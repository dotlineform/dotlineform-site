#!/usr/bin/env python3
"""Focused checks for immediate exact public cleanup after document Delete."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import docs_management_mutation_service as mutation_service
import docs_management_mutations as mutations
import docs_publish_gate
import docs_public_delete_cleanup as cleanup
import docs_source_model as source_model
from docs_document_location_projection import build_document_location_payload
from docs_scope_config import load_docs_scope_configs
from repo_factory import (
    docs_scope_record,
    docs_sub_scope_record,
    write_docs_scope_config,
)
from test_docs_document_transfer import make_lineage_repo


PARENT_ID = "d-20260808-100000-aaaaaa"
DESCENDANT_ID = "d-20260808-100050-ababab"
SIBLING_ID = "d-20260808-100100-bbbbbb"
HOST_ID = "d-20260808-110000-cccccc"
CHILD_ID = "d-20260808-110100-dddddd"
CHILD_SIBLING_ID = "d-20260808-110200-eeeeee"


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def search_payload(docs: list[dict[str, str]]) -> dict[str, object]:
    title_postings: dict[str, list[int]] = {}
    identity_postings: dict[str, list[int]] = {}
    for position, document in enumerate(docs):
        identity_postings[document["id"]] = [position]
        for term in document["title"].lower().split():
            title_postings.setdefault(term, []).append(position)
    terms = {
        term: {"title": positions}
        for term, positions in title_postings.items()
    }
    terms.update(
        {
            term: {"identity": positions}
            for term, positions in identity_postings.items()
        }
    )
    return {
        "header": {
            "schema": "docs_viewer_search_index_v2",
            "scope": "analysis",
            "version": "fixture",
            "count": len(docs),
        },
        "fields": ["title", "parent_title", "identity", "last_updated"],
        "docs": docs,
        "terms": terms,
    }


def write_source(
    path: Path,
    doc_id: str,
    title: str,
    body: str | None = None,
    **front_matter: object,
) -> None:
    payload = {
        "doc_id": doc_id,
        "title": title,
        "added_date": "2026-08-08 10:00:00",
        "last_updated": "2026-08-08 10:00:00",
        **front_matter,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        source_model.format_source(payload, body or f"# {title}\n"),
        encoding="utf-8",
    )


def work_payload(urls: list[str]) -> dict[str, object]:
    return {
        "header": {
            "schema": "work_record_v4",
            "version": "fixture",
            "generated_at_utc": "2026-08-08T10:00:00Z",
            "work_id": "00042",
            "count": 0,
        },
        "work": {"work_id": "00042", "title": "Work", "doc_url": urls},
        "sections": [],
    }


def series_payload(urls: list[str]) -> dict[str, object]:
    return {
        "header": {
            "schema": "series_record_v3",
            "version": "fixture",
            "generated_at_utc": "2026-08-08T10:00:00Z",
            "series_id": "001",
            "count": 0,
        },
        "series": {"series_id": "001", "title": "Series", "doc_url": urls},
        "member_works": [],
    }


def write_location_projection(
    repo_root: Path,
    *,
    search: dict[str, object],
    parent_documents: dict[str, object],
    sub_scope_manifests: dict[str, object],
) -> Path:
    config = load_docs_scope_configs(repo_root)["analysis"]
    path = repo_root / "site/assets/data/search/analysis/document-locations.json"
    write_json(
        path,
        build_document_location_payload(
            config,
            search_payload=search,
            parent_documents=parent_documents,
            sub_scope_manifests=sub_scope_manifests,
        ),
    )
    return path


def prepare_parent_repo(repo_root: Path) -> dict[str, Path]:
    write_docs_scope_config(
        repo_root,
        [
            docs_scope_record(
                "analysis",
                scope_type="public",
                viewer_base_url="/analysis/",
                include_scope_param=False,
                default_doc_id=SIBLING_ID,
            )
        ],
    )
    source_root = repo_root / "docs-viewer/scopes/analysis/source/documents"
    write_source(source_root / f"{PARENT_ID}.md", PARENT_ID, "Delete me", work_id="00042")
    write_source(source_root / f"{SIBLING_ID}.md", SIBLING_ID, "Retained")

    docs_root = repo_root / "site/assets/data/docs/scopes/analysis"
    search_path = repo_root / "site/assets/data/search/analysis/index.json"
    tree = {
        "schema": "docs_index_tree_v1",
        "docs": [
            {"doc_id": PARENT_ID, "title": "Delete me"},
            {"doc_id": SIBLING_ID, "title": "Retained"},
        ],
    }
    recent = {
        "schema": "docs_recent_v1",
        "docs": [
            {"doc_id": PARENT_ID, "title": "Delete me"},
            {"doc_id": SIBLING_ID, "title": "Retained"},
        ],
    }
    search = search_payload(
        [
            {
                "id": PARENT_ID,
                "title": "Delete me",
                "href": f"/analysis/?doc={PARENT_ID}",
            },
            {
                "id": SIBLING_ID,
                "title": "Retained",
                "href": f"/analysis/?doc={SIBLING_ID}",
            },
        ],
    )
    parent_payload = {"doc_id": PARENT_ID, "title": "Delete me"}
    sibling_payload = {"doc_id": SIBLING_ID, "title": "Retained", "content_html": "retained"}
    write_json(docs_root / "index-tree.json", tree)
    write_json(docs_root / "recent.json", recent)
    write_json(docs_root / f"by-id/{PARENT_ID}.json", parent_payload)
    write_json(docs_root / f"by-id/{SIBLING_ID}.json", sibling_payload)
    write_json(docs_root / "by-id/out-of-workflow.json", {"title": "Retained stale file"})
    write_json(search_path, search)
    location_path = write_location_projection(
        repo_root,
        search=search,
        parent_documents={PARENT_ID: parent_payload, SIBLING_ID: sibling_payload},
        sub_scope_manifests={},
    )
    for theme in ("dark", "light"):
        mermaid_path = (
            docs_root
            / "projection-assets/mermaid"
            / f"{PARENT_ID}--mermaid-0001/{theme}.svg"
        )
        mermaid_path.parent.mkdir(parents=True, exist_ok=True)
        mermaid_path.write_text(f"<{theme}/>", encoding="utf-8")
    work_path = repo_root / "site/assets/works/index/00042.json"
    write_json(work_path, work_payload([f"/analysis/?doc={PARENT_ID}"]))
    return {
        "source": source_root / f"{PARENT_ID}.md",
        "docs_root": docs_root,
        "search": search_path,
        "locations": location_path,
        "work": work_path,
    }


def prepare_child_repo(repo_root: Path) -> dict[str, Path]:
    write_docs_scope_config(
        repo_root,
        [
            docs_scope_record(
                "analysis",
                scope_type="public",
                viewer_base_url="/analysis/",
                include_scope_param=False,
                default_doc_id=HOST_ID,
                sub_scopes=[
                    docs_sub_scope_record(
                        "analysis",
                        "works",
                        title="Works",
                        scope_type="public",
                    )
                ],
            )
        ],
    )
    parent_source_root = repo_root / "docs-viewer/scopes/analysis/source/documents"
    child_source_root = (
        repo_root
        / "docs-viewer/scopes/analysis/source/sub-scopes/works/documents"
    )
    write_source(
        parent_source_root / f"{HOST_ID}.md",
        HOST_ID,
        "Works",
        body=(
            "# Works\n\n"
            ":::report\n"
            "id: docs_subscope\n"
            "access: public\n"
            "sub_scope: works\n"
            ":::\n"
        ),
    )
    write_source(
        child_source_root / f"{CHILD_ID}.md",
        CHILD_ID,
        "Delete child",
        series_id="001",
    )
    write_source(
        child_source_root / f"{CHILD_SIBLING_ID}.md",
        CHILD_SIBLING_ID,
        "Retained child",
    )

    docs_root = repo_root / "site/assets/data/docs/scopes/analysis"
    child_root = docs_root / "works"
    search_path = repo_root / "site/assets/data/search/analysis/index.json"
    tree = {"docs": [{"doc_id": HOST_ID, "title": "Works"}]}
    recent = {"docs": [{"doc_id": HOST_ID, "title": "Works"}]}
    search = search_payload(
        [
            {
                "id": HOST_ID,
                "title": "Works",
                "href": f"/analysis/?doc={HOST_ID}",
            }
        ],
    )
    host_payload = {
        "doc_id": HOST_ID,
        "title": "Works",
        "report": {
            "id": "docs_subscope",
            "access": "public",
            "scope": None,
            "preset": None,
            "sub_scope": "works",
        },
    }
    manifest = {
        "docs": [
            {"doc_id": CHILD_ID, "title": "Delete child"},
            {"doc_id": CHILD_SIBLING_ID, "title": "Retained child"},
        ]
    }
    write_json(docs_root / "index-tree.json", tree)
    write_json(docs_root / "recent.json", recent)
    write_json(docs_root / f"by-id/{HOST_ID}.json", host_payload)
    write_json(search_path, search)
    write_json(child_root / "manifest.json", manifest)
    write_json(child_root / f"by-id/{CHILD_ID}.json", {"doc_id": CHILD_ID})
    write_json(
        child_root / f"by-id/{CHILD_SIBLING_ID}.json",
        {"doc_id": CHILD_SIBLING_ID, "content_html": "retained"},
    )
    location_path = write_location_projection(
        repo_root,
        search=search,
        parent_documents={HOST_ID: host_payload},
        sub_scope_manifests={"works": manifest},
    )
    child_url = f"/analysis/?doc={HOST_ID}&subdoc={CHILD_ID}"
    series_path = repo_root / "site/assets/series/index/001.json"
    write_json(series_path, series_payload([child_url]))
    return {
        "docs_root": docs_root,
        "child_root": child_root,
        "search": search_path,
        "locations": location_path,
        "series": series_path,
    }


def test_parent_cleanup_removes_exact_projection_and_updates_inventories_and_catalogue(
    tmp_path: Path,
) -> None:
    paths = prepare_parent_repo(tmp_path)
    sibling_path = paths["docs_root"] / f"by-id/{SIBLING_ID}.json"
    sibling_before = sibling_path.read_bytes()
    stale_path = paths["docs_root"] / "by-id/out-of-workflow.json"
    stale_before = stale_path.read_bytes()

    plan = cleanup.plan_public_document_delete_cleanup(
        tmp_path,
        scope="analysis",
        doc_ids=[PARENT_ID],
    )
    result = cleanup.apply_public_document_delete_cleanup(tmp_path, plan)

    assert plan.projected_doc_ids == (PARENT_ID,)
    assert plan.catalogue_targets == (("work", "00042"),)
    assert result["status"] == "applied"
    assert not (paths["docs_root"] / f"by-id/{PARENT_ID}.json").exists()
    assert not (
        paths["docs_root"]
        / f"projection-assets/mermaid/{PARENT_ID}--mermaid-0001"
    ).exists()
    assert sibling_path.read_bytes() == sibling_before
    assert stale_path.read_bytes() == stale_before
    assert [row["doc_id"] for row in read_json(paths["docs_root"] / "index-tree.json")["docs"]] == [SIBLING_ID]
    assert [row["doc_id"] for row in read_json(paths["docs_root"] / "recent.json")["docs"]] == [SIBLING_ID]
    next_search = read_json(paths["search"])
    assert [row["id"] for row in next_search["docs"]] == [SIBLING_ID]
    assert next_search["terms"][SIBLING_ID]["identity"] == [0]
    assert PARENT_ID not in next_search["terms"]
    assert [row["url"] for row in read_json(paths["locations"])["records"]] == [
        f"/analysis/?doc={SIBLING_ID}"
    ]
    assert read_json(paths["work"])["work"]["doc_url"] == []


def test_parent_preview_expands_descendant_public_cleanup(tmp_path: Path) -> None:
    paths = prepare_parent_repo(tmp_path)
    write_source(
        paths["source"].parent / f"{DESCENDANT_ID}.md",
        DESCENDANT_ID,
        "Delete descendant",
        parent_id=PARENT_ID,
    )
    tree = read_json(paths["docs_root"] / "index-tree.json")
    tree["docs"][0]["children"] = [
        {"doc_id": DESCENDANT_ID, "title": "Delete descendant"}
    ]
    write_json(paths["docs_root"] / "index-tree.json", tree)
    recent = read_json(paths["docs_root"] / "recent.json")
    recent["docs"].insert(1, {"doc_id": DESCENDANT_ID, "title": "Delete descendant"})
    write_json(paths["docs_root"] / "recent.json", recent)
    search = read_json(paths["search"])
    search["docs"].insert(
        1,
        {
            "id": DESCENDANT_ID,
            "title": "Delete descendant",
            "href": f"/analysis/?doc={DESCENDANT_ID}",
        },
    )
    write_json(paths["search"], search)
    write_json(
        paths["docs_root"] / f"by-id/{DESCENDANT_ID}.json",
        {"doc_id": DESCENDANT_ID, "title": "Delete descendant"},
    )

    preview = mutations.plan_delete_preview(tmp_path, "analysis", [PARENT_ID])

    assert preview["delete_doc_ids"] == [PARENT_ID, DESCENDANT_ID]
    assert preview["additional_descendant_count"] == 1
    assert preview["public_cleanup"]["projected_doc_ids"] == [
        PARENT_ID,
        DESCENDANT_ID,
    ]


def test_already_unprojected_cleanup_is_unchanged(tmp_path: Path) -> None:
    prepare_parent_repo(tmp_path)
    initial = cleanup.plan_public_document_delete_cleanup(
        tmp_path,
        scope="analysis",
        doc_ids=[PARENT_ID],
    )
    cleanup.apply_public_document_delete_cleanup(tmp_path, initial)

    repeated = cleanup.plan_public_document_delete_cleanup(
        tmp_path,
        scope="analysis",
        doc_ids=[PARENT_ID],
    )
    result = cleanup.apply_public_document_delete_cleanup(tmp_path, repeated)

    assert repeated.projected_doc_ids == ()
    assert repeated.remove_paths == ()
    assert repeated.writes_by_path == {}
    assert repeated.removed_urls == ()
    assert result["status"] == "unchanged"


def test_next_publish_is_idempotent_after_immediate_cleanup(tmp_path: Path) -> None:
    paths = prepare_parent_repo(tmp_path)
    cleanup_plan = cleanup.plan_public_document_delete_cleanup(
        tmp_path,
        scope="analysis",
        doc_ids=[PARENT_ID],
    )
    cleanup.apply_public_document_delete_cleanup(tmp_path, cleanup_plan)

    working_docs = tmp_path / "docs-viewer/scopes/analysis/published/documents"
    for relative_path in (
        Path("index-tree.json"),
        Path("recent.json"),
        Path(f"by-id/{SIBLING_ID}.json"),
    ):
        target = working_docs / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((paths["docs_root"] / relative_path).read_bytes())
    publication_recent = working_docs / ".publish/recent.json"
    publication_recent.parent.mkdir(parents=True, exist_ok=True)
    publication_recent.write_bytes((paths["docs_root"] / "recent.json").read_bytes())
    working_search = tmp_path / "docs-viewer/scopes/analysis/published/search/index.json"
    working_search.parent.mkdir(parents=True, exist_ok=True)
    working_search.write_bytes(paths["search"].read_bytes())

    preview = docs_publish_gate.publish_confirm(tmp_path, {"scope": "analysis"})

    assert preview["changed_count"] == 0
    assert preview["excluded_count"] == 0
    assert preview["up_to_date"] is True
    assert (
        paths["docs_root"] / "by-id/out-of-workflow.json"
    ).is_file()


def test_child_cleanup_leaves_host_and_sibling_bytes_unchanged(tmp_path: Path) -> None:
    paths = prepare_child_repo(tmp_path)
    host_paths = [
        paths["docs_root"] / "index-tree.json",
        paths["docs_root"] / "recent.json",
        paths["docs_root"] / f"by-id/{HOST_ID}.json",
        paths["search"],
    ]
    host_before = {path: path.read_bytes() for path in host_paths}
    sibling_path = paths["child_root"] / f"by-id/{CHILD_SIBLING_ID}.json"
    sibling_before = sibling_path.read_bytes()

    plan = cleanup.plan_public_document_delete_cleanup(
        tmp_path,
        scope="analysis",
        sub_scope="works",
        doc_ids=[CHILD_ID],
    )
    result = cleanup.apply_public_document_delete_cleanup(tmp_path, plan)

    assert result["status"] == "applied"
    assert plan.projected_doc_ids == (CHILD_ID,)
    assert not (paths["child_root"] / f"by-id/{CHILD_ID}.json").exists()
    assert read_json(paths["child_root"] / "manifest.json")["docs"] == [
        {"doc_id": CHILD_SIBLING_ID, "title": "Retained child"}
    ]
    assert sibling_path.read_bytes() == sibling_before
    assert {path: path.read_bytes() for path in host_paths} == host_before
    assert [row["url"] for row in read_json(paths["locations"])["records"]] == [
        f"/analysis/?doc={HOST_ID}",
        f"/analysis/?doc={HOST_ID}&subdoc={CHILD_SIBLING_ID}",
    ]
    assert read_json(paths["series"])["series"]["doc_url"] == []


def test_report_host_cleanup_removes_routes_but_retains_child_files(tmp_path: Path) -> None:
    paths = prepare_child_repo(tmp_path)
    child_files = [
        paths["child_root"] / "manifest.json",
        paths["child_root"] / f"by-id/{CHILD_ID}.json",
        paths["child_root"] / f"by-id/{CHILD_SIBLING_ID}.json",
    ]
    child_before = {path: path.read_bytes() for path in child_files}

    plan = cleanup.plan_public_document_delete_cleanup(
        tmp_path,
        scope="analysis",
        doc_ids=[HOST_ID],
    )
    cleanup.apply_public_document_delete_cleanup(tmp_path, plan)

    assert plan.projected_doc_ids == (HOST_ID,)
    assert plan.removed_urls == (
        f"/analysis/?doc={HOST_ID}",
        f"/analysis/?doc={HOST_ID}&subdoc={CHILD_ID}",
        f"/analysis/?doc={HOST_ID}&subdoc={CHILD_SIBLING_ID}",
    )
    assert {path: path.read_bytes() for path in child_files} == child_before
    assert not (paths["docs_root"] / f"by-id/{HOST_ID}.json").exists()
    assert read_json(paths["locations"])["records"] == []
    assert read_json(paths["series"])["series"]["doc_url"] == []


def test_local_delete_plan_is_not_applicable(tmp_path: Path) -> None:
    write_docs_scope_config(tmp_path, [docs_scope_record("studio")])

    plan = cleanup.plan_public_document_delete_cleanup(
        tmp_path,
        scope="studio",
        doc_ids=[PARENT_ID],
    )

    assert plan.response(tmp_path) == {
        "applicable": False,
        "status": "planned",
        "scope": "studio",
        "sub_scope": "",
        "doc_ids": [PARENT_ID],
        "projected_doc_ids": [],
        "remove_paths": [],
        "changed_paths": [],
        "removed_urls": [],
        "catalogue_targets": [],
    }


def test_confirmed_delete_runs_public_cleanup_after_source_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = prepare_parent_repo(tmp_path)
    public_path = paths["docs_root"] / f"by-id/{PARENT_ID}.json"
    ordering: list[str] = []

    def fake_rebuild(
        _repo_root: Path,
        _scope: str,
        _changed_paths: list[Path],
        write_operation: object,
        **_kwargs: object,
    ) -> dict[str, object]:
        assert public_path.is_file()
        write_operation()  # type: ignore[operator]
        ordering.append("source")
        assert not paths["source"].exists()
        assert public_path.is_file()
        return {"ok": True}

    monkeypatch.setattr(
        mutation_service.write_rebuild,
        "perform_source_write_and_rebuild",
        fake_rebuild,
    )
    monkeypatch.setattr(mutation_service, "log_event", lambda *_args: None)

    preview = mutations.plan_delete_preview(tmp_path, "analysis", [PARENT_ID])
    plan = mutations.plan_delete_apply(
        tmp_path,
        {"scope": "analysis", "doc_ids": [PARENT_ID], "confirm": True},
    )
    result = mutation_service.execute_management_mutation_plan(
        tmp_path,
        plan,
        dry_run=False,
    )

    assert preview["public_cleanup"]["projected_doc_ids"] == [PARENT_ID]
    assert ordering == ["source"]
    assert not paths["source"].exists()
    assert not public_path.exists()
    assert result["public_cleanup"]["status"] == "applied"


@pytest.mark.parametrize(
    ("scope", "sub_scope", "doc_id", "role", "remaining_record_count"),
    [
        (
            "analysis",
            "works",
            "d-20260802-110000-bbbbbb",
            "editorial",
            1,
        ),
        (
            "dotlineform",
            "projects",
            "d-20260801-100000-aaaaaa",
            "working",
            0,
        ),
    ],
)
def test_delete_applies_lineage_after_public_cleanup_and_rebuilds_projects_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    scope: str,
    sub_scope: str,
    doc_id: str,
    role: str,
    remaining_record_count: int,
) -> None:
    repo_root = make_lineage_repo(tmp_path)
    source_path = repo_root / (
        f"docs-viewer/scopes/{scope}/source/sub-scopes/{sub_scope}/"
        f"documents/{doc_id}.md"
    )
    lineage_path = (
        repo_root / "docs-viewer/data/canonical/document-publication-lineage.json"
    )
    lineage_before = lineage_path.read_bytes()
    working_path = repo_root / (
        "docs-viewer/scopes/dotlineform/source/sub-scopes/projects/documents/"
        "d-20260801-100000-aaaaaa.md"
    )
    editorial_paths = tuple(
        repo_root
        / (
            "docs-viewer/scopes/analysis/source/sub-scopes/works/documents/"
            f"{editorial_id}.md"
        )
        for editorial_id in (
            "d-20260802-110000-bbbbbb",
            "d-20260802-120000-cccccc",
        )
    )
    retained_working_bytes = working_path.read_bytes()
    retained_editorial_bytes = {
        path: path.read_bytes()
        for path in editorial_paths
        if path != source_path
    }
    ordering: list[tuple[str, str, str]] = []

    def fake_source_rebuild(
        _repo_root: Path,
        rebuild_scope: str,
        rebuild_sub_scope: str,
        _changed_paths: list[Path],
        write_operation: object,
        **_kwargs: object,
    ) -> dict[str, object]:
        write_operation()  # type: ignore[operator]
        ordering.append(("source", rebuild_scope, rebuild_sub_scope))
        assert not source_path.exists()
        assert lineage_path.read_bytes() == lineage_before
        return {"ok": True, "kind": "source"}

    def fake_public_cleanup(
        _repo_root: Path,
        _plan: object,
    ) -> dict[str, object]:
        ordering.append(("public", scope, sub_scope))
        assert not source_path.exists()
        assert lineage_path.read_bytes() == lineage_before
        return {"ok": True, "status": "applied"}

    def fake_lineage_rebuild(
        _repo_root: Path,
        rebuild_scope: str,
        rebuild_sub_scope: str,
    ) -> dict[str, object]:
        ordering.append(("lineage", rebuild_scope, rebuild_sub_scope))
        assert lineage_path.read_bytes() != lineage_before
        return {"ok": True, "kind": "lineage"}

    monkeypatch.setattr(
        mutation_service.write_rebuild,
        "perform_sub_scope_source_write_and_rebuild",
        fake_source_rebuild,
    )
    monkeypatch.setattr(
        mutation_service.public_delete_cleanup,
        "apply_public_document_delete_cleanup",
        fake_public_cleanup,
    )
    monkeypatch.setattr(
        mutation_service.write_rebuild,
        "rebuild_sub_scope_outputs",
        fake_lineage_rebuild,
    )
    monkeypatch.setattr(mutation_service, "log_event", lambda *_args: None)

    plan = mutations.plan_sub_scope_delete_apply(
        repo_root,
        {
            "scope": scope,
            "sub_scope": sub_scope,
            "doc_id": doc_id,
            "source_revision": mutations.source_revision(source_path.read_bytes()),
            "confirm": True,
        },
    )
    result = mutation_service.execute_management_mutation_plan(
        repo_root,
        plan,
        dry_run=False,
    )

    assert ordering == [
        ("source", scope, sub_scope),
        ("public", scope, sub_scope),
        ("lineage", "dotlineform", "projects"),
    ]
    assert result["lineage"] == {
        "schema_version": "docs_document_publication_lineage_v3",
        "status": "updated",
        "role": role,
        "affected_working_doc_ids": ["d-20260801-100000-aaaaaa"],
        "record_count": remaining_record_count,
        "rebuild": {"ok": True, "kind": "lineage"},
    }
    table = read_json(lineage_path)
    assert len(table["records"]) == remaining_record_count
    if role == "editorial":
        assert working_path.read_bytes() == retained_working_bytes
        assert [
            editorial["doc_id"]
            for editorial in table["records"][0]["editorials"]
        ] == [
            "d-20260802-120000-cccccc",
            "d-20260802-130000-dddddd",
        ]
    else:
        assert {
            path: path.read_bytes()
            for path in retained_editorial_bytes
        } == retained_editorial_bytes


def test_failed_public_cleanup_leaves_lineage_unchanged(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = make_lineage_repo(tmp_path)
    doc_id = "d-20260802-110000-bbbbbb"
    source_path = repo_root / (
        "docs-viewer/scopes/analysis/source/sub-scopes/works/documents/"
        f"{doc_id}.md"
    )
    lineage_path = (
        repo_root / "docs-viewer/data/canonical/document-publication-lineage.json"
    )
    lineage_before = lineage_path.read_bytes()
    lineage_rebuilds: list[object] = []

    def fake_source_rebuild(
        _repo_root: Path,
        _scope: str,
        _sub_scope: str,
        _changed_paths: list[Path],
        write_operation: object,
        **_kwargs: object,
    ) -> dict[str, object]:
        write_operation()  # type: ignore[operator]
        return {"ok": True}

    def failed_public_cleanup(
        _repo_root: Path,
        _plan: object,
    ) -> dict[str, object]:
        raise cleanup.PublicDeleteCleanupApplyError(
            {
                "ok": False,
                "status": "failed",
                "stage": "public_products",
                "error": "simulated public cleanup failure",
            }
        )

    monkeypatch.setattr(
        mutation_service.write_rebuild,
        "perform_sub_scope_source_write_and_rebuild",
        fake_source_rebuild,
    )
    monkeypatch.setattr(
        mutation_service.public_delete_cleanup,
        "apply_public_document_delete_cleanup",
        failed_public_cleanup,
    )
    monkeypatch.setattr(
        mutation_service.write_rebuild,
        "rebuild_sub_scope_outputs",
        lambda *_args: lineage_rebuilds.append(object()),
    )
    monkeypatch.setattr(mutation_service, "log_event", lambda *_args: None)
    plan = mutations.plan_sub_scope_delete_apply(
        repo_root,
        {
            "scope": "analysis",
            "sub_scope": "works",
            "doc_id": doc_id,
            "source_revision": mutations.source_revision(source_path.read_bytes()),
            "confirm": True,
        },
    )

    with pytest.raises(mutation_service.DocumentDeletePublicCleanupError):
        mutation_service.execute_management_mutation_plan(
            repo_root,
            plan,
            dry_run=False,
        )

    assert not source_path.exists()
    assert lineage_path.read_bytes() == lineage_before
    assert lineage_rebuilds == []


def test_catalogue_failure_returns_committed_non_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = prepare_parent_repo(tmp_path)
    plan = cleanup.plan_public_document_delete_cleanup(
        tmp_path,
        scope="analysis",
        doc_ids=[PARENT_ID],
    )
    monkeypatch.setattr(
        "docs_publish_gate.catalogue_document_url_follow_through",
        lambda _repo_root: {
            "status": "stale",
            "stale": True,
            "affected_targets": [{"kind": "work", "key": "00042"}],
            "updated_paths": [],
            "error": "simulated Catalogue failure",
        },
    )

    with pytest.raises(cleanup.PublicDeleteCleanupApplyError) as caught:
        cleanup.apply_public_document_delete_cleanup(tmp_path, plan)

    assert caught.value.result["status"] == "failed"
    assert caught.value.result["stage"] == "catalogue_document_urls"
    assert "simulated Catalogue failure" in caught.value.result["error"]
    assert not (paths["docs_root"] / f"by-id/{PARENT_ID}.json").exists()


def test_delete_executor_reports_committed_when_catalogue_cleanup_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = prepare_parent_repo(tmp_path)

    def fake_rebuild(
        _repo_root: Path,
        _scope: str,
        _changed_paths: list[Path],
        write_operation: object,
        **_kwargs: object,
    ) -> dict[str, object]:
        write_operation()  # type: ignore[operator]
        return {"ok": True}

    monkeypatch.setattr(
        mutation_service.write_rebuild,
        "perform_source_write_and_rebuild",
        fake_rebuild,
    )
    monkeypatch.setattr(mutation_service, "log_event", lambda *_args: None)
    monkeypatch.setattr(
        "docs_publish_gate.catalogue_document_url_follow_through",
        lambda _repo_root: {
            "status": "stale",
            "stale": True,
            "affected_targets": [{"kind": "work", "key": "00042"}],
            "updated_paths": [],
            "error": "simulated Catalogue failure",
        },
    )
    plan = mutations.plan_delete_apply(
        tmp_path,
        {"scope": "analysis", "doc_ids": [PARENT_ID], "confirm": True},
    )

    with pytest.raises(mutation_service.DocumentDeletePublicCleanupError) as caught:
        mutation_service.execute_management_mutation_plan(
            tmp_path,
            plan,
            dry_run=False,
        )

    payload = caught.value.payload
    assert payload["ok"] is False
    assert payload["committed"] is True
    assert payload["retry_delete"] is False
    assert payload["public_cleanup"]["stage"] == "catalogue_document_urls"
    assert not paths["source"].exists()
    assert not (paths["docs_root"] / f"by-id/{PARENT_ID}.json").exists()
