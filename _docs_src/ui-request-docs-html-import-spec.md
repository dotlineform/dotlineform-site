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

- import can create a new doc or explicitly overwrite an existing doc
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
- keep staged originals untracked by the repo

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
- explicit overwrite of an existing Markdown source doc after a warning step
- same-scope docs rebuild after a successful import
- same-scope docs-search rebuild after a successful import
- warning/reporting for dropped or simplified content

Excluded for this request:

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
   - whether obvious prompt/meta blocks should be included
4. page submits an import request to the localhost docs-management service
5. service parses and converts the HTML into best-attempt Markdown
6. if the generated target collides with an existing doc, the page shows an explicit overwrite warning naming the target doc
7. user either confirms overwrite or returns without writing
8. service writes the new source doc or overwrites the chosen existing source doc
9. service rebuilds the chosen docs scope and same-scope docs search
10. page reports:
   - created doc id
   - created source path
   - overwrite status, when applicable
   - any non-routine conversion warnings
   - link to open the new doc in the viewer

Current confirmed decision:

- there is no preview/edit step before write
- prompt/meta inclusion should be a user-led import choice rather than a fixed global rule

## Output Contract

The import should create a normal source Markdown file in the chosen scope root:

- `_docs_src/*.md`
- `_docs_library_src/*.md`

Current root-layout implication:

- the scope toggle chooses the published docs corpus
- it does not choose a nested on-disk folder because both scope roots are flat

Recommended metadata generation:

- `title`:
  - stripped document `<title>`, if useful
  - otherwise first body `<h1>`, if present
  - otherwise filename stem
- `doc_id`:
  - generated from the final title using the existing docs-create uniqueness rules when creating a new doc
  - preserved from the chosen target doc when explicitly overwriting an existing doc
- filename stem:
  - generated from the final title using the existing docs-create uniqueness rules when creating a new doc
  - preserved from the chosen target file when explicitly overwriting an existing doc
- `parent_id`:
  - blank by default unless later scope-specific defaults are explicitly added for new docs
  - preserved from the target doc when overwriting unless the overwrite contract later decides otherwise
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

Convert these semantic styled blocks into plain Markdown rather than stripping them with layout wrappers:

- prompt panels
- metadata panels
- key-point or `TL;DR` panels
- shaded explanatory callouts

Recommended first-pass rule for prompt/meta blocks:

- expose a user-controlled include/exclude option on the import page
- if included, render obvious prompt/meta source text as wrapped quoted prose
- if excluded, drop those blocks intentionally rather than treating them as conversion failures
- detect only clearly identifiable prompt/meta blocks in v1, using the most obvious source markers rather than broad heuristics
- prefer false negatives over false positives when prompt/meta detection is uncertain

Recommended first-pass rule for semantic callouts other than prompt/meta:

- keep the content
- remove decorative styling
- convert to paragraphs, blockquotes, or short labeled sections depending on structure

Preferred link rule:

- keep external website links
- use Markdown link syntax when the content converts cleanly
- keep link text readable even if surrounding styling is dropped

### Inline Safe HTML

Markdown alone is not enough for all technical notation used in these docs.

Recommended first-pass rule:

- allow a narrow safe subset of inline HTML to survive when it preserves meaning that plain Markdown would lose

Current priority examples:

- `<sub>`
- `<sup>`
- inline `<svg>` and its safe child elements

Reason:

- scientific and mathematical notation appears frequently in the target docs corpus
- preserving meaning is more important than forcing every imported fragment into pure Markdown

### SVG Handling

Inline SVG diagrams are important content and should be kept.

Recommended first-pass rule:

- preserve inline `<svg>` blocks as raw HTML inside the Markdown body
- drop surrounding presentational wrappers when they are not needed for the diagram itself
- keep nearby captions or explanatory text as Markdown where possible
- keep SVG-local `<style>` blocks when they are required for the diagram to render correctly
- reject or strip script-like or externally dependent SVG behavior rather than stripping all SVG-local styling blindly

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
- card shells
- pill styling and chip styling

Examples of styling that may indicate semantic intent and therefore need a case-by-case rule:

- callout boxes that imply note/warning/info meaning
- indentation used to imply nested structure
- hidden/revealed content
- visually grouped label/value rows

