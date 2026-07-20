#!/usr/bin/env python3
"""Review-session temp-folder service tests."""

from __future__ import annotations

from http import HTTPStatus
import json
import sys
import tempfile
from pathlib import Path

import pytest
from repo_factory import docs_scope_record


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
if str(DOCS_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(DOCS_SERVICES_DIR))


import docs_management_read_service  # noqa: E402
import docs_management_routes as routes  # noqa: E402
import docs_management_service  # noqa: E402
import docs_review_sessions  # noqa: E402
from docs_document_packages.workspace import workspace_paths  # noqa: E402


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def make_repo() -> tempfile.TemporaryDirectory[str]:
    temp = tempfile.TemporaryDirectory()
    root = Path(temp.name)
    write_json(root / "site-tools/config/site-tools.json", {"schema_version": "site_tools_config_v1"})
    write_json(
        root / "docs-viewer/config/scopes/docs_scopes.json",
        {
            "schema_version": "docs_scopes_v3",
            "scopes": [
                docs_scope_record("studio")
            ],
        },
    )
    return temp


def write_built_session(root: Path, session_id: str = "session-001") -> Path:
    del root
    session = workspace_paths().import_preview / session_id
    write_json(
        session / "manifest.json",
        {
            "session_id": session_id,
            "source_scope": "library",
            "profile_id": "document-content",
            "content_format": "markdown",
        },
    )
    (session / "source").mkdir(parents=True, exist_ok=True)
    (session / "source/example.md").write_text("---\ndoc_id: example\ntitle: Example\n---\n# Example\n", encoding="utf-8")
    write_json(
        session / "generated/index-tree.json",
        {
            "schema": "docs_index_tree_v1",
            "docs": [
                {
                    "doc_id": "example",
                    "title": "Example",
                    "content_url": "/docs/review-sessions/payload?session_id=session-001&doc_id=example",
                }
            ],
        },
    )
    write_json(session / "generated/by-id/example.json", {"doc_id": "example", "title": "Example"})
    return session


def test_review_session_routes_are_registered() -> None:
    assert routes.REVIEW_SESSIONS_PATH in routes.GET_PATHS
    assert routes.REVIEW_SESSION_INDEX_TREE_PATH in routes.GET_PATHS
    assert routes.REVIEW_SESSION_PAYLOAD_PATH in routes.GET_PATHS
    assert routes.REVIEW_SESSION_BUILD_PATH in routes.POST_PATHS
    assert routes.REVIEW_SESSION_DELETE_PATH in routes.POST_PATHS


def test_review_sessions_use_fixed_document_package_preview_root() -> None:
    with make_repo() as temp:
        root = Path(temp)
        session = workspace_paths().import_preview / "session-custom"
        (session / "source").mkdir(parents=True)

        payload = docs_review_sessions.list_review_sessions(root)

    assert payload["root"] == "$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-preview"
    assert [item["session_id"] for item in payload["sessions"]] == ["session-custom"]


def test_review_session_frontend_has_dedicated_client_and_modal_mount() -> None:
    client = (REPO_ROOT / "docs-viewer/runtime/js/management/docs-viewer-review-sessions-client.js").read_text(encoding="utf-8")
    modal = (REPO_ROOT / "docs-viewer/runtime/js/management/docs-viewer-review-sessions-modal.js").read_text(encoding="utf-8")
    controller = (REPO_ROOT / "docs-viewer/runtime/js/management/docs-viewer-review-sessions-controller.js").read_text(encoding="utf-8")
    shell = (REPO_ROOT / "docs-viewer/runtime/js/management/docs-viewer-management-shell-renderer.js").read_text(encoding="utf-8")
    management = (REPO_ROOT / "docs-viewer/runtime/js/management/docs-viewer-management.js").read_text(encoding="utf-8")

    assert 'from "./docs-viewer-management-client.js"' in client
    assert 'REVIEW_SESSIONS_PATH = "/docs/review-sessions"' in client
    assert 'REVIEW_SESSION_BUILD_PATH = "/docs/review-sessions/build"' in client
    assert 'REVIEW_SESSION_DELETE_PATH = "/docs/review-sessions/delete"' in client
    assert "createDocsViewerReviewSessionsModal" in modal
    assert "data-review-sessions-list" in modal
    assert 'from "./docs-viewer-review-sessions-client.js"' in controller
    assert 'from "./docs-viewer-review-sessions-modal.js"' in controller
    assert "createDocsViewerReviewSessionsController" in controller
    assert "data-docs-viewer-management-modal-mount" in shell
    assert "managementModalMount" in shell
    assert "docs-viewer-review-sessions" not in management


