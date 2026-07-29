#!/usr/bin/env python3
"""Focused parent and configured sub-scope document-create contracts."""

from __future__ import annotations

from http import HTTPStatus
from pathlib import Path
import sys

import pytest

from repo_factory import (
    docs_scope_record,
    docs_sub_scope_record,
    write_docs_scope_config,
    write_site_tools_config,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))

import docs_management_mutation_service as mutation_service  # noqa: E402
import docs_management_mutations as mutations  # noqa: E402
import docs_management_routes as routes  # noqa: E402
import docs_management_service as management_service  # noqa: E402
import docs_source_model as source_model  # noqa: E402


FIXED_DOC_ID = "d-20260729-190000-abcdef"


def write_source(
    path: Path,
    *,
    doc_id: str,
    title: str,
    parent_id: str | None = None,
) -> None:
    front_matter: dict[str, object] = {
        "doc_id": doc_id,
        "title": title,
    }
    if parent_id is not None:
        front_matter["parent_id"] = parent_id
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        source_model.format_source(front_matter, f"# {title}\n"),
        encoding="utf-8",
    )


def prepare_repo(
    repo_root: Path,
    *,
    scope_type: str = "local",
) -> tuple[Path, Path]:
    write_site_tools_config(repo_root)
    write_docs_scope_config(
        repo_root,
        [
            docs_scope_record(
                "analysis",
                scope_type=scope_type,
                viewer_base_url=(
                    "/analysis/" if scope_type == "public" else "/docs/"
                ),
                include_scope_param=scope_type != "public",
                sub_scopes=[
                    docs_sub_scope_record(
                        "analysis",
                        "tags",
                        scope_type=scope_type,
                        title="Tags",
                        document_groups=["subject", "domain", "form", "theme"],
                    )
                ],
            )
        ],
    )
    parent_root = (
        repo_root
        / "docs-viewer/scopes/analysis/source/documents"
    )
    child_root = (
        repo_root
        / "docs-viewer/scopes/analysis/source/sub-scopes/tags/documents"
    )
    write_source(
        parent_root / "report-source.md",
        doc_id="report",
        title="Report",
        parent_id="",
    )
    child_root.mkdir(parents=True, exist_ok=True)
    return parent_root, child_root


def fix_created_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        mutations.source_model,
        "allocate_doc_id",
        lambda _timestamp, _used: FIXED_DOC_ID,
    )


def capture_activity(
    monkeypatch: pytest.MonkeyPatch,
) -> list[tuple[str, dict[str, object]]]:
    events: list[tuple[str, dict[str, object]]] = []
    monkeypatch.setattr(
        mutation_service,
        "log_event",
        lambda _repo_root, event_name, details: events.append(
            (event_name, dict(details))
        ),
    )
    return events


def test_parent_create_keeps_response_and_rebuild_contract_with_exact_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parent_root, _child_root = prepare_repo(tmp_path)
    fix_created_identity(monkeypatch)
    rebuild_calls: list[dict[str, object]] = []

    def fake_parent_rebuild(
        _repo_root: Path,
        scope: str,
        changed_paths: list[Path],
        write_operation,
        **kwargs,
    ) -> dict[str, object]:
        write_operation()
        rebuild_calls.append(
            {
                "scope": scope,
                "changed_paths": list(changed_paths),
                **kwargs,
            }
        )
        return {"ok": True, "mode": "parent"}

    monkeypatch.setattr(
        mutation_service.write_rebuild,
        "perform_source_write_and_rebuild",
        fake_parent_rebuild,
    )
    events = capture_activity(monkeypatch)

    status, payload = management_service.docs_management_post_response(
        tmp_path,
        routes.CREATE_PATH,
        {
            "scope": "analysis",
            "title": "Parent Child",
            "parent_id": "report",
        },
    )

    expected_path = parent_root / f"{FIXED_DOC_ID}.md"
    assert status == HTTPStatus.OK
    assert set(payload) == {
        "ok",
        "scope",
        "doc_id",
        "path",
        "target",
        "record",
        "summary_text",
        "rebuild",
        "dry_run",
    }
    assert payload["target"] == {
        "scope": "analysis",
        "doc_id": FIXED_DOC_ID,
    }
    assert payload["record"] == {
        "doc_id": FIXED_DOC_ID,
        "title": "Parent Child",
        "viewable": True,
        "parent_id": "report",
    }
    assert payload["rebuild"] == {"ok": True, "mode": "parent"}
    assert payload["dry_run"] is False
    assert expected_path.is_file()
    front_matter, body = source_model.parse_source(expected_path)
    assert front_matter["parent_id"] == "report"
    assert body == "# Parent Child\n"
    assert rebuild_calls == [
        {
            "scope": "analysis",
            "changed_paths": [expected_path],
            "suppression_reason": "docs-create",
            "docs_doc_ids": [FIXED_DOC_ID],
            "search_doc_ids": [FIXED_DOC_ID],
        }
    ]
    assert events == [
        (
            "docs-create",
            {
                "scope": "analysis",
                "doc_id": FIXED_DOC_ID,
                "path": (
                    "docs-viewer/scopes/analysis/source/documents/"
                    f"{FIXED_DOC_ID}.md"
                ),
            },
        )
    ]