Recommended simplification rule for pill-like UI:

- preserve the underlying text labels
- flatten pill rows into plain text or comma-delimited lists
- do not attempt to preserve pill presentation as HTML/CSS

### Non-Convertible Content

V1 should ignore this category as a formal spec problem until a concrete source file exposes a real need.

Current rule:

- do not try to pre-classify every possible non-convertible HTML pattern in advance
- keep the importer focused on obvious supported structures and the worked example cases already captured in this spec
- when a concrete unsupported pattern appears, add a specific rule then

## Sanitization Boundary

This feature creates a new raw-content ingestion path, so sanitization is part of the spec rather than an optional cleanup step.

Required rules:

- remove scripts and event handlers unconditionally
- remove unsupported embedded objects
- limit preserved raw HTML to a known-safe subset
- keep the imported output readable without relying on the original page shell
- strip comments, layout-only wrapper attributes, and link attributes that no longer matter after Markdown conversion
- distinguish page-level `<style>` from SVG-local `<style>` inside preserved diagrams

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
- prompt/meta include toggle
- import action
- overwrite warning state when a target collision is detected
- result panel with warnings and next links

Recommended behavior:

- local-only feature
- fail closed when the docs-management service is unavailable
- no inline Markdown editor
- no pre-write preview modal
- allow overwrite only as an explicit warned choice after collision detection
- make the overwrite target clear by naming the existing doc id and title
- do not infer overwrite silently from a loose title match

Visible runtime copy should live in `assets/studio/data/studio_config.json`.

## Docs-Management Server Contract

Recommended new endpoint:

- `POST /docs/import-html`

Recommended request shape:

```json
{
  "scope": "studio",
  "staged_filename": "example-export.html",
  "include_prompt_meta": true,
  "overwrite_doc_id": null,
  "confirm_overwrite": false
}
```

Recommended server responsibilities:

- validate scope
- validate that the staged file exists inside the approved staging directory
- parse and sanitize HTML
- convert to best-attempt Markdown
- generate new-doc metadata
- detect collisions against existing docs in the chosen scope
- require explicit confirmation before overwriting an existing doc
- write one new Markdown source file in the chosen scope root or overwrite one existing source doc
- create a backup manifest for the write batch
- keep overwrite backups untracked by the repo
- rebuild same-scope docs payloads
- rebuild same-scope docs search
- return structured warnings only for non-routine or genuinely lossy conversion outcomes

Recommended response shape should include at least:

- created `doc_id`
- created source path
- created viewer URL
- whether the operation created or overwrote
- collision details when overwrite confirmation is required
- non-routine warnings
- summary counts for preserved, simplified, and dropped blocks

## Implementation Approach

### Phase 1. Lock The Import Contract

