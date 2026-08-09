"""Production parser, registry, projection, and usage checks for Catalogue tokens."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any

from repo_factory import docs_scope_record, write_docs_scope_config, write_json, write_text


REPO_ROOT = Path(__file__).resolve().parents[3]
BUILD_DIR = REPO_ROOT / "docs-viewer" / "build"
SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
for path in (BUILD_DIR, SERVICES_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from docs_builder.pipeline import DocsDataBuilder  # noqa: E402
from docs_builder.semantic_token_registry import (  # noqa: E402
    load_semantic_token_registry,
    parse_semantic_token_registry,
)
from docs_builder.semantic_tokens import (  # noqa: E402
    parse_catalogue_tokens,
    resolve_catalogue_image_target,
    semantic_token_at_selection,
    serialize_catalogue_image_token,
    serialize_semantic_token,
)
from docs_scope_config import load_docs_scope_configs  # noqa: E402


FIXTURE_PATH = REPO_ROOT / "docs-viewer/tests/fixtures/semantic_tokens_catalogue_v1.json"


def load_fixture() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def fixture_registry_payload() -> dict[str, Any]:
    return {
        "schema_version": "docs_semantic_token_registry_v1",
        "target_lookup_url": "/docs-viewer/data/generated/semantic-tokens/target-lookup.json",
        "families": [load_fixture()["catalogue_definition"]],
    }


def test_registry_and_python_parser_match_the_frozen_fixture() -> None:
    fixture = load_fixture()
    registry = parse_semantic_token_registry(fixture_registry_payload())
    assert registry is not None

    for case in fixture["cases"]:
        tokens = parse_catalogue_tokens(case["source"], registry=registry)
        assert len(tokens) == len(case["tokens"]), case["id"]
        for actual, expected in zip(tokens, case["tokens"], strict=True):
            assert actual.raw == expected["raw"], case["id"]
            assert actual.source_range == expected["source_range"], case["id"]
            assert actual.family == expected["family"], case["id"]
            assert actual.target_type == expected["target_type"], case["id"]
            assert actual.target_id == expected["target_id"], case["id"]
            assert actual.title == expected["title"], case["id"]
            assert actual.supported is expected["supported"], case["id"]
            if actual.supported:
                assert serialize_semantic_token(
                    family=actual.family,
                    target_type=actual.target_type,
                    target_id=actual.target_id,
                    title=expected.get("input_title", actual.title),
                ) == expected["serialized"], case["id"]
        for expectation in case.get("caret_expectations", []):
            active = semantic_token_at_selection(
                tokens,
                start=expectation["offset"],
                end=expectation["offset"],
            )
            expected_index = expectation["active_token_index"]
            assert active is (tokens[expected_index] if expected_index is not None else None), case["id"]


def test_production_registry_is_the_accepted_catalogue_definition() -> None:
    payload = json.loads(
        (
            REPO_ROOT / "docs-viewer/config/semantic-tokens/registry.json"
        ).read_text(encoding="utf-8")
    )
    assert payload == fixture_registry_payload()
    assert load_semantic_token_registry(REPO_ROOT) is not None


def test_visual_occurrence_parser_is_canonical_and_context_aware() -> None:
    registry = parse_semantic_token_registry(fixture_registry_payload())
    assert registry is not None
    plain = "[[catalogue:image:work:00638|alt=3%20symbols]]"
    detail = "[[catalogue:image:work:00638|alt=3%20symbols%20detail&detail_id=001]]"
    figure = (
        "[[catalogue:image:series:105|alt=nerve&caption=nerve&"
        "summary=intangible%0Ashifting%20boundaries&placement=left&fill_width=true]]"
    )
    source = f"{plain}\n{detail}\n{figure}\n`{plain}`\n<!-- {figure} -->\n"
    tokens = parse_catalogue_tokens(source, registry=registry)

    assert len(tokens) == 3
    assert tokens[0].presentation == "image"
    assert tokens[0].title == tokens[0].alt == "3 symbols"
    assert tokens[0].caption == ""
    assert tokens[0].fill_width is None
    assert tokens[1].detail_id == "001"
    assert tokens[1].target_type == "work"
    assert tokens[2].title == tokens[2].caption == "nerve"
    assert tokens[2].summary == "intangible\nshifting boundaries"
    assert tokens[2].placement == "left"
    assert tokens[2].fill_width is True
    assert source[tokens[2].start:tokens[2].end] == figure
    assert serialize_catalogue_image_token(
        target_type="work",
        target_id="00638",
        alt="3 symbols detail",
        detail_id="1",
    ) == detail
    assert serialize_catalogue_image_token(
        target_type="series",
        target_id="105",
        alt="nerve",
        caption="nerve",
        summary="intangible\nshifting boundaries",
        placement="left",
        fill_width=True,
    ) == figure

    malformed = [
        "[[catalogue:image:work:00638|caption=3%20symbols&alt=3%20symbols&placement=left&fill_width=true]]",
        "[[catalogue:image:work:00638|alt=3%20symbols&alt=again]]",
        "[[catalogue:image:work:00638|alt=3%20symbols&unknown=value]]",
        "[[catalogue:image:work:00638|alt=3%20symbols&summary=extra]]",
        "[[catalogue:image:work:00638|alt=3%20symbols&caption=caption&placement=left]]",
        "[[catalogue:image:work:00638|alt=3%20symbols&caption=caption&placement=left&fill_width=1]]",
        "[[catalogue:image:work:00638|alt=3%20symbols&caption=caption&placement=LEFT&fill_width=true]]",
        "[[catalogue:image:work:00638|alt=3%20symbols%2fdetail]]",
        "[[catalogue:image:work:00638|alt=3%20symbols&detail_id=1]]",
        "[[catalogue:image:work:00638|alt=3%20symbols&detail_id=000]]",
        "[[catalogue:image:series:105|alt=nerve&detail_id=001]]",
        "[[catalogue:image:work:00638|alt=3%20symbols&caption=caption&detail_id=001&placement=left&fill_width=true]]",
    ]
    for raw in malformed:
        assert parse_catalogue_tokens(raw, registry=registry) == [], raw


def write_builder_fixture(root: Path) -> tuple[str, str]:
    resolved_case = next(
        case for case in load_fixture()["cases"] if case["id"] == "resolved_work_00638"
    )
    broken_case = next(
        case for case in load_fixture()["cases"] if case["id"] == "broken_missing_work"
    )
    scope_record = docs_scope_record(
        "analysis",
        default_doc_id=resolved_case["source_doc_id"],
    )
    write_docs_scope_config(root, [scope_record])
    write_json(
        root / "site-tools/config/site-tools.json",
        {
            "schema_version": "site_tools_config_v1",
            "media": {
                "base": "https://media.dotlineform.com",
                "image_work_details": "/work_details/img",
            },
        },
        indent=2,
    )
    write_json(
        root / "_data/pipeline.json",
        {
            "variants": {
                "primary": {
                    "preferred_width": 1600,
                    "suffix": "primary",
                },
            },
            "encoding": {"format": "webp"},
        },
        indent=2,
    )
    write_json(
        root / "docs-viewer/config/routes/docs-viewer-routes.json",
        {
            "schema_version": "docs_viewer_routes_v1",
            "routes": [
                {
                    "route_id": "docs-manage",
                    "app_kind": "manage",
                    "default_scope_id": "analysis",
                    "features": ["recent"],
                    "recent_basis": "edited",
                }
            ],
        },
    )
    write_json(
        root / "docs-viewer/config/semantic-tokens/registry.json",
        fixture_registry_payload(),
    )
    target_lookup = load_fixture()["target_lookup_example"]
    target_lookup["targets"][0]["has_details"] = True
    target_lookup["targets"].append(
        {
            "family": "catalogue",
            "target_type": "work",
            "target_id": "99999",
            "title": "missing work",
            "href": "",
            "meta": [],
        }
    )
    target_lookup["targets"].append(
        {
            "family": "catalogue",
            "target_type": "series",
            "target_id": "005",
            "title": "3 symbols",
            "href": "/series/?series=005",
            "meta": ["2007"],
            "image": {
                "src": "https://media.dotlineform.com/works/img/00638-primary-1600.webp?v=1"
            },
        }
    )
    write_json(
        root / "docs-viewer/data/generated/semantic-tokens/target-lookup.json",
        target_lookup,
    )
    write_json(
        root / "studio/data/canonical/catalogue/work_details/00638.json",
        {
            "header": {
                "schema": "catalogue_source_work_detail_record_v1",
                "work_id": "00638",
            },
            "work_id": "00638",
            "detail_sections": [
                {
                    "section_id": "00638-1",
                    "details": [
                        {
                            "detail_uid": "00638-001",
                            "detail_id": "001",
                            "project_filename": "3 symbols detail.jpg",
                            "media_version": 3,
                            "title": "3 symbols detail",
                            "width_px": 2400,
                            "height_px": 1600,
                        },
                    ],
                },
            ],
        },
    )
    write_text(
        root / f"docs-viewer/scopes/analysis/source/documents/{resolved_case['source_doc_id']}.md",
        (
            "---\n"
            f"doc_id: {resolved_case['source_doc_id']}\n"
            "title: Resolved fixture\n"
            "added_date: 2026-07-26\n"
            "last_updated: 2026-07-26 12:00:00\n"
            'parent_id: ""\n'
            "---\n"
            f"{resolved_case['source']}"
        ),
    )
    write_text(
        root / f"docs-viewer/scopes/analysis/source/documents/{broken_case['source_doc_id']}.md",
        (
            "---\n"
            f"doc_id: {broken_case['source_doc_id']}\n"
            "title: Broken fixture\n"
            "added_date: 2026-07-26\n"
            "last_updated: 2026-07-26 12:00:00\n"
            'parent_id: ""\n'
            "---\n"
            f"{broken_case['source']}"
        ),
    )
    return resolved_case["source_doc_id"], broken_case["source_doc_id"]


def test_builder_projects_only_resolved_lookup_rows_and_writes_usage() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        resolved_doc_id, broken_doc_id = write_builder_fixture(root)
        registry = load_semantic_token_registry(root)
        assert registry is not None
        builder = DocsDataBuilder(
            repo_root=root,
            config=load_docs_scope_configs(root)["analysis"],
            skip_media_builds=True,
        )
        result = builder.run(write=True)
        resolved_payload = json.loads(
            (
                root
                / f"docs-viewer/scopes/analysis/published/documents/by-id/{resolved_doc_id}.json"
            ).read_text(encoding="utf-8")
        )
        broken_payload = json.loads(
            (
                root
                / f"docs-viewer/scopes/analysis/published/documents/by-id/{broken_doc_id}.json"
            ).read_text(encoding="utf-8")
        )
        usage_index = json.loads(
            (
                root
                / "docs-viewer/scopes/analysis/published/documents/semantic-tokens/index.json"
            ).read_text(encoding="utf-8")
        )
        semantic_tokens_dir = (
            root / "docs-viewer/scopes/analysis/published/documents/semantic-tokens"
        )
        by_document_exists = (semantic_tokens_dir / "by-document").exists()
        by_target_exists = (semantic_tokens_dir / "by-target").exists()

    assert '<a href="/works/?work=00638"' in resolved_payload["content_html"]
    assert "[[catalogue:work:99999|missing work]]" in broken_payload["content_html"]
    assert result["diagnostics"]["warning_count"] == 0
    assert usage_index == load_fixture()["usage_index_example"]
    assert not by_document_exists
    assert not by_target_exists


def test_builder_projects_linked_visual_occurrences_and_preserves_missing_images() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        write_builder_fixture(root)
        doc_id = "d-20260809-120000-a1b2c3"
        plain = "[[catalogue:image:work:00638|alt=3%20symbols]]"
        detail = "[[catalogue:image:work:00638|alt=3%20symbols%20detail&detail_id=001]]"
        figure = (
            "[[catalogue:image:series:005|alt=3%20symbols&caption=Quiet%20field&"
            "summary=Supporting%20copy&placement=right&fill_width=false]]"
        )
        missing_image = "[[catalogue:image:work:00008|alt=nerve]]"
        missing_detail = "[[catalogue:image:work:00638|alt=missing%20detail&detail_id=999]]"
        text_same_target = "[[catalogue:work:00008|nerve]]"
        write_text(
            root / f"docs-viewer/scopes/analysis/source/documents/{doc_id}.md",
            (
                "---\n"
                f"doc_id: {doc_id}\n"
                "title: Visual fixture\n"
                "added_date: 2026-08-09\n"
                "last_updated: 2026-08-09 12:00:00\n"
                'parent_id: ""\n'
                "---\n"
                f"{plain}\n\n{detail}\n\n{figure}\n\n{missing_detail}\n\n{missing_image}\n\n{text_same_target}\n"
            ),
        )
        builder = DocsDataBuilder(
            repo_root=root,
            config=load_docs_scope_configs(root)["analysis"],
            skip_media_builds=True,
        )
        builder.run(write=True)
        payload = json.loads(
            (
                root
                / f"docs-viewer/scopes/analysis/published/documents/by-id/{doc_id}.json"
            ).read_text(encoding="utf-8")
        )
        usage = json.loads(
            (
                root
                / "docs-viewer/scopes/analysis/published/documents/semantic-tokens/index.json"
            ).read_text(encoding="utf-8")
        )

    html = payload["content_html"]
    assert '<a class="docsViewerCatalogueImageLink" href="/works/?work=00638"' in html
    assert 'src="https://media.dotlineform.com/works/img/00638-primary-1600.webp?v=1"' in html
    assert '<a class="docsViewerCatalogueImageLink" href="/work-details/?detail=00638-001&amp;from_work=00638"' in html
    assert 'src="https://media.dotlineform.com/work_details/img/00638-001-primary-1600.webp?v=3"' in html
    assert 'data-semantic-token-target-id="00638"' in html
    assert 'target="_blank" rel="noopener noreferrer"' in html
    assert '<figure class="docsViewerFigure docsViewerFigure--image-right docsViewerFigure--natural-width">' in html
    assert '<a class="docsViewerFigure__imageLink" href="/series/?series=005"' in html
    assert 'data-semantic-token-target-type="series"' in html
    assert 'data-semantic-token-target-id="005"' in html
    assert '<span class="docsViewerFigure__caption">Quiet field</span>' in html
    assert '<span class="docsViewerFigure__summary">Supporting copy</span>' in html
    assert missing_image in html
    assert missing_detail.replace("&", "&amp;") in html
    assert '<a href="/works/?work=00008" data-semantic-token-family="catalogue"' in html
    resolved_rows = [row for row in usage["occurrences"] if row["source_doc_id"] == doc_id]
    assert usage["schema_version"] == "docs_semantic_token_usage_index_v1"
    assert [row["title"] for row in resolved_rows] == ["3 symbols", "3 symbols detail", "Quiet field", "nerve"]
    assert resolved_rows[1]["target_type"] == "work"
    assert resolved_rows[1]["target_id"] == "00638"
    assert resolved_rows[1]["href"] == "/work-details/?detail=00638-001&from_work=00638"
    assert resolved_rows[2]["target_type"] == "series"
    assert resolved_rows[2]["target_id"] == "005"
    assert resolved_rows[2]["href"] == "/series/?series=005"
    assert resolved_rows[3]["raw"] == text_same_target
    assert not any(row["raw"] == missing_image for row in resolved_rows)
    assert not any(row["raw"] == missing_detail for row in resolved_rows)


def test_work_detail_resolution_requires_exact_usable_record() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        write_builder_fixture(root)
        registry = load_semantic_token_registry(root)
        assert registry is not None
        token = parse_catalogue_tokens(
            "[[catalogue:image:work:00638|alt=detail&detail_id=001]]",
            registry=registry,
        )[0]
        target = {
            "href": "/works/?work=00638",
            "image": {
                "src": "https://media.dotlineform.com/works/img/00638-primary-1600.webp?v=1",
            },
        }
        detail_path = root / "studio/data/canonical/catalogue/work_details/00638.json"
        detail_payload = json.loads(detail_path.read_text(encoding="utf-8"))

        resolved = resolve_catalogue_image_target(root, token, target)
        assert resolved is not None
        assert resolved["href"] == "/work-details/?detail=00638-001&from_work=00638"
        assert resolved["image"]["src"].endswith(
            "/work_details/img/00638-001-primary-1600.webp?v=3"
        )

        detail_path.unlink()
        assert resolve_catalogue_image_target(root, token, target) is None

        detail_payload["detail_sections"][0]["details"][0]["media_version"] = None
        write_json(detail_path, detail_payload)
        assert resolve_catalogue_image_target(root, token, target) is None