def test_empty_sub_scope_create_is_confined_and_returns_exact_child_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parent_root, child_root = prepare_repo(tmp_path, scope_type="public")
    fix_created_identity(monkeypatch)
    rebuild_calls: list[dict[str, object]] = []

    def fake_child_rebuild(
        _repo_root: Path,
        scope: str,
        sub_scope: str,
        changed_paths: list[Path],
        write_operation,
        **kwargs,
    ) -> dict[str, object]:
        write_operation()
        rebuild_calls.append(
            {
                "scope": scope,
                "sub_scope": sub_scope,
                "changed_paths": list(changed_paths),
                **kwargs,
            }
        )
        return {"ok": True, "mode": "sub_scope"}

    monkeypatch.setattr(
        mutation_service.write_rebuild,
        "perform_sub_scope_source_write_and_rebuild",
        fake_child_rebuild,
    )
    events = capture_activity(monkeypatch)

    status, payload = management_service.docs_management_post_response(
        tmp_path,
        routes.CREATE_PATH,
        {
            "scope": "analysis",
            "sub_scope": "tags",
            "title": "First Concept",
        },
    )

    expected_path = child_root / f"{FIXED_DOC_ID}.md"
    assert status == HTTPStatus.OK
    assert payload["scope"] == "analysis"
    assert payload["sub_scope"] == "tags"
    assert payload["target"] == {
        "scope": "analysis",
        "sub_scope": "tags",
        "doc_id": FIXED_DOC_ID,
    }
    assert payload["record"] == {
        "doc_id": FIXED_DOC_ID,
        "title": "First Concept",
        "viewable": False,
    }
    assert payload["rebuild"] == {"ok": True, "mode": "sub_scope"}
    assert expected_path.is_file()
    front_matter, body = source_model.parse_source(expected_path)
    assert front_matter["doc_id"] == FIXED_DOC_ID
    assert front_matter["title"] == "First Concept"
    assert front_matter["viewable"] is False
    assert "parent_id" not in front_matter
    assert body == "# First Concept\n"
    assert list(parent_root.glob(f"{FIXED_DOC_ID}.md")) == []
    assert rebuild_calls == [
        {
            "scope": "analysis",
            "sub_scope": "tags",
            "changed_paths": [expected_path],
            "suppression_reason": "docs-create",
        }
    ]
    assert events == [
        (
            "docs-create",
            {
                "scope": "analysis",
                "sub_scope": "tags",
                "doc_id": FIXED_DOC_ID,
                "path": (
                    "docs-viewer/scopes/analysis/source/sub-scopes/tags/"
                    f"documents/{FIXED_DOC_ID}.md"
                ),
            },
        )
    ]


@pytest.mark.parametrize(
    ("request_update", "message"),
    [
        ({"sub_scope": ""}, "sub_scope is required"),
        ({"sub_scope": "missing"}, "unknown sub_scope"),
        ({"sub_scope": "tags/nested"}, "one configured child"),
        (
            {"sub_scope": "tags", "parent_id": ""},
            "parent_id is not accepted",
        ),
    ],
)
def test_sub_scope_create_rejects_invalid_collection_shapes(
    tmp_path: Path,
    request_update: dict[str, object],
    message: str,
) -> None:
    prepare_repo(tmp_path)
    request = {
        "scope": "analysis",
        "title": "Invalid",
        **request_update,
    }

    with pytest.raises(ValueError, match=message):
        management_service.docs_management_post_response(
            tmp_path,
            routes.CREATE_PATH,
            request,
            dry_run=True,
        )


def test_sub_scope_create_rejects_mismatched_and_escaping_existing_sources(
    tmp_path: Path,
) -> None:
    _parent_root, child_root = prepare_repo(tmp_path)
    write_source(
        child_root / "mismatch.md",
        doc_id="different",
        title="Mismatch",
    )

    with pytest.raises(ValueError, match="does not match requested doc_id"):
        management_service.docs_management_post_response(
            tmp_path,
            routes.CREATE_PATH,
            {
                "scope": "analysis",
                "sub_scope": "tags",
                "title": "Blocked",
            },
            dry_run=True,
        )

    (child_root / "mismatch.md").unlink()
    outside = tmp_path / "outside.md"
    write_source(outside, doc_id="escape", title="Escape")
    (child_root / "escape.md").symlink_to(outside)

    with pytest.raises(ValueError, match="escapes configured document root"):
        management_service.docs_management_post_response(
            tmp_path,
            routes.CREATE_PATH,
            {
                "scope": "analysis",
                "sub_scope": "tags",
                "title": "Blocked",
            },
            dry_run=True,
        )


