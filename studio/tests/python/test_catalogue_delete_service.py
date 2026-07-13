#!/usr/bin/env python3
"""Focused service checks for post-delete R2 media cleanup."""

from __future__ import annotations

import json
import sys
from http import HTTPStatus
from pathlib import Path
from types import SimpleNamespace


REPO_ROOT = Path(__file__).resolve().parents[3]
SERVICES_DIR = REPO_ROOT / "studio/services"
SHARED_PYTHON_DIR = REPO_ROOT / "studio/shared/python"
for candidate in (SERVICES_DIR, SHARED_PYTHON_DIR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from catalogue import catalogue_delete_service as delete_service  # noqa: E402
from catalogue.catalogue_service_context import build_catalogue_write_context  # noqa: E402


def stub_local_delete(monkeypatch, *, affected: dict, order: list[str]) -> None:
    preview = {"blocked": False, "affected": affected}
    plan = SimpleNamespace(payloads={}, cleanup={}, activity_affected=affected)
    monkeypatch.setattr(
        delete_service.catalogue_delete_plans,
        "build_delete_preview",
        lambda *_args, **_kwargs: preview,
    )
    monkeypatch.setattr(
        delete_service.catalogue_delete_plans,
        "build_delete_apply_plan",
        lambda *_args, **_kwargs: plan,
    )

    def execute_local_delete(**_kwargs):
        order.append("local")
        return SimpleNamespace(
            payload={
                "deleted_files": 4,
                "updated_json_files": 2,
            },
            written_paths=[],
        )

    monkeypatch.setattr(
        delete_service.transactions,
        "execute_catalogue_cleanup_transaction",
        execute_local_delete,
    )


def test_work_delete_cleans_work_and_dependent_detail_r2_media_after_local_delete(
    tmp_path: Path,
    monkeypatch,
) -> None:
    order: list[str] = []
    affected = {
        "works": ["00042"],
        "work_details": ["00042-001", "00042-002"],
        "series": [],
    }
    stub_local_delete(monkeypatch, affected=affected, order=order)

    def remote_delete(**kwargs):
        order.append("r2")
        targets = kwargs["targets"]
        assert set(targets) == {
            ("works", "00042"),
            ("work_details", "00042-001"),
            ("work_details", "00042-002"),
        }
        return {
            "counts": {"deleted": 8, "missing": 1},
            "objects": [
                {"kind": kind, "item_id": item_id, "status": "deleted"}
                for kind, item_id in targets
                for _width in (800, 1200, 1600)
            ],
        }

    status, payload = delete_service.delete_apply_response(
        build_catalogue_write_context(tmp_path / "repo"),
        {"kind": "work", "id": "42"},
        remote_delete_runner=remote_delete,
    )

    assert status == HTTPStatus.OK
    assert payload["deleted"] is True
    assert order == ["local", "r2"]
    assert payload["cleanup"]["r2_media"] == {
        "status": "completed",
        "target_count": 3,
        "object_count": 9,
        "deleted": 8,
        "missing": 1,
        "failed": 0,
        "failed_targets": [],
    }


def test_section_delete_keeps_local_success_and_returns_safe_warning_when_r2_fails(
    tmp_path: Path,
    monkeypatch,
) -> None:
    order: list[str] = []
    affected = {
        "works": ["00042"],
        "work_details": ["00042-001", "00042-002"],
        "series": [],
    }
    stub_local_delete(monkeypatch, affected=affected, order=order)

    def remote_delete(**_kwargs):
        order.append("r2")
        raise RuntimeError("secret remote failure")

    status, payload = delete_service.delete_apply_response(
        build_catalogue_write_context(tmp_path / "repo"),
        {"kind": "work_detail_section", "section_id": "00042-1"},
        remote_delete_runner=remote_delete,
    )

    assert status == HTTPStatus.OK
    assert payload["ok"] is True
    assert payload["deleted"] is True
    assert order == ["local", "r2"]
    assert payload["cleanup"]["r2_media"] == {
        "status": "warning",
        "target_count": 2,
        "object_count": 6,
        "deleted": 0,
        "missing": 0,
        "failed": 6,
        "failed_targets": [
            {"kind": "work_details", "id": "00042-001"},
            {"kind": "work_details", "id": "00042-002"},
        ],
    }
    assert "secret remote failure" not in json.dumps(payload)


def test_delete_dry_run_does_not_contact_r2(tmp_path: Path, monkeypatch) -> None:
    order: list[str] = []
    affected = {
        "works": ["00042"],
        "work_details": ["00042-001"],
        "series": [],
    }
    stub_local_delete(monkeypatch, affected=affected, order=order)

    status, payload = delete_service.delete_apply_response(
        build_catalogue_write_context(tmp_path / "repo", dry_run=True),
        {"kind": "work", "id": "42"},
        remote_delete_runner=lambda **_kwargs: (_ for _ in ()).throw(AssertionError("unexpected R2 call")),
    )

    assert status == HTTPStatus.OK
    assert payload["dry_run"] is True
    assert "r2_media" not in payload["cleanup"]
    assert order == ["local"]
