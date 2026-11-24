"""Parse Docs TeX with Markdown and emit presentation MathML at build time."""

from __future__ import annotations

from html import unescape
from typing import Any
from xml.etree.ElementTree import tostring

from latex2mathml.converter import convert_to_element
from markdown_it import MarkdownIt
from mdit_py_plugins.dollarmath import dollarmath_plugin

from markdown_renderer import build_markdown_renderer


def render_mathml(tex: str, options: dict[str, Any]) -> str:
    try:
        math = convert_to_element(tex, display="block" if options["display_mode"] else "inline")
    except Exception as error:
        excerpt = " ".join(tex.split())[:120]
        raise ValueError(f"Could not render TeX {excerpt!r}: {error or type(error).__name__}") from error

    # The converter stores symbol references in text nodes. Decode them there
    # so the XML serializer can still escape literal comparison signs and text.
    for node in math.iter():
        if node.text:
            node.text = unescape(node.text)
        # Presentation expressions carry no embedded links or page styling.
        for attribute in ("href", "class", "style"):
            node.attrib.pop(attribute, None)
    return tostring(math, encoding="unicode")


def install_docs_math(renderer: MarkdownIt, *, typeset_math: bool = True) -> None:
    """Register Docs math on a renderer with its existing Markdown rules."""
    dollarmath_plugin(
        renderer,
        allow_labels=False,
        allow_space=False,
        allow_blank_lines=False,
        renderer=render_mathml if typeset_math else None,
    )


def build_docs_markdown_renderer(*, typeset_math: bool = True) -> MarkdownIt:
    """Use the same math grammar for rendered documents and link discovery."""
    renderer = build_markdown_renderer()
    install_docs_math(renderer, typeset_math=typeset_math)
    return renderer
