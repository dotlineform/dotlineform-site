---
draft: false
doc_id: d-20260607-222033-704641
title: Source Editor Scripts
added_date: "2026-06-07 22:20:33"
last_updated: "2026-11-20"
parent_id: d-20260607-222033-647b52
---
# Source editing

Manage opens one exact Working source, keeps one complete Markdown buffer and awaits a fresh rendered document after Save. The browser owns the mounted target, draft, selection and pending files. Services own target confinement, candidate validation, writes and exact generation. [Authoring workflow](../guide/Author_And_Organise_Documents.md) · [Other document mutations](Source_Mutation_Endpoints.md)

## Follow a Save

1. **Open the target.** In the Context collection, open a document and choose **Source editor**. The edit action uses the validated detail target `{collection: "works", doc_id}`. On the collection list itself, the Source action targets its ordinary host. An invalid or loading detail cannot supply a target. The editor captures this identity at mount and retains it for read, Save and Directives.
2. **Load the complete buffer.** `GET /docs/source` resolves the configured owner and reads the exact source. The browser checks that the returned identity matches the mounted document, then sets the text and clean baseline. The rendered report remains mounted behind the editor. Source entry closes a pinned Info panel.
3. **Edit.** Change the Title, Summary or body in the same buffer. Directives edit the captured range. Add/Edit media can retain native Files pending Save. The editor checks a nonblank Title, normalizes newlines and submits the full buffer and only Files referenced by its final text.
4. **Validate, persist and generate.** The service resolves the exact source, parses the candidate, prepares selected media, writes completed bytes before source, and atomically writes changed Markdown. It passes the prepared record, relationship inputs and media effects to exact generation. Generation writes the by-ID document and affected metadata, completes Links and publication handoff, and returns the committed effects.
5. **Show the result.** The management source adapter projects the committed record to Index and retained lists. The editor accepts the returned saved text as clean, including any rewritten media paths. The route owner awaits an exact fresh by-ID read and checks request, target and mode before replacing the rendered payload in the same history entry. Position stays with the document. [Source editor](../../docs-viewer/runtime/js/management/source-editor/source-editor.js) · [Save service](../../docs-viewer/services/docs_management_source_service.py) · [Committed records](../../docs-viewer/runtime/js/management/docs-viewer-management-source-adapter.js) · [Fresh display](../../docs-viewer/runtime/js/shared/docs-viewer-route-workflow.js)

## Target and session

Open **Source editor** from the displayed document's controls. In Manage, Option-clicking an eligible same-reader link also opens Source for that exact target. Catalogue Work authoring belongs to Studio and Regenerate. The mounted Source adapter owns one buffer, its clean baseline, pending Files and a buffer revision that guards modal changes. A modal opened before an intervening edit or editor replacement cannot change the new state. That revision is in memory.

