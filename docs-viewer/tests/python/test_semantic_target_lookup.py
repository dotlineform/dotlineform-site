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

from repo_factory import docs_scope_record


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
            "target_lookup_url": "/docs-viewer/published/semantic-references/target-lookup.json",
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
                {
                    "kind": "moment",
                    "id": {"normalizer": "slug", "input_pattern": "^[a-z0-9][a-z0-9-]*$", "example": "lotus-pond"},
                    "route": {"type": "query", "path": "/moments/", "param": "doc"},
                    "source_editor": {"selection_search": True, "picker": True},
                },
            ],
        },
    )


def write_catalogue(root: Path) -> None:
    write_json(
        root / "docs-viewer/config/scopes/docs_scopes.json",
        {
            "schema_version": "docs_scopes_v2",
            "scopes": [
                docs_scope_record(
                    "moments",
                    scope_type="public",
                    viewer_base_url="/moments/",
                    include_scope_param=False,
                    default_doc_id="moments",
                )
            ],
        },
    )
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
    write_json(
        root / "docs-viewer/published/docs/moments/index-tree.json",
        {
            "schema": "docs_index_tree_v1",
            "viewer_options": {"non_loadable_doc_ids": ["moments"]},
            "docs": [
                {"doc_id": "lotus-pond", "title": "lotus pond", "content_url": "/assets/data/docs/scopes/moments/by-id/lotus-pond.json"},
                {"doc_id": "moments", "title": "Moments", "content_url": "/assets/data/docs/scopes/moments/by-id/moments.json"},
            ],
        },
    )
    write_json(
        root / "docs-viewer/published/docs/moments/by-id/lotus-pond.json",
        {"title": "lotus pond", "date": "2024-10-23", "date_display": "c. 2024"},
    )


def test_semantic_target_lookup_builder_writes_compact_published_rows() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        write_registry(root)
        write_catalogue(root)
        result = SemanticTargetLookupBuilder(repo_root=root).run(write=True)
        output_path = root / "docs-viewer/published/semantic-references/target-lookup.json"
        output_text = output_path.read_text(encoding="utf-8")
        payload = read_json(output_path)

    assert result["diagnostics"]["target_count"] == 3
    assert payload["schema_version"] == "docs_semantic_reference_target_lookup_v1"
    assert [(row["kind"], row["id"]) for row in payload["targets"]] == [("series", "005"), ("work", "00638"), ("moment", "lotus-pond")]
    assert payload["targets"][0] == {"kind": "series", "id": "005", "title": "3 symbols", "meta": ["2007"]}
    assert payload["targets"][1] == {"kind": "work", "id": "00638", "title": "3 symbols", "meta": ["2007", "3 symbols"]}
    assert payload["targets"][2] == {"kind": "moment", "id": "lotus-pond", "title": "lotus pond", "meta": ["c. 2024"]}
    assert output_text.endswith("\n")
    assert '    {"kind":"series","id":"005","title":"3 symbols","meta":["2007"]},\n' in output_text
    assert '    {"kind":"work","id":"00638","title":"3 symbols","meta":["2007","3 symbols"]},\n' in output_text
    assert '    {"kind":"moment","id":"lotus-pond","title":"lotus pond","meta":["c. 2024"]}\n' in output_text


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

        payload = read_json(root / "docs-viewer/published/semantic-references/target-lookup.json")

    assert exit_code == 0
    assert "Semantic target lookup (write)" in stdout.getvalue()
    assert len(payload["targets"]) == 3


def main_test() -> None:
    test_semantic_target_lookup_builder_writes_compact_published_rows()
    test_semantic_target_lookup_cli_writes_payload()


if __name__ == "__main__":
    main_test()
