---
doc_id: docs-viewer-media-handling
title: Docs Viewer Media Handling
added_date: 2026-05-14
last_updated: 2026-05-18
parent_id: docs-viewer
sort_order: 5000
---
# Docs Viewer Media Handling

This document records how Docs Viewer media is represented, imported, staged, and handed off to the configured media store.

It consolidates the durable implementation notes from [Docs HTML Inline Raster Media Request](/docs/?scope=studio&doc=site-request-docs-html-inline-raster-media) with the normal Docs Import media workflow.

## Boundaries

Docs Viewer media handling covers:

- source-file imports staged under `var/docs/import-staging/`
- wrapper docs for standalone images and downloadable files
- inline raster extraction from HTML and Markdown imports
- folder-based Markdown package imports with local images and attachments
- sanitized inline SVG preservation
- scope-specific media path generation
- media-copy handoff information shown in the Docs Import result

It does not cover:

- automatic remote upload
- raster-to-SVG conversion
- catalogue media generation
- Library returned-package Data Sharing imports under `var/studio/data-sharing/`
- browser runtime asset loading outside generated Docs Viewer content

## Scope Configuration

Each Docs Viewer scope defines its media conventions in `scripts/docs/docs_scopes.json`.

Important fields:

- `media_path_prefix`: logical docs media prefix, such as `docs/library`
- `import_media_storage.storage_mode`: write and handoff behavior for imported media
- `import_media_storage.repo_assets_path_prefix`: repo-local asset root used by `repo_assets`
- `import_media_storage.repo_assets_public_path_prefix`: public URL prefix used by `repo_assets`

Current scope prefixes are:

| Scope | `media_path_prefix` |
| --- | --- |
| `studio` | `docs/studio` |
| `library` | `docs/library` |
| `analysis` | `docs/analysis` |

The configured prefix determines the logical media path used in generated Markdown and result payloads.

## Storage Modes

Docs Import currently recognizes three storage modes:

| Mode | Current behavior |
| --- | --- |
| `staging_manual` | Import writes source docs and reports media paths/tokens. The user manually copies staged media to the configured media store. |
| `repo_assets` | Import may copy source media or decoded inline media into the configured repo asset prefix after allowlist checks. Generated Markdown uses the configured public asset path. |
| `r2_upload` | Reserved in config, but not operational. |

The current site scopes use `staging_manual`.
Portable installs without a remote media workflow can choose `repo_assets` when they want imported media to land inside the repo under `assets/docs/<scope>/`.

## Media Tokens

For `staging_manual`, Docs Import writes logical media tokens in Markdown:

