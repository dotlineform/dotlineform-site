#!/usr/bin/env python3
"""Ordinary Markdown front-matter normalization contracts."""

from __future__ import annotations

import pytest

from docs_import_preview import (
    build_markdown_summary,
    normalize_ordinary_markdown_front_matter,
)


def normalized_summary(markdown: str, source_name: str = "ordinary.md"):
    body, title, diagnostics, warnings = (
        normalize_ordinary_markdown_front_matter(
            markdown,
            source_name=source_name,
        )
    )
    summary = build_markdown_summary(
        body,
        source_name.rsplit(".", 1)[0],
        front_matter_title=title,
    )
    if diagnostics is not None:
        diagnostics["title_used"] = summary["title_source"] == "front_matter"
    return body, diagnostics, warnings, summary


def test_well_formed_front_matter_is_stripped_and_only_title_can_fallback() -> None:
    body, diagnostics, warnings, summary = normalized_summary(
        """---
title: Front Matter Title
doc_id: existing-document
summary: Ignored summary
viewable: false
---

Body without a heading.
""",
    )

    assert body == "\nBody without a heading.\n"
    assert diagnostics == {
        "stripped": True,
        "fields": ["title", "doc_id", "summary", "viewable"],
        "ignored_fields": ["doc_id", "summary", "viewable"],
        "title_used": True,
    }
    assert warnings == [
        "Ignored ordinary Markdown front matter fields: "
        "doc_id, summary, viewable.",
    ]
    assert summary["title"] == "Front Matter Title"
    assert summary["title_source"] == "front_matter"
    assert summary["markdown_preview"] == "Body without a heading."
    assert summary["proposed_doc_id"] == "ordinary"


def test_body_h1_wins_and_plain_markdown_is_unchanged() -> None:
    body, diagnostics, warnings, summary = normalized_summary(
        """---
title: Ignored Front Matter Title
---
# Body Title

Body.
""",
    )
    plain_body, plain_title, plain_diagnostics, plain_warnings = (
        normalize_ordinary_markdown_front_matter(
            "# Plain\n\nUnchanged.\n",
            source_name="plain.md",
        )
    )

    assert body == "# Body Title\n\nBody.\n"
    assert diagnostics == {
        "stripped": True,
        "fields": ["title"],
        "ignored_fields": [],
        "title_used": False,
    }
    assert warnings == []
    assert summary["title"] == "Body Title"
    assert summary["title_source"] == "h1"
    assert plain_body == "# Plain\n\nUnchanged.\n"
    assert plain_title == ""
    assert plain_diagnostics is None
    assert plain_warnings == []


@pytest.mark.parametrize(
    ("markdown", "message"),
    [
        (
            "---\ntitle: Missing close\nBody.\n",
            "unterminated",
        ),
        (
            "---\ntitle: First\ntitle: Second\n---\nBody.\n",
            "duplicate field",
        ),
        (
            "---\ntitle: Valid\nmalformed line\n---\nBody.\n",
            "expected a key and scalar value",
        ),
        (
            "--- invalid\ntitle: No\n---\nBody.\n",
            "opening delimiter",
        ),
    ],
)
def test_apparent_malformed_front_matter_fails_before_body_normalization(
    markdown: str,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        normalize_ordinary_markdown_front_matter(
            markdown,
            source_name="malformed.md",
        )


def test_non_scalar_title_is_ignored_with_a_diagnostic() -> None:
    body, title, diagnostics, warnings = normalize_ordinary_markdown_front_matter(
        """---
title: [First, Second]
review_folder_id: review-1
---
Body.
""",
        source_name="structured-title.md",
    )

    assert body == "Body.\n"
    assert title == ""
    assert diagnostics == {
        "stripped": True,
        "fields": ["title", "review_folder_id"],
        "ignored_fields": ["review_folder_id"],
        "title_used": False,
    }
    assert warnings == [
        "Ignored ordinary Markdown front matter title because it was not a "
        "non-blank scalar string.",
        "Ignored ordinary Markdown front matter fields: review_folder_id.",
    ]
