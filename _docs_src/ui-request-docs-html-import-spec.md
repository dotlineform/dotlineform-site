---
doc_id: ui-request-docs-html-import-spec
title: "Docs HTML Import Spec"
last_updated: 2026-04-23
parent_id: ui-requests
sort_order: 30
---

# Docs HTML Import Spec

Status:

- requested feature spec
- Studio page plus local docs-management pipeline change

## Summary

Add a local-only HTML import flow that takes a self-contained `.html` file and creates a best-attempt Markdown source doc for the shared Docs Viewer.

The flow should support both docs scopes:

- `studio` -> `_docs_src/`
- `library` -> `_docs_library_src/`

This is not a new editing or publishing model.
It is an ingestion shortcut for externally authored HTML, especially self-contained exports that include inline CSS and inline SVG.

Current intent:

- import creates new docs only
- imported docs are still edited manually afterward in the normal source files
- publishing still follows the current docs build and docs search rebuild flow

## Product Goal

Reduce manual copy/paste cleanup when an external HTML file already contains useful prose and diagrams, but the Docs Viewer source of truth still needs to end up as a normal Markdown doc in the existing docs pipeline.

The desired outcome is:

- original HTML can be kept for reference in a repo-local staging area
- Studio can import one staged file at a time into a chosen docs scope
- the system strips or simplifies HTML that does not belong in docs source
- the result is a readable Markdown-first doc, not a raw full-page HTML dump
- the new doc then behaves like any other source doc in the current Docs Viewer workflow

## Recommended Initial Boundary

This should be a local Studio maintenance feature, not a hosted-site feature.

Recommended first-pass boundary:

- add a new Studio page for docs HTML import
- use the localhost docs-management server for import writes
- avoid arbitrary server-side file-system browsing
- keep original HTML files in a repo-local staging directory before import
- write only new Markdown docs into the flat scope roots

Recommended staging direction:

- use a dedicated repo-local staging area such as `var/docs/import-staging/`
- keep staged originals out of the published docs roots
- keep staged originals available for later reference when the import result needs manual cleanup

This is simpler and safer than trying to let the Studio page browse arbitrary external filesystem locations.

## Scope

Included:

- a new Studio import page
- selection of one staged `.html` file
- user choice of target docs scope:
  - `studio`
  - `library`
- automatic HTML-to-Markdown conversion
- automatic creation of one new Markdown source doc
- same-scope docs rebuild after a successful import
- same-scope docs-search rebuild after a successful import
- warning/reporting for dropped or simplified content

Excluded for this request:

- overwriting an existing doc
- updating an existing imported doc in place
- manual user editing before write
- arbitrary external filesystem browsing from the server
- turning Docs Viewer into a rich HTML publishing surface
- changing the current manual post-import editing workflow

## User Workflow

Recommended first-pass workflow:

1. user manually copies an external `.html` file into the repo staging directory
2. user opens the Studio docs import page
3. user selects:
   - one staged HTML file
   - target scope: `studio` or `library`
4. page submits an import request to the localhost docs-management service
5. service parses and converts the HTML into best-attempt Markdown
6. service writes a new source doc into the chosen flat source root
7. service rebuilds the chosen docs scope and same-scope docs search
8. page reports:
   - created doc id
   - created source path
   - dropped/simplified content warnings
   - link to open the new doc in the viewer

Current confirmed decision:

- there is no preview/edit step before write

## Output Contract

The import should create a normal source Markdown file in the chosen scope root:

- `_docs_src/*.md`
- `_docs_library_src/*.md`

Current root-layout implication:

- the scope toggle chooses the published docs corpus
- it does not choose a nested on-disk folder because both scope roots are flat

Recommended metadata generation:

- `title`:
  - first body `<h1>`, if present
  - otherwise stripped document `<title>`, if useful
  - otherwise filename stem
- `doc_id`:
  - generated from the final title using the existing docs-create uniqueness rules
- filename stem:
  - generated from the final title using the existing docs-create uniqueness rules
- `parent_id`:
  - blank by default unless later scope-specific defaults are explicitly added
- `last_updated`:
  - import date

Recommended body goal:

