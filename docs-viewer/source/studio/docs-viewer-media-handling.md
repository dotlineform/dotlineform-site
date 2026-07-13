---
doc_id: docs-viewer-media-handling
title: Media Handling
added_date: 2026-05-14
last_updated: 2026-07-13
parent_id: docs-viewer
viewable: true
---
# Docs Viewer Media Handling

This document records how Docs Viewer media is represented, imported, and committed to the active scope's configured media store.

## Boundaries

Docs Viewer media handling covers:

- source-file imports staged under `$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-staging/`
- wrapper docs for standalone images and downloadable files
- inline raster extraction from HTML and Markdown imports
- folder-based Markdown package imports with local images and attachments
- sanitized inline SVG preservation
- scope-specific media path generation
- automatic R2 publication for public scopes
- repo-backed and external-local materialization
- safe publication/materialization results shown by Docs Import

It does not cover:

- raster-to-SVG conversion
- catalogue media generation
- automatic remote deletion, cache versioning, or a Docs asset registry
- interactive HTML, which retains its separate sandbox contract

Reviewed Data Sharing document collections reuse the existing inline raster data-URL path. Docs Import plans, retargets, decodes, and materializes supported PNG, JPEG, WebP, and GIF data URLs from normalized collection records. Non-embedded package assets require an explicit import mapping and are not automatically promoted from the Data Sharing workspace.

Collection asset handling is best effort after trusted intake. An unsupported, missing, unauthorized-collision, or failed asset operation preserves the returned source reference, warns, and allows the document and later records to continue. Document-level `Overwrite` and `Apply to all` never authorize asset overwrite. Unsafe paths, containment or symlink escapes, size failures, and execution-safety failures remain blocking and are never attempted.
For `r2_upload`, a planned record-owned media publication is stricter: a remote conflict or failure blocks that record's source write so Docs Import never commits a newly generated token to media it did not publish successfully.

## Scope Configuration

Each Docs Viewer scope defines its media conventions in `docs-viewer/config/scopes/docs_scopes.json`.

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
| `moments` | `docs/moments` |

The configured prefix determines the logical media path used in generated Markdown and result payloads.

## Storage Modes

Docs Import recognizes four storage modes:

| Mode | Current behavior |
| --- | --- |
| `staging_manual` | Import writes source docs and reports media paths/tokens. The user manually copies staged media to the configured media store. |
| `repo_assets` | Import copies media into an allowlisted repo-owned root and writes its configured local/public link. Current local scopes use `docs-viewer/source/<scope>/media/`. |
| `r2_upload` | Public-scope import preflights and uploads the complete record-owned media set to R2 before committing the Markdown source. |
| `external_assets` | External-local import copies media under `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/media/<scope>/` and writes a confined local-service link. |

Library, Analysis, and Moments use `r2_upload`.
Studio and temporary repo-backed scopes use `repo_assets` beside their docs source.
External-local scopes must use `external_assets`; config validation rejects R2 and repo destinations for them.
`staging_manual` remains available for portable/manual workflows.

## Media Tokens

For `staging_manual` and `r2_upload`, Docs Import writes logical media tokens in Markdown:

<pre><code>![Example](&#91;&#91;media:docs/library/img/example.png&#93;&#93;)
[Download Example](&#91;&#91;media:docs/library/files/example.pdf&#93;&#93;)</code></pre>

Those tokens resolve during docs payload generation against the site's configured media base.
In `r2_upload`, the same token is committed only after the remote object set succeeds.
In `staging_manual`, the importer reports the token and expected media path for manual copying.

For `repo_assets`, Docs Import uses the configured public repo asset path instead of a <code>&#91;&#91;media:...&#93;&#93;</code> token.
Current local scopes use links such as `/docs/media/studio/img/example.png`.

For `external_assets`, Docs Import uses `/docs/media/<scope>/<class>/<filename>`.
The local Docs Viewer service resolves that route only through the scope's derived media root, rejects traversal and symlink escape, sends `nosniff`, and does not serve interactive HTML through this ordinary media route.

## Staging Folder

All Docs Import source formats are staged under:

- `$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-staging/`

This is the W0-configured, user-owned shared import drop-zone outside the repository.
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

Markdown image media tokens may include optional positive-integer dimensions:

<pre><code>![Example](&#91;&#91;media:docs/library/img/example.png width=800 height=600&#93;&#93;)</code></pre>

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

`manual_copy_required` is true only for `staging_manual`.

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

If a planned filename already exists in the shared import drop-zone, the importer uses the next available increment.
No hash suffix is used for the current implementation.

During create or overwrite, the service materializes the decoded inline raster files.
For `staging_manual`, decoded files are written under the shared import drop-zone.
For `repo_assets` and `external_assets`, decoded files are written to the confined configured/derived media root.
For `r2_upload`, decoded files are prepared in a temporary directory and uploaded as part of the record's complete set.

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

For `staging_manual`, converted images and copied attachments are materialized under the shared import drop-zone with the generated readable filenames.
For `repo_assets` and `external_assets`, they are written into the scope-owned local target.
For `r2_upload`, conversion completes before the complete remote preflight; successful remote publication leaves no repo-local copy.
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

For `r2_upload`, result rows report the safe filename/class status without object keys, checksums, ETags, credentials, signed URLs, or absolute paths.

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
It returns the proposed Markdown, media plan metadata, collision information, warnings.

Write happens only on create or confirmed overwrite.
At write time, the service:

- prepares and validates the complete record-owned media plan
- materializes local media or publishes R2 media before the source write
- stops without writing the Markdown source when required R2 publication is blocked or fails
- creates or overwrites the Markdown source doc after the required media boundary succeeds
- rebuilds same-scope docs payloads and targeted docs-search entries after successful source writes
- relies on Git history, host/filesystem backups, or explicit manual copies for source recovery

Inline media extraction plans are checked against the staged source before materialization.
If the source no longer matches the preview plan, the write fails rather than silently writing mismatched media.

## Practical Workflow

For a normal media import:

1. Place the source file in `$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-staging/`.
2. Open `/docs/?scope=<scope>&import=1`.
3. Import the source file.
4. Review the result panel's media plan and apply the import.
5. For `r2_upload`, the service preflights/uploads automatically before it commits the source.
6. For `repo_assets` or `external_assets`, the service materializes the asset automatically.
7. Copy a staged file manually only when `manual_copy_required` is true.

For HTML or Markdown with embedded raster data URLs, the same workflow applies, except the import write creates the staged decoded image files for you.
For Markdown package imports, copy the whole package folder under the shared import drop-zone and select the package folder in the import modal.

## Related References

- [Docs Import](/docs/?scope=studio&doc=user-guide-docs-html-import)
- [Docs Viewer Import Source Registry Spec](/docs/?scope=studio&doc=docs-viewer-import-source-registry-spec)
- [Docs Management Service](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Docs Viewer Portable Setup](/docs/?scope=studio&doc=docs-viewer-portable-setup)