<pre><code>![Example](&#91;&#91;media:docs/library/img/example.png&#93;&#93;)
[Download Example](&#91;&#91;media:docs/library/files/example.pdf&#93;&#93;)</code></pre>

Those tokens resolve during docs payload generation against the site's configured media base.
The importer reports the token and expected media path, but it does not upload or publish the binary file.

For `repo_assets`, Docs Import uses the configured public repo asset path instead of a <code>&#91;&#91;media:...&#93;&#93;</code> token.

## Staging Folder

All Docs Import source formats are staged under:

- `var/docs/import-staging/`

This folder is local and untracked.
It can contain original source files, standalone media import files, generated inline raster image files, and direct child Markdown package folders.

The importer requires staged filenames to resolve inside that directory.
Nested paths, path traversal, unsupported extensions, and unsafe media filenames are rejected before conversion or write.
Markdown package folders must be direct children of the staging folder, and package-local links must resolve inside the package.

## Standalone Image Imports

Standalone raster images create wrapper Markdown docs.

Supported extensions:

- `.jpg`
- `.jpeg`
- `.png`
- `.webp`
- `.gif`

The wrapper body uses the `img` media class:

<pre><code># Example

![Example](&#91;&#91;media:docs/library/img/example.png&#93;&#93;)</code></pre>

The import response uses a singular `media_plan` for standalone image imports.
That plan includes:

- `storage_mode`
- `manual_copy_required`
- `source_path`
- `media_path`
- `media_token`
- `media_link`
- `title`
- `repo_asset_path`
- `public_path`

When `manual_copy_required` is true, copy the staged source image to the reported media path before expecting the rendered doc to display it.

## Downloadable File Imports

Downloadable files create wrapper Markdown docs with a single download link.

Supported extensions:

- `.pdf`
- `.zip`
- `.csv`
- `.tsv`
- `.json`
- `.jsonl`
- `.docx`
- `.xlsx`
- `.pptx`

The wrapper body uses the `files` media class:

<pre><code># Example

[Download Example](&#91;&#91;media:docs/library/files/example.pdf&#93;&#93;)</code></pre>

The import response uses the same singular `media_plan` shape as standalone image imports.

## Inline Raster Extraction

HTML and Markdown imports can extract raster images embedded as Markdown image data URLs:

```md
![Diagram](data:image/png;base64,...)
```

Supported inline raster subtypes are:

- PNG
- JPEG
- WebP
- GIF

During preview, the importer:

- detects Markdown-image-form raster data URLs
- plans generated filenames from the proposed `doc_id`
- replaces each data URL in the Markdown preview with a configured media link
- reports a plural `media_plans` array

Generated filenames are deterministic and readable:

- `<doc_id>-image-01.png`
- `<doc_id>-image-02.jpg`

If a planned filename already exists in `var/docs/import-staging/`, the importer uses the next available increment.
No hash suffix is used for the current implementation.

During create or overwrite, the service materializes the decoded inline raster files.
For `staging_manual`, the decoded files are written under `var/docs/import-staging/`.
For `repo_assets`, decoded files may be written to the configured repo asset path after allowlist checks.

If a collision replacement changes the final `doc_id`, the service retargets inline media plans before write so filenames, media paths, and Markdown links match the final doc id.

## Markdown Package Media

Markdown package imports are directory-backed imports for exports such as Apple Notes Markdown folders.
The package must contain exactly one `.md` or `.markdown` source file.

During preview, the importer:

- resolves local Markdown image and file links relative to the package Markdown file
- leaves external URLs, anchors, mail links, unresolved links, and unsupported file types unchanged with warnings where useful
- rewrites supported local image links to generated docs media links under `img`
- rewrites supported local attachment links to generated docs media links under `files`
- reports every planned image and attachment in `media_plans`
- replaces opaque package image alt text with readable `<doc_id> image NN` text and writes the same value as the Markdown image title

Generated package image filenames use the final proposed `doc_id` plus an incrementing suffix and always end in `.webp`:

- `<doc_id>-image-01.webp`
- `<doc_id>-image-02.webp`

Generated package attachment filenames use:

- `<doc_id>-attachment-01.<ext>`
- `<doc_id>-attachment-02.<ext>`

During create or overwrite, package images are converted with Pillow to WebP.
Images wider than 800px are downscaled to a maximum width of 800px; smaller images are not upscaled.
Attachments are copied unchanged.

For `staging_manual`, converted images and copied attachments are materialized under `var/docs/import-staging/` with the generated readable filenames.
For `repo_assets`, they are written into the configured repo asset path.
Animated image conversion is rejected rather than silently flattening animation.

## Inline Raster Handoff

For each extracted inline raster image, the result panel reports:

- generated staged media filename
- expected media path
- media token or public media link
- MIME type
- decoded byte size
- warning text when manual copy is required

Markdown package image and attachment plans use the same result payload shape, with `kind`, `source_original_path`, and image `conversion` metadata added.

For `staging_manual`, copy each generated staged image file to the reported media path before expecting the rendered doc to display it.
This keeps imported Markdown and generated docs JSON free of long base64 payloads while preserving the original raster bytes.

## SVG Handling

SVG is not treated as raster media.

HTML imports may preserve safe inline SVG as HTML inside the generated Markdown.
Standalone `.svg` imports create wrapper docs with sanitized inline SVG.

SVG safety rules include:

- strip `<script>` content
- strip `on*` event-handler attributes
- warn about external SVG references
- preserve safe `<title>` and `<desc>` content when available

Inline SVG stays in the source doc because it remains readable as markup and does not require the raster media handoff workflow.

## Preview And Write Semantics

Preview does not write source docs.
It returns the proposed Markdown, media plan metadata, collision information, warnings, and Jekyll validation status.

Write happens only on create or confirmed overwrite.
At write time, the service:

- creates or overwrites the Markdown source doc
- materializes decoded inline raster media
- copies source media only when the configured storage mode supports repo-asset writes
- creates operation backups before source overwrite
- rebuilds same-scope docs payloads and targeted docs-search entries after successful source writes

Inline media extraction plans are checked against the staged source before materialization.
If the source no longer matches the preview plan, the write fails rather than silently writing mismatched media.

## Practical Workflow

For a normal media import:

1. Place the source file in `var/docs/import-staging/`.
2. Open `/docs/?scope=<scope>&mode=manage&import=1`.
3. Import the source file.
4. Review the result panel's media plan.
5. Copy any staged media file to the reported media path when `manual_copy_required` is true.
6. Rebuild or refresh docs payloads through the normal management workflow if you changed media availability outside the import write.

For HTML or Markdown with embedded raster data URLs, the same workflow applies, except the import write creates the staged decoded image files for you.
For Markdown package imports, copy the whole package folder under `var/docs/import-staging/` and select the package folder in the import modal.

## Related References

- [Docs Import](/docs/?scope=studio&doc=user-guide-docs-html-import)
- [Docs Viewer Import Source Registry Spec](/docs/?scope=studio&doc=docs-viewer-import-source-registry-spec)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Docs Viewer Portable Setup](/docs/?scope=studio&doc=docs-viewer-portable-setup)
- [Docs HTML Inline Raster Media Request](/docs/?scope=studio&doc=site-request-docs-html-inline-raster-media)
