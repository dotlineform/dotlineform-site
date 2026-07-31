#!/usr/bin/env python3
"""Source-fragment contracts for staged Docs media."""

from __future__ import annotations

import pytest

import docs_staged_media_fragments as fragments


def test_plain_image_fragment_preserves_current_markdown_shape() -> None:
    assert fragments.build_plain_image_fragment(
        r"A [quiet] field \ study",
        "[[media:docs/library/img/photo.png]]",
    ) == (
        r"![A \[quiet\] field \\ study]"
        "([[media:docs/library/img/photo.png]])"
    )


def test_file_link_fragment_preserves_current_markdown_shape() -> None:
    assert fragments.build_file_link_fragment(
        "Research [notes]",
        "[[media:docs/library/files/notes.pdf]]",
    ) == r"[Research \[notes\]]([[media:docs/library/files/notes.pdf]])"


@pytest.mark.parametrize(
    ("placement", "modifier"),
    [
        ("full", "docsViewerFigure--full-column"),
        ("left", "docsViewerFigure--image-left"),
        ("right", "docsViewerFigure--image-right"),
    ],
)
def test_figure_fragment_has_exact_allowlisted_placement_shape(
    placement: str,
    modifier: str,
) -> None:
    assert fragments.build_figure_image_fragment(
        "A quiet field",
        "[[media:docs/library/img/photo.png]]",
        caption="Quiet field",
        summary="A short supporting summary.",
        placement=placement,
    ) == (
        f'<figure class="docsViewerFigure {modifier}">\n'
        '  <img src="[[media:docs/library/img/photo.png]]" alt="A quiet field">\n'
        "  <figcaption>\n"
        '    <span class="docsViewerFigure__caption">Quiet field</span>\n'
        '    <span class="docsViewerFigure__summary">A short supporting summary.</span>\n'
        "  </figcaption>\n"
        "</figure>"
    )


def test_figure_fragment_omits_absent_summary_and_escapes_hostile_text() -> None:
    assert fragments.build_figure_image_fragment(
        '"quoted" <image> & more',
        "[[media:docs/library/img/photo.png]]",
        caption="<script>alert('caption')</script> & copy",
        placement="full",
    ) == (
        '<figure class="docsViewerFigure docsViewerFigure--full-column">\n'
        '  <img src="[[media:docs/library/img/photo.png]]" '
        'alt="&quot;quoted&quot; &lt;image&gt; &amp; more">\n'
        "  <figcaption>\n"
        '    <span class="docsViewerFigure__caption">'
        "&lt;script&gt;alert('caption')&lt;/script&gt; &amp; copy</span>\n"
        "  </figcaption>\n"
        "</figure>"
    )


@pytest.mark.parametrize("placement", ["center", "left wide", "<script>"])
def test_figure_fragment_rejects_invalid_placement(placement: str) -> None:
    with pytest.raises(ValueError, match="placement must be one of: full, left, right"):
        fragments.build_figure_image_fragment(
            "Image",
            "[[media:docs/library/img/photo.png]]",
            caption="Caption",
            placement=placement,
        )


def test_figure_fragment_requires_placement() -> None:
    with pytest.raises(ValueError, match="placement is required"):
        fragments.build_figure_image_fragment(
            "Image",
            "[[media:docs/library/img/photo.png]]",
            caption="Caption",
            placement="",
        )


def test_figure_fragment_escapes_hostile_summary_text() -> None:
    fragment = fragments.build_figure_image_fragment(
        "Image",
        "[[media:docs/library/img/photo.png]]",
        caption="Caption",
        summary='<img src=x onerror="alert(1)"> & more',
        placement="right",
    )

    assert (
        '<span class="docsViewerFigure__summary">'
        '&lt;img src=x onerror="alert(1)"&gt; &amp; more</span>'
    ) in fragment
    assert "<img src=x" not in fragment


def test_figure_fragment_requires_plain_nonempty_caption() -> None:
    with pytest.raises(ValueError, match="caption is required"):
        fragments.build_figure_image_fragment(
            "Image",
            "[[media:docs/library/img/photo.png]]",
            caption=" \n ",
            placement="full",
        )
    with pytest.raises(ValueError, match="caption must be plain text"):
        fragments.build_figure_image_fragment(
            "Image",
            "[[media:docs/library/img/photo.png]]",
            caption={"html": "<b>Caption</b>"},
            placement="full",
        )