**Return to doc** returns to rendered content. For a collection page, **Return to collection** resolves the configured host and can restore a matching retained caller. Dirty navigation uses the same discard decision for text and pending Files. Cancelling keeps both. While Source is open it hides the underlying rendered content without discarding its report mount. [Management action owner](../../docs-viewer/runtime/js/management/docs-viewer-management.js) · [Reader return](Reader_Discovery_And_Return.md#exact-document-navigation-and-return)

## `GET /docs/source`

Use `doc_id` and add `collection` only for a named document. The response carries `ok`, the target, complete `source_text`, a display-safe `path` and `media_options` for image/file suffixes and upload limits. The mounted editor reuses the options.

Working resolves the exact owner, confines the direct-child Markdown path and checks the immutable front-matter ID against the request. For ordinary documents it also checks membership and parentage in `index-order.json`. Saved Draft and report rules are validated on Save, so an exactly identified source with a readiness or report problem can still be opened for correction. From the exact source the editor loads its own metadata and body together. [Target resolver](../../docs-viewer/services/docs_management_document_target.py)

## Bold

Select source text and use **Bold**, just before **Add date** on the Source toolbar. If the selection contains complete Markdown bold spans, the button removes their paired markers. It skips literal code and spans that cross a selection boundary. This works across table cells and paragraphs. To add bold, select text within one inline region, such as a paragraph, heading or table cell.

The button is disabled with no selection. After a change, Source focuses the editor and selects the edited range again. **Save** persists the edit. [Bold control](../../docs-viewer/runtime/js/management/source-editor/source-editor-bold.js)

## Directives

The menu captures the current adapter, selection and revision before moving focus. Apply serializes into the buffer. The source service handles any later persistence.

| Control | Effect in source |
| --- | --- |
| **Add image** / **Edit image** | When Directives opens, the item reads **Edit image** if the caret is inside an authored image token or the selection covers that token exactly. Edit opens the image dialog with the token’s current fields and the **Image detail** setting for a standalone image. Other selections show **Add image**. [Media intake](Media_And_Asset_Handling.md#add-a-new-image-or-download) · [Image detail](Document_Image_Detail.md) |
| **Add file** | Insert or edit an exact download reference. The editor holds a new File until Save. [Media intake](Media_And_Asset_Handling.md#add-a-new-image-or-download) |
| **Add Media View link** / **Edit Media View link** | When Directives opens, the item reads **Edit Media View link** if the caret is inside an authored Media View token or the selection covers that token exactly. Edit restores its saved fields. Every other selection shows **Add Media View link**. Choose a Work and its destination, then **Image**, **Inline link** or **Hidden**. Selecting a Gallery directly offers Inline link or Hidden. [Catalogue source forms](Document_And_Catalogue_References.md#supported-source-forms) |
| **Insert doc link** | Insert the selected exact document route and escaped literal title. [Picker request](#get-docsdocument-link-targets) |
| **Table options** | Edit the selected table’s column widths, rules, header row, shading, text size and detail view. [Table options](#table-options) |
| **Image detail** | Insert the comment before the selected standalone image. [Image detail](Document_Image_Detail.md) |
| **Insert related links**, **Insert icon**, **Summary** | Insert `[[links|]]`, an editable icon stem, or a standalone `[[summary]]`. [Related Links](Related_Links.md#authoring-decision) · [Icons](Icon_Tokens.md) · [Summary](Builder.md#summary-block) |

[Directives owner](../../docs-viewer/runtime/js/management/source-editor/directive-actions.js)

### Table options

In Source, place the caret anywhere in a standalone Markdown table or select the table, then choose **Directives → Table options**. The dialog opens with the table’s existing settings. For **Relative widths**, enter one positive whole number per column, separated by spaces. Both `20 40 40` and `1 2 2` give the last two columns equal space. A blank field uses automatic widths.

**First row is a header** starts on. Turn it off when the first row contains data. The builder renders that row as ordinary cells in the table body, preserving its text, inline formatting and column widths. In Table Detail it scrolls vertically with the other rows. **Horizontal rules only** keeps the horizontal lines and removes vertical borders, including the outside edges, in either view.

**Shade first column** shades the first cell in each body row, including the first row when the header is off. **Small text** uses the reader’s small type size (0.875rem) for the inline table. Table Detail uses normal body size. Horizontal rules, shading and small text are independent and start off.

Select **Enable detail view** to give the reader an Open button. This enables **Table title**. A blank title uses “Table”. **Apply** updates the comments above this table in the current buffer. Restoring all defaults removes the table options. **Cancel** discards the modal edits. **Save** persists the buffer and rebuilds the document.

For hand editing, place a comment such as `<!-- dotlineform:table horizontal-rules no-header -->` above the table. Include `widths="20:40:40"` first if needed, followed by any selected flags from `shade-first-column`, `small-text`, `horizontal-rules` and `no-header`. The separate `<!-- dotlineform:table-detail title="Theorems" -->` comment can go immediately before or after it. The local editor loads the bundled markdown-it 15.0.3 block parser when Table options opens to locate the table and count its columns in unsaved text. The shared Python renderer owns generated output. Manage places its temporary resize handles on the first data row when the header is off. [Table options](../../docs-viewer/runtime/js/management/source-editor/table-options.js) · [Shared Markdown renderer](../../studio/shared/python/markdown_renderer.py)

### `GET /docs/document-link-targets`

Opening **Insert doc link** makes one Working lookup. The service reads exact ordinary Index members and direct-child named collection sources to extract identity and stored title. `docs_document_link_targets_v2` supplies `collections` and `documents`, each document with its exact target, title and portable `href`. The picker filters the loaded list by owner, title or ID. Drafts and excluded documents can be chosen. Source Save and Build handle the authored link and its relationship effects. [Picker service](../../docs-viewer/services/docs_document_link_targets.py) · [Picker UI](../../docs-viewer/runtime/js/management/source-editor/document-link.js)

### `POST /docs/source/media`

For a new native file selection, send the exact target, `media_kind` and basename as JSON to receive `media_identity`. The service checks the configured media owner and filename and supplies the identity needed for the reference. Bytes stay in the browser until Save. Presentation-only editing reuses the current identity. The separate `POST /docs/thumbnail` owns list artwork. [Identity and processing service](../../docs-viewer/services/docs_source_media_service.py) · [Thumb](Media_And_Asset_Handling.md#assigned-document-thumbnails)

## `POST /docs/source/save`

Every Save uses multipart. `metadata` contains the exact target, string `source_text` and `media` array. Each item supplies `media_kind` and boolean `replace` and `preserve_resolution`. Ordered `file_0`, `file_1` and subsequent parts supply bytes and basenames. A text-only edit sends an empty media array. Limits are 64 MiB per file and combined, 1 MiB metadata and 1 MiB multipart overhead. [Upload parsing](../../docs-viewer/services/docs_source_media_upload.py)

Candidate validation binds the parsed front matter to the fixed request identity, checks readiness and report rules, normalizes supported metadata and retains field spans. The configured owner decides collection membership. Ordinary Index placement belongs to the separate order file. Save can adopt active foreign document-owned media and use the rewritten body without parsing the front matter again. It compares the prior saved body with the final body to select media effects. Save sets `last_updated` when the normalized body, Title or Summary changes. Edits to other fields and same-identity media replacements preserve the saved timestamp when those content values stay the same. [Timestamp and identity](Document_Identity.md#date-provenance) · [Media adoption](Media_And_Asset_Handling.md#source-save-media-adoption)

The success payload includes `source_text`, `source_saved`, `generation_complete`, `publication_handoff_complete`, `committed_document` and `rebuild`, with media notes/effects where applicable. Generation uses completed source/metadata and selected effects. Search and Recent retain their saved files. Publish later applies queued effects. [Exact generation and queue](Builder.md#docs-build-flow)

### If Save stops

| Last confirmed phase | What remains to do |
| --- | --- |
| Candidate validation or preparation failed | Correct the draft, file or destination. The editor retains the unsaved text and pending Files. An error during media persistence can have completed individual file effects. |
| Source saved, generation incomplete | The returned source becomes the clean baseline. Correct the generation error and use exact **Rebuild** for the saved source. |
| Local generation complete, handoff incomplete | Inspect the reported phase and completed effects. Address the queue or Working media error at its owner. Rebuild can regenerate from saved source, but it cannot reconstruct a previous before/after media comparison. |
| Save and generation confirmed, fresh read/display failed | The saved source and generated output remain complete. Reload the reader to fetch the current document. The report or list can also show a separate projection error. |

[Media failure and queue ordering](Media_And_Asset_Handling.md#saved-ownership-and-exact-removals) · [Rebuild request](Source_Mutation_Endpoints.md#post-docsrebuild-document)

## Local links and external editor

In Manage, a complete unambiguous path under a configured Projects or Docs root can paste into ordinary prose as a portable `dlf-local:` link. Literal code, mixed text and paths outside the configured roots keep ordinary paste behaviour. Paste edits the buffer. A rendered link uses `POST /docs/open-local-target`, whose confinement and existing-file checks own Finder activation. [Paste owner](../../docs-viewer/runtime/js/management/source-editor/local-folder-links.js) · [Activation owner](../../docs-viewer/services/docs_local_links.py)

**Open in VS Code** sends the exact target and `editor: "vscode"` to `POST /docs/open-source`. The default Markdown editor action uses the configured app or the local system opener. External Markdown edits follow explicit exact Rebuild. [Local opener](../../docs-viewer/services/docs_management_source_service.py) · [External edits](Source_Organisation.md#explicit-external-edit-and-media-rebuilds)

[Design rationale](../design/Source_Editing_And_Document_Mutation.md) · [Source acceptance and follow-ons](../deliveries/Source_Editor_And_Token_Modals_Delivery.md#later-source-handoff)