def test_review_session_get_routes_are_management_only_in_service_layer() -> None:
    service = (REPO_ROOT / "docs-viewer/services/docs_viewer_service.py").read_text(encoding="utf-8")

    assert "REVIEW_SESSION_READ_PATHS" in service
    assert "routes.REVIEW_SESSIONS_PATH" in service
    assert "routes.REVIEW_SESSION_INDEX_TREE_PATH" in service
    assert "routes.REVIEW_SESSION_PAYLOAD_PATH" in service
    assert "path in REVIEW_SESSION_READ_PATHS" in service


def test_list_review_sessions_reports_built_state_from_temp_folders() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_built_session(root)
        unbuilt = workspace_paths().import_preview / "session-002"
        (unbuilt / "source").mkdir(parents=True)

        payload = docs_review_sessions.list_review_sessions(root)

    sessions = {item["session_id"]: item for item in payload["sessions"]}
    assert payload["ok"] is True
    assert sessions["session-001"]["built"] is True
    assert sessions["session-001"]["generated_payload_count"] == 1
    assert sessions["session-001"]["manifest"]["content_format"] == "markdown"
    assert sessions["session-002"]["built"] is False
    assert sessions["session-002"]["source_exists"] is True


def test_review_session_generated_reads_use_session_endpoint_wrappers() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_built_session(root)

        tree = docs_management_read_service.docs_management_get_payload(
            root,
            routes.REVIEW_SESSION_INDEX_TREE_PATH,
            {"session_id": ["session-001"]},
        )
        doc = docs_management_read_service.docs_management_get_payload(
            root,
            routes.REVIEW_SESSION_PAYLOAD_PATH,
            {"session_id": ["session-001"], "doc_id": ["example"]},
        )

    assert tree["ok"] is True
    assert tree["index_tree"]["docs"][0]["doc_id"] == "example"
    assert doc["ok"] is True
    assert doc["payload"]["doc_id"] == "example"


def test_review_session_delete_is_temp_folder_cleanup() -> None:
    with make_repo() as temp:
        root = Path(temp)
        session = write_built_session(root)

        status, payload = docs_management_service.docs_management_post_response(
            root,
            routes.REVIEW_SESSION_DELETE_PATH,
            {"session_id": "session-001"},
        )

        absent_status, absent_payload = docs_management_service.docs_management_post_response(
            root,
            routes.REVIEW_SESSION_DELETE_PATH,
            {"session_id": "session-001"},
        )

    assert status == HTTPStatus.OK
    assert payload["ok"] is True
    assert payload["deleted"] is True
    assert session.exists() is False
    assert absent_status == HTTPStatus.OK
    assert absent_payload["deleted"] is False


def test_review_session_build_placeholder_is_explicit() -> None:
    with make_repo() as temp:
        root = Path(temp)
        session = workspace_paths().import_preview / "session-003"
        (session / "source").mkdir(parents=True)

        status, payload = docs_management_service.docs_management_post_response(
            root,
            routes.REVIEW_SESSION_BUILD_PATH,
            {"session_id": "session-003"},
        )

    assert status == HTTPStatus.OK
    assert payload["ok"] is True
    assert payload["build_status"] == "not_implemented"
    assert payload["session"]["source_exists"] is True


@pytest.mark.parametrize("session_id", ["", ".", "..", "../escape", "nested/session", "/absolute", "bad session"])
def test_review_session_ids_must_be_safe_folder_names(session_id: str) -> None:
    with make_repo() as temp:
        root = Path(temp)

        with pytest.raises(ValueError):
            docs_review_sessions.resolve_session_path(root, session_id)


def test_review_session_symlink_escape_is_rejected() -> None:
    with make_repo() as temp:
        root = Path(temp)
        outside = root / "outside"
        outside.mkdir()
        session_root = workspace_paths().import_preview
        session_root.mkdir(parents=True)
        symlink = session_root / "session-escape"
        symlink.symlink_to(outside, target_is_directory=True)

        with pytest.raises(ValueError, match="symlinks"):
            docs_review_sessions.resolve_session_path(root, "session-escape")
