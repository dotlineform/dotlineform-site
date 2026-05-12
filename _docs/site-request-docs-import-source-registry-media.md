---
doc_id: site-request-docs-import-source-registry-media
title: Docs Import Source Registry And Media Support Request
added_date: 2026-05-07
last_updated: "2026-05-12 10:25"
ui_status: done
parent_id: change-requests
sort_order: 205
---
# Docs Import Source Registry And Media Support Request

Status:

- implemented

## Summary

This request tracks the next Docs Import refinement after staged HTML and body-only Markdown support.

The goal is to make Docs Import format-extensible and support standalone visual/media files that should become normal Docs Viewer source docs.

The primary additions are:

- a source importer registry keyed by file extension and source format
- plain text import
- standalone SVG import using the same SVG safety rules as HTML import
- raster image import for JPEG, PNG, WebP, and similar docs-safe image files
- file-media import for download-style assets
- wrapper Markdown generation around imported media that points at the configured docs media path

## Problem

The current importer now has a generic route and service endpoint, but the implementation still grew from the HTML importer:

- `scripts/docs/docs_html_import.py` owns HTML and Markdown importer logic
- supported extensions are hardcoded in module-level suffix sets
- format dispatch is a branch inside `generate_import_preview`
- the Studio page only knows about the Markdown special case
- service log and suppression names still include `docs-import-html`

That is acceptable for HTML plus Markdown, but it will become harder to reason about as soon as more source formats are added.

The likely next staged files include:

- `.txt` files that should become plain Markdown docs
- `.svg` files saved separately from ChatGPT or other tools
- `.jpg`, `.jpeg`, `.png`, `.webp`, or `.gif` image files that should become docs assets and receive a small wrapper Markdown source doc
- files such as PDFs or other downloads that should be linked from a wrapper Markdown source doc

These files often arrive separately from the original HTML export.
There may be no reliable HTML source left to link them back to, so the import workflow should make each staged file usable on its own.

## Product Goal

Make Docs Import a structured source ingestion workflow rather than a collection of one-off conversion branches.

The desired user experience:

1. User puts staged source files under `var/docs/import-staging/`.
2. The Docs Viewer management modal lists supported files with a visible source format label.
3. User chooses a target scope.
4. User imports one staged source.
5. The importer creates or overwrites one normal Docs Viewer Markdown source doc.
6. For image or file media, the importer generates Markdown that points at the configured docs media path and reports the manual copy action required.
7. User manually copies the media file to the site's configured media store, then opens the source doc and adds text around the imported visual or file link.

## Proposed Architecture

Introduce a source importer registry.

Conceptual shape:

```text
SOURCE_IMPORTERS = [
  html importer,
  markdown importer,
  text importer,
  svg importer,
  raster image importer,
  file media importer
]
```

Each importer should declare:

- `source_format`
- supported suffixes
- whether it uses `include_prompt_meta`
- whether it creates a remote media plan
- a preview function
- optional apply-time source-doc writer

Each preview function should return the same shared preview contract:

- `source_format`
- `source_path`
- `title`
- `title_source`
- `proposed_doc_id`
- `proposed_doc_id_source`
- `doc_id_collision`
- optional `replacement_title_required`
- `markdown_preview`
- `source_stats`
- `warnings`
- `jekyll_validation`
- optional `media_plan`

The existing create/overwrite flow should continue to own:

- target scope validation
- collision detection
- replacement-title handling when a proposed `doc_id` collides with an existing source Markdown stem
- overwrite confirmation
- front matter generation
- source Markdown writes
- backup bundle creation
- same-scope docs and docs-search rebuilds

## Format Rules

### HTML

Keep the existing behavior.

HTML import should:

- convert supported HTML structures into Markdown
- preserve safe inline SVG where needed through the shared SVG safety rules
- keep the prompt/meta toggle
- derive `doc_id` from the staged filename stem
- derive title from HTML title or first heading

### Markdown

Keep the current body-only behavior.

Markdown import should:

- treat the staged file as body-only Markdown
- not expect front matter
- derive title from the first `# H1` when present
- fall back to a humanized filename title
- derive `doc_id` from the staged filename stem

### Text

Text import should:

- accept `.txt`
- treat the file as plain prose
- derive title from the first non-empty line when it is reasonably title-like, otherwise from the filename
- escape or fence content only when needed to prevent accidental Markdown structure
- convert plain URLs to Markdown autolinks, matching HTML import prose behavior
- generate a normal Markdown body

