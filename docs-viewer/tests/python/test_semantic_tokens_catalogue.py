"""Catalogue media/image grammar, source ranges and Series image Build ownership."""

import json
from pathlib import Path
import sys

from repo_factory import docs_scope_record, write_docs_scope_config, write_json, write_site_tools_config, write_text

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "docs-viewer/build"))

from docs_builder.pipeline import DocsDataBuilder  # noqa: E402
from docs_builder.semantic_token_registry import load_semantic_token_registry  # noqa: E402
from docs_builder.semantic_tokens import (  # noqa: E402
    parse_catalogue_tokens,
    semantic_token_at_selection,
    serialize_catalogue_image_token,
)
from docs_scope_config import load_docs_scope_configs  # noqa: E402


def test_media_parser_preserves_literal_labels_ranges_and_code_boundaries() -> None:
    registry = load_semantic_token_registry(REPO_ROOT)
    first = r"[[catalogue:media:work:00638|A \| label \] with \\]]"
    second = "[[catalogue:media:work:00008|Another]]"
    source = f"before {first}{second} after\n`{first}`\n<!-- {second} -->\n```text\n{first}\n```\n"
    tokens = parse_catalogue_tokens(source, registry=registry)
    assert [token.raw for token in tokens] == [first, second]
    assert tokens[0].title == "A | label ] with \\"
    for token in tokens:
        assert token.presentation == "media" and token.supported
        assert source[token.start:token.end] == token.raw
        assert semantic_token_at_selection(tokens, start=token.start + 1, end=token.start + 1) is token
        assert semantic_token_at_selection(tokens, start=token.start, end=token.start) is None
        assert semantic_token_at_selection(tokens, start=token.end, end=token.end) is None


def test_visual_occurrence_parser_is_canonical_and_context_aware() -> None:
    registry = load_semantic_token_registry(REPO_ROOT)
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


def test_builder_retains_series_image_projection_and_usage(tmp_path: Path) -> None:
    root = tmp_path
    doc_id = "d-20260910-120000-a1b2c3"
    write_site_tools_config(root)
    write_docs_scope_config(root, [docs_scope_record("studio", default_doc_id=doc_id)])
    for relative in ("docs-viewer/config/semantic-tokens/registry.json", "docs-viewer/config/routes/docs-viewer-routes.json"):
        write_text(root / relative, (REPO_ROOT / relative).read_text())
    write_json(root / "docs-viewer/data/generated/semantic-tokens/target-lookup.json", {
        "schema_version": "docs_semantic_token_target_lookup_v2",
        "targets": [{"family": "catalogue", "target_type": "series", "target_id": "005",
                     "title": "Series", "href": "/series/?series=005",
                     "image": {"src": "https://media.example.test/series.webp"}}],
    })
    figure = (
        "[[catalogue:image:series:005|alt=Series&caption=Quiet%20field&"
        "summary=Supporting%20copy&placement=right&fill_width=false]]"
    )
    missing = "[[catalogue:image:series:999|alt=Missing]]"
    write_text(root / f"docs-viewer/scopes/studio/source/documents/{doc_id}.md",
               f'---\ndoc_id: {doc_id}\ntitle: Images\nadded_date: "2026-09-10 12:00:00"\n---\n{figure}\n\n{missing}\n')
    builder = DocsDataBuilder(repo_root=root, config=load_docs_scope_configs(root)["studio"], skip_media_builds=True)
    builder.run(write=True)
    generated = root / "docs-viewer/scopes/studio/generated/documents"
    content = json.loads((generated / f"by-id/{doc_id}.json").read_text())["content_html"]
    usage = json.loads((generated / "semantic-tokens/index.json").read_text())
    assert '<a class="docsViewerFigure__imageLink" href="/series/?series=005"' in content
    assert 'src="https://media.example.test/series.webp"' in content
    assert 'target="_blank" rel="noopener noreferrer"' in content
    assert 'docsViewerFigure--image-right docsViewerFigure--natural-width' in content
    assert '<span class="docsViewerFigure__caption">Quiet field</span>' in content
    assert '<span class="docsViewerFigure__summary">Supporting copy</span>' in content
    assert missing in content
    assert not builder.warnings
    assert len(usage["occurrences"]) == 1
    assert usage["occurrences"][0]["raw"] == figure
    assert usage["occurrences"][0]["href"] == "/series/?series=005"
