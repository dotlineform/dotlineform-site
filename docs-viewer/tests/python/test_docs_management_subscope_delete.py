#!/usr/bin/env python3
"""Exact-target service checks for managed sub-scope document deletion."""

from __future__ import annotations

import hashlib
from http import HTTPStatus
from pathlib import Path

import pytest

import docs_management_mutation_service as mutation_service
import docs_management_service as management_service
import docs_source_model as source_model
import docs_write_rebuild as write_rebuild
from repo_factory import (
    docs_scope_record,
    docs_sub_scope_record,
    read_json,
    write_docs_scope_config,
    write_site_tools_config,
    write_text,
)


TARGET_DOC_ID = "d-20260728-150000-000001"
SIBLING_DOC_ID = "d-20260728-150000-000002"
REPORT_DOC_ID = "d-20260728-150000-000003"


def write_source(path: Path, doc_id: str, title: str, body: str) -> bytes:
    source_bytes = source_model.format_source(
        {
            "doc_id": doc_id,
            "title": title,
            "added_date": "2026-07-28 15:00:00",
            "last_updated": "2026-07-28 15:00:00",
        },
        body,
    ).encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(source_bytes)
    return source_bytes


def prepare_delete_repo(repo_root: Path, *, build_outputs: bool = False) -> dict[str, Path | bytes]:
    write_site_tools_config(repo_root)
    write_docs_scope_config(
        repo_root,
        [
            docs_scope_record(
                "studio",
                sub_scopes=[
                    docs_sub_scope_record("studio", "tags", title="Tags")
                ],
            )
        ],
        {"recent_limit": 10},
    )
    report_path = (
        repo_root
        / f"docs-viewer/scopes/studio/source/documents/{REPORT_DOC_ID}.md"
    )
    write_source(report_path, REPORT_DOC_ID, "Tags", "# Tags\n")
    report_text = report_path.read_text(encoding="utf-8").replace(
        "---\n# Tags",
        "viewer_report: docs_subscope\nviewer_report_subscope: tags\n---\n# Tags",
    )
    report_path.write_text(report_text, encoding="utf-8")

    child_root = (
        repo_root
        / "docs-viewer/scopes/studio/source/sub-scopes/tags/documents"
    )
    target_path = child_root / f"{TARGET_DOC_ID}.md"
    sibling_path = child_root / f"{SIBLING_DOC_ID}.md"
    target_bytes = write_source(
        target_path,
        TARGET_DOC_ID,
        "Target",
        "# Target\n\nExact target body.\n",
    )
    write_source(
        sibling_path,
        SIBLING_DOC_ID,
        "Sibling",
        "# Sibling\n\nRetained sibling body.\n",
    )

    parent_sentinels = (
        repo_root / "docs-viewer/scopes/studio/published/documents/index-tree.json",
        repo_root / "docs-viewer/scopes/studio/published/documents/recent.json",
        repo_root / "docs-viewer/scopes/studio/published/search/index.json",
        repo_root / "docs-viewer/config/defaults/docs-viewer-config.json",
        repo_root / "docs-viewer/config/defaults/docs-viewer-public-config.json",
        repo_root / "site/docs-viewer/config/defaults/docs-viewer-public-config.json",
    )
    for index, path in enumerate(parent_sentinels):
        write_text(path, f"parent-sentinel-{index}\n")

    if build_outputs:
        build_link = repo_root / "docs-viewer/build"
        build_link.symlink_to(
            Path(__file__).resolve().parents[2] / "build",
            target_is_directory=True,
        )
        write_rebuild.rebuild_sub_scope_outputs(repo_root, "studio", "tags")

    return {
        "target_path": target_path,
        "target_bytes": target_bytes,
        "sibling_path": sibling_path,
        "manifest_path": (
            repo_root
            / "docs-viewer/scopes/studio/published/documents/sub-scopes/tags/manifest.json"
        ),
        "target_payload_path": (
            repo_root
            / f"docs-viewer/scopes/studio/published/documents/sub-scopes/tags/by-id/{TARGET_DOC_ID}.json"
        ),
        "sibling_payload_path": (
            repo_root
            / f"docs-viewer/scopes/studio/published/documents/sub-scopes/tags/by-id/{SIBLING_DOC_ID}.json"
        ),
        "parent_sentinels": parent_sentinels,
    }


