---
draft: false
doc_id: d-20260514-184303-7914e2
title: Media And Asset Handling
added_date: "2026-05-14 18:43:03"
last_updated: "2026-11-18"
summary: Document-owned media and thumbnails through Save, reuse, Delete, publication and inventory.
parent_id: d-20260424-000000-50b63f

---
# Document media and thumbnails

Docs Viewer stores document-owned media in Working and uses the same logical identities in Manage and Public. Source Save owns body media, **Edit → Thumb** owns the document's list thumbnail, confirmed document Delete owns whole-document cleanup, and Publish applies their completed selections. Catalogue Work media follows its own workflow. [Catalogue media](Catalogue_Media_View.md) · [Publish and deploy](../guide/Publish_And_Deploy.md)

For example, save a photo on a draft, then paste its reference into a publishable document and save that document. The second Save copies the photo into the destination's own folder. You can then delete the draft and its copy. The next Publish sends the destination document and its photo and applies the draft's queued removals. Each document's thumbnail is managed separately.

## Workspace Configuration And Storage

Ordinary body media uses `docs/<type>/<doc_id>/<file>` in source. Named collections use `docs/collections/<collection>/<type>/<doc_id>/<file>`. The configured Working location is `working/assets/media/workspace/<type>/` or `working/assets/media/collections/<collection>/<type>/`. Body types are `img`, `svg`, `files` and `html`. The fixed thumbnail sits directly under the owner's `thumbs/` family as `<doc_id>-thumb.webp`. The owner and document ID distinguish same-named files. Current named document-media owners are Library, Book, Context (`works`), Concepts and Moments. [Workspace configuration](../../docs-viewer/config/workspace/docs-workspace.json)

## Add A New Image Or Download

