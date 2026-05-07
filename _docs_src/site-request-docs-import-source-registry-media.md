---
doc_id: site-request-docs-import-source-registry-media
title: Docs Import Source Registry And Media Support Request
added_date: 2026-05-07
last_updated: 2026-05-07
ui_status: proposed
parent_id: change-requests
sort_order: 205
---
# Docs Import Source Registry And Media Support Request

Status:

- proposed

## Summary

This request tracks the next Docs Import refinement after staged HTML and body-only Markdown support.

The goal is to make `/studio/docs-import/` format-extensible and support standalone visual/media files that should become normal Docs Viewer source docs.

The primary additions are:

- a source importer registry keyed by file extension and source format
- plain text import
- standalone SVG import
- raster image import for JPEG, PNG, WebP, and similar docs-safe image files
- deterministic copying of imported raster media into `assets/docs/...`
- wrapper Markdown generation around imported media

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

These files often arrive separately from the original HTML export.
There may be no reliable HTML source left to link them back to, so the import workflow should make each staged file usable on its own.

## Product Goal

Make Docs Import a structured source ingestion workflow rather than a collection of one-off conversion branches.

The desired user experience:

1. User puts staged source files under `var/docs/import-staging/`.
2. `/studio/docs-import/` lists supported files with a visible source format label.
3. User chooses a target scope.
4. User imports one staged source.
5. The importer creates or overwrites one normal Docs Viewer Markdown source doc.
6. For raster media, the importer also copies the source image into a stable repo docs asset path.
7. User can then open the source doc and add text around the imported visual or file content.

## Proposed Architecture

Introduce a source importer registry.

Conceptual shape:

```text
SOURCE_IMPORTERS = [
  html importer,
  markdown importer,
  text importer,
  svg importer,
  raster image importer
]
```

Each importer should declare:

- `source_format`
- supported suffixes
- whether it uses `include_prompt_meta`
- whether it writes auxiliary assets
- a preview function
- optional apply-time asset copy function

Each preview function should return the same shared preview contract:

- `source_format`
- `source_path`
- `title`
- `title_source`
- `proposed_doc_id`
- `proposed_doc_id_source`
- `markdown_preview`
- `source_stats`
- `warnings`
- `jekyll_validation`
- optional `asset_plan`

The existing create/overwrite flow should continue to own:

- target scope validation
- collision detection
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
- preserve safe inline SVG where needed
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
- generate a normal Markdown body

Open question:

- should plain URLs in text be converted to Markdown autolinks, matching HTML import prose behavior?

### Standalone SVG

SVG import should treat the SVG similarly to safe inline SVG preserved from HTML import.

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

Required SVG safety checks:

- reject or strip `<script>`
- strip `on*` event-handler attributes
- review external references such as remote images, fonts, stylesheets, and links
- preserve accessibility elements such as `<title>` and `<desc>` when safe

Open question:

- should external references be rejected by default, or allowed with warnings when they are ordinary links?

### Raster Images

Raster image import should create a Markdown wrapper doc and copy the image into `assets/docs/...`.

Candidate supported suffixes:

- `.jpg`
- `.jpeg`
- `.png`
- `.webp`
- `.gif`

Initial asset destination:

- `assets/docs/imports/<scope>/<doc_id>/<original-filename>`

Example generated Markdown:

```md
# Imported Image

![Imported Image](/assets/docs/imports/library/imported-image/imported-image.png)
```

Asset-copy requirements:

- copy only from `var/docs/import-staging/`
- write only under `assets/docs/imports/<scope>/<doc_id>/`
- prevent path traversal
- avoid overwriting an existing asset without explicit confirmation or deterministic backup behavior
- record copied assets in the backup bundle metadata
- include copied assets in dry-run and preview responses before write

Open questions:

- should raster imports preserve the original filename exactly, or normalize it to match `doc_id`?
- should duplicate filenames append `-2`, `-3`, and so on, or should import require explicit overwrite confirmation?
- should large images be rejected, warned, or optimized in a later separate media-processing request?

## UI Requirements

The Studio page should remain one route:

- `/studio/docs-import/`

The route should:

- show source format in the staged-file option label
- hide HTML-only controls for formats that do not use them
- show planned asset writes for media imports
- keep command feedback next to the import controls
- continue to use config-backed runtime copy from `studio_config.json`

For media imports, the result panel should show:

- source file
- generated `doc_id`
- target Markdown source path
- copied asset path
- viewer link
- warnings

## Service Requirements

The docs-management service should:

- keep `GET /docs/import-source-files`
- keep `POST /docs/import-source`
- keep older HTML endpoint aliases until callers are updated
- return `source_format` for each staged file
- include `asset_plan` in preview/result payloads when an importer writes assets
- back up overwritten source docs and overwritten/copied assets consistently
- keep write allowlists narrow:
  - source docs under the selected docs scope root
  - docs assets under `assets/docs/imports/...`

## Proposed Implementation Tasks

1. Extract importer registry.
   Move extension matching and preview dispatch into a registry structure.

2. Rename internal module boundaries.
   Either rename `docs_html_import.py` or add a new `docs_source_import.py` wrapper that owns the registry while preserving compatibility imports.

3. Add text importer.
   Implement `.txt` preview and create/overwrite coverage.

4. Add SVG importer.
   Implement SVG title extraction, sanitizer/reject rules, wrapper Markdown generation, and tests for unsafe SVG.

5. Add raster image importer.
   Implement asset planning, asset copy, wrapper Markdown generation, backup metadata, and tests.

6. Update Studio UI.
   Show format-specific labels, hide irrelevant controls, and display copied asset paths in result payloads.

7. Update docs and checks.
   Update the Docs Import user guide, Docs Management Server reference, Studio UI rules, and targeted service tests.

## Acceptance Criteria

This request is complete when:

- the import registry owns all supported source-format dispatch
- HTML and Markdown imports still pass current behavior checks
- `.txt` imports create a normal source Markdown doc
- `.svg` imports create a wrapper Markdown doc with sanitized inline SVG
- raster image imports copy the image under `assets/docs/imports/<scope>/<doc_id>/` and create a Markdown wrapper doc
- preview/dry-run responses show planned asset writes before apply
- overwrite flows back up both source docs and affected imported assets
- `/studio/docs-import/` clearly shows format-specific controls and results

## Benefits

- keeps source-format handling explicit and testable
- lets standalone ChatGPT-exported visuals become normal editable docs
- avoids trying to reconstruct unreliable old HTML-to-asset relationships
- keeps imported raster images in the established repo docs asset area
- makes future formats easier to add without growing route-specific branches

## Risks

- SVG import can introduce security and rendering issues if sanitizer rules are too permissive
- raster media can bloat the repo if large images are imported without size guidance
- asset overwrite behavior can become confusing unless preview and backup reporting are clear
- a registry refactor touches the existing HTML and Markdown import path, so regression coverage must stay focused

## Related References

- [Docs Import](/docs/?scope=studio&doc=user-guide-docs-html-import)
- [Docs Images And Assets](/docs/?scope=studio&doc=user-guide-docs-images)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Docs HTML Import Spec](/docs/?scope=studio&doc=ui-request-docs-html-import-spec)
- [Change Requests](/docs/?scope=studio&doc=change-requests)
