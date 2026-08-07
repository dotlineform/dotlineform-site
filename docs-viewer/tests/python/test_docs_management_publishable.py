#!/usr/bin/env python3
"""Focused exact-selection Set Publishable service contracts."""

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

import docs_management_publishable as publishable_service  # noqa: E402
import docs_management_routes as routes  # noqa: E402
import docs_management_service as management_service  # noqa: E402
import docs_source_model as source_model  # noqa: E402


def write_source(
    path: Path,
    *,
    doc_id: str,
    title: str,
    publishable: bool | None = None,
) -> None:
    front_matter: dict[str, object] = {
        "doc_id": doc_id,
        "title": title,
    }
    if publishable is not None:
        front_matter["publishable"] = publishable
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        source_model.format_source(front_matter, f"# {title}\n"),
        encoding="utf-8",
    )


def prepare_repo(repo_root: Path, *, scope_type: str = "public") -> tuple[Path, Path]:
    write_site_tools_config(repo_root)
    write_docs_scope_config(
        repo_root,
        [
            docs_scope_record(
                "analysis",
                scope_type=scope_type,
                viewer_base_url="/analysis/" if scope_type == "public" else "/docs/",
                include_scope_param=scope_type != "public",
                sub_scopes=[
                    docs_sub_scope_record(
                        "analysis",
                        "works",
                        scope_type=scope_type,
                        title="Works",
                    )
                ],
            )
        ],
    )
    parent_root = repo_root / "docs-viewer/scopes/analysis/source/documents"
    child_root = (
        repo_root
        / "docs-viewer/scopes/analysis/source/sub-scopes/works/documents"
    )
    write_source(parent_root / "a.md", doc_id="a", title="A")
    write_source(
        parent_root / "b.md",
        doc_id="b",
        title="B",
        publishable=False,
    )
    write_source(parent_root / "c.md", doc_id="c", title="C")
    write_source(child_root / "x.md", doc_id="x", title="X")
    write_source(
        child_root / "y.md",
        doc_id="y",
        title="Y",
        publishable=False,
    )
    return parent_root, child_root


def front_matter(path: Path) -> dict[str, object]:
    parsed, _body = source_model.parse_source(path)
    return parsed


def request(
    doc_ids: list[str],
    publishable: bool,
    *,
    sub_scope: str = "",
) -> dict[str, object]:
    return {
        "scope": "analysis",
        **({"sub_scope": sub_scope} if sub_scope else {}),
        "doc_ids": doc_ids,
        "publishable": publishable,
        "confirm": True,
    }


def test_parent_selection_prevalidates_and_rebuilds_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parent_root, _child_root = prepare_repo(tmp_path)
    rebuild_calls: list[dict[str, object]] = []
    activity: list[tuple[str, dict[str, object]]] = []

    def atomic_rebuild(
        _repo_root: Path,
        scope: str,
        changed_paths: list[Path],
        write_operation,
        **kwargs,
    ) -> dict[str, object]:
        rebuild_calls.append(
            {
                "scope": scope,
                "paths": [path.name for path in changed_paths],
                "docs": kwargs["docs_doc_ids"],
                "search": kwargs["search_doc_ids"],
                "snapshots": sorted(path.name for path in kwargs["source_snapshots"]),
            }
        )
        write_operation()
        return {"ok": True, "kind": "parent"}

    monkeypatch.setattr(
        publishable_service.write_rebuild,
        "perform_scope_source_write_and_rebuild_atomic",
        atomic_rebuild,
    )
    monkeypatch.setattr(
        publishable_service,
        "log_event",
        lambda _root, name, details: activity.append((name, dict(details))),
    )

    result = publishable_service.set_publishable(
        tmp_path,
        request(["a", "b"], False),
    )

    assert result["target"] == {"scope": "analysis"}
    assert result["requested_doc_ids"] == ["a", "b"]
    assert result["updated_doc_ids"] == ["a"]
    assert result["unchanged_doc_ids"] == ["b"]
    assert result["updated_count"] == 1
    assert result["rebuild"] == {"ok": True, "kind": "parent"}
    assert rebuild_calls == [
        {
            "scope": "analysis",
            "paths": ["a.md"],
            "docs": ["a"],
            "search": ["a"],
            "snapshots": ["a.md"],
        }
    ]
    assert front_matter(parent_root / "a.md")["publishable"] is False
    assert front_matter(parent_root / "b.md")["publishable"] is False
    assert "publishable" not in front_matter(parent_root / "c.md")
    assert activity == [
        (
            "docs-set-publishable",
            {
                "scope": "analysis",
                "doc_ids": ["a"],
                "publishable": False,
            },
        )
    ]


