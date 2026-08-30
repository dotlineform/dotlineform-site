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

from repo_factory import (
    docs_scope_record,
    docs_sub_scope_record,
    write_docs_scope_config,
)

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


def tag_family_definition() -> dict[str, object]:
    return {
        "schema_version": "docs_semantic_token_family_definition_v1",
        "key": "tag",
        "labels": {
            "family": "Tag",
            "source_action": "Add tag token",
            "info_view": "Tag token",
        },
        "occurrence_fields": [
            {
                "key": "title",
                "label": "Title",
                "required": True,
                "editable": True,
                "control": "text",
            }
        ],
        "ui_contributions": {
            "source_action": "source-add-tag-token",
            "modal": "tag-token-add-modal",
            "info_view": "tag-token-info",
        },
        "target_types": [
            {
                "key": "tag",
                "label": "Tag",
                "id_policy": {
                    "normalizer": "slug",
                    "input_pattern": "^[a-z0-9][a-z0-9-]*$",
                    "canonical_pattern": "^[a-z0-9][a-z0-9-]*$",
                },
                "lookup_adapter": "tag-target-lookup",
                "lookup_fields": ["title", "href", "meta", "aliases"],
            }
        ],
    }


def write_registry(root: Path, *, include_tag: bool = False) -> None:
    fixture = read_json(REPO_ROOT / "docs-viewer/tests/fixtures/semantic_tokens_catalogue_v1.json")
    families = [fixture["catalogue_definition"]]
    if include_tag:
        families.append(tag_family_definition())
    write_json(
        root / "docs-viewer/config/semantic-tokens/registry.json",
        {
            "schema_version": "docs_semantic_token_registry_v1",
            "target_lookup_url": "/docs-viewer/data/generated/semantic-tokens/target-lookup.json",
            "families": families,
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
                "image_work_details": "/work_details/img",
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
    write_json(
        base / "work_details/00638.json",
        {
            "header": {
                "schema": "catalogue_source_work_detail_record_v1",
                "work_id": "00638",
            },
            "work_id": "00638",
            "detail_sections": [],
        },
    )


def tag_document(
    doc_id: str,
    title: str,
    *,
    public: bool,
) -> dict[str, object]:
    locations: list[dict[str, str]] = [
        {
            "access": "manage",
            "url": f"/docs/?scope=analysis&doc=report&subdoc={doc_id}",
            "title": title,
            "report_title": "",
        }
    ]
    if public:
        locations.append(
            {
                "access": "public",
                "url": f"/analysis/?doc=report&subdoc={doc_id}",
                "title": title,
                "report_title": "Concepts",
            }
        )
    return {
        "target": {
            "scope": "analysis",
            "sub_scope": "tags",
            "doc_id": doc_id,
        },
        "title": title,
        "locations": locations,
    }


def write_tags(root: Path) -> None:
    def target(doc_id: str) -> dict[str, str]:
        return {
            "scope": "analysis",
            "sub_scope": "tags",
            "doc_id": doc_id,
        }

    tag_specs = {
        "sole": [tag_document("d-20260811-120000-100001", "Sole document", public=True)],
        "several-default": [
            tag_document("d-20260811-120000-200001", "Default document", public=True),
            tag_document("d-20260811-120000-200002", "Later document", public=True),
        ],
        "several-selected": [
            tag_document("d-20260811-120000-300001", "First document", public=True),
            tag_document("d-20260811-120000-300002", "Selected document", public=True),
        ],
        "stale-primary": [
            tag_document("d-20260811-120000-400001", "Fallback document", public=True),
            tag_document("d-20260811-120000-400002", "Other document", public=True),
        ],
        "unavailable-first": [
            tag_document("d-20260811-120000-500001", "Unavailable first", public=False),
            tag_document("d-20260811-120000-500002", "Available later", public=True),
        ],
        "unavailable-selected": [
            tag_document("d-20260811-120000-600001", "Available first", public=True),
            tag_document("d-20260811-120000-600002", "Unavailable selected", public=False),
        ],
    }
    write_docs_scope_config(
        root,
        [
            docs_scope_record(
                "analysis",
                scope_type="public",
                viewer_base_url="/analysis/",
                include_scope_param=False,
                default_doc_id="d-20260811-120000-000001",
                sub_scopes=[
                    docs_sub_scope_record(
                        "analysis",
                        "tags",
                        scope_type="public",
                    )
                ],
            )
        ],
    )
    registry_rows: list[dict[str, object]] = [
        {
            "tag_id": "zero",
            "group": "subject",
            "updated_at_utc": "2026-08-11T12:00:00Z",
        },
        {
            "tag_id": "sole",
            "group": "subject",
            "updated_at_utc": "2026-08-11T12:00:00Z",
        },
        {
            "tag_id": "several-default",
            "group": "theme",
            "updated_at_utc": "2026-08-11T12:00:00Z",
        },
        {
            "tag_id": "several-selected",
            "group": "theme",
            "updated_at_utc": "2026-08-11T12:00:00Z",
            "primary_document": target("d-20260811-120000-300002"),
        },
        {
            "tag_id": "stale-primary",
            "group": "form",
            "updated_at_utc": "2026-08-11T12:00:00Z",
            "primary_document": target("d-20260811-120000-499999"),
        },
        {
            "tag_id": "unavailable-first",
            "group": "domain",
            "updated_at_utc": "2026-08-11T12:00:00Z",
        },
        {
            "tag_id": "unavailable-selected",
            "group": "domain",
            "updated_at_utc": "2026-08-11T12:00:00Z",
            "primary_document": target("d-20260811-120000-600002"),
        },
    ]
    write_json(
        root / "studio/data/canonical/tags/tag-registry.json",
        {
            "tag_registry_version": "tag_registry_v6",
            "updated_at_utc": "2026-08-11T12:00:00Z",
            "policy": {"allowed_groups": ["subject", "domain", "form", "theme"]},
            "tags": registry_rows,
        },
    )
    write_json(
        root / "studio/data/canonical/tags/tag-aliases.json",
        {
            "tag_aliases_version": "tag_aliases_v2",
            "updated_at_utc": "2026-08-11T12:00:00Z",
            "aliases": {
                "only-one": {"description": "", "tags": ["sole"]},
                "chosen": {"description": "", "tags": ["several-selected"]},
            },
        },
    )
    write_json(
        root
        / "docs-viewer/scopes/analysis/generated/documents/sub-scopes/tags/tag-associations.json",
        {
            "schema_version": "docs_tag_associations_v1",
            "scope": "analysis",
            "sub_scope": "tags",
            "declaration_generation": "sha256:fixture",
            "associations": [
                {"tag_id": tag_id, "documents": documents}
                for tag_id, documents in sorted(tag_specs.items())
            ],
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
        "has_details": True,
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
        '"has_details":true,'
        '"image":{"src":"https://media.dotlineform.test/works/img/00638-primary-1600.webp?v=2"}},\n'
    ) in output_text
    assert all("details" not in row for row in payload["targets"])
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


def test_tag_lookup_uses_exact_primary_or_first_without_later_document_scan() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        write_registry(root, include_tag=True)
        write_media_config(root)
        write_catalogue(root)
        write_tags(root)
        payload = SemanticTargetLookupBuilder(repo_root=root).payload()

    tag_targets = {
        row["target_id"]: row
        for row in payload["targets"]
        if row["family"] == "tag"
    }
    assert list(tag_targets) == [
        "several-default",
        "several-selected",
        "sole",
        "stale-primary",
    ]
    assert tag_targets["sole"] == {
        "family": "tag",
        "target_type": "tag",
        "target_id": "sole",
        "title": "sole",
        "href": (
            "/analysis/?doc=report&subdoc=d-20260811-120000-100001"
        ),
        "meta": ["subject", "Sole document"],
        "aliases": ["only-one"],
    }
    assert tag_targets["several-default"]["href"].endswith("200001")
    assert tag_targets["several-default"]["meta"] == [
        "theme",
        "Default document",
    ]
    assert tag_targets["several-selected"]["href"].endswith("300002")
    assert tag_targets["several-selected"]["meta"] == [
        "theme",
        "Selected document",
    ]
    assert tag_targets["several-selected"]["aliases"] == ["chosen"]
    assert tag_targets["stale-primary"]["href"].endswith("400001")
    assert "zero" not in tag_targets
    assert "unavailable-first" not in tag_targets
    assert "unavailable-selected" not in tag_targets


def main_test() -> None:
    test_semantic_target_lookup_builder_writes_compact_published_rows()
    test_semantic_target_lookup_cli_writes_payload()
    test_lookup_retains_text_targets_when_exact_image_projection_is_unavailable()
    test_tag_lookup_uses_exact_primary_or_first_without_later_document_scan()


if __name__ == "__main__":
    main_test()
