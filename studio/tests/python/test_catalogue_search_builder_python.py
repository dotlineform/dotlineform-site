#!/usr/bin/env python3
"""Focused checks for the Python catalogue search builder."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
BUILD_DIR = REPO_ROOT / "studio" / "services" / "catalogue" / "search"
if str(BUILD_DIR) not in sys.path:
    sys.path.insert(0, str(BUILD_DIR))

import build_search  # noqa: E402


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def search_build_config() -> dict[str, Any]:
    family_policy: dict[str, Any] = {
        "targeted_policy": "additive_only",
        "targeted_operations": ["create"],
    }
    scope_policy: dict[str, Any] = {
        "targeted_policy": "additive_only",
        "targeted_operations": ["create"],
    }
    return {
        "search_build_config_version": "search_build_config_v3",
        "source_families": {
            "canonical_catalogue": {
                "description": "Canonical Catalogue Works and Series source records.",
                "scopes": ["catalogue"],
                **family_policy,
                "id_field": "id",
                "fallback": "full_rebuild",
            },
        },
        "scopes": {
            "catalogue": {
                "artifact_strategy": "combined",
                **scope_policy,
                "fields": {
                    "kind": {"source_families": ["canonical_catalogue"]},
                    "id": {"source_families": ["canonical_catalogue"]},
                    "title": {"source_families": ["canonical_catalogue"]},
                    "year": {"source_families": ["canonical_catalogue"]},
                    "display_meta": {"source_families": ["canonical_catalogue"]},
                    "series_ids": {"source_families": ["canonical_catalogue"]},
                    "series_titles": {"source_families": ["canonical_catalogue"]},
                    "medium_type": {"source_families": ["canonical_catalogue"]},
                    "medium_caption": {"source_families": ["canonical_catalogue"]},
                    "series_type": {"source_families": ["canonical_catalogue"]},
                    "search_terms": {
                        "source_families": ["canonical_catalogue"],
                        "derived": True,
                    },
                    "search_text": {
                        "source_families": ["canonical_catalogue"],
                        "derived": True,
                    },
                },
            }
        },
    }


def series_source_payload() -> dict[str, Any]:
    return {
        "catalogue_source_series_version": "catalogue_source_series_v1",
        "series": {
            "009": {
                "series_id": "009",
                "title": "Field Notes",
                "status": "published",
                "year": 2024,
                "year_display": "2024",
                "series_type": "sequence",
                "primary_work_id": "00001",
            },
            "010": {
                "series_id": "010",
                "title": "Draft Series",
                "status": "draft",
                "primary_work_id": "00003",
            },
        }
    }


def works_source_payload(*, extra_work: bool = False, first_title: str = "Blue Field") -> dict[str, Any]:
    works = {
        "00001": {
            "work_id": "00001",
            "status": "published",
            "title": first_title,
            "year": 2025,
            "year_display": "2025",
            "series_ids": ["009"],
            "medium_type": "drawing",
            "medium_caption": "Graphite on paper",
        },
        "00003": {
            "work_id": "00003",
            "status": "draft",
            "title": "Draft Work",
            "series_ids": ["010"],
        }
    }
    if extra_work:
        works["00002"] = {
            "work_id": "00002",
            "status": "published",
            "title": "Blue Sky",
            "year": 2026,
            "year_display": "2026",
            "series_ids": ["009"],
            "medium_type": "painting",
            "medium_caption": "Ink on panel",
        }
    return {"catalogue_source_works_version": "catalogue_source_works_v1", "works": works}


def prepare_repo(root: Path, *, extra_work: bool = False, first_work_title: str = "Blue Field") -> None:
    write_json(root / "studio/services/catalogue/search/build_config.json", search_build_config())
    source_dir = root / "studio/data/canonical/catalogue"
    write_json(source_dir / "series.json", series_source_payload())
    write_json(
        source_dir / "works.json",
        works_source_payload(extra_work=extra_work, first_title=first_work_title),
    )
    (source_dir / "work_details").mkdir(parents=True, exist_ok=True)
    write_json(root / "site/assets/data/series_index.json", {"series": {"wrong": {"title": "Wrong"}}})
    write_json(root / "site/assets/data/works_index.json", {"works": {"99999": {"title": "Wrong"}}})


def run_cli(root: Path, args: list[str]) -> tuple[int, str, str]:
    cwd = Path.cwd()
    stdout = StringIO()
    stderr = StringIO()
    try:
        os.chdir(root)
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = build_search.main(args)
    finally:
        os.chdir(cwd)
    return exit_code, stdout.getvalue(), stderr.getvalue()


def test_python_catalogue_search_builder_writes_current_schema_and_hash() -> None:
    assert build_search.normalize_text(0) == "0"

    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        exit_code, stdout, stderr = run_cli(root, ["--scope", "catalogue", "--write"])
        payload = read_json(root / "site/assets/data/search/catalogue/index.json")

    assert exit_code == 0
    assert stderr == ""
    assert "Wrote site/assets/data/search/catalogue/index.json with 2 catalogue search entries" in stdout
    header = payload["header"]
    entries = payload["entries"]
    assert header["schema"] == "search_index_v1"
    assert header["version"].startswith("blake2b-")
    assert header["count"] == 2
    assert [(entry["kind"], entry["id"]) for entry in entries] == [
        ("series", "009"),
        ("work", "00001"),
    ]
    series = entries[0]
    assert "href" not in series
    work = entries[1]
    assert "href" not in work
    assert work["series_ids"] == ["009"]
    assert work["series_titles"] == ["Field Notes"]
    assert work["medium_type"] == "drawing"
    assert "medium_caption" not in work
    assert work["search_terms"] == [
        "00001",
        "blue field",
        "blue",
        "field",
        "2025",
        "009",
        "field notes",
        "notes",
        "drawing",
        "graphite on paper",
        "graphite",
        "on",
        "paper",
    ]
    assert work["search_text"] == " ".join(work["search_terms"])
    assert header["version"] == "blake2b-" + build_search.blake2b_payload_hash(
        {"schema": header["schema"], "entries": entries}
    )


def test_python_catalogue_search_builder_dry_run_does_not_write() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        exit_code, stdout, stderr = run_cli(root, ["--scope", "catalogue"])

        assert exit_code == 0
        assert stderr == ""
        assert "Dry run: 2 catalogue search entries" in stdout
        assert "Would write: site/assets/data/search/catalogue/index.json" in stdout
        assert not (root / "site/assets/data/search/catalogue/index.json").exists()


def test_python_catalogue_search_builder_skips_unchanged_second_write_and_force_rewrites() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        run_cli(root, ["--scope", "catalogue", "--write"])
        first_payload = read_json(root / "site/assets/data/search/catalogue/index.json")
        second_exit, second_stdout, second_stderr = run_cli(root, ["--scope", "catalogue", "--write"])
        force_exit, force_stdout, force_stderr = run_cli(root, ["--scope", "catalogue", "--write", "--force"])
        force_payload = read_json(root / "site/assets/data/search/catalogue/index.json")

    assert second_exit == 0
    assert second_stderr == ""
    assert "Search index JSON done. Wrote: 0. Skipped: 1." in second_stdout
    assert force_exit == 0
    assert force_stderr == ""
    assert "Wrote site/assets/data/search/catalogue/index.json with 2 catalogue search entries" in force_stdout
    assert force_payload["header"]["version"] == first_payload["header"]["version"]


def test_python_catalogue_search_builder_targeted_additive_insert() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        run_cli(root, ["--scope", "catalogue", "--write"])
        prepare_repo(root, extra_work=True)

        exit_code, stdout, stderr = run_cli(root, ["--scope", "catalogue", "--write", "--only-records", "work:00002"])
        payload = read_json(root / "site/assets/data/search/catalogue/index.json")

    assert exit_code == 0
    assert stderr == ""
    assert "Targeted search index JSON done. Wrote: 1. Skipped: 0. Changed: 1. Removed: 0. Unchanged: 0. Full fallback: 0." in stdout
    assert [(entry["kind"], entry["id"]) for entry in payload["entries"]] == [
        ("series", "009"),
        ("work", "00001"),
        ("work", "00002"),
    ]


def test_python_catalogue_search_builder_targeted_changed_record_requires_full_rebuild() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        run_cli(root, ["--scope", "catalogue", "--write"])
        prepare_repo(root, first_work_title="Blue Field changed")

        try:
            run_cli(root, ["--scope", "catalogue", "--write", "--only-records", "work:00001"])
        except SystemExit as exc:
            error = str(exc)
        else:
            raise AssertionError("targeted changed catalogue record should fail")

    assert "Targeted catalogue search is additive-only" in error
    assert "work:00001" in error


def test_python_catalogue_search_builder_rejects_docs_only_flags() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        for args, expected in (
            (["--scope", "catalogue", "--only-doc-ids", "anything"], "Catalogue search does not support --only-doc-ids"),
            (["--scope", "catalogue", "--source-index", "index.json"], "Catalogue search does not support --source-index"),
            (["--scope", "catalogue", "--remove-missing"], "Catalogue search does not support --remove-missing"),
        ):
            try:
                run_cli(root, args)
            except SystemExit as exc:
                error = str(exc)
            else:
                raise AssertionError(f"{args} should fail")
            assert error == expected


def main() -> None:
    test_python_catalogue_search_builder_writes_current_schema_and_hash()
    test_python_catalogue_search_builder_dry_run_does_not_write()
    test_python_catalogue_search_builder_skips_unchanged_second_write_and_force_rewrites()
    test_python_catalogue_search_builder_targeted_additive_insert()
    test_python_catalogue_search_builder_targeted_changed_record_requires_full_rebuild()
    test_python_catalogue_search_builder_rejects_docs_only_flags()
    print("Python catalogue search builder tests OK")


if __name__ == "__main__":
    main()
