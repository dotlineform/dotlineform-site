#!/usr/bin/env python3
"""Direct Docs Viewer document-package service contracts."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import shutil
from threading import Thread
import urllib.error
import urllib.request

import pytest

from docs_document_packages import service
from docs_document_packages.workspace import workspace_paths
import docs_document_package_routes as routes
import docs_import_document_package as import_package
import docs_import_source_service as import_source_service
from docs_document_packages.returned_parser import parse_staged_import
from docs_document_packages.returned_common import RETURN_IMPORT_CAPABILITY
from docs_management_document_target import resolve_managed_document_collection
import docs_source_model as source_model
from docs_viewer_service import DocsViewerServer, DocsViewerServiceConfig
from repo_factory import (
    docs_sub_scope_record,
    make_docs_import_repo,
    resolve_data_sharing_marker,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
PARENT_ROOT_ID = "d-20260728-100000-000001"
PARENT_CHILD_ID = "d-20260728-100000-000002"
TAG_A_ID = "d-20260728-100000-000101"
TAG_B_ID = "d-20260728-100000-000102"
NOTE_ID = "d-20260728-100000-000201"


def write_sub_scope_source_doc(
    repo_root: Path,
    sub_scope: str,
    doc_id: str,
    *,
    title: str,
    parent_id: str = "",
    summary: str = "",
    viewable: bool = True,
) -> None:
    lines = [
        "---",
        f"doc_id: {doc_id}",
        f"title: {title}",
        "added_date: 2026-07-28",
        "last_updated: 2026-07-28",
    ]
    if parent_id:
        lines.append(f"parent_id: {parent_id}")
    if summary:
        lines.append(f"summary: {summary}")
    if not viewable:
        lines.append("viewable: false")
    lines.extend(["---", "", f"# {title}", "", f"{title} body.", ""])
    path = (
        repo_root
        / "docs-viewer/scopes/library/source/sub-scopes"
        / sub_scope
        / "documents"
        / f"{doc_id}.md"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def add_sub_scope_package_fixture(
    repo_root: Path,
    *,
    tags_return_import_enabled: bool = False,
) -> None:
    config_path = repo_root / "docs-viewer/config/scopes/docs_scopes.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["scopes"][0]["default_doc_id"] = PARENT_ROOT_ID
    config["scopes"][0]["sub_scopes"] = [
        docs_sub_scope_record(
            "library",
            "tags",
            title="Tags",
            supports_return_import=tags_return_import_enabled,
            scope_type="public",
            public_docs_path="site/assets/data/docs/scopes/library/tags",
        ),
        docs_sub_scope_record(
            "library",
            "notes",
            title="Notes",
            scope_type="public",
            public_docs_path="site/assets/data/docs/scopes/library/notes",
        ),
    ]
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    profiles_path = repo_root / "docs-viewer/config/document-packages/profiles.json"
    profiles = json.loads(profiles_path.read_text(encoding="utf-8"))
    content_profile = profiles["configs"][0]
    content_profile["content_format"] = {
        "format": "markdown",
        "supported_formats": ["markdown", "plain_text"],
    }
    content_profile["document_fields"].append(
        {
            "source": "content",
            "output_path": "content",
            "required": True,
            "transforms": [
                "plain_text_from_rendered_html",
                "normalize_whitespace",
            ],
        }
    )
    profiles_path.write_text(json.dumps(profiles, indent=2) + "\n", encoding="utf-8")
    library_path = repo_root / "docs-viewer/scopes/library/source/documents/library.md"
    library_path.write_text(
        library_path.read_text(encoding="utf-8").replace(
            "doc_id: library",
            f"doc_id: {PARENT_ROOT_ID}",
        ),
        encoding="utf-8",
    )
    alpha_path = repo_root / "docs-viewer/scopes/library/source/documents/alpha.md"
    alpha_path.write_text(
        alpha_path.read_text(encoding="utf-8")
        .replace("doc_id: alpha", f"doc_id: {PARENT_CHILD_ID}")
        .replace("parent_id: library", f"parent_id: {PARENT_ROOT_ID}"),
        encoding="utf-8",
    )
    write_sub_scope_source_doc(
        repo_root,
        "tags",
        TAG_A_ID,
        title="Tag A",
    )
    write_sub_scope_source_doc(
        repo_root,
        "tags",
        TAG_B_ID,
        title="Tag B",
        parent_id=TAG_A_ID,
        summary="Existing summary.",
        viewable=False,
    )
    write_sub_scope_source_doc(
        repo_root,
        "notes",
        NOTE_ID,
        title="Note Only",
    )


def add_document_tree_profile(repo_root: Path) -> None:
    profiles_path = repo_root / "docs-viewer/config/document-packages/profiles.json"
    profiles = json.loads(profiles_path.read_text(encoding="utf-8"))
    tree_profile = json.loads(json.dumps(profiles["configs"][0]))
    tree_profile.update(
        {
            "id": "document-tree",
            "label": "Document tree",
            "target": {"format": "json", "record_shape": "document_tree"},
            "output": {
                "path_pattern": "{timestamp}-{profile_id}.json",
                "timestamp_format": "%Y%m%d-%H%M%S",
            },
            "workflow": {
                "supports_docs_review": False,
                "supports_return_import": False,
            },
        }
    )
    tree_profile["selection"]["include_descendants"] = True
    tree_profile.pop("content_format", None)
    tree_profile["document_fields"] = [
        {"source": "doc_id", "output_path": "doc_id", "required": True},
        {"source": "title", "output_path": "title", "required": True},
    ]
    profiles["configs"].append(tree_profile)
    profiles_path.write_text(json.dumps(profiles, indent=2) + "\n", encoding="utf-8")


def write_returned_package(
    export_id: str,
    *,
    selected_doc_ids: list[str],
    rows: list[dict[str, object]],
    filename: str = "returned.jsonl",
    scope: str = "library",
    sub_scope: str = "",
    supports_docs_review: bool = True,
    supports_return_import: bool = True,
) -> None:
    paths = workspace_paths()
    paths.import_staging.mkdir(parents=True, exist_ok=True)
    paths.meta.mkdir(parents=True, exist_ok=True)
    (paths.import_staging / filename).write_text(
        "".join(
            json.dumps(row) + "\n"
            for row in [
                {
                    "record_type": "data_sharing_header",
                    "schema_version": "data_sharing_returned_package_v1",
                    "export_id": export_id,
                },
                *rows,
            ]
        ),
        encoding="utf-8",
    )
    metadata = {
        "schema_version": "data_sharing_export_meta_v1",
        "export_id": export_id,
        "app": "docs-viewer",
        "adapter_id": "documents",
        "data_domain": "documents",
        "config_id": "document-content",
        "profile_id": "document-content",
        "scope": scope,
        "target_format": "jsonl",
        "record_shape": "document_rows",
        "generated_at": "2026-07-20T12:00:00Z",
        "supports_docs_review": supports_docs_review,
        "supports_return_import": supports_return_import,
        "content_format": "markdown",
        "selected_doc_ids": selected_doc_ids,
    }
    if sub_scope:
        metadata["sub_scope"] = sub_scope
    (paths.meta / f"{export_id}.meta.json").write_text(
        json.dumps(metadata)
        + "\n",
        encoding="utf-8",
    )


def test_fixed_routes_and_config_contract() -> None:
    with make_docs_import_repo() as temp:
        repo_root = Path(temp)
        payload = service.get_payload(repo_root, routes.CONFIG_PATH, {})

    assert routes.GET_PATHS == (
        "/docs/packages/config",
        "/docs/packages/documents",
        "/docs/packages/returned",
    )
    assert set(routes.POST_PATHS) == {
        "/docs/packages/prepare",
        "/docs/packages/returned/review",
    }
    assert [profile["profile_id"] for profile in payload["profiles"]] == ["document-content"]
    assert payload["profiles"][0]["selection"] == {
        "mode": "explicit_doc_ids",
        "include_descendants": False,
        "include_non_viewable": True,
        "supports_include_non_viewable": True,
        "supports_missing_summary_only": True,
        "default_missing_summary_only": False,
    }
    assert payload["profiles"][0]["limits"] == {"max_documents": None}
    assert "external_context" not in payload["profiles"][0]
    assert "document_fields" not in payload["profiles"][0]
    assert "review_actions" not in payload
    assert "apply_actions" not in payload
    assert payload["scopes"] == [{"scope": "library", "label": "Library"}]
    assert payload["workspace"].keys() == {"available", "message"}


def test_prepare_uses_direct_fields_and_rejects_adapter_contract_fields() -> None:
    with make_docs_import_repo() as temp:
        repo_root = Path(temp)
        status, payload = service.post_response(
            repo_root,
            routes.PREPARE_PATH,
            {
                "scope": "library",
                "profile_id": "document-content",
                "doc_ids": ["alpha"],
                "select_all": False,
                "dry_run": True,
            },
        )
        with pytest.raises(ValueError, match="generic adapter fields"):
            service.post_response(
                repo_root,
                routes.PREPARE_PATH,
                {
                    "data_domain": "documents",
                    "scope": "library",
                    "profile_id": "document-content",
                    "doc_ids": ["alpha"],
                },
            )
        with pytest.raises(ValueError, match="atomic"):
            service.post_response(
                repo_root,
                routes.RETURNED_REVIEW_PATH,
                {
                    "scope": "library",
                    "staged_filename": "returned.jsonl",
                    "record_indices": [0],
                },
            )

    assert int(status) == 200
    assert payload["ok"] is True
    assert payload["profile_id"] == "document-content"
    assert "config_id" not in payload
    assert "data_domain" not in payload
    assert "adapter_id" not in payload
    assert payload["counts"]["exported"] == 1
    assert payload["output_written"] is False


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("missing_summary_only", None),
        ("missing_summary_only", "true"),
        ("include_non_viewable", None),
        ("include_non_viewable", 1),
    ],
)
def test_prepare_type_checks_filter_choices(field: str, value: object) -> None:
    with make_docs_import_repo() as temp:
        with pytest.raises(ValueError, match=rf"{field} must be true or false"):
            service.prepare_package(
                Path(temp),
                {
                    "scope": "library",
                    "profile_id": "document-content",
                    "doc_ids": ["alpha"],
                    field: value,
                    "dry_run": True,
                },
            )


def test_prepare_revalidates_stale_summary_without_broadening_target() -> None:
    with make_docs_import_repo() as temp:
        repo_root = Path(temp)
        source_path = repo_root / "docs-viewer/scopes/library/source/documents/alpha.md"
        source_path.write_text(
            source_path.read_text(encoding="utf-8").replace(
                "---\n\n# Body",
                "summary: Existing summary.\n---\n\n# Body",
            ),
            encoding="utf-8",
        )
        status, payload = service.post_response(
            repo_root,
            routes.PREPARE_PATH,
            {
                "scope": "library",
                "profile_id": "document-content",
                "doc_ids": ["library", "alpha"],
                "select_all": False,
                "missing_summary_only": True,
                "include_non_viewable": True,
                "dry_run": True,
            },
        )

    assert int(status) == 200
    assert payload["selected_doc_ids"] == ["library"]
    assert payload["exported_doc_ids"] == ["library"]
    assert payload["skipped"] == [{"doc_id": "alpha", "reason": "has_summary"}]
    assert payload["counts"] == {"selected": 2, "exported": 1, "skipped": 1, "failed": 0, "truncated": 0}


def test_direct_prepare_treats_tree_doc_ids_as_the_final_target() -> None:
    with make_docs_import_repo() as temp:
        repo_root = Path(temp)
        profiles_path = repo_root / "docs-viewer/config/document-packages/profiles.json"
        profiles = json.loads(profiles_path.read_text(encoding="utf-8"))
        tree_profile = json.loads(json.dumps(profiles["configs"][0]))
        tree_profile.update(
            {
                "id": "document-tree",
                "label": "Document tree",
                "target": {"format": "json", "record_shape": "document_tree"},
                "output": {
                    "path_pattern": "{timestamp}-{profile_id}.json",
                    "timestamp_format": "%Y%m%d-%H%M%S",
                },
                "workflow": {
                    "supports_docs_review": False,
                    "supports_return_import": False,
                },
            }
        )
        tree_profile["selection"] = {
            "mode": "explicit_doc_ids",
            "include_descendants": True,
            "include_non_viewable": True,
            "supports_include_non_viewable": False,
            "supports_missing_summary_only": False,
            "default_missing_summary_only": False,
        }
        profiles["configs"].append(tree_profile)
        profiles_path.write_text(json.dumps(profiles, indent=2) + "\n", encoding="utf-8")

        status, payload = service.post_response(
            repo_root,
            routes.PREPARE_PATH,
            {
                "scope": "library",
                "profile_id": "document-tree",
                "doc_ids": ["library"],
                "select_all": False,
                "missing_summary_only": False,
                "include_non_viewable": True,
                "dry_run": True,
            },
        )
        missing_status, missing_payload = service.post_response(
            repo_root,
            routes.PREPARE_PATH,
            {
                "scope": "library",
                "profile_id": "document-tree",
                "doc_ids": ["library"],
                "select_all": False,
                "missing_summary_only": True,
                "include_non_viewable": True,
                "dry_run": True,
            },
        )
        non_viewable_status, non_viewable_payload = service.post_response(
            repo_root,
            routes.PREPARE_PATH,
            {
                "scope": "library",
                "profile_id": "document-tree",
                "doc_ids": ["library"],
                "select_all": False,
                "missing_summary_only": False,
                "include_non_viewable": False,
                "dry_run": True,
            },
        )

    assert int(status) == 200
    assert payload["selected_doc_ids"] == ["library"]
    assert payload["exported_doc_ids"] == ["library"]
    assert payload["counts"] == {"selected": 1, "exported": 1, "skipped": 0, "failed": 0, "truncated": 0}
    assert int(missing_status) == 400
    assert "config document-tree: missing_summary_only true is not supported" in missing_payload["errors"]
    assert int(non_viewable_status) == 400
    assert (
        "config document-tree: include_non_viewable cannot override the profile default"
        in non_viewable_payload["errors"]
    )


def test_package_document_feed_keeps_non_viewable_source_selectable() -> None:
    with make_docs_import_repo() as temp:
        repo_root = Path(temp)
        source_path = repo_root / "docs-viewer/scopes/library/source/documents/alpha.md"
        source_path.write_text(
            source_path.read_text(encoding="utf-8").replace(
                "---\n\n# Body",
                "viewable: false\n---\n\n# Body",
            ),
            encoding="utf-8",
        )
        payload = service.documents_payload(repo_root, {"scope": ["library"]})

    alpha = next(record for record in payload["records"] if record["doc_id"] == "alpha")
    assert alpha["viewable"] is False
    assert alpha["selectable"] is True
    assert "published" not in alpha
    assert alpha["issues"] == [{"level": "warning", "message": "Document is not viewable."}]


def test_sub_scope_config_and_documents_are_flat_export_only() -> None:
    with make_docs_import_repo() as temp:
        repo_root = Path(temp)
        add_sub_scope_package_fixture(repo_root)
        profiles_path = repo_root / "docs-viewer/config/document-packages/profiles.json"
        profiles_before = profiles_path.read_text(encoding="utf-8")

        top_level = service.get_payload(repo_root, routes.CONFIG_PATH, {})
        child = service.get_payload(
            repo_root,
            routes.CONFIG_PATH,
            {"scope": ["library"], "sub_scope": ["tags"]},
        )
        documents = service.get_payload(
            repo_root,
            routes.DOCUMENTS_PATH,
            {"scope": ["library"], "sub_scope": ["tags"]},
        )
        with pytest.raises(ValueError, match="unknown sub_scope"):
            service.get_payload(
                repo_root,
                routes.CONFIG_PATH,
                {"scope": ["library"], "sub_scope": ["missing"]},
            )
        with pytest.raises(ValueError, match="sub_scope is required"):
            service.get_payload(
                repo_root,
                routes.DOCUMENTS_PATH,
                {"scope": ["library"], "sub_scope": [""]},
            )
        profiles_after = profiles_path.read_text(encoding="utf-8")

    assert "scope" not in top_level
    assert "sub_scope" not in top_level
    assert top_level["profiles"][0]["supports_docs_review"] is True
    assert top_level["profiles"][0]["supports_return_import"] is True
    assert child["scope"] == "library"
    assert child["sub_scope"] == "tags"
    assert child["flat_collection"] is True
    assert child["profiles"][0]["supports_docs_review"] is True
    assert child["profiles"][0]["supports_return_import"] is False
    assert child["profiles"][0]["selection"]["include_descendants"] is False
    assert documents["scope"] == "library"
    assert documents["sub_scope"] == "tags"
    assert documents["selection_model"] == "sub_scope_documents"
    assert documents["flat_collection"] is True
    assert documents["source"] == {
        "kind": "docs_sub_scope_source",
        "scope": "library",
        "sub_scope": "tags",
    }
    assert [record["doc_id"] for record in documents["records"]] == [TAG_A_ID, TAG_B_ID]
    assert documents["records"][1]["viewable"] is False
    assert documents["records"][1]["summary"] == "Existing summary."
    assert profiles_after == profiles_before


def test_sub_scope_filters_only_subtract_from_checked_ids(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[tuple[str, dict[str, object]]] = []
    monkeypatch.setattr(
        service,
        "log_event",
        lambda _repo_root, event, details: events.append((event, details)),
    )
    with make_docs_import_repo() as temp:
        repo_root = Path(temp)
        add_sub_scope_package_fixture(repo_root)
        _, missing_summary = service.post_response(
            repo_root,
            routes.PREPARE_PATH,
            {
                "scope": "library",
                "sub_scope": "tags",
                "profile_id": "document-content",
                "doc_ids": [TAG_B_ID, TAG_A_ID],
                "select_all": False,
                "missing_summary_only": True,
                "include_non_viewable": True,
                "dry_run": True,
            },
        )
        _, viewable_only = service.post_response(
            repo_root,
            routes.PREPARE_PATH,
            {
                "scope": "library",
                "sub_scope": "tags",
                "profile_id": "document-content",
                "doc_ids": [TAG_B_ID, TAG_A_ID],
                "select_all": False,
                "missing_summary_only": False,
                "include_non_viewable": False,
                "dry_run": True,
            },
        )

    for payload in (missing_summary, viewable_only):
        assert payload["scope"] == "library"
        assert payload["sub_scope"] == "tags"
        assert payload["supports_docs_review"] is True
        assert payload["supports_return_import"] is False
        assert payload["selected_doc_ids"] == [TAG_A_ID]
        assert payload["exported_doc_ids"] == [TAG_A_ID]
    assert missing_summary["skipped"] == [{"doc_id": TAG_B_ID, "reason": "has_summary"}]
    assert viewable_only["skipped"] == [{"doc_id": TAG_B_ID, "reason": "non_viewable"}]
    assert events == [
        (
            "document-package-prepare",
            {
                "scope": "library",
                "sub_scope": "tags",
                "profile_id": "document-content",
                "dry_run": True,
                "output_written": False,
                "exported": 1,
                "doc_ids": [TAG_A_ID],
            },
        ),
        (
            "document-package-prepare",
            {
                "scope": "library",
                "sub_scope": "tags",
                "profile_id": "document-content",
                "dry_run": True,
                "output_written": False,
                "exported": 1,
                "doc_ids": [TAG_A_ID],
            },
        ),
    ]


@pytest.mark.parametrize("invalid_doc_id", [PARENT_CHILD_ID, NOTE_ID, "missing"])
def test_sub_scope_prepare_rejects_cross_collection_and_stale_ids(
    invalid_doc_id: str,
) -> None:
    with make_docs_import_repo() as temp:
        repo_root = Path(temp)
        add_sub_scope_package_fixture(repo_root)
        paths = workspace_paths()
        outputs_before = set(paths.exports.rglob("*")) if paths.exports.exists() else set()
        status, payload = service.post_response(
            repo_root,
            routes.PREPARE_PATH,
            {
                "scope": "library",
                "sub_scope": "tags",
                "profile_id": "document-content",
                "doc_ids": [TAG_A_ID, invalid_doc_id],
                "select_all": False,
                "dry_run": False,
            },
        )
        outputs_after = set(paths.exports.rglob("*")) if paths.exports.exists() else set()

    assert int(status) == 400
    assert payload["ok"] is False
    assert payload["sub_scope"] == "tags"
    assert payload["output_written"] is False
    assert invalid_doc_id in " ".join(payload["errors"])
    assert outputs_after == outputs_before


def test_sub_scope_prepare_rejects_select_all_and_extra_collection_fields() -> None:
    with make_docs_import_repo() as temp:
        repo_root = Path(temp)
        add_sub_scope_package_fixture(repo_root)
        with pytest.raises(ValueError, match="select_all false"):
            service.post_response(
                repo_root,
                routes.PREPARE_PATH,
                {
                    "scope": "library",
                    "sub_scope": "tags",
                    "profile_id": "document-content",
                    "doc_ids": [TAG_A_ID],
                    "select_all": True,
                    "dry_run": True,
                },
            )
        with pytest.raises(ValueError, match="only scope and optional sub_scope"):
            service.post_response(
                repo_root,
                routes.PREPARE_PATH,
                {
                    "scope": "library",
                    "sub_scope": "tags",
                    "collection": {"scope": "library", "sub_scope": "tags"},
                    "profile_id": "document-content",
                    "doc_ids": [TAG_A_ID],
                    "dry_run": True,
                },
            )


def test_sub_scope_tree_profile_keeps_exact_checked_records_as_roots() -> None:
    with make_docs_import_repo() as temp:
        repo_root = Path(temp)
        add_sub_scope_package_fixture(repo_root)
        add_document_tree_profile(repo_root)
        _, payload = service.post_response(
            repo_root,
            routes.PREPARE_PATH,
            {
                "scope": "library",
                "sub_scope": "tags",
                "profile_id": "document-tree",
                "doc_ids": [TAG_A_ID],
                "select_all": False,
                "missing_summary_only": False,
                "include_non_viewable": True,
                "dry_run": False,
            },
        )
        output_path = resolve_data_sharing_marker(payload["output_file"])
        output = json.loads(output_path.read_text(encoding="utf-8"))
        source_format = import_package.document_package_source_format(
            repo_root,
            output_path,
            metadata_root=workspace_paths().meta,
        )

    assert payload["ok"] is True
    assert payload["selected_doc_ids"] == [TAG_A_ID]
    assert payload["exported_doc_ids"] == [TAG_A_ID]
    assert output["docs"] == [{"doc_id": TAG_A_ID, "title": "Tag A"}]
    assert source_format == import_package.EXPORT_ONLY_COLLECTION_SOURCE_FORMAT


def test_sub_scope_written_package_is_reviewable_but_blocked_from_import() -> None:
    with make_docs_import_repo() as temp:
        repo_root = Path(temp)
        add_sub_scope_package_fixture(repo_root)
        _, payload = service.post_response(
            repo_root,
            routes.PREPARE_PATH,
            {
                "scope": "library",
                "sub_scope": "tags",
                "profile_id": "document-content",
                "doc_ids": [TAG_B_ID, TAG_A_ID],
                "select_all": False,
                "missing_summary_only": False,
                "include_non_viewable": True,
                "dry_run": False,
            },
        )
        paths = workspace_paths()
        metadata = json.loads(
            (paths.meta / f"{payload['export_id']}.meta.json").read_text(encoding="utf-8")
        )
        output_path = resolve_data_sharing_marker(payload["output_file"])
        output_rows = [
            json.loads(line)
            for line in output_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        staged_filename = "returned-tags.jsonl"
        shutil.copy2(output_path, paths.import_staging / staged_filename)
        returned = service.returned_payload(repo_root, {"scope": ["library"]})
        review = service.review_returned(
            repo_root,
            {
                "scope": "library",
                "staged_filename": staged_filename,
                "dry_run": False,
            },
        )
        assert review["ok"] is True, review["issues"]
        reopened_review = service.review_returned(
            repo_root,
            {
                "scope": "library",
                "staged_filename": staged_filename,
                "dry_run": False,
            },
        )
        review_manifest = json.loads(
            resolve_data_sharing_marker(review["manifest_path"]).read_text(
                encoding="utf-8"
            )
        )
        review_sources = {
            record["doc_id"]: source_model.parse_source(
                resolve_data_sharing_marker(record["path"])
            )[0]
            for record in review["source_files"]
        }
        import_files = import_source_service.handle_import_source_files(repo_root)
        source_before = (
            repo_root / "docs-viewer/scopes/library/source/documents/alpha.md"
        ).read_text(encoding="utf-8")
        dependencies = import_source_service.ImportSourceDependencies(
            log_event=lambda *_args, **_kwargs: None,
            perform_source_write_and_rebuild=lambda *_args, **_kwargs: {},
            perform_scope_source_write_and_rebuild_atomic=(
                lambda *_args, **_kwargs: {}
            ),
            perform_sub_scope_source_write_and_rebuild=lambda *_args, **_kwargs: {},
        )
        with pytest.raises(ValueError, match="Export-only document packages"):
            import_source_service.handle_import_source(
                repo_root,
                {
                    "scope": "library",
                    "staged_filename": staged_filename,
                    "preview_only": False,
                },
                False,
                dependencies,
                staging_root=paths.import_staging,
                workspace_root=paths.root,
                metadata_root=paths.meta,
                destination=resolve_managed_document_collection(
                    repo_root,
                    scope="library",
                ),
            )
        source_after = (
            repo_root / "docs-viewer/scopes/library/source/documents/alpha.md"
        ).read_text(encoding="utf-8")

    assert payload["ok"] is True
    assert payload["scope"] == "library"
    assert payload["sub_scope"] == "tags"
    assert payload["supports_docs_review"] is True
    assert payload["supports_return_import"] is False
    assert payload["selected_doc_ids"] == [TAG_A_ID, TAG_B_ID]
    assert payload["exported_doc_ids"] == [TAG_A_ID, TAG_B_ID]
    assert payload["counts"] == {
        "selected": 2,
        "exported": 2,
        "failed": 0,
        "skipped": 0,
        "truncated": 0,
    }
    assert metadata["scope"] == "library"
    assert metadata["sub_scope"] == "tags"
    assert metadata["supports_docs_review"] is True
    assert metadata["supports_return_import"] is False
    assert metadata["selected_doc_ids"] == [TAG_A_ID, TAG_B_ID]
    assert "context_file" not in payload
    assert [row["doc_id"] for row in output_rows[1:]] == [TAG_A_ID, TAG_B_ID]
    assert len(returned["files"]) == 1
    assert returned["files"][0]["filename"] == staged_filename
    assert returned["files"][0]["sub_scope"] == "tags"
    assert returned["files"][0]["scope_label"] == "Library"
    assert returned["files"][0]["sub_scope_label"] == "Tags"
    assert returned["files"][0]["docs_review_supported"] is True
    assert returned["files"][0]["return_import_supported"] is False
    assert returned["blocked_files"] == []
    assert review["ok"] is True
    assert review["review_source_folder_written"] is True
    assert review["source_sub_scope"] == "tags"
    assert reopened_review["ok"] is True
    assert reopened_review["review_existing"] is True
    assert reopened_review["review_package_id"] == review["review_package_id"]
    assert review_manifest["source_scope"] == "library"
    assert review_manifest["source_sub_scope"] == "tags"
    assert review_manifest["supports_docs_review"] is True
    assert review_manifest["supports_return_import"] is False
    assert review_manifest["selected_doc_ids"] == [TAG_A_ID, TAG_B_ID]
    assert "parent_id" not in review_sources[TAG_A_ID]
    assert "parent_id" not in review_sources[TAG_B_ID]
    assert staged_filename not in {
        record["filename"] for record in import_files["files"]
    }
    review_only_candidate = next(
        record
        for record in import_files["candidates"]
        if record["filename"] == staged_filename
    )
    assert review_only_candidate["target"] == {
        "scope": "library",
        "sub_scope": "tags",
    }
    assert review_only_candidate["docs_review_enabled"] is True
    assert review_only_candidate["import_enabled"] is False
    assert review_only_candidate["import_disabled_reason"] == (
        "return_import_unsupported"
    )
    assert source_after == source_before


def test_opted_in_sub_scope_projects_importable_package_and_exact_listing() -> None:
    with make_docs_import_repo() as temp:
        repo_root = Path(temp)
        add_sub_scope_package_fixture(
            repo_root,
            tags_return_import_enabled=True,
        )
        add_document_tree_profile(repo_root)
        child_config = service.get_payload(
            repo_root,
            routes.CONFIG_PATH,
            {"scope": ["library"], "sub_scope": ["tags"]},
        )
        notes_config = service.get_payload(
            repo_root,
            routes.CONFIG_PATH,
            {"scope": ["library"], "sub_scope": ["notes"]},
        )
        _, payload = service.post_response(
            repo_root,
            routes.PREPARE_PATH,
            {
                "scope": "library",
                "sub_scope": "tags",
                "profile_id": "document-content",
                "doc_ids": [TAG_B_ID, TAG_A_ID],
                "select_all": False,
                "missing_summary_only": False,
                "include_non_viewable": True,
                "dry_run": False,
            },
        )
        paths = workspace_paths()
        metadata = json.loads(
            (paths.meta / f"{payload['export_id']}.meta.json").read_text(
                encoding="utf-8"
            )
        )
        output_path = resolve_data_sharing_marker(payload["output_file"])
        staged_filename = "returned-importable-tags.jsonl"
        shutil.copy2(output_path, paths.import_staging / staged_filename)
        write_returned_package(
            "ds_20260720T120011Z",
            selected_doc_ids=[NOTE_ID],
            rows=[{"doc_id": NOTE_ID, "title": "Note Only"}],
            filename="returned-notes.jsonl",
            sub_scope="notes",
            supports_docs_review=True,
            supports_return_import=True,
        )
        write_returned_package(
            "ds_20260720T120012Z",
            selected_doc_ids=[TAG_A_ID],
            rows=[{"doc_id": TAG_A_ID, "title": "Tag A"}],
            filename="returned-review-only-tags.jsonl",
            sub_scope="tags",
            supports_docs_review=True,
            supports_return_import=False,
        )

        exact = service.returned_payload(
            repo_root,
            {"scope": ["library"], "sub_scope": ["tags"]},
        )
        exact_validation = parse_staged_import(
            repo_root=repo_root,
            scope="library",
            sub_scope="tags",
            staged_file=staged_filename,
            staging_root=paths.import_staging,
            metadata_root=paths.meta,
            required_capability=RETURN_IMPORT_CAPABILITY,
        )
        import_files = import_source_service.handle_import_source_files(repo_root)
        mismatch = parse_staged_import(
            repo_root=repo_root,
            scope="library",
            sub_scope="tags",
            staged_file="returned-notes.jsonl",
            staging_root=paths.import_staging,
            metadata_root=paths.meta,
            required_capability=RETURN_IMPORT_CAPABILITY,
        )
        with pytest.raises(
            ValueError,
            match="returned-package import is not enabled",
        ):
            service.returned_payload(
                repo_root,
                {"scope": ["library"], "sub_scope": ["notes"]},
            )
        with pytest.raises(ValueError, match="sub_scope is required"):
            service.returned_payload(
                repo_root,
                {"scope": ["library"], "sub_scope": [""]},
            )
        with pytest.raises(ValueError, match="unknown sub_scope"):
            service.returned_payload(
                repo_root,
                {"scope": ["library"], "sub_scope": ["missing"]},
            )

    child_capabilities = {
        profile["profile_id"]: (
            profile["supports_docs_review"],
            profile["supports_return_import"],
        )
        for profile in child_config["profiles"]
    }
    notes_capabilities = {
        profile["profile_id"]: (
            profile["supports_docs_review"],
            profile["supports_return_import"],
        )
        for profile in notes_config["profiles"]
    }
    assert child_capabilities == {
        "document-content": (True, True),
        "document-tree": (False, False),
    }
    assert notes_capabilities == {
        "document-content": (True, False),
        "document-tree": (False, False),
    }
    assert payload["supports_docs_review"] is True
    assert payload["supports_return_import"] is True
    assert metadata["scope"] == "library"
    assert metadata["sub_scope"] == "tags"
    assert metadata["supports_docs_review"] is True
    assert metadata["supports_return_import"] is True
    assert "context_file" not in payload
    assert exact["scope"] == "library"
    assert exact["sub_scope"] == "tags"
    assert exact["required_capability"] == RETURN_IMPORT_CAPABILITY
    assert [item["filename"] for item in exact["files"]] == [staged_filename]
    assert exact["files"][0]["return_import_supported"] is True
    assert exact_validation["ok"] is True
    assert exact_validation["current_library"]["source_root"].endswith(
        "/source/sub-scopes/tags/documents"
    )
    assert all(
        record["current_library"]["exists"]
        for record in exact_validation["records"]
    )
    assert {
        item["filename"]: item["blocked_reason"]
        for item in exact["blocked_files"]
    } == {
        "returned-review-only-tags.jsonl": "export_only_sub_scope",
    }
    assert "returned-notes.jsonl" not in {
        item["filename"]
        for collection_name in ("files", "blocked_files")
        for item in exact[collection_name]
    }
    assert staged_filename not in {
        item["filename"] for item in import_files["files"]
    }
    importable_candidate = next(
        item
        for item in import_files["candidates"]
        if item["filename"] == staged_filename
    )
    assert importable_candidate["target"] == {
        "scope": "library",
        "sub_scope": "tags",
    }
    assert importable_candidate["docs_review_enabled"] is True
    assert importable_candidate["import_enabled"] is True
    assert mismatch["ok"] is False
    assert "sub_scope_mismatch" in {
        item["code"] for item in mismatch["issues"]
    }


def test_atomic_return_uses_order_insensitive_exact_set_equality() -> None:
    with make_docs_import_repo() as temp:
        repo_root = Path(temp)
        export_id = "ds_20260720T120000Z"
        write_returned_package(
            export_id,
            selected_doc_ids=["library", "alpha"],
            rows=[
                {"doc_id": "alpha", "title": "Alpha"},
                {"doc_id": "library", "title": "Library"},
            ],
        )
        complete_review = service.review_returned(
            repo_root,
            {
                "scope": "library",
                "staged_filename": "returned.jsonl",
                "dry_run": True,
            },
        )
        write_returned_package(
            export_id,
            selected_doc_ids=["library", "alpha"],
            rows=[
                {"doc_id": "alpha", "title": "Alpha"},
                {"doc_id": "outside", "title": "Outside"},
            ],
        )
        changed_status, changed_response = service.post_response(
            repo_root,
            routes.RETURNED_REVIEW_PATH,
            {
                "scope": "library",
                "staged_filename": "returned.jsonl",
                "dry_run": True,
            },
        )

    assert complete_review["ok"] is True
    assert "selected_records" not in complete_review
    assert int(changed_status) == 400
    assert changed_response["ok"] is False
    assert {item["code"] for item in changed_response["issues"]} >= {
        "missing_prepared_documents",
        "unexpected_returned_documents",
    }


def test_content_review_projects_safe_new_or_existing_review_identity() -> None:
    with make_docs_import_repo() as temp:
        repo_root = Path(temp)
        write_returned_package(
            "ds_20260720T120000Z",
            selected_doc_ids=["alpha"],
            rows=[{"doc_id": "alpha", "title": "Alpha", "content": "Reviewed body."}],
        )
        request = {
            "scope": "library",
            "staged_filename": "returned.jsonl",
            "dry_run": False,
        }

        first = service.review_returned(repo_root, request)
        second = service.review_returned(repo_root, request)
        package_path = workspace_paths().import_preview / first["review_package_id"]

    safe_keys = {
        "ok",
        "review_package_id",
        "review_url",
        "review_existing",
        "counts",
        "issues",
        "summary_text",
    }
    assert safe_keys <= set(first)
    assert first["ok"] is True
    assert first["review_existing"] is False
    assert first["review_package_id"]
    assert first["review_url"] == f"/docs-review/?package={first['review_package_id']}"
    assert first["summary_text"] == f"Prepared Docs Review package {first['review_package_id']}."
    assert package_path.is_dir()
    assert safe_keys <= set(second)
    assert second["ok"] is True
    assert second["review_package_id"] == first["review_package_id"]
    assert second["review_url"] == first["review_url"]
    assert second["review_existing"] is True
    assert second["summary_text"] == f"Docs Review package {first['review_package_id']} already exists."


def test_invalid_returned_record_blocks_complete_review() -> None:
    with make_docs_import_repo() as temp:
        repo_root = Path(temp)
        write_returned_package(
            "ds_20260720T120000Z",
            selected_doc_ids=["alpha"],
            rows=[{"doc_id": "alpha"}],
        )
        source_path = repo_root / "docs-viewer/scopes/library/source/documents/alpha.md"
        source_before = source_path.read_text(encoding="utf-8")

        review = service.review_returned(
            repo_root,
            {
                "scope": "library",
                "staged_filename": "returned.jsonl",
                "dry_run": False,
            },
        )

        assert source_path.read_text(encoding="utf-8") == source_before

    assert review["ok"] is False
    assert "missing_title" in {item["code"] for item in review["issues"]}
    assert review["review_package_id"] == ""
    assert review["review_url"] == ""
    assert review["review_existing"] is False


def test_review_rejects_retired_action_discriminator() -> None:
    with make_docs_import_repo() as temp:
        with pytest.raises(ValueError, match="review_action is not supported"):
            service.review_returned(
                Path(temp),
                {
                    "scope": "library",
                    "staged_filename": "returned.jsonl",
                    "review_action": "content",
                },
            )


def test_review_rejects_request_supplied_sub_scope() -> None:
    with make_docs_import_repo() as temp:
        with pytest.raises(ValueError, match="trusted export metadata"):
            service.review_returned(
                Path(temp),
                {
                    "scope": "library",
                    "sub_scope": "tags",
                    "staged_filename": "returned.jsonl",
                },
            )


def test_review_rejects_legacy_single_capability_metadata() -> None:
    with make_docs_import_repo() as temp:
        repo_root = Path(temp)
        export_id = "ds_20260720T120009Z"
        write_returned_package(
            export_id,
            selected_doc_ids=["alpha"],
            rows=[{"doc_id": "alpha", "title": "Alpha"}],
        )
        metadata_path = workspace_paths().meta / f"{export_id}.meta.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata.pop("supports_docs_review")
        metadata_path.write_text(json.dumps(metadata) + "\n", encoding="utf-8")

        returned = service.returned_payload(repo_root, {"scope": ["library"]})
        import_listing = import_source_service.handle_import_source_files(
            repo_root
        )
        review = service.review_returned(
            repo_root,
            {
                "scope": "library",
                "staged_filename": "returned.jsonl",
                "dry_run": False,
            },
        )

    assert returned["files"] == []
    assert returned["blocked_files"][0]["blocked_reason"] == (
        "invalid_capability_metadata"
    )
    blocked_candidate = next(
        item
        for item in import_listing["candidates"]
        if item["filename"] == "returned.jsonl"
    )
    assert blocked_candidate["validation_state"] == "blocked"
    assert blocked_candidate["disabled_reason"] == (
        "invalid_capability_metadata"
    )
    assert blocked_candidate["docs_review_disabled_reason"] == (
        "invalid_capability_metadata"
    )
    assert blocked_candidate["import_disabled_reason"] == (
        "invalid_capability_metadata"
    )
    assert review["ok"] is False
    assert review["review_source_folder_written"] is False
    assert "invalid_supports_docs_review" in {
        item["code"] for item in review["issues"]
    }


def test_sub_scope_review_rejects_cross_collection_selected_ids() -> None:
    with make_docs_import_repo() as temp:
        repo_root = Path(temp)
        add_sub_scope_package_fixture(repo_root)
        write_returned_package(
            "ds_20260720T120010Z",
            selected_doc_ids=[PARENT_CHILD_ID],
            rows=[{"doc_id": PARENT_CHILD_ID, "title": "Parent child"}],
            sub_scope="tags",
            supports_docs_review=True,
            supports_return_import=False,
        )

        review = service.review_returned(
            repo_root,
            {
                "scope": "library",
                "staged_filename": "returned.jsonl",
                "dry_run": False,
            },
        )

    assert review["ok"] is False
    assert review["review_source_folder_written"] is False
    assert "cross_collection_selected_documents" in {
        item["code"] for item in review["issues"]
    }


def test_returned_listing_projects_document_fields_without_adapter_identity() -> None:
    with make_docs_import_repo() as temp:
        repo_root = Path(temp)
        write_returned_package(
            "ds_20260720T120000Z",
            selected_doc_ids=["alpha"],
            rows=[{"doc_id": "alpha", "title": "Alpha"}],
        )
        payload = service.returned_payload(repo_root, {"scope": ["library"]})

    assert payload["ok"] is True
    assert len(payload["files"]) == 1
    assert payload["files"][0]["profile_id"] == "document-content"
    assert payload["files"][0]["document_count"] == 1
    assert payload["files"][0]["supports_docs_review"] is True
    assert payload["files"][0]["supports_return_import"] is True
    assert payload["files"][0]["scope_label"] == "Library"
    assert payload["files"][0]["sub_scope_label"] == ""
    assert {"app", "adapter_id", "config_id", "data_domain"}.isdisjoint(
        payload["files"][0]
    )


def test_returned_listing_excludes_invalid_and_export_only_packages() -> None:
    with make_docs_import_repo() as temp:
        repo_root = Path(temp)
        write_returned_package(
            "ds_20260720T120000Z",
            selected_doc_ids=["library", "alpha"],
            rows=[
                {"doc_id": "library", "title": "Library"},
                {"doc_id": "alpha", "title": "Alpha"},
            ],
            filename="reviewable.jsonl",
        )
        write_returned_package(
            "ds_20260720T120001Z",
            selected_doc_ids=["alpha", "missing"],
            rows=[{"doc_id": "alpha", "title": "Alpha"}],
            filename="incomplete.jsonl",
        )
        write_returned_package(
            "ds_20260720T120002Z",
            selected_doc_ids=["alpha"],
            rows=[{"doc_id": "alpha", "title": "Alpha"}],
            filename="tree.jsonl",
        )
        tree_metadata_path = workspace_paths().meta / "ds_20260720T120002Z.meta.json"
        tree_metadata = json.loads(tree_metadata_path.read_text(encoding="utf-8"))
        tree_metadata.update(
            {
                "config_id": "document-tree",
                "profile_id": "document-tree",
                "supports_docs_review": False,
                "supports_return_import": False,
            }
        )
        tree_metadata_path.write_text(json.dumps(tree_metadata) + "\n", encoding="utf-8")

        payload = service.returned_payload(repo_root, {"scope": ["library"]})

    assert [item["filename"] for item in payload["files"]] == ["reviewable.jsonl"]
    assert payload["files"][0]["document_count"] == 2
    blocked_by_name = {item["filename"]: item for item in payload["blocked_files"]}
    assert blocked_by_name["incomplete.jsonl"]["blocked_reason"] == "invalid_returned_package"
    assert blocked_by_name["tree.jsonl"]["blocked_reason"] == "export_only_profile"


def test_returned_listing_separates_scope_owned_and_unassigned_files() -> None:
    with make_docs_import_repo() as temp:
        repo_root = Path(temp)
        write_returned_package(
            "ds_20260720T120000Z",
            selected_doc_ids=["alpha"],
            rows=[{"doc_id": "alpha", "title": "Alpha"}],
            filename="library.jsonl",
        )
        write_returned_package(
            "ds_20260720T120001Z",
            selected_doc_ids=["studio-doc"],
            rows=[{"doc_id": "studio-doc", "title": "Studio"}],
            filename="studio.jsonl",
            scope="studio",
        )
        write_returned_package(
            "ds_20260720T120002Z",
            selected_doc_ids=["alpha"],
            rows=[{"doc_id": "alpha", "title": "Alpha"}],
            filename="unscoped.jsonl",
            scope="",
        )
        (workspace_paths().import_staging / "orphan.jsonl").write_text(
            json.dumps(
                {
                    "record_type": "data_sharing_header",
                    "schema_version": "data_sharing_returned_package_v1",
                    "export_id": "ds_20260720T120003Z",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        (workspace_paths().import_staging / "orphan.context.json").write_text(
            "{}\n",
            encoding="utf-8",
        )

        payload = service.returned_payload(repo_root, {"scope": ["library"]})

    assert [item["filename"] for item in payload["files"]] == ["library.jsonl"]
    assert payload["blocked_files"] == []
    assert {item["filename"] for item in payload["unassigned_files"]} == {
        "orphan.context.json",
        "orphan.jsonl",
        "unscoped.jsonl",
    }
    assert all(
        {"app", "adapter_id", "config_id", "data_domain"}.isdisjoint(item)
        for item in payload["unassigned_files"]
    )


@pytest.mark.parametrize(
    ("field", "value", "issue_code"),
    [
        ("data_domain", "tags", "invalid_data_domain"),
        ("scope", "studio", "scope_mismatch"),
        ("selected_doc_ids", [], "empty_selected_doc_ids"),
    ],
)
def test_atomic_return_rejects_invalid_trusted_routing_identity(
    field: str,
    value: object,
    issue_code: str,
) -> None:
    with make_docs_import_repo() as temp:
        repo_root = Path(temp)
        export_id = "ds_20260720T120000Z"
        write_returned_package(
            export_id,
            selected_doc_ids=["alpha"],
            rows=[{"doc_id": "alpha", "title": "Alpha"}],
        )
        metadata_path = workspace_paths().meta / f"{export_id}.meta.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata[field] = value
        metadata_path.write_text(json.dumps(metadata) + "\n", encoding="utf-8")

        payload = service.review_returned(
            repo_root,
            {
                "scope": "library",
                "staged_filename": "returned.jsonl",
                "dry_run": True,
            },
        )

    assert payload["ok"] is False
    assert issue_code in {item["code"] for item in payload["issues"]}


def test_docs_viewer_http_service_retires_package_pages_and_keeps_package_api() -> None:
    with make_docs_import_repo() as temp:
        repo_root = Path(temp)
        add_sub_scope_package_fixture(repo_root)
        config = DocsViewerServiceConfig(
            host="127.0.0.1",
            port=0,
            base_url="http://127.0.0.1:0",
            management_enabled=True,
            generated_reads_enabled=True,
            watch_enabled=False,
        )
        try:
            server = DocsViewerServer(("127.0.0.1", 0), repo_root, config)
        except PermissionError:
            pytest.skip("local socket binding is unavailable in this sandbox")
        base_url = f"http://127.0.0.1:{server.server_address[1]}"
        server.docs_viewer_config = replace(
            config,
            port=server.server_address[1],
            base_url=base_url,
        )
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with urllib.request.urlopen(f"{base_url}{routes.CONFIG_PATH}", timeout=5) as response:
                config_payload = json.loads(response.read().decode("utf-8"))
            with urllib.request.urlopen(
                (
                    f"{base_url}{routes.CONFIG_PATH}"
                    "?scope=library&sub_scope=tags"
                ),
                timeout=5,
            ) as response:
                child_config_payload = json.loads(response.read().decode("utf-8"))
            with urllib.request.urlopen(
                (
                    f"{base_url}{routes.DOCUMENTS_PATH}"
                    "?scope=library&sub_scope=tags"
                ),
                timeout=5,
            ) as response:
                child_documents_payload = json.loads(response.read().decode("utf-8"))
            with pytest.raises(urllib.error.HTTPError) as prepare_route_error:
                urllib.request.urlopen(f"{base_url}/docs/packages/prepare/", timeout=5)
            with pytest.raises(urllib.error.HTTPError) as returned_route_error:
                urllib.request.urlopen(f"{base_url}/docs/packages/returned/", timeout=5)
            with urllib.request.urlopen(
                f"{base_url}{routes.RETURNED_PATH}?scope=library", timeout=5
            ) as response:
                returned_payload = json.loads(response.read().decode("utf-8"))
            request = urllib.request.Request(
                f"{base_url}{routes.PREPARE_PATH}",
                data=json.dumps(
                    {
                        "scope": "library",
                        "profile_id": "document-content",
                        "doc_ids": [PARENT_CHILD_ID],
                        "dry_run": True,
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=5) as response:
                prepare_payload = json.loads(response.read().decode("utf-8"))
            child_request = urllib.request.Request(
                f"{base_url}{routes.PREPARE_PATH}",
                data=json.dumps(
                    {
                        "scope": "library",
                        "sub_scope": "tags",
                        "profile_id": "document-content",
                        "doc_ids": [TAG_A_ID],
                        "select_all": False,
                        "dry_run": True,
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(child_request, timeout=5) as response:
                child_prepare_payload = json.loads(response.read().decode("utf-8"))
            retired_inspect = urllib.request.Request(
                f"{base_url}/docs/packages/returned/inspect",
                data=json.dumps(
                    {
                        "scope": "library",
                        "staged_filename": "returned.jsonl",
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with pytest.raises(urllib.error.HTTPError) as inspect_error:
                urllib.request.urlopen(retired_inspect, timeout=5)
            rejected = urllib.request.Request(
                f"{base_url}{routes.CONFIG_PATH}",
                headers={"Origin": "https://example.com"},
            )
            with pytest.raises(urllib.error.HTTPError) as error:
                urllib.request.urlopen(rejected, timeout=5)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    assert config_payload["ok"] is True
    assert child_config_payload["scope"] == "library"
    assert child_config_payload["sub_scope"] == "tags"
    assert child_config_payload["profiles"][0]["supports_docs_review"] is True
    assert child_config_payload["profiles"][0]["supports_return_import"] is False
    assert child_documents_payload["flat_collection"] is True
    assert [record["doc_id"] for record in child_documents_payload["records"]] == [
        TAG_A_ID,
        TAG_B_ID,
    ]
    assert prepare_route_error.value.code == 404
    assert returned_route_error.value.code == 404
    assert returned_payload["ok"] is True
    assert prepare_payload["ok"] is True
    assert prepare_payload["output_written"] is False
    assert child_prepare_payload["ok"] is True
    assert child_prepare_payload["scope"] == "library"
    assert child_prepare_payload["sub_scope"] == "tags"
    assert child_prepare_payload["selected_doc_ids"] == [TAG_A_ID]
    assert child_prepare_payload["output_written"] is False
    assert inspect_error.value.code == 404
    assert error.value.code == 403