def test_create_refuses_a_destination_that_appears_after_planning(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _parent_root, child_root = prepare_repo(tmp_path)
    fix_created_identity(monkeypatch)
    collision_path = child_root / f"{FIXED_DOC_ID}.md"

    def collide_before_write(
        _repo_root: Path,
        _scope: str,
        _sub_scope: str,
        _changed_paths: list[Path],
        write_operation,
        **_kwargs,
    ) -> dict[str, object]:
        collision_path.write_text("existing collision\n", encoding="utf-8")
        write_operation()
        raise AssertionError("create-only write should refuse the collision")

    monkeypatch.setattr(
        mutation_service.write_rebuild,
        "perform_sub_scope_source_write_and_rebuild",
        collide_before_write,
    )

    with pytest.raises(FileExistsError, match="source path already exists"):
        management_service.docs_management_post_response(
            tmp_path,
            routes.CREATE_PATH,
            {
                "scope": "analysis",
                "sub_scope": "tags",
                "title": "Collision",
            },
        )

    assert collision_path.read_text(encoding="utf-8") == "existing collision\n"


def test_sub_scope_create_write_failure_is_pre_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _parent_root, child_root = prepare_repo(tmp_path)
    fix_created_identity(monkeypatch)

    def fail_write(_path: Path, _text: str) -> None:
        raise OSError("simulated create write failure")

    def invoke_write(
        _repo_root: Path,
        _scope: str,
        _sub_scope: str,
        _changed_paths: list[Path],
        write_operation,
        **_kwargs,
    ) -> dict[str, object]:
        write_operation()
        raise AssertionError("failed write must stop before rebuild")

    monkeypatch.setattr(
        mutation_service.source_model,
        "write_text_atomic_new",
        fail_write,
    )
    monkeypatch.setattr(
        mutation_service.write_rebuild,
        "perform_sub_scope_source_write_and_rebuild",
        invoke_write,
    )
    events = capture_activity(monkeypatch)

    with pytest.raises(OSError, match="simulated create write failure"):
        management_service.docs_management_post_response(
            tmp_path,
            routes.CREATE_PATH,
            {
                "scope": "analysis",
                "sub_scope": "tags",
                "title": "Write Failure",
            },
        )

    assert not (child_root / f"{FIXED_DOC_ID}.md").exists()
    assert events == []


def test_sub_scope_create_rebuild_failure_reports_the_committed_target_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _parent_root, child_root = prepare_repo(tmp_path)
    fix_created_identity(monkeypatch)

    def fail_after_write(
        _repo_root: Path,
        _scope: str,
        _sub_scope: str,
        _changed_paths: list[Path],
        write_operation,
        **_kwargs,
    ) -> dict[str, object]:
        write_operation()
        raise RuntimeError("simulated child projection failure")

    monkeypatch.setattr(
        mutation_service.write_rebuild,
        "perform_sub_scope_source_write_and_rebuild",
        fail_after_write,
    )
    events = capture_activity(monkeypatch)

    status, payload = management_service.docs_management_post_response(
        tmp_path,
        routes.CREATE_PATH,
        {
            "scope": "analysis",
            "sub_scope": "tags",
            "title": "Committed Child",
        },
    )

    committed_path = child_root / f"{FIXED_DOC_ID}.md"
    assert status == HTTPStatus.INTERNAL_SERVER_ERROR
    assert payload["ok"] is False
    assert payload["operation"] == "create"
    assert payload["committed"] is True
    assert payload["retry_create"] is False
    assert payload["target"] == {
        "scope": "analysis",
        "sub_scope": "tags",
        "doc_id": FIXED_DOC_ID,
    }
    assert payload["rebuild"] == {
        "ok": False,
        "error": "simulated child projection failure",
    }
    assert committed_path.is_file()
    assert len(list(child_root.glob("*.md"))) == 1
    assert events == [
        (
            "docs-create",
            {
                "scope": "analysis",
                "sub_scope": "tags",
                "doc_id": FIXED_DOC_ID,
                "path": (
                    "docs-viewer/scopes/analysis/source/sub-scopes/tags/"
                    f"documents/{FIXED_DOC_ID}.md"
                ),
                "rebuild_ok": False,
            },
        )
    ]