### Shared SVG Safety Rules

SVG handling should be one shared rule set used by:

- inline SVG preserved from HTML import
- standalone `.svg` source files

The implementation should not define separate HTML-SVG and raw-SVG policies.
If the sanitizer or rejection rules change, the same change should apply to both paths.

Shared SVG safety checks:

- reject or strip `<script>`
- strip `on*` event-handler attributes
- review external references such as remote images, fonts, stylesheets, and links
- preserve accessibility elements such as `<title>` and `<desc>` when safe

Open question:

- should external references be rejected by default, or allowed with warnings when they are ordinary links?

### Standalone SVG

Standalone SVG import should reuse the shared SVG safety rules above.

SVG import should:

- accept `.svg`
- derive title from `<title>` inside the SVG when present, otherwise from the filename
- sanitize or reject unsafe SVG content before write
- generate wrapper Markdown with the raw SVG block in the body
- derive `doc_id` from the staged filename stem

Initial wrapper body:

```md
# Imported Diagram

<svg ...>
...
</svg>
```

### Raster Images

Raster image import should create a Markdown wrapper doc that points at the configured docs media location.
The importer should not copy images into `assets/docs/...` for this workflow.
Manual media-store copy remains the publishing step for now.

Candidate supported suffixes:

- `.jpg`
- `.jpeg`
- `.png`
- `.webp`
- `.gif`

Initial media path pattern:

- `docs/<scope>/img/<original-filename>`

Examples:

- `docs/library/img/imported-image.png`
- `docs/studio/img/imported-image.png`

Example generated Markdown:

```md
# Imported Image

![Imported Image]([[media:docs/library/img/imported-image.png]])
```

Media-plan requirements:

- treat `var/docs/import-staging/` as the only valid local source for the manual copy plan
- never copy image media into tracked repo paths as part of this workflow
- report the expected media path and resolved Markdown media token before apply
- prevent path traversal
- warn that the image must be manually copied to the media store before the rendered doc can display it
- include media plans in dry-run and preview responses before write

The `docs/<scope>/img/` folder structure intentionally mirrors the existing catalogue `works/img/` media convention while adding a docs scope segment.
That keeps Library images under `docs/library/img/` and leaves room for future Studio docs media under `docs/studio/img/`.

### Linked Files

File-media import should create a Markdown wrapper doc that links to a downloadable file in the configured media location.
This is a separate media class from images, matching the existing catalogue split between `works/img/` and `works/files/`.

Initial media path pattern:

- `docs/<scope>/files/<original-filename>`

Examples:

- `docs/library/files/imported-reference.pdf`
- `docs/studio/files/imported-reference.zip`

Example generated Markdown:

```md
# Imported Reference

[Download Imported Reference]([[media:docs/library/files/imported-reference.pdf]])
```

File-media requirements:

- use an explicit allowlist for supported downloadable file extensions
- keep `.txt` as a source-text importer rather than a file-media import unless deliberately overridden later
- report the expected media path and Markdown link before apply
- warn that the file must be manually copied to the media store before the rendered link works
- avoid embedding files inline unless a future importer explicitly supports that format

Open questions:

- should media imports preserve the original filename exactly, or normalize it to match `doc_id`?
- should large images be rejected, warned, or optimized in a later separate media-processing request?
- which downloadable file extensions should be allowed in the first file-media milestone?

## Duplicate Stem Rule

If the staged file stem would produce the same `doc_id` as an existing Markdown source file in the selected scope, the importer should not auto-append a suffix.
Instead, the Studio UI should prompt for a replacement title before apply.

The prompt should:

- be seeded with the current derived title or humanized file stem
- make it easy to add a suffix manually
- show the existing colliding `doc_id`
- regenerate the proposed `doc_id` from the edited title
- re-run collision validation before enabling apply

Example:

- staged file: `imported-reference.pdf`
- existing source doc: `imported-reference.md`
- prompt value: `Imported Reference`
- user edits to: `Imported Reference 2`
- new proposed `doc_id`: `imported-reference-2`

The same rule should apply to HTML, Markdown, text, SVG, image, and file-media imports.
Overwrite remains a separate explicit action for cases where the user intentionally chooses an existing doc.

## UI Requirements

