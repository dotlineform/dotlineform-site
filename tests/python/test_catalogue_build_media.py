#!/usr/bin/env python3
"""Verify catalogue scoped-build media planning and readiness helpers."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from catalogue import catalogue_build_media as media  # noqa: E402
from catalogue.catalogue_source import payload_for_map  # noqa: E402
from catalogue.moment_sources import moment_metadata_payload  # noqa: E402
from pipeline_config import source_moments_images_subdir, source_works_root_subdir  # noqa: E402


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_source_fixture(source_dir: Path) -> None:
    write_json(
        source_dir / "works.json",
        payload_for_map(
            "works",
            {
                "00001": {
                    "work_id": "00001",
                    "status": "published",
                    "project_folder": "2026/alpha",
                    "project_filename": "alpha.jpg",
                    "title": "Alpha",
                },
                "00002": {
                    "work_id": "00002",
                    "status": "published",
                    "project_filename": "beta.jpg",
                    "title": "Beta",
                },
            },
        ),
    )
    write_json(
        source_dir / "work_details.json",
        payload_for_map(
            "work_details",
            {
                "00001-001": {
                    "detail_uid": "00001-001",
                    "work_id": "00001",
                    "detail_id": "001",
                    "project_subfolder": "details",
                    "project_filename": "alpha-detail.jpg",
                    "status": "published",
                }
            },
        ),
    )
    write_json(source_dir / "series.json", payload_for_map("series", {}))
    write_json(
        source_dir / "moments.json",
        moment_metadata_payload(
            {
                "keys": {
                    "moment_id": "keys",
                    "title": "Keys",
                    "status": "published",
                    "date": "2026-01-01",
                    "source_image_file": "keys-source.jpg",
                },
                "missing-moment": {
                    "moment_id": "missing-moment",
                    "title": "Missing Moment",
                    "status": "published",
                    "date": "2026-01-02",
                    "source_image_file": "missing-moment-source.jpg",
                },
            }
        ),
    )


def projects_env(projects_base: Path) -> dict[str, str]:
    return {media.PROJECTS_BASE_DIR_ENV_NAME: str(projects_base)}


def touch_outputs(paths: list[Path], *, newer_than: Path) -> None:
    source_time = newer_than.stat().st_mtime
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"generated")
        newer_time = source_time + 10
        path.touch()
        path.chmod(0o644)
        os.utime(path, (newer_time, newer_time))


def test_resolves_work_detail_sources_and_missing_metadata_reasons() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source_dir = root / "assets/studio/data/catalogue"
        projects_base = root / "projects"
        projects_base.mkdir(parents=True, exist_ok=True)
        write_source_fixture(source_dir)
        records = media.records_from_json_source(source_dir)

        work_path, reason, base_dir, availability = media.resolve_work_media_source(
            records,
            "00001",
            env=projects_env(projects_base),
        )
        detail_path, detail_reason, _, _ = media.resolve_detail_media_source(
            records,
            "00001-001",
            env=projects_env(projects_base),
        )
        missing_path, missing_reason, _, _ = media.resolve_work_media_source(
            records,
            "00002",
            env=projects_env(projects_base),
        )

    works_root = source_works_root_subdir(media.PIPELINE_CONFIG)
    assert work_path == (projects_base / works_root / "2026/alpha/alpha.jpg").resolve()
    assert reason == ""
    assert base_dir == projects_base.resolve()
    assert availability == ""
    assert detail_path == (projects_base / works_root / "2026/alpha/details/alpha-detail.jpg").resolve()
    assert detail_reason == ""
    assert missing_path is None
    assert missing_reason == "missing_project_folder"


def test_local_media_plan_reports_pending_current_blocked_and_unavailable_states() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        repo_root = root / "repo"
        source_dir = repo_root / "assets/studio/data/catalogue"
        projects_base = root / "projects"
        source_image = projects_base / source_works_root_subdir(media.PIPELINE_CONFIG) / "2026/alpha/alpha.jpg"
        moment_image = projects_base / source_moments_images_subdir(media.PIPELINE_CONFIG) / "keys-source.jpg"
        source_image.parent.mkdir(parents=True, exist_ok=True)
        moment_image.parent.mkdir(parents=True, exist_ok=True)
        source_image.write_bytes(b"source")
        moment_image.write_bytes(b"moment source")
        write_source_fixture(source_dir)

        scope = {"source_dir": str(source_dir), "work_ids": ["00001", "00002"], "detail_uid": "00001-001"}
        plan = media.build_local_media_plan(repo_root, scope=scope, env=projects_env(projects_base))
        current_paths = [
            Path(plan["tasks"][0]["staged_source_abs_path"]),
            *[repo_root / path for path in plan["tasks"][0]["output_paths"]],
        ]
        touch_outputs(current_paths, newer_than=source_image)
        current_plan = media.build_local_media_plan(repo_root, scope={**scope, "work_ids": ["00001"]}, env=projects_env(projects_base))
        forced_plan = media.build_local_media_plan(
            repo_root,
            scope={**scope, "work_ids": ["00001"]},
            env=projects_env(projects_base),
            force=True,
        )
        unavailable_plan = media.build_local_media_plan(repo_root, scope={**scope, "work_ids": ["00001"]}, env={})

    assert plan["counts"] == {"pending": 1, "current": 0, "blocked": 2, "unavailable": 0}
    assert plan["tasks"][0]["status"] == "pending"
    assert plan["tasks"][0]["staged_source_path"] == "var/catalogue/media/works/make_srcset_images/00001.jpg"
    assert plan["tasks"][1]["reason"] == "project folder is missing"
    assert plan["tasks"][2]["kind"] == "work_details"
    assert plan["tasks"][2]["status"] == "blocked"
    assert current_plan["counts"] == {"pending": 0, "current": 1, "blocked": 1, "unavailable": 0}
    assert current_plan["tasks"][0]["status"] == "current"
    assert forced_plan["tasks"][0]["status"] == "pending"
    assert forced_plan["tasks"][0]["pending_staged_source"] is True
    assert unavailable_plan["counts"] == {"pending": 0, "current": 0, "blocked": 0, "unavailable": 2}
    assert unavailable_plan["tasks"][0]["status"] == "unavailable"


def test_media_readiness_distinguishes_pending_and_missing_metadata() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        repo_root = root / "repo"
        projects_base = root / "projects"
        source_path = projects_base / "works" / "2026/alpha/alpha.jpg"
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_bytes(b"source")

        pending = media.build_media_readiness_item(
            repo_root=repo_root,
            kind="work",
            item_id="00001",
            key="work_media",
            title="work media",
            source_path=source_path,
            missing_reason="",
            projects_base_dir=projects_base,
            availability_error="",
        )
        missing_metadata = media.build_media_readiness_item(
            repo_root=repo_root,
            kind="work",
            item_id="00002",
            key="work_media",
            title="work media",
            source_path=None,
            missing_reason="missing_project_folder",
            projects_base_dir=projects_base,
            availability_error="",
        )

    assert pending["status"] == "pending_generation"
    assert pending["source_path"] == "works/2026/alpha/alpha.jpg"
    assert pending["exists"] is True
    assert missing_metadata["status"] == "missing_metadata"
    assert missing_metadata["exists"] is False


def test_execute_local_media_plan_dry_run_suppresses_writes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source = root / "source.jpg"
        staged_source = root / "var/catalogue/media/works/make_srcset_images/00001.jpg"
        staged_thumb = root / "var/catalogue/media/works/srcset_images/thumb/00001-thumb-96.webp"
        asset_thumb = root / "assets/works/img/00001-thumb-96.webp"
        source.write_bytes(b"source")
        plan = {
            "tasks": [
                {
                    "kind": "work",
                    "id": "00001",
                    "status": "pending",
                    "source_abs_path": str(source),
                    "staged_source_abs_path": str(staged_source),
                    "pending_staged_source": True,
                    "pending_thumb_outputs": [{"size": 96, "absolute_path": str(staged_thumb)}],
                    "pending_primary_outputs": [],
                    "pending_asset_thumbs": [{"absolute_path": str(asset_thumb), "staged_absolute_path": str(staged_thumb)}],
                }
            ],
            "counts": {"pending": 1, "current": 0, "blocked": 0, "unavailable": 0},
        }

        result = media.execute_local_media_plan(root, scope={}, write=False, plan_builder=lambda *args, **kwargs: plan)

    assert result["status"] == "completed"
    assert result["planned"] == {"work": ["00001"], "work_details": [], "moment": []}
    assert not staged_source.exists()
    assert not asset_thumb.exists()


def test_thumbnail_only_plan_skips_missing_sources_without_failing() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        repo_root = root / "repo"
        source_dir = repo_root / "assets/studio/data/catalogue"
        projects_base = root / "projects"
        source_image = projects_base / source_works_root_subdir(media.PIPELINE_CONFIG) / "2026/alpha/alpha.jpg"
        moment_image = projects_base / source_moments_images_subdir(media.PIPELINE_CONFIG) / "keys-source.jpg"
        source_image.parent.mkdir(parents=True, exist_ok=True)
        moment_image.parent.mkdir(parents=True, exist_ok=True)
        source_image.write_bytes(b"source")
        moment_image.write_bytes(b"moment source")
        write_source_fixture(source_dir)

        plan = media.build_catalogue_thumbnail_only_plan(
            repo_root,
            source_dir=source_dir,
            env=projects_env(projects_base),
            force=True,
        )

    assert plan["counts"] == {"pending": 2, "current": 0, "skipped": 3}
    assert plan["tasks"][0]["status"] == "pending"
    assert plan["tasks"][0]["pending_outputs"] == [
        {
            "size": 96,
            "path": "assets/works/img/00001-thumb-96.webp",
            "absolute_path": str((repo_root / "assets/works/img/00001-thumb-96.webp").resolve()),
        }
    ]
    assert plan["tasks"][1]["status"] == "skipped"
    assert plan["tasks"][1]["reason"] == "project folder is missing"
    assert plan["tasks"][2]["status"] == "skipped"
    assert plan["tasks"][2]["kind"] == "work_details"
    assert plan["tasks"][2]["reason"] == "configured source media file is missing"
    assert plan["tasks"][3]["status"] == "pending"
    assert plan["tasks"][3]["kind"] == "moment"
    assert plan["tasks"][3]["pending_outputs"] == [
        {
            "size": 96,
            "path": "assets/moments/img/keys-thumb-96.webp",
            "absolute_path": str((repo_root / "assets/moments/img/keys-thumb-96.webp").resolve()),
        }
    ]
    assert plan["tasks"][4]["status"] == "skipped"
    assert plan["tasks"][4]["kind"] == "moment"


def test_execute_thumbnail_only_plan_writes_thumbnails_and_reports_skips() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        repo_root = root / "repo"
        source_dir = repo_root / "assets/studio/data/catalogue"
        projects_base = root / "projects"
        source_image = projects_base / source_works_root_subdir(media.PIPELINE_CONFIG) / "2026/alpha/alpha.jpg"
        moment_image = projects_base / source_moments_images_subdir(media.PIPELINE_CONFIG) / "keys-source.jpg"
        source_image.parent.mkdir(parents=True, exist_ok=True)
        moment_image.parent.mkdir(parents=True, exist_ok=True)
        source_image.write_bytes(b"source")
        moment_image.write_bytes(b"moment source")
        write_source_fixture(source_dir)

        def fake_thumb(src: Path, size: int, dest: Path) -> tuple[int, str]:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(f"{src.name}:{size}".encode("utf-8"))
            return 0, ""

        result = media.execute_catalogue_thumbnail_only_plan(
            repo_root,
            source_dir=source_dir,
            write=True,
            env=projects_env(projects_base),
            force=True,
            thumb_runner=fake_thumb,
        )
        asset_thumb = repo_root / "assets/works/img/00001-thumb-96.webp"
        moment_thumb = repo_root / "assets/moments/img/keys-thumb-96.webp"
        staged_root = repo_root / "var/catalogue/media"
        asset_thumb_bytes = asset_thumb.read_bytes()
        moment_thumb_bytes = moment_thumb.read_bytes()
        staged_root_exists = staged_root.exists()

    assert result["status"] == "completed"
    assert result["generated"] == {"work": ["00001"], "work_details": [], "moment": ["keys"]}
    assert result["skipped"] == {"work": ["00002"], "work_details": ["00001-001"], "moment": ["missing-moment"]}
    assert "3 skipped" in result["summary"]
    assert asset_thumb_bytes == b"alpha.jpg:96"
    assert moment_thumb_bytes == b"keys-source.jpg:96"
    assert not staged_root_exists


if __name__ == "__main__":
    test_resolves_work_detail_sources_and_missing_metadata_reasons()
    test_local_media_plan_reports_pending_current_blocked_and_unavailable_states()
    test_media_readiness_distinguishes_pending_and_missing_metadata()
    test_execute_local_media_plan_dry_run_suppresses_writes()
    test_thumbnail_only_plan_skips_missing_sources_without_failing()
    test_execute_thumbnail_only_plan_writes_thumbnails_and_reports_skips()
    print("catalogue build media checks passed")
