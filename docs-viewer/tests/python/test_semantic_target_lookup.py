#!/usr/bin/env python3
"""Focused checks for semantic-token target lookup generation."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
BUILD_DIR = REPO_ROOT / "docs-viewer" / "build"
if str(BUILD_DIR) not in sys.path:
    sys.path.insert(0, str(BUILD_DIR))

from docs_builder.semantic_target_lookup import SemanticTargetLookupBuilder, main  # noqa: E402


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_registry(root: Path) -> None:
    fixture = read_json(REPO_ROOT / "docs-viewer/tests/fixtures/semantic_tokens_catalogue_v1.json")
    write_json(
        root / "docs-viewer/config/semantic-tokens/registry.json",
        {
            "schema_version": "docs_semantic_token_registry_v1",
            "target_lookup_url": "/docs-viewer/data/generated/semantic-tokens/target-lookup.json",
            "families": [fixture["catalogue_definition"]],
        },
    )


def write_media_config(root: Path) -> None:
    write_json(
        root / "site-tools/config/site-tools.json",
        {
            "schema_version": "site_tools_config_v1",
            "media": {
                "base": "https://media.dotlineform.test",
                "image_works": "/works/img",
            },
        },
    )
    write_json(
        root / "_data/pipeline.json",
        {
            "variants": {
                "primary": {
                    "widths": [800, 1600],
                    "preferred_width": 1600,
                    "suffix": "primary",
                }
            },
            "encoding": {"format": "webp"},
        },
    )


def write_catalogue(root: Path) -> None:
    base = root / "studio/data/canonical/catalogue"
    write_json(
        base / "series.json",
        {
            "series": {
                "005": {
                    "series_id": "005",
                    "title": "3 symbols",
                    "status": "published",
                    "year_display": "2007",
                    "primary_work_id": "00638",
                },
                "006": {"series_id": "006", "title": "Draft series", "status": "draft", "year_display": "2026"},
            }
        },
    )
    write_json(
        base / "works.json",
        {
            "works": {
                "00638": {
                    "work_id": "00638",
                    "title": "3 symbols",
                    "status": "published",
                    "series_ids": ["005"],
                    "year_display": "2007",
                    "project_filename": "3 symbols.jpg",
                    "media_version": 2,
                    "width_px": 2400,
                    "height_px": 1600,
                },
                "00639": {"work_id": "00639", "title": "Draft work", "status": "draft", "year_display": "2026"},
            }
        },
    )
def test_semantic_target_lookup_builder_writes_compact_published_rows() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        write_registry(root)
        write_media_config(root)
        write_catalogue(root)
        result = SemanticTargetLookupBuilder(repo_root=root).run(write=True)
        output_path = root / "docs-viewer/data/generated/semantic-tokens/target-lookup.json"
        output_text = output_path.read_text(encoding="utf-8")
        payload = read_json(output_path)

    assert result["diagnostics"]["target_count"] == 2
    assert payload["schema_version"] == "docs_semantic_token_target_lookup_v2"
    assert [
        (row["family"], row["target_type"], row["target_id"])
        for row in payload["targets"]
    ] == [
        ("catalogue", "work", "00638"),
        ("catalogue", "series", "005"),
    ]
    assert payload["targets"][0] == {
        "family": "catalogue",
        "target_type": "work",
        "target_id": "00638",
        "title": "3 symbols",
        "href": "/works/?work=00638",
        "meta": ["2007", "3 symbols"],
        "image": {
            "src": "https://media.dotlineform.test/works/img/00638-primary-1600.webp?v=2"
        },
    }
    assert payload["targets"][1] == {
        "family": "catalogue",
        "target_type": "series",
        "target_id": "005",
        "title": "3 symbols",
        "href": "/series/?series=005",
        "meta": ["2007"],
        "image": {
            "src": "https://media.dotlineform.test/works/img/00638-primary-1600.webp?v=2"
        },
    }
    assert output_text.endswith("\n")
    assert (
        '    {"family":"catalogue","target_type":"work","target_id":"00638",'
        '"title":"3 symbols","href":"/works/?work=00638","meta":["2007","3 symbols"],'
        '"image":{"src":"https://media.dotlineform.test/works/img/00638-primary-1600.webp?v=2"}},\n'
    ) in output_text
    assert (
        '    {"family":"catalogue","target_type":"series","target_id":"005",'
        '"title":"3 symbols","href":"/series/?series=005","meta":["2007"],'
        '"image":{"src":"https://media.dotlineform.test/works/img/00638-primary-1600.webp?v=2"}}\n'
    ) in output_text


def test_semantic_target_lookup_cli_writes_payload() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        write_registry(root)
        write_media_config(root)
        write_catalogue(root)
        cwd = Path.cwd()
        stdout = StringIO()
        try:
            os.chdir(root)
            with redirect_stdout(stdout):
                exit_code = main(["--write"])
        finally:
            os.chdir(cwd)

        payload = read_json(root / "docs-viewer/data/generated/semantic-tokens/target-lookup.json")

    assert exit_code == 0
    assert "Semantic target lookup (write)" in stdout.getvalue()
    assert len(payload["targets"]) == 2


def test_lookup_retains_text_targets_when_exact_image_projection_is_unavailable() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        write_registry(root)
        write_media_config(root)
        write_catalogue(root)
        works_path = root / "studio/data/canonical/catalogue/works.json"
        works = read_json(works_path)
        works["works"]["00008"] = {
            "work_id": "00008",
            "title": "No complete media",
            "status": "published",
            "series_ids": ["999"],
            "project_filename": "",
            "media_version": 1,
            "width_px": 100,
            "height_px": 100,
        }
        write_json(works_path, works)
        series_path = root / "studio/data/canonical/catalogue/series.json"
        series = read_json(series_path)
        series["series"]["105"] = {
            "series_id": "105",
            "title": "Exact series destination",
            "status": "published",
            "primary_work_id": "00008",
        }
        write_json(series_path, series)
        payload = SemanticTargetLookupBuilder(repo_root=root).payload()

    targets = {
        (row["target_type"], row["target_id"]): row
        for row in payload["targets"]
    }
    assert "image" not in targets[("work", "00008")]
    assert targets[("work", "00008")]["href"] == "/works/?work=00008"
    assert "image" not in targets[("series", "105")]
    assert targets[("series", "105")]["href"] == "/series/?series=105"


def main_test() -> None:
    test_semantic_target_lookup_builder_writes_compact_published_rows()
    test_semantic_target_lookup_cli_writes_payload()
    test_lookup_retains_text_targets_when_exact_image_projection_is_unavailable()


if __name__ == "__main__":
    main_test()