def preview_body(doc_id: str = TARGET_DOC_ID) -> dict[str, object]:
    return {
        "scope": "studio",
        "sub_scope": "tags",
        "doc_id": doc_id,
    }


def apply_body(source_revision: str) -> dict[str, object]:
    return {
        **preview_body(),
        "source_revision": source_revision,
        "confirm": True,
    }


def test_sub_scope_delete_service_removes_only_exact_child_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = prepare_delete_repo(tmp_path, build_outputs=True)
    parent_before = {
        path: path.read_bytes()
        for path in paths["parent_sentinels"]
    }
    sibling_source_before = paths["sibling_path"].read_bytes()
    sibling_payload_before = paths["sibling_payload_path"].read_bytes()
    preview_source_before = paths["target_path"].read_bytes()
    preview_payload_before = paths["target_payload_path"].read_bytes()
    activity: list[tuple[str, dict[str, object]]] = []
    monkeypatch.setattr(
        mutation_service,
        "log_event",
        lambda _repo_root, event_name, details: activity.append(
            (event_name, details)
        ),
    )

    preview_status, preview = management_service.docs_management_post_response(
        tmp_path,
        "/docs/delete-preview",
        preview_body(),
    )

    assert preview_status == HTTPStatus.OK
    assert preview["operation"] == "preview"
    assert preview["target"] == preview_body()
    assert preview["source_revision"].startswith("sha256:")
    assert paths["target_path"].read_bytes() == preview_source_before
    assert paths["target_payload_path"].read_bytes() == preview_payload_before

    apply_status, applied = management_service.docs_management_post_response(
        tmp_path,
        "/docs/delete-apply",
        apply_body(preview["source_revision"]),
    )

    assert apply_status == HTTPStatus.OK
    assert applied["operation"] == "apply"
    assert applied["target"] == preview_body()
    assert applied["deleted_doc_ids"] == [TARGET_DOC_ID]
    assert applied["delete_count"] == 1
    assert applied["rebuild"]["search"] == {"mode": "none", "doc_ids": []}
    assert "--skip-browser-config" in applied["rebuild"]["steps"][0]["command"]
    assert len(applied["rebuild"]["steps"]) == 1
    assert not paths["target_path"].exists()
    assert not paths["target_payload_path"].exists()
    assert paths["sibling_path"].read_bytes() == sibling_source_before
    assert paths["sibling_payload_path"].read_bytes() == sibling_payload_before
    assert read_json(paths["manifest_path"]) == {
        "docs": [{"doc_id": SIBLING_DOC_ID, "title": "Sibling"}]
    }
    assert {
        path: path.read_bytes()
        for path in paths["parent_sentinels"]
    } == parent_before
    assert activity == [
        (
            "docs-delete",
            {
                "scope": "studio",
                "sub_scope": "tags",
                "doc_id": TARGET_DOC_ID,
                "deleted_doc_ids": [TARGET_DOC_ID],
                "delete_count": 1,
                "path": (
                    "docs-viewer/scopes/studio/source/sub-scopes/tags/"
                    f"documents/{TARGET_DOC_ID}.md"
                ),
            },
        )
    ]


