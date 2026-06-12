---
doc_id: docs-viewer-dependencies
title: Dependencies
added_date: 2026-05-14
last_updated: 2026-06-01
summary: Docs Viewer-specific dependency boundary, especially the parser stack introduced for staged source import.
parent_id: docs-viewer
viewable: true
---
# Docs Viewer Dependencies

This document records the Docs Viewer-specific dependency boundary, especially the parser stack introduced for staged source import.

For the site-wide dependency register, see [Runtime Dependencies](/docs/?scope=studio&doc=runtime-dependencies).

## Source Of Truth

Python package dependencies for repo scripts are pinned in:

- `requirements.txt`

`requirements.txt` is the checked-in Python dependency contract for local and cloud script environments.

Portable Docs Viewer installs that copy the build scripts, Docs Viewer service, or Docs Import should also copy `requirements.txt` or an equivalent pinned dependency file.

## Current Python Packages

The current checked-in Python packages are:

| Package     | Docs Viewer role | Required when |
| --- | --- | --- |
| `beautifulsoup4` | Builds the HTML import parse tree through Beautiful Soup. | Using Docs Import for staged HTML. |
| `lxml` | Parser backend selected by `BeautifulSoup(source_html, "lxml")`. | Using Docs Import for staged HTML. |
| `bleach` | Sanitization boundary for the Docs HTML import feature. | Using or extending HTML sanitization rules for Docs Import. |
| `Pillow` | Opens, resizes, and writes package images as 800px-max WebP outputs. | Using Docs Import for Markdown packages with local images. |
| `openpyxl` | Not a Docs Viewer dependency; used by workbook/spreadsheet pipeline scripts. | Catalogue or spreadsheet-driven workflows need it. |
| `pytest` | Test runner used by the repo check profiles. | Running Python tests through the repo check workflow. |
| `markdown-it-py` | CommonMark Markdown renderer selected for Docs Viewer payload generation and catalogue prose rendering. | Building or testing the Python Markdown renderer, Docs Viewer payloads, or catalogue prose generation. |

The Docs HTML import implementation currently lives in `docs-viewer/services/docs_html_import.py`.
Its parser boundary depends on `beautifulsoup4` plus `lxml`, its sanitization contract treats `bleach` as part of the pinned import stack, and Markdown package image conversion depends on `Pillow`.

- The shared Python Markdown renderer lives at `studio/shared/python/markdown_renderer.py`. It starts from `MarkdownIt("commonmark")`, enables the built-in `table` rule because authored Studio docs already use Markdown tables, and enables no external renderer plugins.
- Raw HTML is allowed by default for the current authored content model, but the helper does not sanitize HTML; imported or untrusted HTML must still pass through explicit sanitization boundaries such as `bleach`.
- Later syntax additions must record their enabled rules/plugins in this document and in the renderer fixtures.
- Acceptance fixtures in `studio/tests/python/test_markdown_renderer_acceptance.py` assert rendered HTML semantics and generated plain text directly.
- Python app builders protect generated app contracts.

## Parser Stack Roles

The import feature deliberately separates library-owned parsing from project-owned conversion rules:

- `beautifulsoup4` provides the navigable HTML document model used by the importer.
- `lxml` is the robust parser backend used by Beautiful Soup instead of Python's standard-library HTML parser.
- `bleach` is the pinned sanitizer dependency for stripping or constraining unsafe HTML when import sanitization rules need library support.

Conversion decisions remain in project code.
The importer should decide locally which elements are converted to Markdown, flattened, preserved as safe HTML, rewritten as plain text, or reported as warnings.
A generic third-party HTML-to-Markdown converter is not the product logic boundary.

## Role Of requirements.txt

`requirements.txt` should be treated as:

- the install source for Python packages used by repo scripts
- the parity contract between local setup, Codespaces, and Codex Cloud
- the place to pin parser and sanitizer versions when Docs Import behavior depends on them
- the place to pin Markdown renderer versions when generated Docs Viewer output depends on them

It should not be treated as:

- a browser dependency manifest
- a complete list of system tools used by media workflows
- proof that every package is required for every repo task

The Docs Import parser and conversion stack is feature-specific, but it is intentionally checked into the main `requirements.txt`.
That keeps local and cloud sessions on the same parser and image-conversion behavior whenever Docs Import is used.

## Operational Checks

Before treating Docs Import or Docs Viewer v2 Markdown rendering as available in a new environment, confirm the parser, conversion, and renderer stack can be imported by the configured project Python:

```bash
python -c "import bs4, lxml, bleach, PIL; from markdown_it import MarkdownIt; MarkdownIt('commonmark')"
```

If this fails, install the pinned packages from `requirements.txt` in the active Python environment before starting the Docs Viewer service, running Docs Import checks, or running Docs Viewer renderer fixtures.

## Related References

- [Docs Viewer Portable Setup](/docs/?scope=studio&doc=docs-viewer-portable-setup)
- [Docs Viewer Import Source Registry Spec](/docs/?scope=studio&doc=docs-viewer-import-source-registry-spec)
- [Docs Management Service](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Runtime Dependencies](/docs/?scope=studio&doc=runtime-dependencies)