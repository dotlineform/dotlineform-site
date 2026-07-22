#!/usr/bin/env python3
"""Direct Docs Viewer document-package service contracts."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
from threading import Thread
import urllib.error
import urllib.request

import pytest

from docs_document_packages import service
from docs_document_packages.workspace import workspace_paths
import docs_document_package_routes as routes
from docs_viewer_service import DocsViewerServer, DocsViewerServiceConfig
from repo_factory import make_docs_import_repo


REPO_ROOT = Path(__file__).resolve().parents[3]


def write_returned_package(
    export_id: str,
    *,
    selected_doc_ids: list[str],
    rows: list[dict[str, object]],
    filename: str = "returned.jsonl",
    scope: str = "library",
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
    (paths.meta / f"{export_id}.meta.json").write_text(
        json.dumps(
            {
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
                "supports_return_import": True,
                "content_format": "markdown",
                "selected_doc_ids": selected_doc_ids,
            }
        )
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
        "/docs/packages/context",
        "/docs/packages/returned/inspect",
        "/docs/packages/returned/review",
        "/docs/packages/returned/apply",
    }
    assert [profile["profile_id"] for profile in payload["profiles"]] == ["document-content"]
    assert payload["profiles"][0]["selection"] == {
        "mode": "explicit_doc_ids",
        "include_descendants": False,
    }
    assert payload["profiles"][0]["external_context"]["task"] == "review_document_content"
    assert payload["profiles"][0]["document_fields"] == [
        {"output_path": "doc_id", "required": True},
        {"output_path": "title", "required": True},
    ]
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
                    "review_action": "summaries",
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
        complete = service.inspect_returned(
            repo_root,
            {"scope": "library", "staged_filename": "returned.jsonl"},
        )
        review = service.review_returned(
            repo_root,
            {
                "scope": "library",
                "staged_filename": "returned.jsonl",
                "review_action": "summaries",
                "dry_run": True,
            },
        )
        apply = service.apply_returned(
            repo_root,
            {
                "scope": "library",
                "staged_filename": "returned.jsonl",
                "apply_action": "summary_apply",
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
        changed = service.inspect_returned(
            repo_root,
            {"scope": "library", "staged_filename": "returned.jsonl"},
        )
        changed_status, changed_response = service.post_response(
            repo_root,
            routes.RETURNED_INSPECT_PATH,
            {"scope": "library", "staged_filename": "returned.jsonl"},
        )

    assert complete["ok"] is True
    assert review["ok"] is True
    assert "selected_records" not in review
    assert all("selectable" not in row for row in review["review_rows"])
    assert apply["ok"] is True
    assert apply["apply_action"] == "summary_apply"
    assert {"adapter_id", "data_domain", "operation", "selected_records"}.isdisjoint(apply)
    assert changed["ok"] is False
    assert int(changed_status) == 400
    assert changed_response["ok"] is False
    assert {item["code"] for item in changed["issues"]} >= {
        "missing_prepared_documents",
        "unexpected_returned_documents",
    }


def test_invalid_returned_record_blocks_every_review_and_apply_action() -> None:
    with make_docs_import_repo() as temp:
        repo_root = Path(temp)
        write_returned_package(
            "ds_20260720T120000Z",
            selected_doc_ids=["alpha"],
            rows=[{"doc_id": "alpha"}],
        )
        source_path = repo_root / "docs-viewer/scopes/library/source/documents/alpha.md"
        source_before = source_path.read_text(encoding="utf-8")

        inspection = service.inspect_returned(
            repo_root,
            {"scope": "library", "staged_filename": "returned.jsonl"},
        )
        reviews = {
            action: service.review_returned(
                repo_root,
                {
                    "scope": "library",
                    "staged_filename": "returned.jsonl",
                    "review_action": action,
                    "dry_run": False,
                },
            )
            for action in ("content", "summaries", "hierarchy")
        }
        applies = {
            action: service.apply_returned(
                repo_root,
                {
                    "scope": "library",
                    "staged_filename": "returned.jsonl",
                    "apply_action": action,
                    "confirm": True,
                    "dry_run": False,
                },
            )
            for action in ("summary_apply", "hierarchy_apply")
        }

        assert source_path.read_text(encoding="utf-8") == source_before

    assert inspection["ok"] is False
    assert "missing_title" in {item["code"] for item in inspection["issues"]}
    assert all(payload["ok"] is False for payload in reviews.values())
    assert reviews["content"]["review_source_folder_written"] is False
    assert reviews["summaries"]["review_written"] is False
    assert reviews["hierarchy"]["review_written"] is False
    assert all(payload["ok"] is False for payload in applies.values())
    assert applies["summary_apply"]["summary_apply_written"] is False
    assert applies["hierarchy_apply"]["hierarchy_apply_written"] is False


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
    assert {"app", "adapter_id", "config_id", "data_domain"}.isdisjoint(
        payload["files"][0]
    )


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

        payload = service.returned_payload(repo_root, {"scope": ["library"]})

    assert [item["filename"] for item in payload["files"]] == ["library.jsonl"]
    assert payload["blocked_files"] == []
    assert {item["filename"] for item in payload["unassigned_files"]} == {
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

        payload = service.inspect_returned(
            repo_root,
            {"scope": "library", "staged_filename": "returned.jsonl"},
        )

    assert payload["ok"] is False
    assert issue_code in {item["code"] for item in payload["issues"]}


def test_docs_viewer_http_service_retires_prepare_page_and_keeps_package_api() -> None:
    with make_docs_import_repo() as temp:
        repo_root = Path(temp)
        shell_root = repo_root / "docs-viewer/shell"
        shell_root.mkdir(parents=True, exist_ok=True)
        for filename in ("docs-viewer-package-returned.html",):
            shell_root.joinpath(filename).write_text(
                (REPO_ROOT / "docs-viewer/shell" / filename).read_text(encoding="utf-8"),
                encoding="utf-8",
            )
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
            with pytest.raises(urllib.error.HTTPError) as prepare_route_error:
                urllib.request.urlopen(f"{base_url}/docs/packages/prepare/", timeout=5)
            with urllib.request.urlopen(
                f"{base_url}/docs/packages/returned/", timeout=5
            ) as response:
                returned_shell = response.read().decode("utf-8")
            request = urllib.request.Request(
                f"{base_url}{routes.PREPARE_PATH}",
                data=json.dumps(
                    {
                        "scope": "library",
                        "profile_id": "document-content",
                        "doc_ids": ["alpha"],
                        "dry_run": True,
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=5) as response:
                prepare_payload = json.loads(response.read().decode("utf-8"))
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
    assert prepare_route_error.value.code == 404
    assert "Returned document packages" in returned_shell
    assert prepare_payload["ok"] is True
    assert prepare_payload["output_written"] is False
    assert error.value.code == 403
