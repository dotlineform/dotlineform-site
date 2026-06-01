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


def search_build_config(*, obsolete_targeted: bool = False) -> dict[str, Any]:
    family_policy: dict[str, Any] = {
        "targeted_policy": "additive_only",
        "targeted_operations": ["create"],
    }
    scope_policy: dict[str, Any] = {
        "targeted_policy": "additive_only",
        "targeted_operations": ["create"],
    }
    if obsolete_targeted:
        family_policy["targeted"] = True
    return {
        "search_build_config_version": "search_build_config_v2",
        "source_families": {
            "catalogue_indexes": {
                "description": "Generated catalogue aggregate indexes for series, works, and moments.",
                "scopes": ["catalogue"],
                **family_policy,
                "id_field": "id",
                "fallback": "full_rebuild",
            },
            "catalogue_work_payloads": {
                "description": "Generated per-work JSON payloads used for work-level search enrichment.",
                "scopes": ["catalogue"],
                "targeted_policy": "additive_only",
                "targeted_operations": ["create"],
                "id_field": "work_id",
                "fallback": "full_rebuild",
            },
        },
        "scopes": {
            "catalogue": {
                "artifact_strategy": "combined",
                **scope_policy,
                "fields": {
                    "kind": {"source_families": ["catalogue_indexes"]},
                    "id": {"source_families": ["catalogue_indexes"]},
                    "title": {"source_families": ["catalogue_indexes"]},
                    "href": {"source_families": ["catalogue_indexes"]},
                    "year": {"source_families": ["catalogue_indexes"]},
                    "date": {"source_families": ["catalogue_indexes"]},
                    "display_meta": {"source_families": ["catalogue_indexes"]},
                    "series_ids": {"source_families": ["catalogue_indexes"]},
                    "series_titles": {"source_families": ["catalogue_indexes"]},
                    "medium_type": {"source_families": ["catalogue_work_payloads"]},
                    "medium_caption": {"source_families": ["catalogue_work_payloads"]},
                    "series_type": {"source_families": ["catalogue_indexes"]},
                    "search_terms": {
                        "source_families": ["catalogue_indexes", "catalogue_work_payloads"],
                        "derived": True,
                    },
                    "search_text": {
                        "source_families": ["catalogue_indexes", "catalogue_work_payloads"],
                        "derived": True,
                    },
                },
            }
        },
    }


def series_index_payload() -> dict[str, Any]:
    return {
        "series": {
            "009": {
                "title": "Field Notes",
                "year": 2024,
                "year_display": "2024",
                "series_type": "sequence",
            }
        }
    }


def works_index_payload() -> dict[str, Any]:
    return {
        "works": {
            "00001": {
                "title": "Blue Field",
                "year": 2025,
                "year_display": "2025",
                "series_ids": ["009"],
            }
        }
    }


def moments_index_payload(*, extra_moment: bool = False, first_title: str = "4 stories") -> dict[str, Any]:
    moments = {
        "4-stories": {
            "title": first_title,
            "date": "2020-01-01",
            "date_display": "c. 2020?",
        }
    }
    if extra_moment:
        moments["blue-sky"] = {
            "title": "Blue Sky",
            "date": "2026-06-01",
            "date_display": "2026",
        }
    return {"moments": moments}


def prepare_repo(root: Path, *, extra_moment: bool = False, first_moment_title: str = "4 stories") -> None:
    write_json(root / "studio/services/catalogue/search/build_config.json", search_build_config())
    write_json(root / "assets/data/series_index.json", series_index_payload())
    write_json(root / "assets/data/works_index.json", works_index_payload())
    write_json(root / "assets/data/moments_index.json", moments_index_payload(extra_moment=extra_moment, first_title=first_moment_title))
    write_json(
        root / "assets/works/index/00001.json",
        {
            "work": {
                "medium_type": "drawing",
                "medium_caption": "Graphite on paper",
            }
        },
    )


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
        payload = read_json(root / "assets/data/search/catalogue/index.json")

    assert exit_code == 0
    assert stderr == ""
    assert "Wrote assets/data/search/catalogue/index.json with 3 catalogue search entries" in stdout
    header = payload["header"]
    entries = payload["entries"]
    assert header["schema"] == "search_index_v1"
    assert header["version"].startswith("blake2b-")
    assert header["count"] == 3
    assert [(entry["kind"], entry["id"]) for entry in entries] == [
        ("moment", "4-stories"),
        ("series", "009"),
        ("work", "00001"),
    ]
    work = entries[2]
    assert work["href"] == "/works/00001/"
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
        assert "Dry run: 3 catalogue search entries" in stdout
        assert "Would write: assets/data/search/catalogue/index.json" in stdout
        assert not (root / "assets/data/search/catalogue/index.json").exists()


