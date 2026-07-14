---
doc_id: user-guide-docs-html-import
title: Docs Import
added_date: 2026-04-24
last_updated: 2026-07-14
parent_id: docs-viewer
viewable: true
---
# Docs Import

Use this page when you have a staged source file that should become a Library, Analysis, or Studio docs source doc.

The import workflow is owned by Docs Viewer management.
Open it from `/docs/?scope=<scope>` with the icon-only `Import` toolbar action or `Actions` > `Import`.

The import UI runs directly inside the Docs Viewer management modal.
There is no separate Studio Docs Import route.

## Before You Start

Put the original source file in the shared import drop-zone:

- `$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-staging/`

The path is resolved from `DOTLINEFORM_PROJECTS_BASE_DIR` through the shared Data Sharing workspace configuration. It is user-owned staging outside the repository and is shared by all supported import formats.
For Markdown package imports, copy the whole exported folder as a direct child of this staging directory.

Staged Markdown files should not include predefined front matter.
The importer creates or preserves the normal Docs Viewer front matter when it writes the target source doc.

Media handling follows the selected scope's configured storage mode.
Public Library, Analysis, and Moments imports preflight and upload record-owned media to R2 before committing the Markdown source.
Repo-backed local scopes copy media beside their docs source, and external-local scopes copy media under the external Docs Viewer workspace.
Only `staging_manual` requires you to copy staged media after import.
For Markdown package imports, package images are converted to 800px-max WebP outputs and package attachments keep readable generated filenames before the configured storage action runs.

For interactive HTML widgets, test a standalone HTML file in a browser first.
Add `<meta name="dlf:docs-import-role" content="interactive-html">` to the file.
Role-marked interactive HTML files are copied into the current scope's repo-local interactive assets during any normal source import.
The source Markdown is not edited automatically; add an <code>&#91;&#91;interactive-html:example-widget.html&#93;&#93;</code> token yourself where the iframe should appear.

## What The Modal Does

The import modal:

- refreshes supported staged files from the shared import drop-zone every time it opens
- shows staged files in a visible list of about ten rows
- accepts one staged file or reviewed collection at a time; multi-file selection is not currently exposed
- lets you choose any configured docs scope
- keeps `Tab` and `Shift+Tab` focus inside the open modal
- optionally keeps clearly identifiable prompt/meta blocks for HTML imports
- converts HTML into a best-attempt Markdown source doc
- imports staged Markdown as the source body without HTML conversion
- imports staged Markdown package folders as one Markdown source doc plus planned image and attachment media
- imports `.txt` files as plain Markdown prose and converts plain URLs to autolinks
- imports standalone `.svg` files as wrapper docs with sanitized inline SVG
- imports raster images as wrapper docs that point at the scope-owned image destination
- imports supported downloadable files as wrapper docs that point at the scope-owned file destination
- recognizes trusted returned Data Sharing JSON/JSONL as complete reviewed-document collections before generic file fallback
- extracts Markdown-image-form inline raster data URLs from HTML and Markdown imports into generated staged media files
- hides role-marked interactive HTML files from the staged file picker and copies each one into `site/assets/docs/interactive/<scope>/` for manual iframe-token embedding
- keeps literal pipe characters in source text as text, including mathematical notation such as `I(X;Y|Z)`
- validates the generated Markdown through the shared Python Docs Viewer Markdown renderer before write success
- writes a new doc immediately when the target is free
- opens a filename-conflict modal when the staged filename stem matches an existing doc target

## Basic Workflow

1. Open `/docs/?scope=library&import=1` or the matching Docs Viewer management scope.
2. Click the icon-only `Import` toolbar action, or choose `Actions` > `Import`.
3. Choose the staged file.
4. Confirm or change the publish scope:
   - `library` for the public Library viewer
   - `analysis` for the public Analysis viewer
   - `studio` for the Studio docs viewer
5. For HTML files, decide whether to include obvious prompt/meta blocks.
6. Click `Import`.