def test_sub_scope_include_removes_false_and_rebuilds_exact_child_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _parent_root, child_root = prepare_repo(tmp_path)
    rebuild_calls: list[dict[str, object]] = []

    def atomic_child_rebuild(
        _repo_root: Path,
        scope: str,
        sub_scope: str,
        changed_paths: list[Path],
        write_operation,
        **kwargs,
    ) -> dict[str, object]:
        rebuild_calls.append(
            {
                "scope": scope,
                "sub_scope": sub_scope,
                "paths": [path.name for path in changed_paths],
                "snapshots": sorted(path.name for path in kwargs["source_snapshots"]),
            }
        )
        write_operation()
        return {"ok": True, "kind": "child"}

    monkeypatch.setattr(
        publishable_service.write_rebuild,
        "perform_sub_scope_source_write_and_rebuild",
        atomic_child_rebuild,
    )
    monkeypatch.setattr(publishable_service, "log_event", lambda *_args: None)

    result = publishable_service.set_publishable(
        tmp_path,
        request(["x", "y"], True, sub_scope="works"),
    )

    assert result["target"] == {"scope": "analysis", "sub_scope": "works"}
    assert result["updated_doc_ids"] == ["y"]
    assert result["unchanged_doc_ids"] == ["x"]
    assert rebuild_calls == [
        {
            "scope": "analysis",
            "sub_scope": "works",
            "paths": ["y.md"],
            "snapshots": ["y.md"],
        }
    ]
    assert "publishable" not in front_matter(child_root / "x.md")
    assert "publishable" not in front_matter(child_root / "y.md")


def test_all_no_op_set_skips_write_rebuild_and_activity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepare_repo(tmp_path)
    rebuild_called = False
    activity_called = False

    def unexpected_rebuild(*_args, **_kwargs):
        nonlocal rebuild_called
        rebuild_called = True
        raise AssertionError("no-op Set Publishable must not rebuild")

    def unexpected_activity(*_args, **_kwargs):
        nonlocal activity_called
        activity_called = True

    monkeypatch.setattr(
        publishable_service.write_rebuild,
        "perform_scope_source_write_and_rebuild_atomic",
        unexpected_rebuild,
    )
    monkeypatch.setattr(publishable_service, "log_event", unexpected_activity)

    result = publishable_service.set_publishable(
        tmp_path,
        request(["a", "c"], True),
    )

    assert result["updated_doc_ids"] == []
    assert result["unchanged_doc_ids"] == ["a", "c"]
    assert result["rebuild"] is None
    assert rebuild_called is False
    assert activity_called is False


def test_invalid_or_unavailable_selection_fails_before_any_write(
    tmp_path: Path,
) -> None:
    parent_root, _child_root = prepare_repo(tmp_path)
    before = (parent_root / "a.md").read_bytes()

    with pytest.raises(FileNotFoundError, match="missing"):
        publishable_service.plan_set_publishable(
            tmp_path,
            request(["a", "missing"], False),
        )
    assert (parent_root / "a.md").read_bytes() == before

    with pytest.raises(ValueError, match="duplicate doc_id"):
        publishable_service.plan_set_publishable(
            tmp_path,
            request(["a", "a"], False),
        )
    with pytest.raises(ValueError, match="publishable must be true or false"):
        publishable_service.plan_set_publishable(
            tmp_path,
            {**request(["a"], False), "publishable": "false"},
        )
    with pytest.raises(ValueError, match="confirm=true"):
        publishable_service.plan_set_publishable(
            tmp_path,
            {**request(["a"], False), "confirm": False},
        )