Phase 1 contract decisions are now locked in [Phase 1 Decisions](/docs/?scope=studio&doc=ui-request-docs-html-import-spec#phase-1-decisions).

### Phase 2. Add A Shared Conversion Module

Recommended implementation boundary:

- keep the import orchestration and rule logic in Python, alongside the local docs-management service
- use a library-backed HTML parser and sanitization layer to parse the full source document into a DOM-like in-memory node tree
- let Python-owned rules decide what to keep, flatten, preserve as safe HTML, rewrite as plain text, or drop with warnings
- do not treat a third-party HTML-to-Markdown converter as the product logic

Pinned v1 parser/sanitizer stack:

- `beautifulsoup4`
- `lxml`
- `bleach`

The parser output should be a navigable node tree in memory, not a JSON artifact written to disk as part of the normal import path.

Add a conversion module under `scripts/docs/` that can:

- parse self-contained HTML with a robust HTML parser library
- extract meaningful body content
- sanitize unsafe elements with a library-backed sanitization step
- convert supported structures into Markdown
- preserve selected safe HTML blocks such as inline SVG
- preserve selected inline safe HTML for technical notation such as subscripts and superscripts
- produce a structured conversion report

Recommended library boundary:

- external libraries are preferred for HTML parsing and sanitization
- conversion decisions remain project-owned and rule-driven in local code
- a separate Markdown parser or linter is not the canonical validator for this feature
- the parser/sanitizer libraries should be pinned in `requirements.txt` and installed before the importer is treated as building against its real v1 parser stack

### Phase 3. Add Server-Side Import Write Support

Extend `scripts/docs/docs_management_server.py` with:

- staged-file validation
- import endpoint
- scope-root write behavior
- overwrite collision detection and confirmation handling
- rebuild/search follow-through
- operation-scoped backup behavior

### Phase 4. Add The Studio Page

Add a new Studio route and page controller that:

- lists available staged `.html` files
- allows scope selection
- submits the import request
- reports created-doc details and any non-routine warnings

### Phase 5. Verify And Document

Verify:

- import success for both `studio` and `library`
- output file creation in the correct flat root
- same-scope docs rebuild
- same-scope docs-search rebuild
- safe stripping of scripts and page-shell content
- readable rendering of preserved SVG in the viewer
- generated Markdown renders successfully through the repo's existing Jekyll docs build path

Preferred validation rule:

- treat successful rendering through the current Jekyll docs pipeline as the canonical Markdown validation step
- do not require a separate Markdown syntax checker or linter for v1

Reason:

- the docs builder already renders Markdown through the repo's configured Jekyll converter
- this is a more accurate contract for the Docs Viewer than generic Markdown validation alone

After implementation, update:

- Studio docs for the new page
- Docs Management Server doc for the new endpoint
- Docs Viewer Builder doc if the import path changes authoring guidance
- site and search change logs where the shipped behavior materially changes

## Benefits

- much less manual cleanup for ChatGPT-style exported HTML
- keeps the current Docs Viewer source-of-truth model intact
- keeps validation aligned with the repo's real Jekyll Markdown behavior
- preserves useful diagrams without forcing SVG-to-image conversion
- preserves technical notation that plain Markdown cannot represent cleanly
- keeps the import workflow inside the existing local docs-management boundary
- keeps original HTML available for later reference
- supports rapid iteration during testing without forcing repeated manual cleanup of temporary imports

## Risks

- HTML-to-Markdown conversion will be lossy for layout-heavy exports
- preserving too much raw HTML would weaken the docs-source contract
- preserving too little would discard useful structure or diagrams
- staged originals could create repo clutter if the staging path and ignore policy are not explicit
- no preview step means warnings and deterministic rules need to be strong enough to trust
- overwrite behavior could replace the wrong source doc if collision handling is too loose or ambiguous
- a third-party converter or linter could disagree with the repo's Jekyll behavior if treated as the source of truth

## Open Questions

### 1. What exactly counts as non-convertible content?

This now has an initial worked-example interpretation, but some categories still need tighter final rules.

Current status:

- semantic callouts should usually be converted rather than dropped
- layout-only wrappers should be stripped
- interactive disclosure behavior should be flattened

Remaining unresolved cases:

- complex tables
- multi-column layout fragments
- interactive widgets beyond simple disclosure
- figures composed from positioned HTML instead of SVG

### 2. How aggressive should SVG cleanup be?

Possible choices:

- keep full inline SVG exactly as found
- strip non-essential SVG wrappers and metadata
- reject SVG that depends on external assets or scripts

Current recommendation:

- preserve inline SVG when it is self-contained and script-free
- keep SVG-local styling needed for rendering
- strip or reject active/external behavior

### 3. What should happen with embedded images?

Current recommendation:

- allow normal external image URLs in v1 on a best-effort basis
- allow `data:` URLs in v1 on a best-effort basis
- if an external image or `data:` URL produces a fragile, unclear, or semantically messy result, degrade to plain text with a warning
- repo-local image paths should degrade to plain text in v1

Locked for v1:

- `data:` URLs should remain inline

### 4. Should imported docs default to a specific `parent_id`?

Current recommendation:

- no
- create at the root unless a later explicit default is agreed
- preserve the existing `parent_id` when overwriting an existing doc

### 5. Should the Studio page select only from staged files, or also support browser upload later?

Current recommendation:

- staged-file selection only for v1

Reason:

- it keeps the first implementation closer to the existing local-write model and preserves the original source file in the repo workspace

### 6. How should prompt and metadata blocks be handled?

Current recommendation:

- make inclusion user-controlled at import time
- if included, render obvious prompt/meta source blocks as wrapped quoted prose
- do not let prompt/meta handling force a preview/edit workflow
- use only clearly identifiable source markers in v1 because the exported HTML corpus spans several months and styling may drift

### 7. How should overwrite be targeted?

Current recommendation:

- allow overwrite only as an explicit warned action
- target overwrite by existing `doc_id`, not by loose title text alone
- preserve the overwritten doc's `doc_id`, filename, and viewer identity
- always create a backup of the replaced source before write
- keep backups untracked by the repo
- use a light-touch same-day backup policy, for example replacing the prior same-day backup for the same target rather than accumulating every overwrite iteration

## Phase 1 Decisions

The following implementation decisions are now locked for the first pass.

- staging directory: `var/docs/import-staging/`
- staged HTML files: untracked by the repo
- overwrite backups: untracked by the repo
- title derivation: prefer `<title>` over `<h1>` when they disagree
- non-convertible handling: pragmatic v1 best effort with warnings
- external images: allowed in v1
- `data:` URLs: allowed in v1
- image and `data:` fallback: degrade to plain text when the result is doubtful
- repo-local image paths: plain text in v1
- prompt/meta inclusion: user-controlled, but detected only from clearly identifiable source markers
- overwrite target model: existing `doc_id`
- overwrite backup policy: light-touch same-day replacement is acceptable for v1
- external libraries: preferred for HTML parsing and sanitization
- parser/sanitizer stack: `beautifulsoup4`, `lxml`, `bleach`
- Markdown validation: use the repo's Jekyll render path rather than a separate required linter

## Worked Example Interpretation

The initial import rules should be tested against the four reviewed external HTML examples.

### Example 1. Conventional prose document

Observed structure:

- headings
- paragraphs
- lists
- one simple citation table
- one prompt block

Interpretation:

- fully convertible except for page-level styling
- prompt block should follow the user-controlled prompt/meta rule
- simple table should convert to Markdown
- repeated test imports of the same converted doc are a likely overwrite candidate

### Example 2. Styled semantic callouts plus formulas

Observed structure:

- metadata block
- prompt block
- `TL;DR` callout
- blockquote
- simple tables
- inline technical notation using subscripts

Interpretation:

- semantic callout blocks should be preserved as simplified Markdown sections
- prompt/meta handling should follow the user toggle
- simple tables should convert to Markdown
- inline `<sub>` should be preserved as safe inline HTML where Markdown would lose meaning
- iterative refinement of formula handling is a likely overwrite use case during importer development

### Example 3. Collapsible sections

Observed structure:

- metadata block
- multiple `<details>` / `<summary>` sections
- content-bearing footer

Interpretation:

- disclosure interaction is non-convertible and should be flattened
- each summary should become a heading or labeled lead line
- enclosed content should be preserved
- footer should be kept because it reads as document content
- repeated import tests should overwrite only by explicit choice because flattening rules may evolve

### Example 4. Diagram-led visual document

Observed structure:

- prompt block
- layout wrappers for cards and grid
- inline SVG diagram with local `<style>` inside the SVG
- pill-like legend labels
- supporting prose and simple table

Interpretation:

- preserve the SVG as raw safe HTML
- keep SVG-local styling needed for rendering
- strip outer layout wrappers after content extraction
- flatten pill rows into plain text labels or comma-delimited lists
- convert the simple table and prose normally
- diagram-heavy files are especially likely to need repeated overwrite testing while sanitization rules settle

## Acceptance Criteria

- Studio has a local-only page for docs HTML import
- the user can choose one staged `.html` file and a target scope
- successful import creates one new Markdown source doc in `_docs_src/` or `_docs_library_src/`
- import can overwrite an existing doc only after an explicit warning and confirmation step
- the converter removes `head`, scripts, and irrelevant page-shell styling
- external links remain usable
- inline SVG diagrams are preserved in a form the Docs Viewer can render
- technical notation that depends on safe inline HTML can survive conversion
- interactive HTML behavior is flattened into readable static content
- overwrite preserves the target doc identity and creates a backup before replacement
- same-scope docs payloads rebuild automatically after import
- same-scope docs search rebuilds automatically after import
- the import result is reported with non-routine warnings only, not routine spec-conformant transformations

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
