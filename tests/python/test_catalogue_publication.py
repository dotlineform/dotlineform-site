#!/usr/bin/env python3
"""Verify catalogue publication preview planners."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from catalogue import catalogue_publication  # noqa: E402
from catalogue.catalogue_source import payload_for_map  # noqa: E402
from catalogue.moment_sources import moment_metadata_payload  # noqa: E402


def assert_equal(actual, expected, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(f"{label}: expected truthy value, got {value!r}")


def assert_false(value, label: str) -> None:
    if value:
        raise AssertionError(f"{label}: expected falsey value, got {value!r}")


def assert_raises(message: str, callback) -> None:
    try:
        callback()
    except ValueError as exc:
        assert_equal(str(exc), message, "error message")
        return
    raise AssertionError(f"expected ValueError: {message}")


def write_json(path: Path, payload: dict) -> None:
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
                    "published_date": "2026-01-01",
                    "series_ids": ["009"],
                    "project_folder": "2026/alpha",
                    "project_filename": "alpha.jpg",
                    "title": "Alpha",
                    "year": "2026",
                    "year_display": "2026",
                },
                "00002": {
                    "work_id": "00002",
                    "status": "draft",
                    "series_ids": ["010"],
                    "project_folder": "2026/beta",
                    "project_filename": "beta.jpg",
                    "title": "Beta",
                    "year": "2026",
                    "year_display": "2026",
                },
                "00003": {
                    "work_id": "00003",
                    "status": "draft",
                    "series_ids": [],
                    "project_folder": "2026/gamma",
                    "project_filename": "gamma.jpg",
                    "title": "Gamma",
                    "year": "2026",
                    "year_display": "2026",
                },
            },
        ),
    )
    write_json(
        source_dir / "work_details.json",
        payload_for_map(
            "work_details",
            {
                "00002-001": {
                    "detail_uid": "00002-001",
                    "work_id": "00002",
                    "detail_id": "001",
                    "section_id": "00002-1",
                    "section_title": "Details",
                    "project_filename": "beta-detail.jpg",
                    "title": "Beta detail",
                    "status": "draft",
                }
            },
        ),
    )
    write_json(
        source_dir / "series.json",
        payload_for_map(
            "series",
            {
                "009": {
                    "series_id": "009",
                    "title": "Published series",
                    "status": "published",
                    "published_date": "2026-01-01",
                    "year": "2026",
                    "year_display": "2026",
                    "primary_work_id": "00001",
                },
                "010": {
                    "series_id": "010",
                    "title": "Draft series",
                    "status": "draft",
                    "year": "2026",
                    "year_display": "2026",
                    "primary_work_id": "00002",
                },
            },
        ),
    )
    write_json(
        source_dir / "moments.json",
        moment_metadata_payload(
            {
                "keys": {
                    "moment_id": "keys",
                    "title": "Keys",
                    "status": "draft",
                    "date": "2026-01-01",
                    "date_display": "January 2026",
                    "image_alt": "Keys",
                }
            }
        ),
    )


def test_work_publish_requires_published_series() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source_dir = root / "assets/studio/data/catalogue"
        write_source_fixture(source_dir)

        preview = catalogue_publication.build_publication_preview(
            source_dir,
            root,
            {"kind": "work", "action": "publish", "id": "00003"},
        )

    assert_true(preview["blocked"], "work publish blocked")
    assert_equal(preview["target_status"], "published", "work target status")
    assert_equal(preview["blockers"], ["work 00003 must belong to a published series before publishing"], "work blockers")


def test_series_publish_bootstraps_draft_member_work() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source_dir = root / "assets/studio/data/catalogue"
        write_source_fixture(source_dir)

        preview = catalogue_publication.build_publication_preview(
            source_dir,
            root,
            {"kind": "series", "action": "publish", "id": "010"},
        )

    assert_false(preview["blocked"], "series publish blocked")
    assert_equal(preview["bootstrap_publish_work_ids"], ["00002"], "bootstrap work ids")
    assert_true(preview["source_changed"], "series source changed")
    assert_equal(preview["impact"]["source"]["additional_paths"][0]["changed_record_ids"], ["00002"], "additional paths")


def test_detail_publish_requires_published_parent_work() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source_dir = root / "assets/studio/data/catalogue"
        write_source_fixture(source_dir)

        preview = catalogue_publication.build_publication_preview(
            source_dir,
            root,
            {"kind": "work_detail", "action": "publish", "id": "00002-001"},
        )

    assert_true(preview["blocked"], "detail publish blocked")
    assert_equal(
        preview["blockers"],
        ["parent work 00002 must be published before publishing detail 00002-001"],
        "detail blockers",
    )


def test_unpublish_preview_attaches_cleanup_impact() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source_dir = root / "assets/studio/data/catalogue"
        write_source_fixture(source_dir)

        preview = catalogue_publication.build_publication_preview(
            source_dir,
            root,
            {"kind": "work", "action": "unpublish", "id": "00001"},
        )

    assert_false(preview["blocked"], "work unpublish blocked")
    assert_equal(preview["impact"]["public"]["type"], "public_cleanup", "cleanup impact type")
    assert_equal(preview["impact"]["public"]["cleanup"]["delete_paths"], [], "cleanup delete paths")


def test_save_published_rejects_status_change() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source_dir = root / "assets/studio/data/catalogue"
        write_source_fixture(source_dir)

        assert_raises(
            "save_published must not change publication status",
            lambda: catalogue_publication.build_publication_preview(
                source_dir,
                root,
                {"kind": "work", "action": "save_published", "id": "00001", "record_update": {"status": "draft"}},
            ),
        )


def test_publication_source_payloads_include_series_bootstrap_work_write() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source_dir = root / "assets/studio/data/catalogue"
        write_source_fixture(source_dir)

        preview = catalogue_publication.build_publication_preview(
            source_dir,
            root,
            {"kind": "series", "action": "publish", "id": "010"},
        )
        payloads = catalogue_publication.publication_source_payloads(
            source_dir,
            "series",
            "010",
            preview["target_record"],
            preview,
        )

    assert_equal(sorted(path.name for path in payloads), ["series.json", "works.json"], "source payload files")
    assert_equal(payloads[(source_dir / "series.json").resolve()]["series"]["010"]["status"], "published", "series target status")
    assert_equal(payloads[(source_dir / "works.json").resolve()]["works"]["00002"]["status"], "published", "bootstrap work status")


def test_publication_build_transaction_dry_run_preserves_payload_shape() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source_dir = root / "assets/studio/data/catalogue"
        write_source_fixture(source_dir)
        called = False

        success, payload = catalogue_publication.run_publication_build_transaction(
            repo_root=root,
            source_dir=source_dir,
            backups_dir=root / "var/studio/catalogue/backups",
            dry_run=True,
            kind="work",
            record_id="00001",
            target_record={"work_id": "00001"},
            extra_series_ids=[],
            extra_work_ids=[],
            force=False,
            run_build_operation=lambda **kwargs: (_ for _ in ()).throw(AssertionError("build should not run")),
            rel_path=lambda path: str(path.relative_to(root)),
        )

    assert_false(called, "build operation called")
    assert_true(success, "dry-run build success")
    assert_equal(payload["dry_run"], True, "dry-run flag")
    assert_equal(payload["would_run"], True, "would-run flag")
    assert_equal(payload["kind"], "work", "payload kind")


def main() -> None:
    test_work_publish_requires_published_series()
    test_series_publish_bootstraps_draft_member_work()
    test_detail_publish_requires_published_parent_work()
    test_unpublish_preview_attaches_cleanup_impact()
    test_save_published_rejects_status_change()
    test_publication_source_payloads_include_series_bootstrap_work_write()
    test_publication_build_transaction_dry_run_preserves_payload_shape()
    print("Catalogue publication tests OK")


if __name__ == "__main__":
    main()