@pytest.mark.parametrize("sub_scope", ["", "works"])
def test_local_collection_rejects_publishability_without_replacement(
    tmp_path: Path,
    sub_scope: str,
) -> None:
    prepare_repo(tmp_path, scope_type="local")
    with pytest.raises(ValueError, match="not supported for local collection"):
        publishable_service.plan_set_publishable(
            tmp_path,
            request(["x" if sub_scope else "a"], False, sub_scope=sub_scope),
        )


def test_stale_snapshot_conflict_precedes_all_mutation(tmp_path: Path) -> None:
    parent_root, _child_root = prepare_repo(tmp_path)
    plan = publishable_service.plan_set_publishable(
        tmp_path,
        request(["a", "c"], False),
    )
    a_path = parent_root / "a.md"
    c_path = parent_root / "c.md"
    a_path.write_bytes(a_path.read_bytes() + b"\nConcurrent edit.\n")
    c_before = c_path.read_bytes()

    with pytest.raises(
        publishable_service.PublishableSelectionConflict
    ) as error:
        publishable_service.apply_set_publishable_plan(tmp_path, plan)

    assert error.value.payload["committed"] is False
    assert error.value.payload["retry_safe"] is True
    assert error.value.payload["rollback"]["status"] == "not_started"
    assert "publishable" not in front_matter(c_path)
    assert c_path.read_bytes() == c_before


def test_atomic_rebuild_failure_restores_complete_parent_selection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parent_root, _child_root = prepare_repo(tmp_path)
    before = {
        doc_id: (parent_root / f"{doc_id}.md").read_bytes()
        for doc_id in ("a", "c")
    }
    rebuild_count = 0

    def fail_then_recover(*_args, **_kwargs):
        nonlocal rebuild_count
        rebuild_count += 1
        if rebuild_count == 1:
            raise RuntimeError("synthetic rebuild failure")
        return {"ok": True, "recovered": True}

    monkeypatch.setattr(
        publishable_service.write_rebuild,
        "rebuild_scope_outputs",
        fail_then_recover,
    )

    with pytest.raises(
        publishable_service.PublishableSelectionApplyError
    ) as error:
        publishable_service.set_publishable(
            tmp_path,
            request(["a", "c"], False),
        )

    assert rebuild_count == 2
    assert error.value.payload["committed"] is False
    assert error.value.payload["retry_safe"] is True
    assert error.value.payload["rollback"] == {
        "status": "completed",
        "sources_restored": True,
        "rebuild": {"ok": True, "recovered": True},
        "error": "",
    }
    assert {
        doc_id: (parent_root / f"{doc_id}.md").read_bytes()
        for doc_id in ("a", "c")
    } == before


def test_route_maps_set_publishable_success_conflict_and_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepare_repo(tmp_path)
    body = request(["a"], False)

    monkeypatch.setattr(
        management_service.docs_management_publishable,
        "set_publishable",
        lambda _root, _body, dry_run: {"ok": True, "dry_run": dry_run},
    )
    status, payload = management_service.docs_management_post_response(
        tmp_path,
        routes.SET_PUBLISHABLE_PATH,
        body,
        dry_run=True,
    )
    assert status == HTTPStatus.OK
    assert payload == {"ok": True, "dry_run": True}

    def conflict(*_args, **_kwargs):
        raise publishable_service.PublishableSelectionConflict(
            {"ok": False, "error": "stale"}
        )

    monkeypatch.setattr(
        management_service.docs_management_publishable,
        "set_publishable",
        conflict,
    )
    status, payload = management_service.docs_management_post_response(
        tmp_path,
        routes.SET_PUBLISHABLE_PATH,
        body,
    )
    assert status == HTTPStatus.CONFLICT
    assert payload == {"ok": False, "error": "stale"}

    def failed(*_args, **_kwargs):
        raise publishable_service.PublishableSelectionApplyError(
            {"ok": False, "error": "rebuild failed"}
        )

    monkeypatch.setattr(
        management_service.docs_management_publishable,
        "set_publishable",
        failed,
    )
    status, payload = management_service.docs_management_post_response(
        tmp_path,
        routes.SET_PUBLISHABLE_PATH,
        body,
    )
    assert status == HTTPStatus.INTERNAL_SERVER_ERROR
    assert payload == {"ok": False, "error": "rebuild failed"}
