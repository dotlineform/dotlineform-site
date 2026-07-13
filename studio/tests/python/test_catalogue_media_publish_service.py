#!/usr/bin/env python3
"""Focused checks for the Work editor R2 publish service."""

from __future__ import annotations

import json
from http import HTTPStatus
from pathlib import Path

import pytest

from catalogue.catalogue_media_publish_service import media_publish_apply_response, media_publish_preview_response
from catalogue.catalogue_service_context import build_catalogue_write_context


def make_context(tmp_path: Path, *, media_version: int = 3, status: str = "published"):
    repo_root = tmp_path / "repo"
    source_dir = repo_root / "studio/data/canonical/catalogue"
    source_dir.mkdir(parents=True)
    (source_dir / "works.json").write_text(
        json.dumps(
            {
                "catalogue_source_works_version": "catalogue_source_works_v1",
                "works": {
                    "00042": {
                        "work_id": "00042",
                        "title": "Work",
                        "status": status,
                        "series_ids": [],
                        "project_folder": "project",
                        "project_filename": "work.jpg",
                        "media_version": media_version,
                    }
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return build_catalogue_write_context(repo_root)


def report(*, status: str, media_versions=None, digest: str = "secret-ish-digest"):
    return {
        "counts": {status: 3},
        "missing_variants": [],
        "objects": [
            {
                "kind": "works",
                "item_id": "00042",
                "width": width,
                "status": status,
                "reason": "dry-run" if status.startswith("would_") else "",
                "local_path": f"works/primary/00042-primary-{width}.webp",
                "object_key": f"works/img/00042-primary-{width}.webp",
                "md5": digest,
            }
            for width in (800, 1200, 1600)
        ],
        "media_versions": media_versions or [],
    }


def test_preview_projects_replacement_without_paths_or_credentials(tmp_path: Path) -> None:
    context = make_context(tmp_path)
    calls = []

    def runner(**kwargs):
        calls.append(kwargs)
        return report(status="would_overwrite")

    status, payload = media_publish_preview_response(
        context,
        {"work_id": "42", "expected_media_version": 3},
        publisher_runner=runner,
    )

    assert status == HTTPStatus.OK
    assert payload["ok"] is True
    assert payload["preview"]["blocked"] is False
    assert payload["preview"]["requires_force"] is True
    assert len(payload["preview"]["preview_fingerprint"]) == 64
    assert payload["preview"]["counts"] == {"would_overwrite": 3}
    assert payload["preview"]["objects"] == [
        {"width": width, "status": "would_overwrite", "reason": "dry-run"}
        for width in (800, 1200, 1600)
    ]
    assert "local_path" not in json.dumps(payload)
    assert "object_key" not in json.dumps(payload)
    assert "md5" not in json.dumps(payload)
    assert calls == [
        {
            "repo_root": context.repo_root,
            "kind": "works",
            "item_id": "00042",
            "write": False,
            "force": True,
            "changed_only": False,
            "allow_partial": False,
        }
    ]


def test_preview_sanitizes_remote_and_finalization_failure_details(tmp_path: Path) -> None:
    context = make_context(tmp_path)
    failed_report = report(
        status="failed",
        media_versions=[
            {
                "status": "failed",
                "reason": "media-version finalization failed: /Users/example/private/path",
            }
        ],
    )
    for item in failed_report["objects"]:
        item["reason"] = f"remote check failed: HEAD {item['object_key']} failed with HTTP 500"

    status, payload = media_publish_preview_response(
        context,
        {"work_id": "42", "expected_media_version": 3},
        publisher_runner=lambda **_kwargs: failed_report,
    )

    serialized = json.dumps(payload)
    assert status == HTTPStatus.OK
    assert payload["preview"]["blocked"] is True
    assert {item["reason"] for item in payload["preview"]["objects"]} == {"remote check failed"}
    assert payload["preview"]["media_versions"][0]["reason"] == "media-version finalization failed"
    assert "works/img" not in serialized
    assert "/Users/" not in serialized


def test_apply_requires_explicit_overwrite_acknowledgement(tmp_path: Path) -> None:
    context = make_context(tmp_path)
    with pytest.raises(ValueError, match="confirm_overwrite"):
        media_publish_apply_response(
            context,
            {"work_id": "42", "expected_media_version": 3, "force": True},
            publisher_runner=lambda **_kwargs: report(status="overwritten"),
        )


def test_apply_returns_promoted_record_and_activity(tmp_path: Path) -> None:
    context = make_context(tmp_path)
    dry_report = report(status="would_overwrite")
    _preview_status, preview_payload = media_publish_preview_response(
        context,
        {"work_id": "42", "expected_media_version": 3},
        publisher_runner=lambda **_kwargs: dry_report,
    )

    def runner(**kwargs):
        if not kwargs["write"]:
            return dry_report
        works_payload = json.loads(context.works_path.read_text(encoding="utf-8"))
        works_payload["works"]["00042"]["media_version"] = 4
        context.works_path.write_text(json.dumps(works_payload) + "\n", encoding="utf-8")
        return report(
            status="overwritten",
            media_versions=[
                {
                    "status": "promoted",
                    "previous_version": 3,
                    "media_version": 4,
                    "advanced": True,
                    "reason": "complete upload promoted the confirmed media version",
                }
            ],
        )

    status, payload = media_publish_apply_response(
        context,
        {
            "work_id": "42",
            "expected_media_version": 3,
            "preview_fingerprint": preview_payload["preview"]["preview_fingerprint"],
            "force": True,
            "confirm_overwrite": True,
            "activity_context": {
                "page_id": "catalogue-work",
                "action_id": "publish-work-media",
                "route": "/studio/catalogue-work/",
                "control_id": "catalogueWorkSave",
                "control_selector": "#catalogueWorkSave",
                "work_id": "00042",
                "correlation_id": "publish-media-test",
            },
        },
        publisher_runner=runner,
    )

    assert status == HTTPStatus.OK
    assert payload["ok"] is True
    assert payload["previous_media_version"] == 3
    assert payload["media_version"] == 4
    assert payload["record"]["media_version"] == 4
    assert payload["result"]["counts"] == {"overwritten": 3}
    assert payload["activity_log"]["written_count"] == 1


def test_version_conflict_stops_before_remote_work(tmp_path: Path) -> None:
    context = make_context(tmp_path, media_version=4)
    called = False

    def runner(**_kwargs):
        nonlocal called
        called = True
        return report(status="would_upload")

    status, payload = media_publish_preview_response(
        context,
        {"work_id": "42", "expected_media_version": 3},
        publisher_runner=runner,
    )

    assert status == HTTPStatus.CONFLICT
    assert payload["media_version"] == 4
    assert called is False


def test_apply_surfaces_incomplete_remote_result(tmp_path: Path) -> None:
    context = make_context(tmp_path)
    dry_report = report(status="would_upload")
    _preview_status, preview_payload = media_publish_preview_response(
        context,
        {"work_id": "42", "expected_media_version": 3},
        publisher_runner=lambda **_kwargs: dry_report,
    )

    def runner(**kwargs):
        return dry_report if not kwargs["write"] else report(status="blocked_changed")

    status, payload = media_publish_apply_response(
        context,
        {
            "work_id": "42",
            "expected_media_version": 3,
            "preview_fingerprint": preview_payload["preview"]["preview_fingerprint"],
            "force": False,
        },
        publisher_runner=runner,
    )

    assert status == HTTPStatus.BAD_GATEWAY
    assert payload["ok"] is False
    assert payload["result"]["blocked"] is True


def test_apply_rejects_local_plan_drift_before_write(tmp_path: Path) -> None:
    context = make_context(tmp_path)
    initial_report = report(status="would_upload", digest="initial")
    _preview_status, preview_payload = media_publish_preview_response(
        context,
        {"work_id": "42", "expected_media_version": 3},
        publisher_runner=lambda **_kwargs: initial_report,
    )
    writes = []

    def runner(**kwargs):
        if kwargs["write"]:
            writes.append(kwargs)
        return report(status="would_upload", digest="changed")

    status, payload = media_publish_apply_response(
        context,
        {
            "work_id": "42",
            "expected_media_version": 3,
            "preview_fingerprint": preview_payload["preview"]["preview_fingerprint"],
            "force": False,
        },
        publisher_runner=runner,
    )

    assert status == HTTPStatus.CONFLICT
    assert "changed since preview" in payload["error"]
    assert writes == []