The Docs Viewer management modal should:

- show source format in the staged-file option label
- hide HTML-only controls for formats that do not use them
- show planned media paths and manual-copy requirements for media imports
- prompt for a replacement title when the proposed `doc_id` collides with an existing Markdown source stem
- keep command feedback next to the import controls
- use Docs Viewer-owned runtime copy from `assets/docs-viewer/data/ui-text.json`

For media imports, the result panel should show:

- source file
- generated `doc_id`
- target Markdown source path
- expected media path
- generated Markdown media token or file link
- viewer link
- warnings

## Service Requirements

The docs-management service should:

- keep `GET /docs/import-source-files`
- keep `POST /docs/import-source`
- keep older HTML endpoint aliases until callers are updated
- return `source_format` for each staged file
- include `media_plan` in preview/result payloads when an importer references remote media
- report `doc_id` collisions with enough detail for the UI to prompt for a replacement title
- accept a replacement title and derive the replacement `doc_id` server-side before write
- back up overwritten source docs consistently
- keep write allowlists narrow:
  - source docs under the selected docs scope root

The first implementation should not write imported images or files into repo asset folders.
It should treat media-store copying as a manual post-import action until a later upload automation request is implemented for docs media.

## Proposed Implementation Tasks

1. Extract importer registry.
   Move extension matching and preview dispatch into a registry structure.

2. Rename internal module boundaries.
   Either rename `docs_html_import.py` or add a new `docs_source_import.py` wrapper that owns the registry while preserving compatibility imports.

3. Add text importer.
   Implement `.txt` preview, Markdown autolink conversion, and create/overwrite coverage.

4. Add SVG importer.
   Implement SVG title extraction, shared SVG sanitizer/reject rules, wrapper Markdown generation, and tests proving HTML inline SVG and standalone SVG use the same policy.

5. Add raster image importer.
   Implement media-path planning, wrapper Markdown generation, manual-copy warnings, and tests.

6. Add file-media importer.
   Implement file media-path planning, wrapper Markdown generation, manual-copy warnings, and tests for the first allowed file extensions.

7. Update Studio UI.
   Show format-specific labels, hide irrelevant controls, display planned media paths in result payloads, and prompt for replacement titles on `doc_id` collisions.

8. Update docs and checks.
   Update the Docs Import user guide, Docs Management Server reference, Studio UI rules, and targeted service tests.

## Acceptance Criteria

This request is complete when:

- the import registry owns all supported source-format dispatch
- HTML and Markdown imports still pass current behavior checks
- `.txt` imports create a normal source Markdown doc
- `.txt` imports convert plain URLs to Markdown autolinks consistently with HTML import
- HTML inline SVG and standalone `.svg` imports use the same SVG safety rules
- `.svg` imports create a wrapper Markdown doc with sanitized inline SVG
- raster image imports create a Markdown wrapper doc that points at `[[media:docs/<scope>/img/<filename>]]`
- file-media imports create a Markdown wrapper doc that points at `[[media:docs/<scope>/files/<filename>]]`
- duplicate source Markdown stems prompt for a replacement title seeded with the current name, then derive a new non-colliding `doc_id`
- preview/dry-run responses show planned media paths and manual-copy requirements before apply
- overwrite flows back up affected source docs
- the Docs Viewer management modal clearly shows format-specific controls and results

## Benefits

- keeps source-format handling explicit and testable
- lets standalone ChatGPT-exported visuals become normal editable docs
- avoids trying to reconstruct unreliable old HTML-to-asset relationships
- keeps media links aligned with the existing `works/img/` and `works/files/` split
- leaves docs media upload automation as a separate concern from source-doc import
- makes future formats easier to add without growing route-specific branches

## Risks

- SVG import can introduce security and rendering issues if sanitizer rules are too permissive
- media links can render broken until the manual media copy is completed
- duplicate remote filenames can become confusing unless preview reporting is clear
- a registry refactor touches the existing HTML and Markdown import path, so regression coverage must stay focused

## Related References

- [Docs Import](/docs/?scope=studio&doc=user-guide-docs-html-import)
- [Docs Images And Assets](/docs/?scope=studio&doc=user-guide-docs-images)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Docs HTML Import Spec](/docs/?scope=studio&doc=ui-request-docs-html-import-spec)
- [Change Requests](/docs/?scope=studio&doc=change-requests)
