---
doc_id: scripts-docs-management-server-import-rebuild
title: Docs Management Service Import And Rebuild
added_date: 2026-05-19
last_updated: 2026-05-19
parent_id: scripts-docs-management-server
sort_order: 15200
---
# Docs Management Service Import And Rebuild

`POST /docs/create` expects:

```json
{
  "scope": "studio",
  "title": "New Doc",
  "after_doc_id": "docs-viewer-management"
}
```

Request behavior:

- `scope` must be one of the configured scope ids in `docs-viewer/config/scopes/docs_scopes.json`
- `title` defaults to `New Doc` when omitted or blank
- new docs write `added_date` and `last_updated` to the current minute in `YYYY-MM-DD HH:MM` form
- new Studio docs write `published: true`, `viewable: true`
- new Analysis docs write `published: true`, `viewable: false`
- new Library docs write `published: true`, `viewable: false`
- `doc_id` and filename stem are generated from the title and made unique with `-2`, `-3`, and so on
- `after_doc_id`, when present, inserts the new doc after the referenced doc and reuses that doc's `parent_id`
- `parent_id`, when present without `after_doc_id`, must resolve inside the same scope
- `sort_order` appends as the last sibling when both `after_doc_id` and explicit `sort_order` are omitted

`GET /docs/import-source-files` returns:

- the current supported staged source files under `var/docs/import-staging/`
- filename, repo-relative path, source format, size, and modified time for each staged file
- a read-only listing intended for the Studio import page

Supported source formats:

- `html`: `.html`, `.htm`
- `markdown`: `.md`, `.markdown`
- `markdown_package`: direct child package folders containing exactly one Markdown file
- `text`: `.txt`
- `svg`: `.svg`
- `image`: `.jpg`, `.jpeg`, `.png`, `.webp`, `.gif`
- `file`: `.pdf`, `.zip`, `.csv`, `.tsv`, `.json`, `.jsonl`, `.docx`, `.xlsx`, `.pptx`

`GET /docs/import-html-files` remains a compatibility alias for older callers and returns the same source-file listing.

`POST /docs/import-source` expects:

```json
{
  "scope": "studio",
  "staged_filename": "example 1.html",
  "include_prompt_meta": false,
  "overwrite_doc_id": "",
  "confirm_overwrite": false,
  "replacement_doc_id": "",
  "replacement_title": "",
  "preview_only": false
}
```

Import behavior:

- `scope` must be one of the configured scope ids in `docs-viewer/config/scopes/docs_scopes.json`
- `staged_filename` must resolve inside `var/docs/import-staging/`
- accepts the supported staged source formats listed above
- parses full staged HTML files through the shared converter
- imports staged Markdown as the source body without predefined front matter
- imports staged Markdown package folders as one source doc, rewrites local package images and attachments to docs media links, converts package images to 800px-max WebP outputs, and copies package attachments unchanged
- imports staged text as plain Markdown prose and converts plain URLs to Markdown autolinks
- imports standalone SVG as a wrapper Markdown doc with sanitized inline SVG
- imports raster images as wrapper Markdown docs pointing at <code>&#91;&#91;media:docs/&lt;scope&gt;/img/&lt;filename&gt;&#93;&#93;</code>
- imports downloadable files as wrapper Markdown docs pointing at <code>&#91;&#91;media:docs/&lt;scope&gt;/files/&lt;filename&gt;&#93;&#93;</code>
- extracts Markdown-image-form inline raster data URLs from HTML and Markdown imports into generated staged media files under `var/docs/import-staging/`
- escapes literal pipe characters from source text so mathematical notation such as `I(X;Y|Z)` does not become an accidental Markdown table
- converts plain-text `http://` and `https://` URLs in prose into Markdown autolinks while leaving existing anchors and code/preformatted text alone
- applies the same SVG safety rules to HTML inline SVG and standalone SVG files
- validates the generated Markdown through the repo's Jekyll renderer helper before returning success
- supports the prompt/meta include toggle already defined by the import spec for HTML imports
- derives the proposed `doc_id` and new Markdown filename stem from the staged source filename, not from the imported document title
- derives Markdown import titles from the first `# H1` when present, then falls back to the staged filename
- derives replacement `doc_id` values from `replacement_doc_id` when the initial staged filename stem collides
- keeps `replacement_title` as a compatibility fallback for older callers
- creates a new Markdown source doc immediately when the generated import target does not collide
- new imported docs write `added_date` and `last_updated` to the current minute in `YYYY-MM-DD HH:MM` form
- new Studio imports write `published: true`, `viewable: true`
- new Analysis imports write `published: true`, `viewable: false`
- new Library imports write `published: true`, `viewable: false`
- preserves blank `parent_id` and appends the new imported doc at the end of the root-level `sort_order`
- reports `media_plan` for standalone image and file-media imports, including the expected media path and generated media token
- reports `media_plans` for extracted inline raster images, including staged filenames, expected media paths, generated media tokens, MIME type, and decoded byte sizes
- reports collision details when the generated import target already matches an existing `doc_id` or source filename stem
- asks browser callers to provide `replacement_doc_id` for normal collision recovery
- requires both `overwrite_doc_id` and `confirm_overwrite: true` before overwriting an existing doc through the low-level overwrite path
- the Studio filename-conflict modal uses `overwrite_doc_id` plus `confirm_overwrite: true` for its explicit Replace action
- preserves the overwritten doc's `doc_id`, filename, `added_date`, `parent_id`, `sort_order`, and existing `published`/`viewable` state
- refreshes the overwritten doc's `last_updated` to the current minute
- creates an import-specific backup before overwrite using a light-touch same-day replacement rule
- writes decoded inline raster media files only during create or overwrite, not during preview-only responses
- `preview_only: true` forces a non-writing preview response even when the server is not running with `--dry-run`
- successful create/overwrite writes rebuild targeted same-scope docs payloads and run targeted docs-search updates for affected ids

`POST /docs/import-html` remains a compatibility alias for older callers through route dispatch and delegates to the same source import handler.

`POST /docs/rebuild` expects:

```json
{
  "scope": "studio"
}
```

Rebuild behavior:

- `scope` must be one of the configured scope ids in `docs-viewer/config/scopes/docs_scopes.json`
- rebuilds generated docs payloads for the requested scope
- rebuilds the docs-search artifact for the requested scope
- includes `docs` and `diagnostics` objects alongside the existing `ok`, `steps`, and `search` keys
- `docs` reports the docs payload rebuild mode, selected doc ids, and the reason for targeted mode or full fallback
- `diagnostics.docs` is parsed from the docs builder diagnostics line and reports source files scanned, emitted docs, changed/removed generated payload counts, semantic-reference changed/removed counts, warning count, warning messages, and elapsed seconds
- `diagnostics.search` reports the search mode, affected ids for targeted updates, and any parsed changed/removed/unchanged/write counts exposed by the search builder output
- each row in `steps` keeps the existing `command`, `returncode`, `stdout`, and `stderr` fields and now also reports `elapsed_seconds`
- is intended for local manage mode rather than the public hosted site

`POST /docs/broken-links` expects:

```json
{
  "scope": "studio"
}
```

Broken-links behavior:

- `scope` must be `studio` or `library`
- runs the shared docs broken-links audit for that scope
- reports missing target issues only
- does not write source docs or generated outputs
- is intended for the Studio audit page and terminal-backed local maintenance