If the generated import target does not already exist, the importer writes the new Markdown source doc immediately.
After a successful import, Docs Viewer refreshes the target index and selects the imported document. The terminal result remains in the modal until you click `Close`; an import into another scope navigates directly to that scope and document.
The new source doc's `doc_id` and Markdown filename come from the staged source filename stem.
HTML imports preserve the imported HTML title.
Markdown imports use the first `# H1` as the title when present and otherwise humanize the staged filename stem.
Text, SVG, image, and file-media imports humanize the staged filename stem unless the source format contains a better title.

New imports into public scopes such as `library`, `analysis`, and `moments` use the same default behavior: they are created with `viewable: false`, generated, and opened for review through manage-mode viewer links before becoming normal public tree items.

## Reviewed-Package Collection Workflow

A validated package in Docs Review can open managed Docs Import with its matching staged JSON/JSONL collection preselected. The handoff carries only the safe package identity; Docs Import resolves it against the server-listed staged file. If that staged file has been deleted, the persistent review remains readable but import is unavailable.

Collection import always plans the complete package before writing:

1. Choose the target scope and review every package record, parent mapping, warning, and blocker.
2. Resolve document collisions one at a time with `Overwrite`, `Skip`, or `Cancel`.
3. Leave `Apply to all` unchecked to decide only the current collision, or check it to apply the chosen action to remaining document collisions.
4. Resolve invalid-front-matter or unsupported-content records individually with `Skip` or `Cancel`; an optional note may accompany a skipped invalid record.
5. Review the final read-only plan and confirm apply.

The collection workflow does not offer replacement ids, `Create as new`, ordinary per-record selection, or automatic overwrite. `Apply to all` does not affect invalid-record decisions or authorize media and attachment overwrites. `Cancel` is available before apply and writes nothing; once confirmed apply begins, the synchronous operation runs to completion or failure.

Existing target parents are reused. A missing parent is created only when the package supplies a complete explicit document record for that identity; missing undeclared parents and hierarchy cycles block confirmation. Multi-level supplied parent chains are supported. Hierarchy-only existing records preserve their current body and unrelated front matter, while a new structural record without supplied content receives an empty body.

Apply rereads the immutable staged package and recomputes target state. A changed collision target, target identity, parent resolution, hierarchy state, blocker state, or package identity returns a refreshed plan without writes. Successful writes run in package order. If a source write fails, earlier writes remain and later records are reported as not attempted; there is no collection rollback. Generation failure is reported separately and does not undo successful source writes.

The result groups records as created, overwritten, skipped, failed, or not attempted and includes generation status, warnings, manual-copy instructions, and a marker-rooted Markdown report path under `import-staging/results/`.
While an import preview or write request is active, the modal disables `Cancel`; closing the browser page remains the local recovery path for an unexpectedly hung request. After a terminal single-source or collection result, the modal replaces `Import` and `Cancel` with one `Close` button. Errors and pre-apply cancellations retain the normal controls so the operation can be corrected or retried; reopening the modal restores its normal `Import` and `Cancel` actions.

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

For `r2_upload` and `staging_manual`, raster image wrappers use:

- <code>&#91;&#91;media:docs/&lt;scope&gt;/img/&lt;filename&gt;&#93;&#93;</code>

For those same modes, downloadable file wrappers use:

- <code>&#91;&#91;media:docs/&lt;scope&gt;/files/&lt;filename&gt;&#93;&#93;</code>

For `r2_upload` and `staging_manual`, those tokens resolve against `_config.yml` `media_base` when docs payloads are built.
For `repo_assets` and `external_assets`, the importer writes the configured `/docs/media/<scope>/...` local-service link instead.

HTML and Markdown imports also extract inline raster data URLs that appear as Markdown images, such as:

```md
![Diagram](data:image/png;base64,...)
```

Generated filenames use the final proposed `doc_id` plus an incrementing suffix, such as:

- `example-doc-image-01.png`
- `example-doc-image-02.jpg`