def test_python_catalogue_search_builder_skips_unchanged_second_write_and_force_rewrites() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        run_cli(root, ["--scope", "catalogue", "--write"])
        first_payload = read_json(root / "assets/data/search/catalogue/index.json")
        second_exit, second_stdout, second_stderr = run_cli(root, ["--scope", "catalogue", "--write"])
        force_exit, force_stdout, force_stderr = run_cli(root, ["--scope", "catalogue", "--write", "--force"])
        force_payload = read_json(root / "assets/data/search/catalogue/index.json")

    assert second_exit == 0
    assert second_stderr == ""
    assert "Search index JSON done. Wrote: 0. Skipped: 1." in second_stdout
    assert force_exit == 0
    assert force_stderr == ""
    assert "Wrote assets/data/search/catalogue/index.json with 3 catalogue search entries" in force_stdout
    assert force_payload["header"]["version"] == first_payload["header"]["version"]


def test_python_catalogue_search_builder_targeted_additive_insert() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        run_cli(root, ["--scope", "catalogue", "--write"])
        prepare_repo(root, extra_moment=True)

        exit_code, stdout, stderr = run_cli(root, ["--scope", "catalogue", "--write", "--only-records", "moment:blue-sky"])
        payload = read_json(root / "assets/data/search/catalogue/index.json")

    assert exit_code == 0
    assert stderr == ""
    assert "Targeted search index JSON done. Wrote: 1. Skipped: 0. Changed: 1. Removed: 0. Unchanged: 0. Full fallback: 0." in stdout
    assert [(entry["kind"], entry["id"]) for entry in payload["entries"]] == [
        ("moment", "4-stories"),
        ("moment", "blue-sky"),
        ("series", "009"),
        ("work", "00001"),
    ]


def test_python_catalogue_search_builder_targeted_changed_record_requires_full_rebuild() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        run_cli(root, ["--scope", "catalogue", "--write"])
        prepare_repo(root, first_moment_title="4 stories changed")

        try:
            run_cli(root, ["--scope", "catalogue", "--write", "--only-records", "moment:4-stories"])
        except SystemExit as exc:
            error = str(exc)
        else:
            raise AssertionError("targeted changed catalogue record should fail")

    assert "Targeted catalogue search is additive-only" in error
    assert "moment:4-stories" in error


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


def test_python_catalogue_search_builder_validates_search_build_config() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        write_json(root / "studio/services/catalogue/search/build_config.json", search_build_config(obsolete_targeted=True))

        try:
            run_cli(root, ["--scope", "catalogue"])
        except SystemExit as exc:
            error = str(exc)
        else:
            raise AssertionError("obsolete targeted config should fail")

    assert "uses obsolete targeted boolean" in error


def main() -> None:
    test_python_catalogue_search_builder_writes_current_schema_and_hash()
    test_python_catalogue_search_builder_dry_run_does_not_write()
    test_python_catalogue_search_builder_skips_unchanged_second_write_and_force_rewrites()
    test_python_catalogue_search_builder_targeted_additive_insert()
    test_python_catalogue_search_builder_targeted_changed_record_requires_full_rebuild()
    test_python_catalogue_search_builder_rejects_docs_only_flags()
    test_python_catalogue_search_builder_validates_search_build_config()
    print("Python catalogue search builder tests OK")


if __name__ == "__main__":
    main()
