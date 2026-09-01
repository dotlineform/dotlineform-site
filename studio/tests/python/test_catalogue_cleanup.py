#!/usr/bin/env python3
"""Verify catalogue generated-artifact cleanup planning."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

from catalogue_factory import write_json


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = REPO_ROOT / "scripts"
STUDIO_SERVICES_DIR = REPO_ROOT / "studio" / "services"
for path in (SCRIPTS_DIR, STUDIO_SERVICES_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from catalogue import catalogue_cleanup  # noqa: E402
from tags import tag_source_paths  # noqa: E402


TAG_ASSIGNMENTS_PATH = tag_source_paths.TAG_ASSIGNMENTS_REL_PATH


@pytest.fixture(autouse=True)
def external_catalogue_media_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    projects_base = tmp_path / "projects-base"
    projects_base.mkdir()
    monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(projects_base))
    return projects_base / "catalogue/media"


def catalogue_media_root() -> Path:
    return Path(os.environ["DOTLINEFORM_PROJECTS_BASE_DIR"]) / "catalogue/media"


def touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("x", encoding="utf-8")


def rel_paths(root: Path, paths) -> list[str]:
    root = root.resolve()
    return sorted(str(Path(path).resolve().relative_to(root)) for path in paths)


def test_work_delete_cleanup_preview_counts_generated_and_media_paths() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        touch(root / "site/assets/works/index/00001.json")
        touch(root / "site/assets/works/img/00001-thumb-800.jpg")
        touch(root / "site/assets/work_details/img/00001-001-thumb-800.jpg")
        touch(catalogue_media_root() / "works/make_srcset_images/00001.jpg")
        touch(catalogue_media_root() / "works/srcset_images/thumb/00001-thumb-96.webp")
        touch(catalogue_media_root() / "work_details/srcset_images/thumb/00001-001-thumb-800.webp")
        touch(root / "site/assets/data/series_index.json")
        touch(root / "site/assets/data/recent_index.json")
        touch(root / "site/assets/series/index/009.json")
        touch(root / TAG_ASSIGNMENTS_PATH)

        preview = catalogue_cleanup.catalogue_delete_preview_cleanup(
            root,
            "work",
            "00001",
            {"works": ["00001"], "work_details": ["00001-001"], "series": ["009"]},
        )

    assert preview["repo_artifacts"] == 1
    assert preview["repo_media"] == 2
    assert preview["staged_media"] == 3
    assert preview["catalogue_search"] == "site/assets/data/search/catalogue/index.json"
    assert preview["public_json_updates"] == [
        "site/assets/data/series_index.json",
        "site/assets/data/recent_index.json",
        "site/assets/series/index/009.json",
    ]
    assert preview["studio_json_updates"] == [
        TAG_ASSIGNMENTS_PATH.as_posix(),
    ]
    assert "site/assets/works/img/00001-thumb-800.jpg" in preview["delete_paths"]
    assert "$DOTLINEFORM_PROJECTS_BASE_DIR/catalogue/media/works/srcset_images/thumb/00001-thumb-96.webp" in preview["delete_paths"]
    assert "$DOTLINEFORM_PROJECTS_BASE_DIR/catalogue/media/work_details/srcset_images/thumb/00001-001-thumb-800.webp" in preview["delete_paths"]


def test_cleanup_scope_rejects_unallowlisted_delete_path() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        bad_path = root / "site/assets/data/unexpected.json"
        touch(bad_path)
        try:
            catalogue_cleanup.ensure_catalogue_delete_cleanup_scope(root, {"delete_paths": [bad_path]})
        except ValueError as exc:
            assert "outside allowlisted catalogue cleanup roots" in str(exc)
        else:
            raise AssertionError("expected cleanup scope rejection")


def test_stale_public_record_cleanup_keeps_only_published_exact_payloads() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        works_dir = root / "works"
        series_dir = root / "series"
        for work_id in ("00001", "00002", "99999"):
            touch(works_dir / f"{work_id}.json")
        for series_id in ("001", "002", "999"):
            touch(series_dir / f"{series_id}.json")

        stale_paths = [
            *catalogue_cleanup.collect_stale_work_record_artifacts(works_dir, {"00001"}),
            *catalogue_cleanup.collect_stale_series_record_artifacts(series_dir, {"001"}),
        ]
        assert rel_paths(root, stale_paths) == [
            "series/002.json",
            "series/999.json",
            "works/00002.json",
            "works/99999.json",
        ]

        assert catalogue_cleanup.delete_existing_files(stale_paths) == 4
        assert rel_paths(root, [*works_dir.glob("*.json"), *series_dir.glob("*.json")]) == [
            "series/001.json",
            "works/00001.json",
        ]


def test_work_delete_generated_payloads_remove_generated_records() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_json(
            root / "site/assets/data/series_index.json",
            {
                "header": {"schema": "series_index_v3"},
                "series": {
                    "009": {"series_id": "009", "title": "Series", "primary_work_id": "00002"},
                    "010": {"series_id": "010", "title": "Other", "primary_work_id": "00003"},
                },
            },
        )
        write_json(
            root / "site/assets/data/recent_index.json",
            {
                "header": {"schema": "recent_index_v2"},
                "entries": [
                    {"kind": "work", "target_id": "00001", "href": "/works/?from=recent&work=00001"},
                    {"kind": "series", "target_id": "009", "thumb_id": "00001", "caption": "2 works", "href": "/series/?series=009&from=recent"},
                    {"kind": "series", "target_id": "010", "thumb_id": "00003", "caption": "2 works", "href": "/series/?series=010&from=recent"},
                ],
            },
        )
        write_json(
            root / "site/assets/series/index/009.json",
            {
                "header": {"schema": "series_record_v4"},
                "series": {
                    "series_id": "009",
                    "title": "Series",
                    "project_folders": ["deleted-folder", "retained-folder"],
                },
                "member_works": [
                    {"work_id": "00001", "title": "One"},
                    {"work_id": "00002", "title": "Two"},
                ],
            },
        )
        write_json(root / TAG_ASSIGNMENTS_PATH, {"series": {"009": {"works": {"00001": ["tag"], "00002": ["tag"]}}}})

        payloads = catalogue_cleanup.build_catalogue_delete_generated_payloads(
            root,
            "work",
            "00001",
            {"works": ["00001"], "work_details": [], "series": ["009"]},
            series_project_folders_by_id={"009": ["retained-folder"]},
        )

    assert rel_paths(root, payloads.keys()) == [
        "site/assets/data/recent_index.json",
        "site/assets/data/series_index.json",
        "site/assets/series/index/009.json",
        TAG_ASSIGNMENTS_PATH.as_posix(),
    ]
    assert payloads[(root / "site/assets/data/series_index.json").resolve()]["series"]["009"]["single_work_id"] == "00002"
    assert payloads[(root / "site/assets/data/recent_index.json").resolve()]["entries"] == [
        {"kind": "series", "target_id": "010", "thumb_id": "00003", "caption": "2 works", "href": "/series/?series=010&from=recent"},
        {"kind": "series", "target_id": "009", "thumb_id": "00002", "caption": "1 work", "href": "/works/?from=recent&work=00002"},
    ]
    assert payloads[(root / "site/assets/data/recent_index.json").resolve()]["header"]["schema"] == "recent_index_v2"
    assert payloads[(root / "site/assets/series/index/009.json").resolve()]["member_works"] == [
        {"work_id": "00002", "title": "Two"}
    ]
    assert payloads[(root / "site/assets/series/index/009.json").resolve()]["series"]["documents"] == []
    assert payloads[(root / "site/assets/series/index/009.json").resolve()]["series"]["project_folders"] == [
        "retained-folder"
    ]
    assert payloads[(root / "site/assets/series/index/009.json").resolve()]["header"]["schema"] == "series_record_v4"
    assert "00001" not in payloads[(root / TAG_ASSIGNMENTS_PATH).resolve()]["series"]["009"]["works"]


def test_work_detail_generated_payloads_remove_all_affected_details() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        touch(root / "site/assets/work_details/img/00001-001-thumb-800.jpg")
        touch(root / "site/assets/work_details/img/00001-002-thumb-800.jpg")
        touch(catalogue_media_root() / "work_details/srcset_images/thumb/00001-001-thumb-800.webp")
        touch(catalogue_media_root() / "work_details/srcset_images/thumb/00001-002-thumb-800.webp")
        write_json(
            root / "site/assets/works/index/00001.json",
            {
                "header": {"schema": "work_record_v3"},
                "work": {"work_id": "00001"},
                "sections": [
                    {
                        "section_id": "00001-1",
                        "details": [
                            {"detail_uid": "00001-001"},
                            {"detail_uid": "00001-002"},
                            {"detail_uid": "00001-003"},
                        ],
                    }
                ],
            },
        )

        preview = catalogue_cleanup.catalogue_delete_preview_cleanup(
            root,
            "work_detail",
            "00001-1",
            {"works": ["00001"], "work_details": ["00001-001", "00001-002"], "series": []},
        )
        payloads = catalogue_cleanup.build_catalogue_delete_generated_payloads(
            root,
            "work_detail",
            "00001-1",
            {"works": ["00001"], "work_details": ["00001-001", "00001-002"], "series": []},
        )

    assert preview["repo_media"] == 2
    assert preview["staged_media"] == 2
    work_payload = payloads[(root / "site/assets/works/index/00001.json").resolve()]
    assert work_payload["sections"][0]["details"] == [{"detail_uid": "00001-003"}]
    assert work_payload["work"]["documents"] == []
    assert work_payload["header"]["schema"] == "work_record_v5"


def main() -> None:
    test_work_delete_cleanup_preview_counts_generated_and_media_paths()
    test_cleanup_scope_rejects_unallowlisted_delete_path()
    test_stale_public_record_cleanup_keeps_only_published_exact_payloads()
    test_work_delete_generated_payloads_remove_generated_records()
    test_work_detail_generated_payloads_remove_all_affected_details()
    print("Catalogue cleanup tests OK")


if __name__ == "__main__":
    main()