The generated Markdown points at the matching scope-owned media link.
The importer publishes R2 media before the source write, copies local media automatically, or reports a manual-copy action according to the scope's storage mode.

## Markdown Package Imports

Use a Markdown package import for folder exports such as Apple Notes Markdown export.

The package must be a direct child folder under the shared import drop-zone and must contain exactly one `.md` or `.markdown` file.
Local image and attachment links are resolved relative to that Markdown file and must remain inside the package folder.

Package image behavior:

- supported source image extensions are `.jpg`, `.jpeg`, `.png`, `.webp`, and `.gif`
- generated image outputs are always `.webp`
- images wider than 800px are downscaled to 800px wide
- smaller images are not upscaled
- animated images are rejected instead of being silently flattened
- generated filenames use `<doc_id>-image-NN.webp`
- generated Markdown uses readable alt/title text such as `<doc_id> image NN`

Package attachment behavior:

- supported attachment extensions match the downloadable file allowlist
- attachments are copied unchanged
- generated filenames use `<doc_id>-attachment-NN.<ext>`

The generated Markdown points at docs media links for each resolved package image or attachment.
The result panel lists every planned media item, including original package-relative paths and image conversion details.

## Interactive HTML Assets

An import can carry one or more staged interactive HTML assets:

- selected staged source: `coincidence-salience.html`
- role-marked asset: `Coincidence Widget.html`
- copied asset: `site/assets/docs/interactive/<scope>/coincidence-widget.html`
- Markdown token to add manually: <code>&#91;&#91;interactive-html:coincidence-widget.html&#93;&#93;</code>

The interactive file must be a complete standalone HTML document and must include this metadata:

```html
<meta name="dlf:docs-import-role" content="interactive-html">
```

Role-marked files are not listed as selectable staged sources.
During a normal source import, the importer copies every role-marked HTML file in the shared import drop-zone into the selected scope's repo-local interactive assets.
The target filename is the slugified original filename stem plus `.html`.
The import result lists each copied interactive file as another two-column result row with the slugified stem and `script file`, but it does not insert iframe tokens into the generated source doc.
This keeps the import conversion unchanged and leaves placement as an explicit source edit.
You can add multiple interactive HTML tokens manually when a document uses multiple interactive assets.
When the default iframe height does not fit the asset, add a measured pixel height to the token, for example <code>&#91;&#91;interactive-html:coincidence-widget.html height=546&#93;&#93;</code>.

If any target interactive asset already exists, the importer asks for overwrite confirmation before replacing it.
Cancel leaves the existing asset unchanged.

Template: `site/assets/docs/interactive/template.html`

## Recovery Behavior

The importer no longer creates local backup bundles before source writes.
Recover overwritten source through Git history, host/filesystem backups, or an explicit manual copy made before import.

## What To Expect In The Result

After a successful import, the page reports:

- whether the operation created or overwrote a doc
- the target scope
- the final `doc_id`
- the imported title
- the original staged source path
- the viewer link for the imported doc
- safe media class, filename, status, and link details for image, file-media, extracted inline raster, and Markdown package media imports
- converted WebP image outputs and copied package attachments
- copied interactive HTML script files as result rows labelled `script file`
- any non-routine conversion warnings

## Route Ready State

The page root `#docsHtmlImportRoot` participates in [Route Ready State](/docs/?scope=studio&doc=route-ready-state).
It currently uses Studio-style attributes inside the Docs Viewer bundle.
Route-specific details:

- import and confirmed overwrite commands set route busy
- `data-studio-mode` is `idle` before import, `confirm` when an overwrite warning is shown, and `result` after a successful import
- `data-studio-service` reports whether the Docs Management Service is available
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
They are still validated through the shared Python Docs Viewer Markdown renderer before write success.

## Related References

- [Docs Images And Assets](/docs/?scope=studio&doc=user-guide-docs-images)
- [Docs Management Service](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Docs Import Source Registry](/docs/?scope=studio&doc=docs-viewer-import-source-registry-spec)