- Markdown first
- raw HTML only where the converter intentionally preserves a safe element that Markdown cannot represent cleanly

## Conversion Contract

### Required Stripping

The converter should always remove:

- `<head>`
- `<script>`
- `<style>` when it is only present to style the original page shell
- event-handler attributes such as `onclick`
- page-app chrome that has no meaningful document content

The converter should work from the meaningful body content rather than preserving full-page HTML structure.

### Preferred Markdown Conversion

Convert these into normal Markdown where practical:

- headings
- paragraphs
- ordered and unordered lists
- emphasis and strong text
- blockquotes
- code blocks and inline code
- tables when the structure is simple enough to survive as Markdown
- links to external websites
- images when the source is already suitable for Markdown output

Preferred link rule:

- keep external website links
- use Markdown link syntax when the content converts cleanly
- keep link text readable even if surrounding styling is dropped

### SVG Handling

Inline SVG diagrams are important content and should be kept.

Recommended first-pass rule:

- preserve inline `<svg>` blocks as raw HTML inside the Markdown body
- drop surrounding presentational wrappers when they are not needed for the diagram itself
- keep nearby captions or explanatory text as Markdown where possible

This fits the current docs builder contract, which already allows raw HTML inside Markdown docs.

### CSS Handling

Current requirement:

- strip inline CSS if it cannot be converted into equivalent Markdown meaning

Recommended first-pass interpretation:

- preserve semantic structure
- do not try to reproduce full visual layout from inline CSS
- remove styling that exists only for appearance, spacing, color, or page layout
- keep only content and structure that survive without CSS

Examples of styling that should usually be dropped:

- grid/flex layout wrappers
- absolute positioning
- font-family and font-size declarations
- decorative colors and backgrounds
- border and shadow treatments
- responsive layout rules

Examples of styling that may indicate semantic intent and therefore need a case-by-case rule:

- callout boxes that imply note/warning/info meaning
- indentation used to imply nested structure
- hidden/revealed content
- visually grouped label/value rows

### Non-Convertible Content

This needs explicit case-by-case rules in the final implementation spec.

Examples of content that may not convert cleanly into Markdown:

- layout tables used purely for positioning
- multi-column page compositions
- collapsible UI widgets
- tabs
- forms
- embedded scripts or interactive demos
- CSS-dependent callout systems with no semantic markup
- complex tables with rowspans or colspans
- figures whose readable text is baked into positioned HTML rather than SVG

Current confirmed direction:

- do not silently assume the answer
- capture these examples and decide the preservation/drop rule per content type

## Sanitization Boundary

This feature creates a new raw-content ingestion path, so sanitization is part of the spec rather than an optional cleanup step.

Required rules:

- remove scripts and event handlers unconditionally
- remove unsupported embedded objects
- limit preserved raw HTML to a known-safe subset
- keep the imported output readable without relying on the original page shell

Important reason:

- the docs builder already passes raw HTML through from Markdown source
- a careless import path could therefore turn full external page HTML into published docs content

## Studio Page Contract

Recommended route:

- `/studio/docs-import/`

Recommended UI:

- staged-file selector
- scope toggle:
  - `studio`
  - `library`
- import action
- result panel with warnings and next links

Recommended behavior:

- local-only feature
- fail closed when the docs-management service is unavailable
- no inline Markdown editor
- no pre-write preview modal
- no overwrite path

Visible runtime copy should live in `assets/studio/data/studio_config.json`.

## Docs-Management Server Contract

Recommended new endpoint:

- `POST /docs/import-html`

Recommended request shape:

```json
{
  "scope": "studio",
  "staged_filename": "example-export.html"
}
```

Recommended server responsibilities:

- validate scope
- validate that the staged file exists inside the approved staging directory
- parse and sanitize HTML
- convert to best-attempt Markdown
- generate new-doc metadata
- write one new Markdown source file in the chosen scope root
- create a backup manifest for the write batch
- rebuild same-scope docs payloads
- rebuild same-scope docs search
- return structured warnings about dropped or simplified content

Recommended response shape should include at least:

- created `doc_id`
- created source path
- created viewer URL
- warnings
- summary counts for preserved, simplified, and dropped blocks

## Implementation Approach

