#!/usr/bin/env python3
"""Focused checks for semantic-reference target lookup generation."""

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
    write_json(
        root / "docs-viewer/config/semantic-references/registry.json",
        {
            "schema_version": "docs_semantic_reference_registry_v1",
            "target_lookup_url": "/docs-viewer/generated/semantic-references/target-lookup.json",
            "kinds": [
                {
                    "kind": "series",
                    "id": {"normalizer": "series_id_or_slug", "input_pattern": "^[a-z0-9][a-z0-9-]*$", "example": "005"},
                    "route": {"type": "query", "path": "/series/", "param": "series"},
                    "source_editor": {"selection_search": True, "picker": True},
                },
                {
                    "kind": "work",
                    "id": {"normalizer": "digits_left_pad", "width": 5, "input_pattern": "^\\d{1,5}$", "canonical_pattern": "^\\d{5}$", "example": "00638"},
                    "route": {"type": "query", "path": "/works/", "param": "work"},
                    "source_editor": {"selection_search": True, "picker": True},
                },
            ],
        },
    )


def write_catalogue(root: Path) -> None:
    base = root / "studio/data/canonical/catalogue"
    write_json(
        base / "series.json",
        {
            "series": {
                "005": {"series_id": "005", "title": "3 symbols", "status": "published", "year_display": "2007"},
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
                },
                "00639": {"work_id": "00639", "title": "Draft work", "status": "draft", "year_display": "2026"},
            }
        },
    )


def test_semantic_target_lookup_builder_writes_compact_published_rows() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        write_registry(root)
        write_catalogue(root)
        result = SemanticTargetLookupBuilder(repo_root=root).run(write=True)
        payload = read_json(root / "docs-viewer/generated/semantic-references/target-lookup.json")

    assert result["diagnostics"]["target_count"] == 2
    assert payload["schema_version"] == "docs_semantic_reference_target_lookup_v1"
    assert [(row["kind"], row["id"]) for row in payload["targets"]] == [("series", "005"), ("work", "00638")]
    assert payload["targets"][0] == {"kind": "series", "id": "005", "title": "3 symbols", "meta": ["2007"]}
    assert payload["targets"][1] == {"kind": "work", "id": "00638", "title": "3 symbols", "meta": ["2007", "3 symbols"]}


def test_semantic_target_lookup_cli_writes_payload() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        write_registry(root)
        write_catalogue(root)
        cwd = Path.cwd()
        stdout = StringIO()
        try:
            os.chdir(root)
            with redirect_stdout(stdout):
                exit_code = main(["--write"])
        finally:
            os.chdir(cwd)

        payload = read_json(root / "docs-viewer/generated/semantic-references/target-lookup.json")

    assert exit_code == 0
    assert "Semantic target lookup (write)" in stdout.getvalue()
    assert len(payload["targets"]) == 2


def main_test() -> None:
    test_semantic_target_lookup_builder_writes_compact_published_rows()
    test_semantic_target_lookup_cli_writes_payload()


if __name__ == "__main__":
    main_test()
