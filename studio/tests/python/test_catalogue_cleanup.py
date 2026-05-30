#!/usr/bin/env python3
"""Verify catalogue generated-artifact cleanup planning."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = REPO_ROOT / "scripts"
ANALYTICS_PACKAGE_DIR = REPO_ROOT / "analytics-app" / "app" / "server" / "analytics_app"
for path in (SCRIPTS_DIR, ANALYTICS_PACKAGE_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from catalogue import catalogue_cleanup  # noqa: E402
from tag_services import tag_source_paths  # noqa: E402


TAG_ASSIGNMENTS_PATH = tag_source_paths.TAG_ASSIGNMENTS_REL_PATH


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("x", encoding="utf-8")


def rel_paths(root: Path, paths) -> list[str]:
    root = root.resolve()
    return sorted(str(Path(path).resolve().relative_to(root)) for path in paths)


def test_work_delete_cleanup_preview_counts_generated_and_media_paths() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        touch(root / "_works/00001.md")
        touch(root / "_work_details/00001-001.md")
        touch(root / "assets/works/index/00001.json")
        touch(root / "assets/works/img/00001-thumb-800.jpg")
        touch(root / "assets/work_details/img/00001-001-thumb-800.jpg")
        touch(root / "var/catalogue/media/works/make_srcset_images/00001.jpg")
        touch(root / "var/catalogue/media/work_details/srcset_images/thumb/00001-001-thumb-800.webp")
        touch(root / "assets/data/works_index.json")
        touch(root / "assets/data/series_index.json")
        touch(root / "assets/data/recent_index.json")
        touch(root / "assets/series/index/009.json")
        touch(root / "studio/data/generated/activity/work-storage-index.json")
        touch(root / TAG_ASSIGNMENTS_PATH)

        preview = catalogue_cleanup.catalogue_delete_preview_cleanup(
            root,
            "work",
            "00001",
            {"works": ["00001"], "work_details": ["00001-001"], "series": ["009"]},
        )

    assert preview["repo_artifacts"] == 3
    assert preview["repo_media"] == 2
    assert preview["staged_media"] == 2
    assert preview["catalogue_search"] == "assets/data/search/catalogue/index.json"
    assert preview["public_json_updates"] == [
        "assets/data/works_index.json",
        "assets/data/series_index.json",
        "assets/data/recent_index.json",
        "assets/series/index/009.json",
    ]
    assert preview["studio_json_updates"] == [
        "studio/data/generated/activity/work-storage-index.json",
        TAG_ASSIGNMENTS_PATH.as_posix(),
    ]
    assert "assets/works/img/00001-thumb-800.jpg" in preview["delete_paths"]
    assert "var/catalogue/media/work_details/srcset_images/thumb/00001-001-thumb-800.webp" in preview["delete_paths"]


def test_cleanup_scope_rejects_unallowlisted_delete_path() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        bad_path = root / "assets/data/works_index.json"
        touch(bad_path)
        try:
            catalogue_cleanup.ensure_catalogue_delete_cleanup_scope(root, {"delete_paths": [bad_path]})
        except ValueError as exc:
            assert "outside allowlisted catalogue cleanup roots" in str(exc)
        else:
            raise AssertionError("expected cleanup scope rejection")


def test_work_delete_generated_payloads_remove_generated_records() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_json(root / "assets/data/works_index.json", {"header": {"schema": "works_index_v4"}, "works": {"00001": {}, "00002": {}}})
        write_json(root / "studio/data/generated/activity/work-storage-index.json", {"header": {"schema": "work_storage_index_v1"}, "works": {"00001": {}, "00002": {}}})
        write_json(
            root / "assets/data/series_index.json",
            {"header": {"schema": "series_index_v2"}, "series": {"009": {"works": ["00001", "00002"], "primary_work_id": "00001"}}},
        )
        write_json(
            root / "assets/data/recent_index.json",
            {
                "header": {"schema": "recent_index_v1"},
                "entries": [
                    {"kind": "work", "target_id": "00001"},
                    {"kind": "series", "target_id": "009", "thumb_id": "00001", "caption": "2 works"},
                ],
            },
        )
        write_json(
            root / "assets/series/index/009.json",
            {"header": {"schema": "series_record_v1"}, "series": {"works": ["00001", "00002"], "primary_work_id": "00001"}},
        )
        write_json(root / TAG_ASSIGNMENTS_PATH, {"series": {"009": {"works": {"00001": ["tag"], "00002": ["tag"]}}}})

        payloads = catalogue_cleanup.build_catalogue_delete_generated_payloads(
            root,
            "work",
            "00001",
            {"works": ["00001"], "work_details": [], "series": ["009"]},
        )

    assert rel_paths(root, payloads.keys()) == [
        TAG_ASSIGNMENTS_PATH.as_posix(),
        "assets/data/recent_index.json",
        "assets/data/series_index.json",
        "assets/data/works_index.json",
        "assets/series/index/009.json",
        "studio/data/generated/activity/work-storage-index.json",
    ]
    assert "00001" not in payloads[(root / "assets/data/works_index.json").resolve()]["works"]
    assert payloads[(root / "assets/data/series_index.json").resolve()]["series"]["009"]["works"] == ["00002"]
    assert payloads[(root / "assets/data/recent_index.json").resolve()]["entries"] == [
        {"kind": "series", "target_id": "009", "thumb_id": "00001", "caption": "1 work"}
    ]
    assert "works" not in payloads[(root / "assets/series/index/009.json").resolve()]["series"]
    assert "primary_work_id" not in payloads[(root / "assets/series/index/009.json").resolve()]["series"]
    assert "00001" not in payloads[(root / TAG_ASSIGNMENTS_PATH).resolve()]["series"]["009"]["works"]


def test_moment_delete_generated_payloads_remove_moment_index_record() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_json(
            root / "assets/data/moments_index.json",
            {
                "header": {"schema": "moments_index_v1"},
                "moments": {
                    "keys": {"title": "Keys"},
                    "clouds": {"title": "Clouds"},
                },
            },
        )

        payloads = catalogue_cleanup.build_moment_delete_generated_payloads(root, "keys")

    assert rel_paths(root, payloads.keys()) == ["assets/data/moments_index.json"]
    moments_payload = payloads[(root / "assets/data/moments_index.json").resolve()]
    assert "keys" not in moments_payload["moments"]
    assert moments_payload["moments"] == {"clouds": {"title": "Clouds"}}
    assert moments_payload["header"]["count"] == 1
    assert moments_payload["header"]["schema"] == "moments_index_v1"


def main() -> None:
    test_work_delete_cleanup_preview_counts_generated_and_media_paths()
    test_cleanup_scope_rejects_unallowlisted_delete_path()
    test_work_delete_generated_payloads_remove_generated_records()
    test_moment_delete_generated_payloads_remove_moment_index_record()
    print("Catalogue cleanup tests OK")


if __name__ == "__main__":
    main()