1. In Source, choose **Add image** or **Add file**, then select the native file. Review its image presentation or download label and insert the reference. The editor retains the selected File in the draft.
2. **Save** uploads the selected Files still used by the final buffer, prepares and verifies their Working writes, persists source and awaits exact document generation and publication handoff before displaying the result. Removing a new reference before its first Save leaves no body file. Discard releases unsaved Files.
3. Use **Edit → Thumb** separately when the document needs artwork in collection lists. [Assigned document thumbnails](#assigned-document-thumbnails)

Static raster inputs become WebP. The default sets the long edge to 800px, including for smaller inputs. **Preserve original resolution** keeps pixel dimensions. SVG is sanitized and stored as SVG. **Add file** keeps supported downloads such as PDF, ZIP, CSV, ordinary JSON/JSONL and supported Office files as opaque bytes. The Source upload limit is 64 MiB per file and combined, with a 1 MiB source/metadata limit and 1 MiB multipart overhead allowance. [Image processing](../../docs-viewer/services/docs_source_image_conversion.py) · [Upload limits](../../docs-viewer/services/docs_source_media_upload.py)

To reopen an image occurrence, place the caret inside its token or select the exact token, then choose **Directives → Edit image**. Turning on **Add caption** fills an empty Caption field with the current alt text. Use **Add file** from an authored file link to reopen its dialog. These dialogs let you edit presentation or select replacement bytes. Same-identity replacement counts as a change even if the source string is identical. Add image also permits replacing the normalized filename, so `Photo.jpg` and `Photo.png` can both address `photo.webp` in one document. Choose distinct basenames to keep both. Add file requires Edit to replace differing existing bytes. Identical prepared bytes are reused. Competing selected Files for one destination report a conflict. [Source media preparation](../../docs-viewer/services/docs_source_media_service.py) · [Image source form](Document_And_Catalogue_References.md#docs-owned-images)

## Source Save Media Adoption

Reuse another document's body media by copying its logical reference. **Save the destination before saving a cut in the original or deleting the original document.** Save copies each selected file from its configured Working owner to the destination's own document-ID folder and rewrites the active occurrences. It preserves the completed bytes, basename, nested relative path and authored presentation. This works across configured document owners, and **Copy to Book** uses the same rule.

The original source document need not exist. Its ready Working bytes must still be present. An identical destination file is reused, while missing source bytes or conflicting destination bytes stop preparation before writes. Current-document paths, old flat files, thumbnails, external URLs and Catalogue Work references keep their own identities. [Adoption owner](../../docs-viewer/services/docs_source_media_adoption.py) · [Copy to Book](../../docs-viewer/services/docs_book_copy.py)

## Saved Ownership And Exact Removals

Source Save compares the saved body with the prepared body in memory. Removing the last occurrence of a file in the document's own folder selects that exact file for removal. An image reused twice in the same document keeps its file until both occurrences are gone. Replacement Import compares its loaded target and candidate too. Excluding a document or making it Draft retains Working media. Newly eligible documents select their full current media for publication.

An eligible Save selects new references and changed bytes, preserving earlier pending writes still required by the saved document. Generation durably queues exact public removals before unlinking the chosen Working files. A later Save with ready bytes for the same owned identity can cancel its exact pending removal. The queue keeps writes and `removed_media` in `working/docs-publish-pending.json`. Current references and before/after differences live in the operation, with no persisted media baseline or extra by-ID media field. [Source Save](../../docs-viewer/services/docs_management_source_service.py) · [Media ownership](../../docs-viewer/services/docs_document_media_ownership.py) · [Publication queue](../../docs-viewer/services/docs_publication_queue.py)

For external source edits, exact Rebuild and CLI generation use current references. They have no previous saved body from which to reconstruct a removal. Use explicit maintenance for such edits and review leftover files manually. On a failed Save, use the reported phase and completed effects. Media can have been written before a source or generation failure. If Working unlink fails after handoff, the public removal remains queued and the remaining Working file needs manual cleanup. [Builder](Builder.md#publish-preparation)

## Document Delete Media Cleanup

Confirmed document **Delete** selects all files, including unused files, in each selected document's owned folders and its exact fixed thumbnail. For ordinary documents this includes the selected subtree. For a named collection it uses the exact document, or the selected Book batch and its affected placements. Flat body files, other documents' folders and Catalogue Work assets remain outside cleanup. Generation queues the document withdrawal and exact media removals before unlinking selected Working files. Publish handles Preview and public removal later. [Delete owner](../../docs-viewer/services/docs_management_delete.py)

## Assigned Document Thumbnails

Open **Document actions → Thumb** in a Library, Book, Context, Concepts, Moments or Texts document. **From this document** uses an image in the saved rendered document, including SVG and Catalogue images, fitted proportionally within 96 × 96 pixels. **Catalogue Works** copies the selected Work's existing thumbnail. **Apply** replaces the document's independent copy. **Delete thumbnail** removes it, saving the public removal first. Removing or replacing the originating body image leaves the thumbnail in place.

The file's presence supplies `has_thumbnail` for by-ID, collection and Selected rows. Thumb updates those exact records and their publication selections while preserving queued body-media writes. There is no `thumbnail:` source field to maintain. The browser supplies the chosen document image as canvas PNG pixels, and the service writes WebP or copies existing Catalogue thumbnail bytes. Docs Media excludes these independent list thumbnails from its Working file/reference inventory. [Thumbnail service](../../docs-viewer/services/docs_document_thumbnails.py) · [Working and R2 reports](#docs-media-inventory-report)

## Link Resolution And Delivery

Build preserves portable `docs-media:` identities in generated payloads. Manage resolves them to Working via the configured `/docs/assets/media/` owner. Public uses the configured media base, with current R2 Docs keys beneath `docs/media/`. Use logical references for managed media rather than embedding either provider URL. Static Export packages rendered media and Review resolves its package assets. [Renderer](../../docs-viewer/build/docs_builder/rendering.py) · [Workspace configuration](../../docs-viewer/config/workspace/docs-workspace.json)

```md
[Download data]([[media:docs/files/d-20261118-090000-abcdef/example.json]])
[[image:docs/collections/works/img/d-20261118-090000-abcdef/example.webp|alt=Evening%20light&placement=full&fill_width=true]]
```

**Publish** applies the selected body, media writes and removals to Preview and configured public destinations. A removal can complete without the Working file still present. The unit clears only after its selected effects complete. Missing selected inputs and transfer failures report the phase and target. Fix the cause and rerun Publish for the remaining selections. Exact R2 uploads can reuse matching objects. R2 deletions take effect during Publish, so an older deployed Pages snapshot can temporarily request media that has already been removed. Commit and push the updated `site/` snapshot before Deploy Public. [Selected publication](../../docs-viewer/services/docs_selected_publication.py) · [Publish and deploy](../guide/Publish_And_Deploy.md)

## Docs Media Inventory Report

**Docs Media → Working** opens the saved local inventory. Run/Refresh scans configured Working owners and joins saved references with existing files. A blank **Referenced by** cell marks a file with no reference in that snapshot. An absent referenced file has no inventory row. Use **Broken Links** for missing references and thumbnails. Opening the report does not rescan it, and Save, Delete and Publish do not refresh it. [Working report](../../docs-viewer/services/docs_media_metadata.py) · [Broken Links](Broken_Links.md#saved-local-report)

In Manage, select **Thumbs** to see a scrollable list of raster and SVG files from that inventory. It keeps the report's collection filter, search and sort. The **File name** column includes a preview and the Finder link. **Referenced by** links to the documents that use the image, with **Unreferenced** shown when the saved inventory has none. Select a preview to open the stored image in Content Detail. **Back** returns to the same scroll position and focuses the thumbnail. **Open in new tab** opens the same Working asset. [Working report view](../../docs-viewer/runtime/js/reports/docs-media-report.js) · [Manage image preview](../../docs-viewer/runtime/js/management/docs-viewer-managed-image-detail.js)

### R2 Orphan Report

**Docs Media → R2 → Refresh** checks document-owned R2 objects, including fixed thumbnails, against Working references (including drafts), prepared site data, the currently deployed Pages commit and selected removals already queued. It saves the findings and deployed commit for inspection. Old flat objects and Catalogue Work media are outside the report's inventory. Review findings manually, including independent sites that may link to a file. The report makes no deletions. [R2 report owner](../../docs-viewer/services/docs_r2_media_report.py)

## Import Materialization

Docs Import interprets supported document sources such as Markdown, HTML, text and trusted documents packages. It extracts supported embedded images and copies accepted package attachments into the resolved document owner. A document overwrite does not authorize overwriting a conflicting asset. For a new standalone image, diagram or file, use Source Add image/Add file. [Docs Import](Docs_Import.md) · [Import media preparation](../../docs-viewer/services/docs_import_media.py)

### SVG And Interactive Assets

Keep editable diagram source with its external owner and add the finished SVG as an image. Use [Image detail](Document_Image_Detail.md) to open a larger reading view. A role-marked HTML companion is stored in the configured `html` family. Include it explicitly, for example with `[[html-media:docs/html/<doc_id>/example.html height=546]]`, for the reader's sandboxed iframe. [Document diagrams](Document_Identity.md#diagrams)

[Design rationale](../design/Document_Media_And_Thumbnails.md) · [Migration and acceptance evidence](../deliveries/Document_Media_And_Thumbnails_Review.md)