### Phase 1. Lock The Import Contract

Decide:

- staging directory path and whether staged files are tracked or ignored
- title-derivation priority when `<h1>` and `<title>` disagree
- final preservation/drop rules for each non-convertible content type
- whether imported images or data URLs are allowed in v1

### Phase 2. Add A Shared Conversion Module

Add a conversion module under `scripts/docs/` that can:

- parse self-contained HTML
- extract meaningful body content
- sanitize unsafe elements
- convert supported structures into Markdown
- preserve selected safe HTML blocks such as inline SVG
- produce a structured conversion report

### Phase 3. Add Server-Side Import Write Support

Extend `scripts/docs/docs_management_server.py` with:

- staged-file validation
- import endpoint
- scope-root write behavior
- rebuild/search follow-through
- operation-scoped backup behavior

### Phase 4. Add The Studio Page

Add a new Studio route and page controller that:

- lists available staged `.html` files
- allows scope selection
- submits the import request
- reports created-doc details and warnings

### Phase 5. Verify And Document

Verify:

- import success for both `studio` and `library`
- output file creation in the correct flat root
- same-scope docs rebuild
- same-scope docs-search rebuild
- safe stripping of scripts and page-shell content
- readable rendering of preserved SVG in the viewer

After implementation, update:

- Studio docs for the new page
- Docs Management Server doc for the new endpoint
- Docs Viewer Builder doc if the import path changes authoring guidance
- site and search change logs where the shipped behavior materially changes

## Benefits

- much less manual cleanup for ChatGPT-style exported HTML
- keeps the current Docs Viewer source-of-truth model intact
- preserves useful diagrams without forcing SVG-to-image conversion
- keeps the import workflow inside the existing local docs-management boundary
- keeps original HTML available for later reference

## Risks

- HTML-to-Markdown conversion will be lossy for layout-heavy exports
- preserving too much raw HTML would weaken the docs-source contract
- preserving too little would discard useful structure or diagrams
- staged originals could create repo clutter if the staging path and ignore policy are not explicit
- no preview step means warnings and deterministic rules need to be strong enough to trust

## Open Questions

### 1. What exactly counts as non-convertible content?

This now needs a worked example set and explicit rules.

The main unresolved cases are:

- CSS-dependent callouts
- complex tables
- multi-column layout fragments
- hidden/revealed content
- interactive widgets
- figures composed from positioned HTML instead of SVG

### 2. How aggressive should SVG cleanup be?

Possible choices:

- keep full inline SVG exactly as found
- strip non-essential SVG wrappers and metadata
- reject SVG that depends on external assets or scripts

### 3. What should happen with embedded images?

Cases to decide:

- normal external image URLs
- repo-local image paths that are meaningless after import
- `data:` URLs embedded directly in the HTML

### 4. Should imported docs default to a specific `parent_id`?

Current recommendation:

- no
- create at the root unless a later explicit default is agreed

### 5. Should the Studio page select only from staged files, or also support browser upload later?

Current recommendation:

- staged-file selection only for v1

Reason:

- it keeps the first implementation closer to the existing local-write model and preserves the original source file in the repo workspace

## Acceptance Criteria

- Studio has a local-only page for docs HTML import
- the user can choose one staged `.html` file and a target scope
- successful import creates one new Markdown source doc in `_docs_src/` or `_docs_library_src/`
- import does not overwrite existing docs
- the converter removes `head`, scripts, and irrelevant page-shell styling
- external links remain usable
- inline SVG diagrams are preserved in a form the Docs Viewer can render
- same-scope docs payloads rebuild automatically after import
- same-scope docs search rebuilds automatically after import
- the import result is reported with warnings for simplified or dropped content

## Related References

- [UI Requests](/docs/?scope=studio&doc=ui-requests)
- [Studio UI Start](/docs/?scope=studio&doc=studio-ui-start)
- [Studio](/docs/?scope=studio&doc=studio)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Docs Viewer](/docs/?scope=studio&doc=docs-viewer)
- [Docs Viewer Source Organisation](/docs/?scope=studio&doc=docs-viewer-source-organisation)
- [Docs Viewer Management](/docs/?scope=studio&doc=docs-viewer-management)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