def test_sub_scope_delete_apply_rejects_stale_source_without_writing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = prepare_delete_repo(tmp_path)
    _status, preview = management_service.docs_management_post_response(
        tmp_path,
        "/docs/delete-preview",
        preview_body(),
    )
    changed_bytes = paths["target_path"].read_bytes() + b"\nChanged after preview.\n"
    paths["target_path"].write_bytes(changed_bytes)
    rebuild_calls: list[object] = []
    monkeypatch.setattr(
        mutation_service.write_rebuild,
        "perform_sub_scope_source_write_and_rebuild",
        lambda *_args, **_kwargs: rebuild_calls.append(object()),
    )

    status, payload = management_service.docs_management_post_response(
        tmp_path,
        "/docs/delete-apply",
        apply_body(preview["source_revision"]),
    )

    assert status == HTTPStatus.CONFLICT
    assert payload["ok"] is False
    assert payload["target"] == preview_body()
    assert payload["source_revision"] == preview["source_revision"]
    assert payload["current_source_revision"] != preview["source_revision"]
    assert payload["retry_safe"] is False
    assert paths["target_path"].read_bytes() == changed_bytes
    assert paths["sibling_path"].is_file()
    assert rebuild_calls == []


def test_sub_scope_delete_revision_hashes_exact_source_bytes(tmp_path: Path) -> None:
    paths = prepare_delete_repo(tmp_path)
    crlf_bytes = paths["target_path"].read_bytes().replace(b"\n", b"\r\n")
    paths["target_path"].write_bytes(crlf_bytes)

    status, preview = management_service.docs_management_post_response(
        tmp_path,
        "/docs/delete-preview",
        preview_body(),
    )

    assert status == HTTPStatus.OK
    assert preview["source_revision"] == (
        f"sha256:{hashlib.sha256(crlf_bytes).hexdigest()}"
    )
    assert paths["target_path"].read_bytes() == crlf_bytes


@pytest.mark.parametrize(
    "payload",
    [
        {
            **preview_body(),
            "doc_ids": [TARGET_DOC_ID, SIBLING_DOC_ID],
        },
        {
            **preview_body(),
            "tag_id": "external-association",
        },
        {
            **preview_body(),
            "fallback_doc_id": SIBLING_DOC_ID,
        },
    ],
)
def test_sub_scope_delete_preview_rejects_broadened_payloads(
    tmp_path: Path,
    payload: dict[str, object],
) -> None:
    paths = prepare_delete_repo(tmp_path)

    with pytest.raises(ValueError, match="must contain exactly"):
        management_service.docs_management_post_response(
            tmp_path,
            "/docs/delete-preview",
            payload,
        )

    assert paths["target_path"].is_file()
    assert paths["sibling_path"].is_file()


def test_sub_scope_delete_preview_rejects_path_escape(tmp_path: Path) -> None:
    paths = prepare_delete_repo(tmp_path)

    with pytest.raises(
        ValueError,
        match="doc_id must identify one direct-child source document",
    ):
        management_service.docs_management_post_response(
            tmp_path,
            "/docs/delete-preview",
            preview_body("../outside"),
        )

    assert paths["target_path"].is_file()
    assert paths["sibling_path"].is_file()


def test_sub_scope_delete_apply_rejects_broadened_payload_after_preview(
    tmp_path: Path,
) -> None:
    paths = prepare_delete_repo(tmp_path)
    _status, preview = management_service.docs_management_post_response(
        tmp_path,
        "/docs/delete-preview",
        preview_body(),
    )
    broadened = {
        **apply_body(preview["source_revision"]),
        "doc_ids": [TARGET_DOC_ID, SIBLING_DOC_ID],
        "tag_id": "external-association",
    }

    with pytest.raises(ValueError, match="must contain exactly"):
        management_service.docs_management_post_response(
            tmp_path,
            "/docs/delete-apply",
            broadened,
        )

    assert paths["target_path"].is_file()
    assert paths["sibling_path"].is_file()


