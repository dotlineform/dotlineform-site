#!/usr/bin/env python3
"""Verify scoped catalogue build planning helpers."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from catalogue import catalogue_build_scopes as scopes  # noqa: E402
from catalogue.catalogue_source import payload_for_map  # noqa: E402
from catalogue.moment_sources import moment_metadata_payload  # noqa: E402


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
                    "series_ids": ["009"],
                    "project_folder": "2026/alpha",
                    "project_filename": "alpha.jpg",
                    "title": "Alpha",
                },
                "00002": {
                    "work_id": "00002",
                    "status": "published",
                    "series_ids": ["010"],
                    "project_folder": "2026/beta",
                    "project_filename": "beta.jpg",
                    "title": "Beta",
                },
                "00003": {
                    "work_id": "00003",
                    "status": "draft",
                    "series_ids": ["009"],
                    "title": "Draft",
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
                    "section_id": "00001-1",
                    "section_title": "Details",
                    "project_filename": "alpha-detail.jpg",
                    "title": "Alpha detail",
                    "status": "published",
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
                    "title": "Alpha series",
                    "status": "published",
                    "primary_work_id": "00001",
                },
                "010": {
                    "series_id": "010",
                    "title": "Beta series",
                    "status": "published",
                    "primary_work_id": "00002",
                },
                "011": {
                    "series_id": "011",
                    "title": "Draft series",
                    "status": "draft",
                    "primary_work_id": "00003",
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
                    "status": "published",
                    "published_date": "2026-01-02",
                    "date": "2026-01-01",
                    "date_display": "January 2026",
                    "image_alt": "Keys",
                }
            }
        ),
    )


def readiness_item(key: str) -> dict[str, Any]:
    return {"items": [{"key": key, "status": "ready"}]}


def test_work_scope_includes_extra_series_detail_readiness_and_stable_keys() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        source_dir = Path(tmp) / "assets/studio/data/catalogue"
        write_source_fixture(source_dir)

        scope = scopes.build_scope_for_work(
            source_dir,
            "1",
            extra_series_ids=["10", "010"],
            detail_uid="00001-001",
            work_readiness_builder=lambda records, work_id, **kwargs: readiness_item(f"work:{work_id}"),
            detail_readiness_builder=lambda records, detail_uid, **kwargs: readiness_item(f"detail:{detail_uid}"),
        )

    assert list(scope.keys()) == [
        "work_ids",
        "series_ids",
        "current_series_ids",
        "extra_series_ids",
        "generate_only",
        "rebuild_search",
        "search_scope",
        "source_mode",
        "source_dir",
        "refresh_published",
        "summary",
        "detail_uid",
        "readiness",
    ]
    assert scope["work_ids"] == ["00001"]
    assert scope["series_ids"] == ["009", "010"]
    assert scope["current_series_ids"] == ["009"]
    assert scope["extra_series_ids"] == ["010"]
    assert scope["detail_uid"] == "00001-001"
    assert [item["key"] for item in scope["readiness"]["items"]] == ["work:00001", "detail:00001-001"]
    assert scope["generate_only"] == scopes.DEFAULT_ARTIFACTS


def test_series_scope_includes_extra_work_ids_and_stable_keys() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        source_dir = Path(tmp) / "assets/studio/data/catalogue"
        write_source_fixture(source_dir)

        scope = scopes.build_scope_for_series(
            source_dir,
            "9",
            extra_work_ids=["2", "00002"],
            series_readiness_builder=lambda records, series_id, **kwargs: readiness_item(f"series:{series_id}"),
        )

    assert list(scope.keys()) == [
        "kind",
        "work_ids",
        "series_ids",
        "current_work_ids",
        "extra_work_ids",
        "generate_only",
        "rebuild_search",
        "search_scope",
        "source_mode",
        "source_dir",
        "refresh_published",
        "summary",
        "readiness",
    ]
    assert scope["kind"] == "series"
    assert scope["work_ids"] == ["00001", "00002"]
    assert scope["current_work_ids"] == ["00001"]
    assert scope["extra_work_ids"] == ["00002"]
    assert scope["series_ids"] == ["009"]
    assert scope["readiness"]["items"][0]["key"] == "series:009"


def test_invalid_series_scope_reports_build_preconditions() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        source_dir = Path(tmp) / "assets/studio/data/catalogue"
        write_source_fixture(source_dir)

        try:
            scopes.build_scope_for_series(
                source_dir,
                "011",
                series_readiness_builder=lambda records, series_id, **kwargs: readiness_item("unused"),
            )
        except ValueError as exc:
            assert str(exc) == "series 011: status must be published for runtime build"
        else:
            raise AssertionError("expected draft series failure")

        payload = json.loads((source_dir / "series.json").read_text(encoding="utf-8"))
        payload["series"]["009"]["primary_work_id"] = "00002"
        write_json(source_dir / "series.json", payload)
        try:
            scopes.build_scope_for_work(
                source_dir,
                "00001",
                work_readiness_builder=lambda records, work_id, **kwargs: readiness_item("unused"),
            )
        except ValueError as exc:
            assert "series 009: primary_work_id '00002' is not in that work's series_ids" in str(exc)
        else:
            raise AssertionError("expected invalid primary-work failure")


def test_moment_scope_uses_preview_metadata_and_readiness_dependencies() -> None:
    repo_root = Path("/tmp/catalogue-build-scope-test")

    def preview(repo_root_arg: Path, moment_file: str, **kwargs: Any) -> dict[str, Any]:
        assert repo_root_arg == repo_root
        assert moment_file == "keys.md"
        return {"valid": True, "moment_id": "keys", "moment_file": "keys.md", "title": "Keys"}

    def metadata(source_dir: Path, moment_id: str, incoming: dict[str, Any] | None) -> dict[str, Any]:
        assert source_dir == repo_root / "assets/studio/data/catalogue"
        assert moment_id == "keys"
        return {"moment_id": "keys", "title": incoming["title"] if incoming else "Keys"}

    scope = scopes.build_scope_for_moment(
        repo_root,
        "keys.md",
        metadata={"title": "Updated Keys"},
        force=True,
        moment_preview_builder=preview,
        moment_metadata_builder=metadata,
        moment_readiness_builder=lambda root, moment_file, **kwargs: readiness_item(f"moment:{moment_file}"),
    )

    assert scope == {
        "kind": "moment",
        "moment_ids": ["keys"],
        "moment_file": "keys.md",
        "moment_metadata": {"moment_id": "keys", "title": "Updated Keys"},
        "work_ids": [],
        "series_ids": [],
        "generate_only": ["moments"],
        "rebuild_search": True,
        "search_scope": "catalogue",
        "source_mode": "moment-source",
        "summary": "Build moments [keys], rebuild the moments index, and rebuild catalogue search.",
        "effective_force": True,
        "refresh_published": True,
        "preview": {"valid": True, "moment_id": "keys", "moment_file": "keys.md", "title": "Keys"},
        "readiness": {"items": [{"key": "moment:keys.md", "status": "ready"}]},
    }


def test_moment_import_metadata_merges_existing_record_and_overrides() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        source_dir = Path(tmp) / "assets/studio/data/catalogue"
        write_source_fixture(source_dir)

        metadata = scopes.build_moment_import_metadata(source_dir, "keys", {"title": "Updated Keys"})

    assert metadata["moment_id"] == "keys"
    assert metadata["title"] == "Updated Keys"
    assert metadata["status"] == "published"
    assert metadata["published_date"] == "2026-01-02"


def main() -> None:
    test_work_scope_includes_extra_series_detail_readiness_and_stable_keys()
    test_series_scope_includes_extra_work_ids_and_stable_keys()
    test_invalid_series_scope_reports_build_preconditions()
    test_moment_scope_uses_preview_metadata_and_readiness_dependencies()
    test_moment_import_metadata_merges_existing_record_and_overrides()
    print("Catalogue build scope tests OK")


if __name__ == "__main__":
    main()
