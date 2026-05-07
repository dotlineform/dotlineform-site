---
doc_id: user-guide-docs-html-import
title: "Docs Import"
added_date: 2026-04-24
last_updated: 2026-05-07
parent_id: user-guide
sort_order: 20
---
# Docs Import

Use this page when you have a staged source file that should become a Library, Analysis, or Studio docs source doc.

The Studio route is:

- `/studio/docs-import/`

## Before You Start

Put the original source file in:

- `var/docs/import-staging/`

This staging directory is repo-local and untracked, so it is a practical place to keep the original export nearby while you test imports.

Staged Markdown files should not include predefined front matter.
The importer creates or preserves the normal Docs Viewer front matter when it writes the target source doc.

For image and downloadable file imports, copy the media file to R2 manually after import.
The importer creates the wrapper Markdown and reports the expected R2 key, but it does not upload media.
For inline raster images extracted from HTML or Markdown data URLs, copy the generated staged image file to R2 after import.

## What The Page Does

The import page:

- lists supported staged files from `var/docs/import-staging/`
- lets you choose whether the imported doc should publish into `library`, `analysis`, or `studio`
- optionally keeps clearly identifiable prompt/meta blocks for HTML imports
- converts HTML into a best-attempt Markdown source doc
- imports staged Markdown as the source body without HTML conversion
- imports `.txt` files as plain Markdown prose and converts plain URLs to autolinks
- imports standalone `.svg` files as wrapper docs with sanitized inline SVG
- imports raster images as wrapper docs that point at `docs/<scope>/img/<filename>` R2 media
- imports supported downloadable files as wrapper docs that point at `docs/<scope>/files/<filename>` R2 media
- extracts Markdown-image-form inline raster data URLs from HTML and Markdown imports into generated staged media files
- keeps literal pipe characters in source text as text, including mathematical notation such as `I(X;Y|Z)`
- validates the generated Markdown through the current Jekyll docs renderer before write success
- writes a new doc immediately when the target is free
- prompts for a replacement title when the staged filename stem matches an existing doc target

## Basic Workflow

1. Open `/studio/docs-import/`.
2. Choose the staged file.
3. Choose the publish scope:
   - `library` for the public Library viewer
   - `analysis` for the public Analysis viewer
   - `studio` for the Studio docs viewer
4. For HTML files, decide whether to include obvious prompt/meta blocks.
5. Click `Import`.

If the generated import target does not already exist, the importer writes the new Markdown source doc immediately.
The new source doc's `doc_id` and Markdown filename come from the staged source filename stem.
HTML imports preserve the imported HTML title.
Markdown imports use the first `# H1` as the title when present and otherwise humanize the staged filename stem.
Text, SVG, image, and file-media imports humanize the staged filename stem unless the source format contains a better title.

New `library` and `analysis` imports use the same default import behavior: they are generated and opened for review through manage-mode viewer links before becoming normal public tree items.

## Prompt / Meta Option

When `Include obvious prompt/meta blocks` is enabled:

- clearly identifiable prompt/meta sections are kept
- they are simplified into wrapped quoted prose

When it is disabled:

- those sections are dropped when the importer can identify them clearly

This option is hidden for non-HTML files because those formats do not use the HTML prompt/meta detector.
If you are unsure for HTML, start with the option off and only enable it when the prompt/meta content is part of the document you actually want to keep.

## Duplicate Filename Behavior

If the generated import target already matches an existing doc:

- the page shows a warning naming the existing target
- nothing is written yet
- the page prompts for a replacement title seeded with the current imported title
- the edited title is used to generate a new `doc_id`
- the importer checks the new `doc_id` again before writing

Example:

- staged file: `diagram.svg`
- existing source doc: `diagram.md`
- prompt value: `Diagram`
- user edits to: `Diagram 2`
- imported doc: `diagram-2.md`

Low-level overwrite support remains available to the local service for explicit callers, but the Studio page treats filename collisions as a rename prompt rather than as a normal overwrite flow.

## Media Imports

Raster image wrappers use:

- <code>&#91;&#91;media:docs/&lt;scope&gt;/img/&lt;filename&gt;&#93;&#93;</code>

Downloadable file wrappers use:

- <code>&#91;&#91;media:docs/&lt;scope&gt;/files/&lt;filename&gt;&#93;&#93;</code>

Those tokens resolve against `_config.yml` `media_base` when docs payloads are built.
The import result shows the expected R2 key so you can copy the source file manually to the matching R2 folder.

HTML and Markdown imports also extract inline raster data URLs that appear as Markdown images, such as:

```md
![Diagram](data:image/png;base64,...)
```

The importer writes decoded image files under `var/docs/import-staging/` during the import write.
Generated filenames use the final proposed `doc_id` plus an incrementing suffix, such as:

- `example-doc-image-01.png`
- `example-doc-image-02.jpg`

The generated Markdown points at the matching docs media token and the result panel lists each staged media path, R2 key, and media token.
Copy each generated staged image file to the reported R2 key before expecting the rendered doc to display it.

Supported raster image extensions:

- `.jpg`
- `.jpeg`
- `.png`
- `.webp`
- `.gif`

Supported downloadable file extensions:

- `.pdf`
- `.zip`
- `.csv`
- `.tsv`
- `.json`
- `.jsonl`
- `.docx`
- `.xlsx`
- `.pptx`

## Backup Behavior

Before overwriting through the low-level service, the importer creates an untracked backup under:

- `var/docs/backups/`

## What To Expect In The Result

After a successful import, the page reports:

- whether the operation created or overwrote a doc
- the target scope
- the final `doc_id`
- the imported title
- the original staged source path
- the viewer link for the imported doc
- generated staged media paths for inline raster images
- the expected R2 key and media token for image, file-media, and extracted inline raster imports
- any non-routine conversion warnings

## Route Ready State

The page root `#docsHtmlImportRoot` exposes the shared Studio route-ready contract:

- `data-studio-ready` is `false` during initial config, service, and staged-file checks, then `true` after the initial disabled or interactive state is rendered
- `data-studio-busy` is `true` while an import or confirmed overwrite is running
- `data-studio-mode` is `idle` before import, `confirm` when an overwrite warning is shown, and `result` after a successful import
- `data-studio-service` reports whether the Docs Management Server is available
- `data-studio-record-loaded` is `true` when supported staged files are available

## Current Practical Limits

This importer is intentionally best-effort.

Expect good HTML conversion results for:

- normal prose docs
- headings and lists
- simple tables
- external links
- plain-text `http://` and `https://` URLs, which become clickable autolinks
- inline SVG diagrams
- standalone SVG files, using the same SVG safety rules as HTML inline SVG
- inline raster images that appear as Markdown images with `data:image/<type>;base64,...` targets
- technical notation that needs safe inline HTML such as subscripts

Expect simplified output for:

- presentation-heavy layout wrappers
- interactive disclosure UI such as `details/summary`
- prompt/meta shells
- source images or downloadable files that have not yet been copied to R2

Markdown, text, SVG, image-wrapper, and file-wrapper imports bypass the HTML converter.
They are still validated through the current Jekyll docs renderer before write success.

## Related References

- [User Guide](/docs/?scope=studio&doc=user-guide)
- [Docs Images And Assets](/docs/?scope=studio&doc=user-guide-docs-images)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Studio Ready State Contract Request](/docs/?scope=studio&doc=site-request-studio-ready-state-contract)
