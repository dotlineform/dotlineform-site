"""Catalogue media/image grammar, source ranges and Work-only image authoring."""

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "docs-viewer/build"))

from docs_builder.semantic_token_registry import load_semantic_token_registry  # noqa: E402
from docs_builder.semantic_tokens import (  # noqa: E402
    parse_catalogue_tokens,
    semantic_token_at_selection,
    serialize_catalogue_image_token,
)


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
        "[[catalogue:image:work:00105|alt=nerve&caption=nerve&"
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
        target_type="work",
        target_id="00105",
        alt="nerve",
        caption="nerve",
        summary="intangible\nshifting boundaries",
        placement="left",
        fill_width=True,
    ) == figure

    malformed = [
        "[[catalogue:image:series:143|alt=Series]]",
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