def test_sub_scope_delete_preview_rejects_missing_mismatched_and_unconfigured_targets(
    tmp_path: Path,
) -> None:
    paths = prepare_delete_repo(tmp_path)

    with pytest.raises(FileNotFoundError, match="was not found"):
        management_service.docs_management_post_response(
            tmp_path,
            "/docs/delete-preview",
            preview_body("missing-doc"),
        )

    target_text = paths["target_path"].read_text(encoding="utf-8").replace(
        f"doc_id: {TARGET_DOC_ID}",
        "doc_id: mismatched-id",
    )
    paths["target_path"].write_text(target_text, encoding="utf-8")
    with pytest.raises(ValueError, match="does not match requested doc_id"):
        management_service.docs_management_post_response(
            tmp_path,
            "/docs/delete-preview",
            preview_body(),
        )

    with pytest.raises(ValueError, match="unknown sub_scope"):
        management_service.docs_management_post_response(
            tmp_path,
            "/docs/delete-preview",
            {
                "scope": "studio",
                "sub_scope": "unconfigured",
                "doc_id": TARGET_DOC_ID,
            },
        )

    assert paths["target_path"].is_file()
    assert paths["sibling_path"].is_file()


def test_sub_scope_delete_rebuild_failure_restores_exact_source_and_reports_retry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = prepare_delete_repo(tmp_path)
    _status, preview = management_service.docs_management_post_response(
        tmp_path,
        "/docs/delete-preview",
        preview_body(),
    )
    calls: list[str] = []
    activity: list[object] = []

    def fail_then_recover(
        _repo_root,
        _scope,
        _sub_scope,
        _changed_paths,
        write_operation,
        *,
        suppression_reason,
    ):
        write_operation()
        calls.append(suppression_reason)
        if len(calls) == 1:
            assert not paths["target_path"].exists()
            raise RuntimeError("synthetic child builder failure")
        assert paths["target_path"].read_bytes() == paths["target_bytes"]
        return {
            "ok": True,
            "docs": {"mode": "sub_scope"},
            "search": {"mode": "none", "doc_ids": []},
        }

    monkeypatch.setattr(
        mutation_service.write_rebuild,
        "perform_sub_scope_source_write_and_rebuild",
        fail_then_recover,
    )
    monkeypatch.setattr(
        mutation_service,
        "log_event",
        lambda *_args, **_kwargs: activity.append(object()),
    )

    status, payload = management_service.docs_management_post_response(
        tmp_path,
        "/docs/delete-apply",
        apply_body(preview["source_revision"]),
    )

    assert status == HTTPStatus.INTERNAL_SERVER_ERROR
    assert payload["ok"] is False
    assert payload["target"] == preview_body()
    assert payload["deleted_doc_ids"] == []
    assert payload["delete_count"] == 0
    assert payload["source_restored"] is True
    assert payload["recovery_rebuild"]["ok"] is True
    assert payload["retry_safe"] is True
    assert paths["target_path"].read_bytes() == paths["target_bytes"]
    assert paths["sibling_path"].is_file()
    assert calls == [
        "docs-sub-scope-document-delete",
        "docs-sub-scope-document-delete-recovery",
    ]
    assert activity == []


def test_sub_scope_delete_reports_unreconciled_recovery_as_not_retry_safe(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = prepare_delete_repo(tmp_path)
    _status, preview = management_service.docs_management_post_response(
        tmp_path,
        "/docs/delete-preview",
        preview_body(),
    )
    calls = 0

    def fail_both_rebuilds(
        _repo_root,
        _scope,
        _sub_scope,
        _changed_paths,
        write_operation,
        *,
        suppression_reason,
    ):
        nonlocal calls
        del suppression_reason
        calls += 1
        write_operation()
        raise RuntimeError(f"synthetic builder failure {calls}")

    monkeypatch.setattr(
        mutation_service.write_rebuild,
        "perform_sub_scope_source_write_and_rebuild",
        fail_both_rebuilds,
    )

    status, payload = management_service.docs_management_post_response(
        tmp_path,
        "/docs/delete-apply",
        apply_body(preview["source_revision"]),
    )

    assert status == HTTPStatus.INTERNAL_SERVER_ERROR
    assert payload["source_restored"] is True
    assert payload["recovery_rebuild"] == {
        "ok": False,
        "error": "synthetic builder failure 2",
    }
    assert payload["retry_safe"] is False
    assert paths["target_path"].read_bytes() == paths["target_bytes"]
    assert paths["sibling_path"].is_file()
    assert calls == 2
