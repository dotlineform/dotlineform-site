---
doc_id: site-request-docs-html-inline-raster-media
title: Docs HTML Inline Raster Media Request
added_date: 2026-05-07
last_updated: "2026-05-12 10:25"
ui_status: done
parent_id: archive
sort_order: 62000
---
# Docs HTML Inline Raster Media Request

Status:

- implemented

## Summary

This request tracks a follow-up to Docs Import so HTML and Markdown imports can extract inline raster data URLs into normal staged media files.

The immediate case is an imported Library doc that looked as though it contained inline SVG, but actually contained a Markdown image whose target was a long `data:image/png;base64,...` URI.
That keeps the source doc and generated docs payload difficult to read, search, review, and edit.

The desired behavior is:

- detect inline raster image data URLs during import
- decode each supported inline image into a generated file under `var/docs/import-staging/`
- replace the inline data URL with a normal docs media token
- return a list of media plans so the user can manually copy each generated file to the configured media store

## Implementation Status

Implemented for HTML and Markdown imports.

The importer now:

- rewrites Markdown-image-form raster data URLs to docs media tokens during preview
- returns `media_plans` for extracted inline raster images
- writes decoded media files to `var/docs/import-staging/` during create or overwrite
- keeps standalone image and file imports on the existing singular `media_plan` contract
- shows staged media paths, configured media paths, and media tokens in the Docs Viewer import result panel

## Problem

Docs Import already supports standalone raster image files as wrapper docs with remote media tokens.
It does not yet normalize raster images that are embedded inside HTML or Markdown bodies as data URLs.

Current effect:

- imported source Markdown can contain very long wrapped base64 lines
- generated docs JSON can carry the full encoded image payload
- reviewing a small prose change becomes noisy
- the existing remote docs media workflow is bypassed
- the user still has to manually extract the image if they want to move it to the configured media store

The importer already counts `data:` image URLs in preview summaries, so the issue is visible but not actionable enough.

## Goals

Add inline raster extraction to the Docs Import conversion path.

The workflow should:

- support `data:image/png;base64,...` first
- support the same raster formats as standalone image imports where practical: PNG, JPEG, WebP, and GIF
- write decoded media files under `var/docs/import-staging/`
- generate deterministic filenames from the proposed doc id
- increment filenames for multiple images, such as `<doc_id>-image-01.png`, `<doc_id>-image-02.png`
- avoid hash suffixes for now
- replace each inline data URL with <code>&#91;&#91;media:docs/&lt;scope&gt;/img/&lt;filename&gt;&#93;&#93;</code>
- return a `media_plans` array, not only a single `media_plan`
- report the expected media path for each generated file
- keep manual media-store copying as the handoff step

## Non-Goals

This request should not:

- convert raster PNG/JPEG/WebP/GIF images into SVG
- trace raster diagrams into vector markup
- upload media automatically
- change the remote media token format
- inline decoded binary data into tracked repo files
- treat sanitized inline SVG as raster media

Inline SVG should continue to follow the existing SVG sanitizer path.
Raster data URLs should become staged media files.

## Proposed Behavior

For an imported HTML or Markdown image like:

```md
![Diagram](data:image/png;base64,...)
```

The importer should generate a staged file such as:

```text
var/docs/import-staging/beyond-conscious-subconscious-image-01.png
```

The generated Markdown should become:

<pre><code>![Diagram](&#91;&#91;media:docs/library/img/beyond-conscious-subconscious-image-01.png&#93;&#93;)</code></pre>

The preview and write response should include a media plan entry like:

<pre><code>{
  "manual_copy_required": true,
  "source_path": "beyond-conscious-subconscious-image-01.png",
  "media_path": "docs/library/img/beyond-conscious-subconscious-image-01.png",
  "media_token": "&#91;&#91;media:docs/library/img/beyond-conscious-subconscious-image-01.png&#93;&#93;",
  "title": "Diagram"
}</code></pre>

If more than one inline raster image exists, the importer should return:

```json
{
  "media_plans": [
    { "source_path": "example-image-01.png" },
    { "source_path": "example-image-02.png" }
  ]
}
```

The older singular `media_plan` field may remain for standalone image and file-media imports, but Studio should be able to render `media_plans` whenever present.

## Filename Rules

Filenames should be deterministic and readable:

- base name: proposed doc id
- suffix: `image-NN`
- extension: derived from the data URL MIME type
- examples:
  - `beyond-conscious-subconscious-image-01.png`
  - `beyond-conscious-subconscious-image-02.jpg`

If a generated filename already exists in `var/docs/import-staging/`, the importer should use the next available increment.
No hash suffix is needed for this first version.

## Preview And Write Semantics

The preferred workflow is:

- preview reports planned inline media extraction and generated filenames
- write/import creates the decoded staged media files and writes the source Markdown
- both preview and write responses report the resulting `media_plans`

If implementation needs preview to create files for validation, it must make that behavior explicit in the response and avoid overwriting existing staged files silently.

## Studio UI Requirements

The Docs Import result UI should:

- show every generated staged media filename
- show every expected media path
- show the generated media token
- clearly state that manual media copy is still required
- handle both `media_plan` and `media_plans`
- avoid assuming an imported source has only one media asset

## Benefits

This change should:

- keep imported Markdown short and reviewable
- keep generated docs JSON free of large base64 payloads
- align inline raster images with the existing remote docs media workflow
- make the manual media-copy step visible and repeatable
- preserve the original image fidelity by decoding the source PNG/JPEG/WebP/GIF bytes directly

## Risks

Main risks:

- writing derived media during import can leave unused staged files if the user abandons an import
- malformed base64 needs clear warnings rather than partial silent output
- filename increments can produce surprising names if old staged files are left behind
- Studio result rendering may need to handle both singular and plural media-plan contracts during transition

These risks are acceptable if the importer reports planned filenames before write, avoids silent overwrite, and keeps the manual media-copy action explicit.

## Likely Files To Change

Implementation will likely touch:

- `docs-viewer/services/docs_html_import.py`
- `docs-viewer/services/docs_management_server.py`
- `docs-viewer/runtime/js/docs-html-import.js`
- `docs-viewer/config/ui-text/ui-text.json`
- `docs-viewer/source/studio/user-guide-docs-html-import.md`
- `docs-viewer/source/studio/scripts-docs-management-server.md`
- `docs-viewer/source/studio/site-request-docs-import-source-registry-media.md`

If the behavior becomes part of the standard Docs Import contract, update the relevant docs and rebuild the Studio docs payload.
