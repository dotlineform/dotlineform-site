---
doc_id: user-guide-docs-html-import
title: "Docs Import"
added_date: 2026-04-24
last_updated: "2026-05-16 13:35"
parent_id: user-guide
sort_order: 20
---
# Docs Import

Use this page when you have a staged source file that should become a Library, Analysis, or Studio docs source doc.

The import workflow is owned by Docs Viewer management.
Open it from `/docs/?scope=<scope>&mode=manage` with the `Import` toolbar action.

The import UI runs directly inside the Docs Viewer management modal.
There is no separate Studio Docs Import route.

## Before You Start

Put the original source file in:

- `var/docs/import-staging/`

This staging directory is repo-local and untracked, so it is a practical place to keep the original export nearby while you test imports.

Staged Markdown files should not include predefined front matter.
The importer creates or preserves the normal Docs Viewer front matter when it writes the target source doc.

For image and downloadable file imports, copy the media file to the configured media store manually after import.
The importer creates the wrapper Markdown and reports the expected media path, but it does not upload media.
For inline raster images extracted from HTML or Markdown data URLs, copy the generated staged image file after import.

For interactive HTML widgets, test a standalone HTML file in a browser first.
If the selected staged source is `example.html`, an optional `example-interactive.html` sidecar in the same staging folder is copied into the current scope's repo-local interactive assets during import.
The source Markdown is not edited automatically; add the reported <code>&#91;&#91;interactive-html:example-interactive.html&#93;&#93;</code> token yourself where the iframe should appear.

## What The Modal Does

The import modal:

- lists supported staged files from `var/docs/import-staging/`
- lets you choose any configured docs scope
- optionally keeps clearly identifiable prompt/meta blocks for HTML imports
- converts HTML into a best-attempt Markdown source doc
- imports staged Markdown as the source body without HTML conversion
- imports `.txt` files as plain Markdown prose and converts plain URLs to autolinks
- imports standalone `.svg` files as wrapper docs with sanitized inline SVG
- imports raster images as wrapper docs that point at the configured `<media_path_prefix>/img/<filename>` media path
- imports supported downloadable files as wrapper docs that point at the configured `<media_path_prefix>/files/<filename>` media path
- extracts Markdown-image-form inline raster data URLs from HTML and Markdown imports into generated staged media files
- copies an optional `<staged-stem>-interactive.html` companion into `assets/docs/interactive/<scope>/` for manual iframe-token embedding
- keeps literal pipe characters in source text as text, including mathematical notation such as `I(X;Y|Z)`
- validates the generated Markdown through the current Jekyll docs renderer before write success
- writes a new doc immediately when the target is free
- opens a filename-conflict modal when the staged filename stem matches an existing doc target

## Basic Workflow

1. Open `/docs/?scope=library&mode=manage&import=1` or the matching Docs Viewer management scope.
2. Click `Import`.
3. Choose the staged file.
4. Confirm or change the publish scope:
   - `library` for the public Library viewer
   - `analysis` for the public Analysis viewer
   - `studio` for the Studio docs viewer
5. For HTML files, decide whether to include obvious prompt/meta blocks.
6. Click `Import`.

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

- the page opens a `File already exists` modal naming the existing Markdown filename
- nothing is written yet
- the modal's text input is seeded with the existing `doc_id`
- the edited `doc_id` is used as the new Markdown filename stem
- `Replace` overwrites the existing source file instead of creating a renamed import
- the importer checks the new `doc_id` again before writing

Example:

- staged file: `diagram.svg`
- existing source doc: `diagram.md`
- modal value: `diagram`
- user edits to: `diagram-2`
- imported doc: `diagram-2.md`

Low-level overwrite support remains available to the local service for explicit callers, but the Studio page treats filename collisions as a rename prompt rather than as a normal overwrite flow.
Use `Replace` only when the staged file should intentionally replace the existing source doc at the same filename.

## Media Imports

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

Raster image wrappers use:

- <code>&#91;&#91;media:docs/&lt;scope&gt;/img/&lt;filename&gt;&#93;&#93;</code>

Downloadable file wrappers use:

- <code>&#91;&#91;media:docs/&lt;scope&gt;/files/&lt;filename&gt;&#93;&#93;</code>

Those tokens resolve against `_config.yml` `media_base` when docs payloads are built.
The import result shows the expected media path so you can copy the source file manually to the matching media location.

HTML and Markdown imports also extract inline raster data URLs that appear as Markdown images, such as:

```md
![Diagram](data:image/png;base64,...)
```

The importer writes decoded image files under `var/docs/import-staging/` during the import write.
Generated filenames use the final proposed `doc_id` plus an incrementing suffix, such as:

- `example-doc-image-01.png`
- `example-doc-image-02.jpg`

The generated Markdown points at the matching docs media token and the result panel lists each staged media path, configured media path, and media token.
Copy each generated staged image file to the reported media path before expecting the rendered doc to display it.


## Interactive HTML Companions

An import can carry a same-stem interactive sidecar:

- selected staged source: `coincidence-salience.html`
- optional sidecar: `coincidence-salience-interactive.html`
- copied asset: `assets/docs/interactive/<scope>/coincidence-salience-interactive.html`
- Markdown token to add manually: <code>&#91;&#91;interactive-html:coincidence-salience-interactive.html&#93;&#93;</code>

The companion file must be a complete standalone HTML document.
The importer copies it into the selected scope's repo-local interactive assets and reports the token, but it does not insert the token into the generated source doc.
This keeps the import conversion unchanged and leaves placement as an explicit source edit.

If the target interactive asset already exists, the importer asks for overwrite confirmation before replacing it.
Cancel leaves the existing asset unchanged.

Template: `assets/docs/interactive/template.html`

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
- the expected media path and media token for image, file-media, and extracted inline raster imports
- copied interactive HTML asset path and iframe token when a sidecar is present
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
- source images or downloadable files that have not yet been copied to the configured media store

Markdown, text, SVG, image-wrapper, and file-wrapper imports bypass the HTML converter.
They are still validated through the current Jekyll docs renderer before write success.

## Related References

- [User Guide](/docs/?scope=studio&doc=user-guide)
- [Docs Images And Assets](/docs/?scope=studio&doc=user-guide-docs-images)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Studio Ready State Contract Request](/docs/?scope=studio&doc=site-request-studio-ready-state-contract)
